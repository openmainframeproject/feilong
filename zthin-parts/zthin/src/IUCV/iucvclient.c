/*
 * * Copyright 2017 IBM Corporation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#include "../IUCV/iucvclient.h"


/* print log to console and save it to /var/log/messages.
* @param $1: the return value for client.
*        $2: the reason for the details.
*        $3: results.
*        $4: whether to print error reason which is get from errno. 0 not print info, 1 print the error info.
*
* @return returncode:
*/
int printAndLogIUCVserverReturnCodeReasonCodeoutput(int returncode, int reasoncode, char * message, int with_strerr)
{
    if (returncode || reasoncode)
    {
        syslog(LOG_ERR, "ERROR: %s  Return code %d, Reason code %d", message, returncode, reasoncode);
        if (reasoncode && with_strerr)
        {
            printf("ERROR: %s\n%s\nReturn code %d, Reason code %d.\n", message, strerror(reasoncode), returncode, reasoncode);
            return returncode;
        }
        printf("ERROR: %s\nReturn code %d, Reason code %d.\n", message, returncode, reasoncode);
    }
    else
    {
        syslog(LOG_INFO,"%s", message);
        printf("%s", message);
    }
    return returncode;
}


/* Pre-check the environment good to execute the command before setup socket connection.
*  @param $1: get from main.
*  @return  0 check result successful. 
*          -1 check result failed.
*/
int pre_checks(char *argv[])
{
    char buffer[SMALL_BUFFER_SIZE];
    FILE *fp;
    int i = 0;
    /* need to check whether iucvserv existed, we need to check its version.*/
    /* Check whether the IUCV server exist */
    if ((fp = fopen(FILE_PATH_IUCV_SERVER,"r")) == NULL)
    {
        sprintf(buffer, "ERROR: can't find IUCV server in path %s, please copy file to the path and try again.", FILE_PATH_IUCV_SERVER);
        printAndLogIUCVserverReturnCodeReasonCodeoutput(IUCV_FILE_NOT_EXIST, errno, buffer, 1);
        return IUCV_FILE_NOT_EXIST;
    }
    close(fp);
    fp = NULL;
    /* if command is transport file, need to check whether the source path is valid*/
    if (strcmp(argv[2], FILE_TRANSPORT)==0)
    {
        if ((fp = fopen(argv[3], "rb"))==NULL)
        {
            sprintf(buffer, "ERROR: In pre_check, failed to open file %s for read.", argv[3]);
            printAndLogIUCVserverReturnCodeReasonCodeoutput(FILE_TRANSPORT_ERROR, errno, buffer, 1);
            return FILE_TRANSPORT_ERROR;
        }
    }
    close(fp);
    fp = NULL;
    return 0;
}


