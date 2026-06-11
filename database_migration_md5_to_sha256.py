#!/usr/bin/env python3
"""
Database Migration Script: MD5 to SHA-256 Checksum Migration
==============================================================

This script migrates the Feilong image database from MD5 to SHA-256 checksums.

IMPORTANT NOTES:
1. This is a BREAKING CHANGE - existing MD5 checksums cannot be converted to SHA-256
2. The script automatically reads image repository location from zvmsdk.conf
3. Database backup is created automatically before any modifications
4. All image checksums are recalculated using SHA-256

Features:
---------
- Configuration-based image repository discovery
- Automatic database backup with timestamp
- SHA-256 checksum recalculation for all images
- Comprehensive validation and error handling
- Detailed migration report

Usage:
------
  python3 database_migration_md5_to_sha256.py --db-path /path/to/database.db [--config /etc/zvmsdk/zvmsdk.conf]

Author: Manish Kumar (in.manishkr@gmail.com)
Date: 2026-06-09
"""

import argparse
import configparser
import hashlib
import os
import sqlite3
import sys
import time


# Default configuration values
DEFAULT_CONFIG_PATH = '/etc/zvmsdk/zvmsdk.conf'
DEFAULT_DB_PATH = '/var/lib/zvmsdk/databases/sdk_image.sqlite'
DEFAULT_IMAGE_REPOSITORY = '/var/lib/zvmsdk/images'
IMAGE_TYPE_DEPLOY = 'netboot'


def read_config(config_path):
    """
    Read zvmsdk configuration file and extract image repository path

    Args:
        config_path: Path to zvmsdk.conf file

    Returns:
        dict: Configuration values including image_repository
    """
    config = {
        'image_repository': DEFAULT_IMAGE_REPOSITORY
    }

    if not os.path.exists(config_path):
        print("⚠ Warning: Config file not found: {}".format(config_path))
        print("  Using default image repository: {}".format(
            DEFAULT_IMAGE_REPOSITORY))
        return config

    try:
        parser = configparser.ConfigParser()
        parser.read(config_path)

        # Read sdk_image_repository from [image] section
        if parser.has_section('image') and \
           parser.has_option('image', 'sdk_image_repository'):
            config['image_repository'] = parser.get(
                'image', 'sdk_image_repository')
            print("✓ Read image repository from config: {}".format(
                config['image_repository']))
        else:
            print("⚠ Warning: sdk_image_repository not found in config")
            print("  Using default: {}".format(DEFAULT_IMAGE_REPOSITORY))

    except Exception as e:
        print("⚠ Warning: Error reading config file: {}".format(e))
        print("  Using default image repository: {}".format(
            DEFAULT_IMAGE_REPOSITORY))

    return config


