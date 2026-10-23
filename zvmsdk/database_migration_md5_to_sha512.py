#!/usr/bin/env python3
"""
Database Migration Script: MD5 to SHA-512 Checksum Migration
=============================================================

This script migrates the Feilong image database from MD5 checksums to
SHA-512 checksums.

IMPORTANT NOTES:
1. This is a BREAKING CHANGE - existing MD5 checksums cannot be converted
   to SHA-512 without re-reading the original image files
2. The script automatically reads image repository location from zvmsdk.conf
3. Database backup is created automatically before any modifications
4. All image checksums are recalculated using SHA-512

Features:
---------
- Configuration-based image repository discovery
- Automatic database backup with timestamp
- SHA-512 checksum recalculation for all images
- Comprehensive validation and error handling
- Detailed migration report

Usage:
------
  python3 database_migration_md5_to_sha512.py --db-path /path/to/database.db \
      [--config /etc/zvmsdk/zvmsdk.conf]

Author: Manish Kumar (Manish.Kumar176@ibm.com)
Date: 2026-06-18
"""

import argparse
import configparser
import hashlib
import os
import shutil
import sqlite3
import sys
import time


DEFAULT_CONFIG_PATH = '/etc/zvmsdk/zvmsdk.conf'
DEFAULT_DB_PATH = '/var/lib/zvmsdk/databases/sdk_image.sqlite'
DEFAULT_IMAGE_REPOSITORY = '/var/lib/zvmsdk/images'
IMAGE_TYPE_DEPLOY = 'netboot'


def read_config(config_path):
    config = {'image_repository': DEFAULT_IMAGE_REPOSITORY}

    if not os.path.exists(config_path):
        print("Warning: Config file not found: {}".format(config_path))
        print("  Using default image repository: {}".format(
            DEFAULT_IMAGE_REPOSITORY))
        return config

    try:
        parser = configparser.ConfigParser()
        parser.read(config_path)
        if parser.has_section('image') and \
                parser.has_option('image', 'sdk_image_repository'):
            config['image_repository'] = parser.get(
                'image', 'sdk_image_repository')
            print("Read image repository from config: {}".format(
                config['image_repository']))
        else:
            print("Warning: sdk_image_repository not found in config, "
                  "using default: {}".format(DEFAULT_IMAGE_REPOSITORY))
    except Exception as e:
        print("Warning: Error reading config file: {}".format(e))
        print("  Using default image repository: {}".format(
            DEFAULT_IMAGE_REPOSITORY))

    return config


def calculate_sha512(filepath):
    sha512_hash = hashlib.sha512()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha512_hash.update(chunk)
        return sha512_hash.hexdigest()
    except Exception as e:
        print("  Error calculating checksum for {}: {}".format(filepath, e))
        return None


def backup_database(db_path):
    timestamp = int(time.time())
    backup_path = "{}.backup_{}".format(db_path, timestamp)
    try:
        shutil.copy2(db_path, backup_path)
        if os.path.exists(backup_path) and \
                os.path.getsize(backup_path) == os.path.getsize(db_path):
            print("Database backed up to: {}".format(backup_path))
            return backup_path
        else:
            print("Backup size mismatch, aborting")
            return None
    except Exception as e:
        print("Failed to backup database: {}".format(e))
        return None


def find_image_file(image_repository, imagename, imageosdistro):
    image_path = os.path.join(
        image_repository, IMAGE_TYPE_DEPLOY, imageosdistro, imagename, '0100')
    if os.path.exists(image_path):
        return image_path

    alt_path = os.path.join(
        image_repository, IMAGE_TYPE_DEPLOY, imageosdistro, imagename)
    if os.path.exists(alt_path) and os.path.isfile(alt_path):
        return alt_path

    return None


