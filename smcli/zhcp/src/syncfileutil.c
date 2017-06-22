/**
 * IBM (C) Copyright 2017 Apache License Version 2.0
 * http://www.apache.org/licenses/LICENSE-2.0
 */

#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>

/**
 * sync a file (device file) to disk
 *
 * @param $1: The file name to be synced
 *
 * @return 0 Successfully synced
 *         -1 no file name inputed
 *         -2 input file can't be found
 */
int main(int argc, char* argv[])
{
    int fd;
    if (argc != 2)
    {
        printf("please input a file to sync\n");
        return -1;
    }

    fd = open(argv[1], O_RDWR);
    if (fd < 0)
    {
        printf("can't open %s\n", argv[1]);
        return -2;
    }

    fsync(fd);

    close(fd);

    return 0;
}