/* Prepare the commands which will sent to server.
*  the command format should be:
*  client_userid clientside_server_version command [parameters]
*  @param $1: output parm which is used to get the commands.
*         $2: get from main.
*         $3: get from main.
*
*  @return 0: successfully.
           errno:
*/
int prepare_commands(char* buffer, int argc, char *argv[])
{
    /* 1. Prepare client_userid. */
    /* Now ask for a message from the user, this message will be read by server */
    /* Need to add userid to make authorized, if not a opencloud user, request will be refused */
    char user_buf[32], err_buf[256];
    int i = 0;

    bzero(buffer,BUFFER_SIZE);

    /* try to re-use previous iucv authorized userid at first */
    FILE *fp = fopen(FILE_PATH_IUCV_AUTH_USERID, "r");
    if (fp != NULL) {
        fgets(user_buf, 9, fp);
        strcpy(buffer, user_buf);
        fclose(fp);
        fp = NULL;
    }
    else
    {
        fp = popen("sudo vmcp q userid", "r");
        if (fgets(user_buf,sizeof(user_buf),fp) != NULL)
        {
            strcpy(buffer, strtok(user_buf," "));
            pclose(fp);
            fp = NULL;
        }
        else
        {
            printAndLogIUCVserverReturnCodeReasonCodeoutput(UNAUTHORIZED_ERROR, errno,"ERROR: failed to get userid:", 0);
            pclose(fp);
            fp = NULL;
            return UNAUTHORIZED_ERROR;
        }
    }

    /* 2. Get the IUCV server's version which exists on zThin
       This is used for IUCV server's upgrade, when the server's version which installed on VM is lower,
       upgrade is needed.
    */
    /* Check whether the IUCV server exist */
    if (fopen(FILE_PATH_IUCV_SERVER,"r") == NULL)
    {
        sprintf(err_buf, "ERROR: can't find IUCV server in path %s, please copy file to the path and try again.", FILE_PATH_IUCV_SERVER);
        printAndLogIUCVserverReturnCodeReasonCodeoutput(IUCV_FILE_NOT_EXIST, errno, err_buf, 1);
        return IUCV_FILE_NOT_EXIST;
    }
    char tmp_buf[BUFFER_SIZE];
    sprintf(tmp_buf, "%s --version", FILE_PATH_IUCV_SERVER);
    fp = popen(tmp_buf, "r");
    if (fgets(tmp_buf, sizeof(tmp_buf), fp) != NULL)
    {
        //printf(tmp_buf);
        strcat(buffer, " ");
        strcat(buffer, tmp_buf);
        buffer[strlen(buffer)-1]='\0';//command has an enter;
    }
    pclose(fp);
    fp = NULL;

    /* 3.commands */
    for (i = 2; i < argc;i++)
    {
        /*if command is transport file, the source path is useless*/
        if (strcmp(argv[2], FILE_TRANSPORT)==0)
        {
            if (i == 3)
            {
                continue;
            }
        }
        strcat(buffer, " ");
        strcat(buffer, argv[i]);
    }
    syslog(LOG_INFO, "command=%s\n",buffer);
    return 0;
}

/* When server's version is lower than client side server version,
   upgrade is needed.
*  @param $1 the socket which is used to make IUCV communication to server.
*         $2 the upgrade signal
*
*  @return 0: successfully.
*/
int handle_upgrade(int sockfd, char* signal_buf)
{
    char src_path[BUFFER_SIZE], recv_buf[BUFFER_SIZE];
    int returncode;
    /* Send the upgrade files to server.*/
    syslog(LOG_INFO,"Target system service use %s, Send the upgrade files to server.\n", signal_buf);
    // iucvserv
    recv(sockfd, recv_buf, SMALL_BUFFER_SIZE, 0);
    if ((returncode = send_file_to_server(sockfd, FILE_PATH_IUCV_SERVER))!= 0)
    {
        printf("ERROR: Upgrade failed! Failed to send iucvserv file");
        return returncode;
    }
    if (strcmp(signal_buf, UPGRADE_NEEDED_SYSTEMV)==0)
    {
        // iucvserd
        sprintf(src_path, "%s/%s", FILE_PATH_IUCV_FOLDER, "iucvserd");
        recv(sockfd, recv_buf, SMALL_BUFFER_SIZE, 0);
        if ((returncode = send_file_to_server(sockfd, src_path))!= 0)
        {
            printf("ERROR: Upgrade failed! Failed to send iucvserd file");
            return returncode;
        }
    }
    if (strcmp(signal_buf, UPGRADE_NEEDED_SYSTEMD)==0)
    {
        // iucvserd
        sprintf(src_path, "%s/%s", FILE_PATH_IUCV_FOLDER, "iucvserd.service");
        recv(sockfd, recv_buf, SMALL_BUFFER_SIZE, 0);
        if ((returncode = send_file_to_server(sockfd, src_path))!= 0)
        {
            printf("ERROR: Upgrade failed! Failed to send iucvserd.service file");
            return returncode;
        }
    }
    // iucvupgrade.sh
    sprintf(src_path, "%s/%s", FILE_PATH_IUCV_FOLDER, "iucvupgrade.sh");
    recv(sockfd, recv_buf, SMALL_BUFFER_SIZE, 0);
    if ((returncode = send_file_to_server(sockfd, src_path))!= 0)
    {
        printf("ERROR: Upgrade failed! Failed to send iucvupgrade.sh file");
        return returncode;
    }
    syslog(LOG_INFO, "Successfully to send the upgrade files to server.\n");
    return 0;
}

/*  Get file mode.
 *  @param $1: file name
 * @return  file access.
 */
int get_file_mod(char *fileName)
{
    struct stat fileInfo;
    if (stat(fileName, &fileInfo) < 0){
          return 0;
    }
    unsigned int mask = 0000777;
    unsigned int access = mask & fileInfo.st_mode;
    //printf("%o\n", access);
    return access;
}

