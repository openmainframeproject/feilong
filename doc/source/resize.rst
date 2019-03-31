Resize Image to a Bigger Size
*****************************

This section provides info on how resize an image to a bigger size disk
during deploy process was performed.

The following sample describes:

1. Create a 3390 disk with 2300 cylinders.

2. Capture the disk and make it a deployable image.

3. Deploy the image (this sample use openstack) to larger number cylinders, this sample using 10G disk size, which is 14564 cylinders.

4. After deploy, the new spawned guest has 10G disk size.

5. Note only the size of last partition has been enlarged.

.. note::
  Following test result only tested on SLES12SP4 for now.

Flow of resize
--------------

Create a 3390 disk with 2300 cylinders has 2 partitions.

  .. code-block:: text

    q v dasd
    00: DASD 0100 3390 JM6013 R/W       2300 CYL ON DASD  6013 SUBCHANNEL = 0001

    # lsdasd
    Bus-ID     Status      Name      Device  Type  BlkSz  Size      Blocks
    ==============================================================================
    0.0.0100   active      dasda     94:0    ECKD  4096   1617MB    414000

    # fdasd --table /dev/dasda
    WARNING: Your DASD '/dev/dasda' is in use.
    If you proceed, you can heavily damage your system.
    If possible exit all applications using this disk
    and/or unmount it.

    reading volume label ..: VOL1
    reading vtoc ..........: ok

    Disk /dev/dasda:
      cylinders ............: 2300
      tracks per cylinder ..: 15
      blocks per track .....: 12
      bytes per block ......: 4096
      volume label .........: VOL1
      volume serial ........: 0X0100
      max partitions .......: 3

    ------------------------------- tracks -------------------------------
                 Device      start      end   length   Id  System
            /dev/dasda1          2     4267     4266    1  Linux native
            /dev/dasda2       4268    34499    30232    2  Linux native
    exiting...

    # parted /dev/dasda print
    Model: IBM S390 DASD drive (dasd)
    Disk /dev/dasda: 1696MB
    Sector size (logical/physical): 512B/4096B
    Partition Table: dasd
    Disk Flags: 

    Number  Start   End     Size    File system  Flags
     1      98.3kB  210MB   210MB   ext2
     2      210MB   1696MB  1486MB  ext4

The disk size of the guest where the sles12 sp4 image was deployed using openstack.:

  .. code-block:: text

    # openstack flavor list
    | ID                                   | Name       |   RAM | Disk | Ephemeral | VCPUs | Is Public |
    | d80df349-e277-4c08-a578-10dd8ff5ba02 | zvm-small  |  2048 |   10 |         0 |     2 | True      |

    # openstack server show s124-2part-ext4
    | flavor                              | zvm-small (d80df349-e277-4c08-a578-10dd8ff5ba02)          |

    s124-2part-ext4:~ # vmcp q v dasd
    DASD 0100 3390 JM601B R/W      14564 CYL ON DASD  601B SUBCHANNEL = 0003

    s124-2part-ext4:~ # lsdasd
    Bus-ID     Status      Name      Device  Type  BlkSz  Size      Blocks
    ==============================================================================
    0.0.0100   active      dasda     94:0    ECKD  4096   10240MB   2621520

    s124-2part-ext4:~ # fdasd --table /dev/dasda

    WARNING: Your DASD '/dev/dasda' is in use.
             If you proceed, you can heavily damage your system.
             If possible exit all applications using this disk
             and/or unmount it.

    reading volume label ..: VOL1
    reading vtoc ..........: ok

    Disk /dev/dasda:
      cylinders ............: 14564
      tracks per cylinder ..: 15
      blocks per track .....: 12
      bytes per block ......: 4096
      volume label .........: VOL1
      volume serial ........: 0X0100
      max partitions .......: 3

    ------------------------------- tracks -------------------------------
      Device      start      end   length   Id  System
      /dev/dasda1          2     4267     4266    1  Linux native
      /dev/dasda2       4268   218459   214192    2  Linux native
      exiting...

    s124-2part-ext4:~ # parted /dev/dasda print
    Model: IBM S390 DASD drive (dasd)
    Disk /dev/dasda: 10.7GB
    Sector size (logical/physical): 512B/4096B
    Partition Table: dasd
    Disk Flags:

    Number  Start   End     Size    File system  Flags
     1      98.3kB  210MB   210MB   ext2
     2      210MB   10.7GB  10.5GB  ext4

The last partition on dasda was the partition that was expanded to fill the remainder of the ECKD disk .