def migrate_database(db_path, image_repository):
    stats = {'total': 0, 'updated': 0, 'failed': 0, 'not_found': 0,
             'errors': []}

    print("\n" + "=" * 70)
    print("Starting Database Migration: MD5 -> SHA-512")
    print("=" * 70)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Rename md5sum column to checksum if it still exists under old name
        print("\n1. Checking database column name...")
        try:
            cursor.execute(
                "ALTER TABLE image RENAME COLUMN md5sum TO checksum")
            conn.commit()
            print("   Column renamed: md5sum -> checksum")
        except sqlite3.OperationalError as e:
            if "no such column" in str(e).lower():
                print("   Column 'checksum' already exists, skipping rename")
            else:
                raise

        print("\n2. Fetching image records...")
        cursor.execute(
            "SELECT imagename, imageosdistro, checksum FROM image")
        images = cursor.fetchall()
        stats['total'] = len(images)
        print("   Found {} image record(s)".format(stats['total']))

        if stats['total'] == 0:
            print("\nNo images found. Migration complete.")
            return stats

        print("\n3. Recalculating SHA-512 checksums...")
        print("   Image repository: {}".format(image_repository))

        for idx, (imagename, imageosdistro, old_checksum) in \
                enumerate(images, 1):
            print("\n[{}/{}] {}  ({})".format(
                idx, stats['total'], imagename, imageosdistro))

            if old_checksum and len(old_checksum) == 128:
                print("   Already SHA-512, skipping")
                stats['updated'] += 1
                continue

            image_path = find_image_file(
                image_repository, imagename, imageosdistro)
            if not image_path:
                stats['not_found'] += 1
                msg = "Image file not found for {}".format(imagename)
                stats['errors'].append(msg)
                print("   SKIP: {}".format(msg))
                continue

            print("   File: {}".format(image_path))
            new_checksum = calculate_sha512(image_path)
            if not new_checksum:
                stats['failed'] += 1
                msg = "Failed to calculate SHA-512 for {}".format(imagename)
                stats['errors'].append(msg)
                print("   FAIL: {}".format(msg))
                continue

            try:
                cursor.execute(
                    "UPDATE image SET checksum = ? WHERE imagename = ?",
                    (new_checksum, imagename))
                stats['updated'] += 1
                print("   OK: {}...{}".format(
                    new_checksum[:16], new_checksum[-16:]))
                if old_checksum:
                    algo = "MD5" if len(old_checksum) == 32 else "unknown"
                    print("   (was {}: {})".format(algo, old_checksum))
            except Exception as e:
                stats['failed'] += 1
                msg = "DB update failed for {}: {}".format(imagename, e)
                stats['errors'].append(msg)
                print("   FAIL: {}".format(msg))

        conn.commit()
        print("\nDatabase changes committed.")
        return stats

    except Exception as e:
        print("\nMigration failed: {}".format(e))
        conn.rollback()
        raise
    finally:
        conn.close()


def print_report(stats, backup_path):
    print("\n" + "=" * 70)
    print("Migration Report")
    print("=" * 70)
    if backup_path:
        print("Backup:  {}".format(backup_path))
    print("Total:   {}".format(stats['total']))
    print("Updated: {}".format(stats['updated']))
    print("Skipped: {}".format(stats['not_found']))
    print("Failed:  {}".format(stats['failed']))

    if stats['errors']:
        print("\nErrors:")
        for err in stats['errors'][:10]:
            print("  - {}".format(err))
        if len(stats['errors']) > 10:
            print("  ... and {} more".format(len(stats['errors']) - 10))

    print("=" * 70)
    if stats['failed'] == 0 and stats['not_found'] == 0:
        print("Migration completed successfully.")
    elif stats['updated'] > 0:
        print("Migration completed with warnings — review errors above.")
    else:
        print("Migration failed — no images updated.")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='Migrate Feilong image database from MD5 to SHA-512',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__)
    parser.add_argument('--db-path', type=str, default=DEFAULT_DB_PATH,
                        help='Path to sdk_image.sqlite (default: {})'.format(
                            DEFAULT_DB_PATH))
    parser.add_argument('--config', type=str, default=DEFAULT_CONFIG_PATH,
                        help='Path to zvmsdk.conf (default: {})'.format(
                            DEFAULT_CONFIG_PATH))
    parser.add_argument('--no-backup', action='store_true',
                        help='Skip database backup (NOT RECOMMENDED)')
    parser.add_argument('--image-repository', type=str,
                        help='Override image repository path from config')
    args = parser.parse_args()

    if not os.path.exists(args.db_path):
        print("Error: Database not found: {}".format(args.db_path))
        return 1

    print("=" * 70)
    print("Feilong Database Migration: MD5 -> SHA-512")
    print("=" * 70)
    print("Database: {}".format(args.db_path))
    print("Config:   {}".format(args.config))

    if args.image_repository:
        image_repository = args.image_repository
    else:
        config = read_config(args.config)
        image_repository = config['image_repository']

    if not os.path.exists(image_repository):
        print("\nWarning: Image repository not found: {}".format(
            image_repository))
        response = input("Continue anyway? (yes/no): ")
        if response.lower() != 'yes':
            print("Migration cancelled.")
            return 1

    backup_path = None
    if not args.no_backup:
        print("\nCreating database backup...")
        backup_path = backup_database(args.db_path)
        if not backup_path:
            print("Backup failed. Aborting. Use --no-backup to skip.")
            return 1
    else:
        print("\nWARNING: Running without backup!")
        response = input("Are you sure? (yes/no): ")
        if response.lower() != 'yes':
            print("Migration cancelled.")
            return 1

    try:
        stats = migrate_database(args.db_path, image_repository)
        print_report(stats, backup_path)
        if stats['updated'] == stats['total']:
            return 0
        elif stats['updated'] > 0:
            return 2
        else:
            return 1
    except Exception as e:
        print("\nFatal error: {}".format(e))
        if backup_path:
            print("To restore: cp {} {}".format(backup_path, args.db_path))
        return 1


if __name__ == '__main__':
    sys.exit(main())
