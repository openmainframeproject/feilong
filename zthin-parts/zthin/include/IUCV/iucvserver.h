/*
 * Copyright Contributors to the Feilong Project.
 * SPDX-License-Identifier: Apache-2.0
 *
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
#include <errno.h>
#include <netdb.h>
#include <sys/stat.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <netiucv/iucv.h>
#include <syslog.h>
#include <string.h>
#include <pthread.h>

/*size define*/
#define SOCKET_TIMEOUT   20
#define BUFFER_SIZE 1024

/*string define*/

#define PATH_FOR_AUTHORIZED_USERID "/etc/iucv_authorized_userid"
//#define PATH_FOR_IUCV_SERVER "/usr/bin/iucvserver"
//#define PATH_FOR_IUCV_SERVER_SERVICE "/etc/init.d/iucvserverd"

#define IUCV_SERVER_VERSION "0.0.0.1"
#define FILE_TRANSPORT "iucv_file_transport"
#define PIPE_FIFO_NAME "pipe_fifo"
#define READY_TO_RECEIVE "ready_to_receive"
#define FILE_SENT_OVER "FILE_SENT_OVER"
#define IUCV_SERVER_NEED_UPGRADE "need_upgrade"
#define IUCV_SERV_PATH "/usr/bin/iucvserv"
#define IUCV_SERD_SYSTEMV_PATH "/etc/init.d/iucvserd"
#define IUCV_SERD_SYSTEMD_PATH_RH7_UB "/lib/systemd/system/iucvserd.service"
#define IUCV_SERD_SYSTEMD_PATH_SL12 "/usr/lib/systemd/system/iucvserd.service"
#define UPGRADE_NEEDED_SYSTEMD "UPGRADE_NEEDED_SYSTEMD"
#define UPGRADE_NEEDED_SYSTEMV "UPGRADE_NEEDED_SYSTEMV"
#define IUCV_UPGRADE_PATH "/var/lib/iucvupgrade.sh"

/*ERROR defined*/
#define UNAUTHORIZED_ERROR 1
#define CLIENT_USAGE_ERROR 2
#define FILE_TRANSPORT_ERROR 16
#define IUCV_UPGRADE_ERROR 64

/*struct*/
struct lnx_dist{
    char name[32];
    int version;
};
/*functions*/
int check_client_authorization(int newsockfd, char *req_userid);
int receive_file_from_client(int newsockfd, char *des_path);
int handle_upgrade(int sockfd, int newsockfd);
int server_socket();
int main(int argc,char* argv[]);