/* Send specified file (NOT support to transport folder) to IUCV server.
* @param $1: the socket which is used to make IUCV communication to server.
*        $2: the path for the file which need to be sent.
*
* @return 0: if file transport is successful.
*         FILE_TRANSPORT_ERROR: if file transport is failed.
*         errno: if there are any socket connection error.
*/
int send_file_to_server(int sockfd, char *src_path)
{
    char buffer[SMALL_BUFFER_SIZE],info[SMALL_BUFFER_SIZE];
    char *file_buf;
    FILE *fp = NULL;
    int n_time = 0, n = 0;
    size_t len = n_time = n = 0;

    //printf("Will send file %s to IUCV server.\n", src_path);
    syslog(LOG_INFO, "Will send file %s to IUCV server.\n", src_path);
    file_buf = (char *) malloc(BUFFER_SIZE);
    if ((fp = fopen(src_path, "rb"))==NULL)
    {
        sprintf(buffer, "ERROR: Failed to open file %s for read.", src_path);
        printAndLogIUCVserverReturnCodeReasonCodeoutput(FILE_TRANSPORT_ERROR, errno, buffer, 1);
        free(file_buf);
        file_buf = NULL;
        return FILE_TRANSPORT_ERROR;
    }
    else
    {
        //printf("Start to read file\n");
        syslog(LOG_INFO, "Start to read file\n");
        while (!feof(fp))
        {
            bzero(file_buf, BUFFER_SIZE);
            len = fread(file_buf, sizeof(char), BUFFER_SIZE, fp);
            if ((len = send(sockfd, file_buf, len, 0)) < 0)
            {
                 printAndLogIUCVserverReturnCodeReasonCodeoutput(SOCKET_ERROR, errno, "ERROR: Failed to send file to serer.", 1);
                 free(file_buf);
                 file_buf = NULL;
                 fclose(fp);
                 fp = NULL;
                 return SOCKET_ERROR;
            }
        }
        if (fclose(fp) != 0)
        {
            syslog(LOG_ERR, "ERROR: Fail to close sent file after reading: %s.\n",strerror(errno));
        }
        fp = NULL;
        free(file_buf);
        file_buf = NULL;

        /* send send_over signal + md5 + file_mod*/
        sprintf(buffer, "md5sum %s",src_path);
        if ((fp = popen(buffer, "r"))==NULL)
        {
            printAndLogIUCVserverReturnCodeReasonCodeoutput(FILE_TRANSPORT_ERROR, errno,"ERROR: Failed to get md5 for file.", 1);
            strcpy(buffer, "FILE_SENT_OVER");
            send(sockfd, buffer, strlen(buffer) + 1, 0);
        }
        else
        {
            bzero(buffer,SMALL_BUFFER_SIZE);
            if (fgets(buffer, sizeof(buffer), fp) != NULL)
            {
                buffer[MD5_LENGTH]='\0';
                sprintf(info,"FILE_SENT_OVER %s %o", buffer, get_file_mod(src_path));
            }
            send(sockfd, info, strlen(info) + 1, 0);
        }
        pclose(fp);
        fp = NULL;
        /* After finish sending file, wait for the message from server to get the file transport result */
        //printf("Finish sending file, just need to wait for the server's receive respond\n");
        syslog(LOG_INFO, "Finish sending file, just need to wait for the server's receive respond\n");
        bzero(buffer,SMALL_BUFFER_SIZE);
        recv(sockfd, buffer, SMALL_BUFFER_SIZE, 0);
        if (strcmp(buffer, "FILE_RECEIVED_OK")==0)
        {
            sprintf(buffer,"Transport file %s successfully.\n", src_path);
            //printAndLogIUCVserverReturnCodeReasonCodeoutput(0, 0, buffer, 0);
            syslog(LOG_INFO, buffer);
            return 0;
        }
        else
        {
            sprintf(buffer,"ERROR: Transport file %s failed. %s.", src_path, buffer);
            printAndLogIUCVserverReturnCodeReasonCodeoutput(FILE_TRANSPORT_ERROR, FILE_TRANSPORT_ERROR, buffer, 0);
            return FILE_TRANSPORT_ERROR;
        }
    }
    return 0;
}