def calculate_sha256(filepath):
    """
    Calculate SHA-256 checksum of a file

    Args:
        filepath: Path to the file

    Returns:
        str: SHA-256 checksum in hexadecimal format, or None on error
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            # Read file in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"  ✗ Error calculating checksum for {filepath}: {e}")
        return None


def backup_database(db_path):
    """
    Create a timestamped backup of the database

    Args:
        db_path: Path to the database file

    Returns:
        str: Path to backup file, or None on error
    """
    timestamp = int(time.time())
    backup_path = "{}.backup_{}".format(db_path, timestamp)

    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print("✓ Database backed up to: {}".format(backup_path))

        # Verify backup was created successfully
        if os.path.exists(backup_path):
            backup_size = os.path.getsize(backup_path)
            original_size = os.path.getsize(db_path)
            if backup_size == original_size:
                print("✓ Backup verified: {} bytes".format(backup_size))
                return backup_path
            else:
                print("✗ Backup size mismatch: {} vs {}".format(
                    backup_size, original_size))
                return None
        else:
            print("✗ Backup file not found after creation")
            return None

    except Exception as e:
        print("✗ Failed to backup database: {}".format(e))
        return None


def find_image_file(image_repository, imagename, imageosdistro):
    """
    Locate the image file in the repository

    Args:
        image_repository: Base path to image repository
        imagename: Name of the image
        imageosdistro: OS distribution of the image

    Returns:
        str: Full path to image file, or None if not found
    """
    # Standard image path structure:
    # repository/netboot/os_version/image_name/0100
    image_path = os.path.join(
        image_repository,
        IMAGE_TYPE_DEPLOY,
        imageosdistro,
        imagename,
        '0100'
    )

    if os.path.exists(image_path):
        return image_path

    # Try alternative path without '0100' suffix
    alt_path = os.path.join(
        image_repository,
        IMAGE_TYPE_DEPLOY,
        imageosdistro,
        imagename
    )

    if os.path.exists(alt_path) and os.path.isfile(alt_path):
        return alt_path

    return None


def migrate_database(db_path, image_repository):
    """
    Perform the complete database migration

    Args:
        db_path: Path to the database file
        image_repository: Path to the image repository

    Returns:
        dict: Migration statistics
    """
    stats = {
        'total': 0,
        'updated': 0,
        'failed': 0,
        'not_found': 0,
        'errors': []
    }

    print("\n" + "=" * 70)
    print("Starting Database Migration")
    print("=" * 70)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Step 1: Rename the md5sum column to checksum
        print("\n1. Renaming database column: md5sum → checksum")
        try:
            cursor.execute("ALTER TABLE image RENAME COLUMN md5sum TO checksum")
            conn.commit()
            print("✓ Column renamed successfully")
        except sqlite3.OperationalError as e:
            if "no such column" in str(e).lower():
                print("✓ Column already renamed (checksum exists)")
            else:
                raise

        # Step 2: Get all image records
        print("\n2. Fetching image records from database...")
        cursor.execute("SELECT imagename, imageosdistro, checksum FROM image")
        images = cursor.fetchall()
        stats['total'] = len(images)
        print("✓ Found {} image records".format(stats['total']))

        if stats['total'] == 0:
            print("\n⚠ No images found in database. Migration complete.")
            return stats

        # Step 3: Recalculate checksums for each image
        print("\n3. Recalculating SHA-256 checksums...")
        print("   Image repository: {}".format(image_repository))
        print()

        for idx, (imagename, imageosdistro, old_checksum) in \
                enumerate(images, 1):
            print("[{}/{}] Processing: {} ({})".format(
                idx, stats['total'], imagename, imageosdistro))

            # Find the image file
            image_path = find_image_file(
                image_repository, imagename, imageosdistro)

            if not image_path:
                stats['not_found'] += 1
                error_msg = "Image file not found for {}".format(imagename)
                stats['errors'].append(error_msg)
                print("  ✗ {}".format(error_msg))
                continue

            print("  → Found: {}".format(image_path))

            # Calculate new SHA-256 checksum
            new_checksum = calculate_sha256(image_path)

            if not new_checksum:
                stats['failed'] += 1
                error_msg = "Failed to calculate checksum for {}".format(
                    imagename)
                stats['errors'].append(error_msg)
                print("  ✗ {}".format(error_msg))
                continue

            # Update database with new checksum
            try:
                cursor.execute(
                    "UPDATE image SET checksum = ? WHERE imagename = ?",
                    (new_checksum, imagename)
                )
                stats['updated'] += 1
                print("  ✓ Updated checksum: {}...{}".format(
                    new_checksum[:16], new_checksum[-16:]))

                # Show old vs new for comparison
                if old_checksum and len(old_checksum) == 32:
                    print("    (was MD5: {})".format(old_checksum))

            except Exception as e:
                stats['failed'] += 1
                error_msg = "Database update failed for {}: {}".format(
                    imagename, e)
                stats['errors'].append(error_msg)
                print("  ✗ {}".format(error_msg))

        # Commit all changes
        conn.commit()
        print("\n✓ Database changes committed")

        return stats

    except Exception as e:
        print("\n✗ Migration failed: {}".format(e))
        conn.rollback()
        raise
    finally:
        conn.close()


def print_migration_report(stats, backup_path):
    """
    Print a comprehensive migration report

    Args:
        stats: Migration statistics dictionary
        backup_path: Path to the database backup
    """
    print("\n" + "=" * 70)
    print("Migration Report")
    print("=" * 70)

    print("\nDatabase Backup:")
    print("  Location: {}".format(backup_path))

    print("\nMigration Statistics:")
    print("  Total images:        {}".format(stats['total']))
    print("  Successfully updated: {}".format(stats['updated']))
    print("  Files not found:     {}".format(stats['not_found']))
    print("  Failed updates:      {}".format(stats['failed']))

    success_rate = (stats['updated'] / stats['total'] * 100) \
        if stats['total'] > 0 else 0
    print("\n  Success rate:        {:.1f}%".format(success_rate))

    if stats['errors']:
        print("\nErrors encountered ({}):".format(len(stats['errors'])))
        # Show first 10 errors
        for i, error in enumerate(stats['errors'][:10], 1):
            print("  {}. {}".format(i, error))
        if len(stats['errors']) > 10:
            print("  ... and {} more errors".format(
                len(stats['errors']) - 10))

    print("\n" + "=" * 70)

    if stats['updated'] == stats['total']:
        print("✓ Migration completed successfully!")
        print("  All image checksums have been updated to SHA-256")
    elif stats['updated'] > 0:
        print("⚠ Migration completed with warnings")
        print("  {} images updated, {} failed".format(
            stats['updated'], stats['failed'] + stats['not_found']))
        print("  Review the errors above and manually fix failed images")
    else:
        print("✗ Migration failed")
        print("  No images were updated. Check errors above")

    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='Migrate Feilong image database from MD5 to SHA-256',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--db-path',
        type=str,
        default=DEFAULT_DB_PATH,
        help='Path to the SQLite database file (default: {})'.format(
            DEFAULT_DB_PATH)
    )
    parser.add_argument(
        '--config',
        type=str,
        default=DEFAULT_CONFIG_PATH,
        help=f'Path to zvmsdk.conf file (default: {DEFAULT_CONFIG_PATH})'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip database backup (NOT RECOMMENDED)'
    )
    parser.add_argument(
        '--image-repository',
        type=str,
        help='Override image repository path from config'
    )

    args = parser.parse_args()

    # Validate database path
    if not os.path.exists(args.db_path):
        print("✗ Error: Database file not found: {}".format(args.db_path))
        print("  Expected default location: {}".format(DEFAULT_DB_PATH))
        return 1

    print("=" * 70)
    print("Feilong Database Migration: MD5 to SHA-256")
    print("=" * 70)
    print("Database: {}".format(args.db_path))
    print("Config:   {}".format(args.config))

    # Read configuration
    if args.image_repository:
        print("\nUsing override image repository: {}".format(
            args.image_repository))
        image_repository = args.image_repository
    else:
        config = read_config(args.config)
        image_repository = config['image_repository']

    # Verify image repository exists
    if not os.path.exists(image_repository):
        print("\n⚠ Warning: Image repository not found: {}".format(
            image_repository))
        response = input("Continue anyway? (yes/no): ")
        if response.lower() != 'yes':
            print("Migration cancelled")
            return 1

    # Backup database
    backup_path = None
    if not args.no_backup:
        print("\nCreating database backup...")
        backup_path = backup_database(args.db_path)
        if not backup_path:
            print("\n✗ Backup failed. Aborting migration for safety.")
            print("  Use --no-backup to skip backup (not recommended)")
            return 1
    else:
        print("\n⚠ WARNING: Running without backup!")
        response = input("Are you sure? (yes/no): ")
        if response.lower() != 'yes':
            print("Migration cancelled")
            return 1

    # Perform migration
    try:
        stats = migrate_database(args.db_path, image_repository)
        print_migration_report(stats, backup_path)

        # Return appropriate exit code
        if stats['updated'] == stats['total']:
            return 0  # Complete success
        elif stats['updated'] > 0:
            return 2  # Partial success
        else:
            return 1  # Failure

    except Exception as e:
        print("\n✗ Fatal error during migration: {}".format(e))
        if backup_path:
            print("\nTo restore from backup:")
            print("  cp {} {}".format(backup_path, args.db_path))
        return 1


if __name__ == '__main__':
    sys.exit(main())
