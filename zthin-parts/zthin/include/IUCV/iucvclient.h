/*
 * Copyright 2017 IBM Corporation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
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
#define FILE_PATH_IUCV_SERVER "/opt/zthin/bin/IUCV/iucvserv"
#define FILE_PATH_IUCV_FOLDER "/opt/zthin/bin/IUCV"
#define FILE_PATH_IUCV_AUTH_USERID "/etc/zvmsdk/iucv_authorized_userid"
#define IUCV_SERVER_NEED_UPGRADE "need_upgrade"
#define UPGRADE_NEEDED_SYSTEMD "UPGRADE_NEEDED_SYSTEMD"
#define UPGRADE_NEEDED_SYSTEMV "UPGRADE_NEEDED_SYSTEMV"

/*functions*/
int printAndLogIUCVserverReturnCodeReasonCodeoutput(int returncode, int reasoncode, char * message, int with_strerr);
int prepare_commands(char* buffer, int argc, char *argv[]);
int handle_upgrade();
int send_file_to_server(int sockfd, char *src_path);
int main(int argc, char *argv[]);