/* main function.
* @param $1: the number of param.
*        $2: the params which is input.
*
* @return 0: command are executed successfully.
*         1: UNAUTHORIZED_ERROR
*         2: USAGE_ERROR
*         4: SOCKET_ERROR
*         8: CMD_EXEC_ERROR
*        16: FILE_TRANSPORT_ERROR
*        32: IUCV_FILE_NOT_EXIST
*        -1: Usage:
*/
int main(int argc, char *argv[])
{
    int sockfd, portno, n, i;
    struct sockaddr_iucv serv_addr;
    int flags;
    char buffer[BUFFER_SIZE],result[BUFFER_SIZE],cmd_rc[8];
    int returncode = 0;
    char* pos = NULL;
    int need_reconnect = 1;
    int check_upgrade_version = 0;

    /* Print the log to console and /var/log/messages */
    openlog(NULL, LOG_CONS, 0);
    if (argc < 3)
    {
        if (argc==2 && strcmp(argv[1],"--version")==0)
        {
            printAndLogIUCVserverReturnCodeReasonCodeoutput(0, 0, IUCV_CLIENT_VERSION, 0);
            return 0;
        }
        bzero(buffer,BUFFER_SIZE);
        sprintf(buffer, "Usage:\niucvclnt [--version]\n\
                              iucvclnt server_userid %s src_file_path/filename dst_file_path/filename\n\
                              iucvclnt server_userid command [command_parm2, ...]",
                      FILE_TRANSPORT);
        /*(to-do) add pars password to not show it in log file.
        sprintf(buffer, "Usage:\niucvclnt [--version]\n\
                              iucvclnt server_userid %s src_file_path dst_file_path\n\
                              iucvclnt server_userid command [command_parm2, pw:passwd_parm, ...]\n \
                      Pw:passwd_parm is used for password in command, will not show passwd in log file\n",
                      FILE_TRANSPORT);
        */
        printAndLogIUCVserverReturnCodeReasonCodeoutput(USAGE_ERROR, 1, buffer, 0);
        return -1;
    }
    if (pre_checks(argv) != 0)
    {
        return -1;
    }
    while (need_reconnect == 1)
    {
        need_reconnect = 0;
        /* Create a socket point */
        sockfd = socket(AF_IUCV, SOCK_STREAM, IPPROTO_IP);
        if (sockfd < 0)
        {
            printAndLogIUCVserverReturnCodeReasonCodeoutput(SOCKET_ERROR, errno, "ERROR opening socket:", 1);
            close(sockfd);
            return SOCKET_ERROR;
        }
        bzero((char *) &serv_addr, sizeof(serv_addr));
        serv_addr.siucv_family = AF_IUCV;
        memset(&serv_addr.siucv_user_id, ' ', 8);
        memcpy(&serv_addr.siucv_user_id, argv[1], strlen(argv[1]));
        memcpy(&serv_addr.siucv_name, "OPNCLOUD", 8);

         /* Now connect to the server */
        if (connect(sockfd, (struct sockaddr*)&serv_addr, sizeof(serv_addr)) < 0)
        {
            printAndLogIUCVserverReturnCodeReasonCodeoutput(SOCKET_ERROR, errno, "ERROR connecting socket:", 1);
            close(sockfd);
            return SOCKET_ERROR;
        }
        if ((returncode = prepare_commands(buffer, argc, argv)) != 0)
        {
            close(sockfd);
            return returncode;
        }
        syslog(LOG_INFO, "command=%s\n",buffer);
        /* Send messages to server. */
        n = send(sockfd, buffer, strlen(buffer)+1,0);
        if (n < 0) {
            printAndLogIUCVserverReturnCodeReasonCodeoutput(SOCKET_ERROR, errno, "ERROR writing to socket:", 1);
            close(sockfd);
            return SOCKET_ERROR;
        }
        /* Receive messages from server, to determine what should be done next */
        bzero(buffer,BUFFER_SIZE);
        while (n = recv(sockfd, buffer, BUFFER_SIZE,0) > 0)
        {
            //printf("result =%s\n",buffer);
            /* Check the result is NOT_AUTHORIZED_USERID */
            if (strncmp(buffer, "UNAUTHORIZED_ERROR", strlen("UNAUTHORIZED_ERROR")) == 0)
            {
                bzero(result, 8);
                strcpy(result, strtok(buffer, "#"));
                bzero(cmd_rc, 8);
                strcpy(cmd_rc, strtok(NULL,"#"));
                returncode = (atoi(cmd_rc) == UNAUTHORIZED_ERROR) ? 0 : atoi(cmd_rc);
                printAndLogIUCVserverReturnCodeReasonCodeoutput(UNAUTHORIZED_ERROR, returncode, buffer, 0);
                close(sockfd);
                return UNAUTHORIZED_ERROR;
            }
            /* if upgrade is needed */
            if ((strcmp(buffer, UPGRADE_NEEDED_SYSTEMD) == 0) || (strcmp(buffer, UPGRADE_NEEDED_SYSTEMV) == 0))
            {
                if (check_upgrade_version == 1)
                {
                    printf("ERROR: Failed to make upgrade!\n");
                    return IUCV_UPGRADE_FAILED;
                }
                //printf("Need to make %s upgrade!\n", buffer);
                if ((returncode = handle_upgrade(sockfd, buffer)) != 0)
                {
                    close(sockfd);
                    return returncode;
                }
                need_reconnect = 1;
                check_upgrade_version = 1;
                sleep(2);
                break;
            }
            /* If command is to transport file to VM */
            /* (to-do)later should add a Mutex, when file is transport, command is not be allowed */
            if (strcmp(argv[2], FILE_TRANSPORT)==0)
            {
                /* If the source path is a folder, return error */
                struct stat st;
                stat(argv[3], &st);
                if ((st.st_mode & S_IFDIR) == S_IFDIR)
                {
                    sprintf(buffer, "The source path %s should include the file name.", argv[3]);
                    printAndLogIUCVserverReturnCodeReasonCodeoutput(FILE_TRANSPORT_ERROR, 1, buffer, 0);
                    close(sockfd);
                    return FILE_TRANSPORT_ERROR;
                }
                //printf("Receive %s, begin to send file.\n", buffer);
                if (n < 0 || strcmp(buffer,READY_TO_RECEIVE) != 0)
                {
                    sprintf(result, "ERROR: Server can't receive file. Reason: %s.", buffer);
                    printAndLogIUCVserverReturnCodeReasonCodeoutput(SOCKET_ERROR, errno, result, 0);
                    close(sockfd);
                    return SOCKET_ERROR;
                }
                if ((returncode = send_file_to_server(sockfd, argv[3])) != 0)
                {
                    close(sockfd);
                    return returncode;
                }
                break;
            }
            /* If command is normal linux command */
            else
            {
                /* Now read server response */
                //printf("result =%s\n",buffer);
                /* check the command return code */
                pos = strstr(buffer, "iucvcmdrc=");
                if (pos == NULL)
                {
                    strcpy(cmd_rc, "0");
                    bzero(result,BUFFER_SIZE);
                    strcpy(result, buffer);
                }
                else
                {
                    bzero(cmd_rc, 8);
                    strncpy(cmd_rc, pos+strlen("iucvcmdrc="), 8);
                    bzero(result,BUFFER_SIZE);
                    strncpy(result, buffer, strlen(buffer)-strlen(pos));
                }
                //printf("rc=%d,result=%s,buffer=%s",atoi(cmd_rc),result,buffer);
                if (atoi(cmd_rc) == 0)
                {
                    printAndLogIUCVserverReturnCodeReasonCodeoutput(0, 0, result, 0);
                    /* If message has sent over, close the socket immediately to enhance performance */
                    if (pos != NULL)
                    {
                        close(sockfd);
                        return 0;
                    }
                }
                else
                {
                    printAndLogIUCVserverReturnCodeReasonCodeoutput(CMD_EXEC_ERROR, atoi(cmd_rc), result, 0);
                    close(sockfd);
                    return CMD_EXEC_ERROR;
                }
                if (n < 0)
                {
                    printAndLogIUCVserverReturnCodeReasonCodeoutput(SOCKET_ERROR, errno, "ERROR reading from socket:", 1);
                    close(sockfd);
                    return SOCKET_ERROR;
                }
            }
        }
    }
    close(sockfd);
    closelog();
    return 0;
}
