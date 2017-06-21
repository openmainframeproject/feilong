/*
 * IBM (C) Copyright 2016, 2016 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */

#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <netdb.h>
#include <sys/stat.h>
#include <netinet/in.h>
#include <netiucv/iucv.h>
#include <errno.h>
#include <syslog.h>
#include <string.h>

/*length define*/
#define BUFFER_SIZE 1024
#define SMALL_BUFFER_SIZE 256
#define MD5_LENGTH 32

/*ERROR defined*/
#define UNAUTHORIZED_ERROR 1
#define USAGE_ERROR 2
#define SOCKET_ERROR 4
#define CMD_EXEC_ERROR 8
#define FILE_TRANSPORT_ERROR 16
#define IUCV_FILE_NOT_EXIST 32
#define IUCV_UPGRADE_FAILED 64

/*string define*/
#define IUCV_CLIENT_VERSION "0.0.0.1"
#define FILE_TRANSPORT "iucv_file_transport"
#define READY_TO_RECEIVE "ready_to_receive"
#define FILE_SENT_OVER "FILE_SENT_OVER"
#define FILE_PATH_IUCV_SERVER "/opt/zhcp/bin/IUCV/iucvserv"
#define FILE_PATH_IUCV_FOLDER "/opt/zhcp/bin/IUCV"
#define IUCV_SERVER_NEED_UPGRADE "need_upgrade"
#define UPGRADE_NEEDED_SYSTEMD "UPGRADE_NEEDED_SYSTEMD"
#define UPGRADE_NEEDED_SYSTEMV "UPGRADE_NEEDED_SYSTEMV"

/*functions*/
int printAndLogIUCVserverReturnCodeReasonCodeoutput(int returncode, int reasoncode, char * message, int with_strerr);
int prepare_commands(char* buffer, int argc, char *argv[]);
int handle_upgrade();
int send_file_to_server(int sockfd, char *src_path);
int main(int argc, char *argv[]);
