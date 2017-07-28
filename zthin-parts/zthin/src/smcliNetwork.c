/**
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

#include "smcliNetwork.h"
#include "wrapperutils.h"

int networkIpInterfaceCreate(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Network_IP_Interface_Create";
	int rc;
	int i;
	int entryCount = 0;
	int option;
	char * targetIdentifier = NULL;
	char * entryArray[15];
	vmApiNetworkIPInterfaceCreateOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];
    char strMsg[250];

	// Options that have arguments are followed by a : character
	while ((option = getopt(argC, argV, "T:k:h?")) != -1)
	    switch (option) {
	        case 'T':
	            targetIdentifier = optarg;
	            break;

            case 'k':
	            if (!optarg) {
                    DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
	                return INVALID_DATA;
	            }
	            if (entryCount < 15) {
	                entryArray[entryCount] = optarg;
	                entryCount++;
	            } else {
                    DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
	                printf(" Error Too many -k values entered.\n");
	                return INVALID_DATA;
	            }
                break;

	        case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
	                "  Network_IP_Interface_Create\n\n"
	                "SYNOPSIS\n"
	                "  smcli Network_IP_Interface_Create [-T] targetIdentifier\n"
	                "  [-k] entry1 [-k] entry2 ...\n\n"
	                "DESCRIPTION\n"
	                "  Use Network_IP_Interface_Create to create the initial network interface \n"
	                "  configuration for the z/VM TCP/IP stack\n\n"
	                "  The following options are required:\n"
	                "    -T    This must match an entry in the authorization file\n"
	                "    -k    A keyword=value item to be created in the directory.\n"
	                "          They may be specified in any order. Possible keywords are:\n"
	                "             tcpip_stack - The TCP/IP stack to which the new interface applies.\n"
	                "                           This input parameter is required.\n\n"
	                "             interface_id - The identifier of the new interface. Note that this\n"
	                "                            value cannot begin with a dash(-),end with a colon\n"
	                "                            (:),or contain a semicolon(;).\n"
		            "                            This input parameter is required.\n\n"
	                "             permanent - One of the following:\n"
	                "                YES - The added interface will be permanent.\n"
	                "                NO  - The added interface will be temporary (created only for\n"
	                "                      the current session). This is the default.\n\n"
	                "             primary_ipv4 - The primary IPv4 address. The address should be\n"
	                "                            specified in dot-decimal notation with a length\n"
	                "                            separated by a slash delimiter('/').\n"
	                "                            (For example: 192.168.0.9/24.) The mask length\n"
	                "                            is optional,and its value should be in the\n"
	                "                            range 1-30. Specifying a port number here\n"
	                "                            (:port) is not allowed. At least one of the IP\n"
	                "                            input parameters (primary_ipv4=,primary_ipv6=)\n"
	                "                            is required.\n\n"
	                "             primary_ipv6 - The primary IPv6 address.The address should be\n"
	                "                            specified by 8 groups of 16-bit hexadecimal\n"
	                "                            values separated by colons (:), with a prefix\n"
	                "                            length separated by a slash delimiter('/'). \n"
	                "                            (For example:1080:0:0:0:AB32:800:FF83:10/64.)\n"
	                "                            The prefix length is optional, and its value\n"
	                "                            should be in the range 1-128. One group of\n"
	                "                            consecutive zeroes within an address may be\n"
	                "                            replaced by a double colon ('::').IPv4-embedded\n"
	                "                            IPv6 addresses are not allowed. At least one of\n"
	                "                            the IP input parameters(primary_ipv4=,\n"
	                "                            primary_ipv6=) is required.\n\n"
	                "             interface - Type of interface to be created. Only one of the\n"
	                "                         following types can be specified per value,and only\n"
	                "                         one interface can be created per API call. The options\n"
	                "                         for each type are blank-delimited,and are required \n"
	                "                         unless otherwise stated. This input parameter is\n"
	                "                         required.\n\n"
	                "                           ETH rdevno ipv4router ipv6router\n"
	                "                              Defines an LCS, IEDN, INMN or QDIO Ethernet\n"
                    "                              interface.\n"
	                "                                 rdevno The real device address\n"
	                "                                 ipv4router Optional, the router interface\n"
	                "                                            type for IPv4. Possible values\n"
	                "                                            are: PRI, SEC, NON.\n"
	                "                                 ipv6router Optional, the router interface\n"
    	            "                                            type for IPv6. Possible values\n"
                    "                                            are: IPV6PRI, IPV6SEC, IPV6NON\n"
                    "                           HS rdevno   Defines a real HyperSocket connection\n"
                    "                                        rdevno The real device address\n"
                    "                           IUCV userid Defines an IUCV interface.\n"
                    "                                        userid The communication partner userid\n"
                    "                           CTC rdevno Defines a real channel-to-channel interface.\n"
                    "                                        rdevno The real device address\n"
                    "                           VETH vdevno ownerid lanname\n"
                    "                                Defines a virtual IEDN, INMN or QDIO Ethernet\n"
                    "                                connection to the named guest LAN or virtual\n"
                    "                                switch.\n"
                    "                                    rdevno  The real device address\n"
                    "                                    ownerid The owner of the LAN/VSWITCH. If\n"
                    "                                            a VSWITCH name is specified, the\n"
                    "                                            ownerid must be SYSTEM\n"
                    "                                    lanname  The LAN or VSWITCH name.\n"
                    "                           VCTC vdevno1 userid vdevno2\n"
                    "                                Defines a virtual channel-to-channel interface\n"
                    "                                A virtual CTC is defined and coupled to the\n"
                    "                                specified user's virtual device\n"
                    "                                    vdevno1  The real device address\n"
                    "                                    userid The owner of the vdevno1\n"
                    "                                    vdevno2  The real device address\n"
                    "                           VHS vdevno ownerid lanname\n"
                    "                                Defines a virtual HyperSocket connection. A\n"
                    "                                HyperSockets guest LAN will be created.\n"
                    "                                    vdevno   The virtual device address.\n"
                    "                                    ownerid  The LAN owner.\n"
                    "                                    lanname  The LAN name.\n\n"
    	            "             cpu - Specifies the virtual processor to be used to run the device\n"
    	            "                   driver for the interface. The value must be an integer in\n"
    	            "                   the range 0-6. The default is 0\n\n"
    	            "             transport_type - One of the following:\n"
    	            "                            IP        The transport for the link is IP.\n"
    	            "                            ETHERNET  The transport for the link is Ethernet.\n\n"
        	        "             mtu - Defines the maximum transmission unit (MTU) size that is to\n"
        	        "                   be used on the interface. If you specify 0 or omit this\n"
                    "                   option, the TCP/IP stack will select an intelligent default\n\n"
        	        "             noforward - One of the following:\n"
        	        "                    ON Specifies that packets received on this link are not to\n"
                    "                    OFF Specifies that packets received or transmitted on the\n"
                    "                        link can be forwarded to another host. This is the\n"
                    "                        default.\n\n"
        	        "             pathmtu - One of the following:\n"
        	        "                     YES Specifies that path MTU discovery will be used on IPv4\n"
                    "                         routes for a given link.\n"
        	        "                     NO  Specifies that path MTU discovery will not be used on\n"
                    "                         IPv4 routes for a given link.\n\n"
            	    "             p2p - Defines the IPv4 address associated with the other end of a\n"
            	    "                   point-to-point interface. The value should be specified in\n"
                    "                   dot-decimal notation. This is a required parameter for IUCV\n"
                    "                   and CTC interfaces\n\n"
            	    "             port_name - Specifies the queued direct I/O (QDIO port name when\n"
            	    "                   it is being defined for use by this interface.\n\n"
                	"             port_number - Specifies the physical port or adapter number on\n"
                	"                           the device when it is being defined to be used by\n"
                    "                           this interface.\n\n"
                    "            vlan - Specifies the identifier for a virtual local area network\n"
                	"                   (VLAN). The format of the value is either ipv4vlan or\n"
                    "                   ipv4vlan ipv6vlan (blank delimited).\n\n");
                printRCheaderHelp();
                return 0;

            case '?':
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                if (isprint (optopt)) {
                    sprintf(tempStr,"%c", optopt);
                    if (strstr(argumentsRequired, tempStr)) {
                        printf("This option requires an argument: -%c\n", optopt);
                    } else {
                        printf("Unknown option -%c\n", optopt);
                    }
                } else {
                    printf("Unknown option character \\x%x\n", optopt);
                }
                return 1;
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
                break;
	    }

	if (!targetIdentifier ||  entryCount < 6)  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
	    printf("\nERROR: Missing required options\n");
	    return 1;
	}

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Creating  Network IP Interface... ");

    rc = smNetwork_IP_Interface_Create(vmapiContextP, "", 0, "", targetIdentifier, entryCount, entryArray, &output);
    if (rc) {
        printAndLogProcessingErrors("Network_IP_Interface_Create", rc, vmapiContextP, strMsg, 0);
	} else {
	    // Handle SMAPI return code and reason code
	    rc = printAndLogSmapiReturnCodeReasonCodeDescriptionAndErrorBuffer("Network_IP_Interface_Create", rc,
                output->common.returnCode, output->common.reasonCode, output->errorDataLength, output->errorData, vmapiContextP, strMsg);
	}
	return rc;
}

int networkIpInterfaceModify(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Network_IP_Interface_Modify";
	int rc;
	int i;
	int entryCount = 0;
	int option;
	char * targetIdentifier = NULL;
	char * entryArray[4];
	vmApiNetworkIPInterfaceModifyOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];
    char strMsg[250];

	// Options that have arguments are followed by a : character
	while ((option = getopt(argC, argV, "T:k:h?")) != -1)
	    switch (option) {
	        case 'T':
	            targetIdentifier = optarg;
	            break;

            case 'k':
	            if (!optarg) {
                    DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
	                return INVALID_DATA;
	            }
	            if (entryCount < 4) {
	                entryArray[entryCount] = optarg;
	                entryCount++;
	            } else {
                    DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
	                printf(" Error Too many -k values entered.\n");
	                return INVALID_DATA;
	            }
                break;

	        case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
	                "  Network_IP_Interface_Modify\n\n"
	                "SYNOPSIS\n"
	                "  smcli Network_IP_Interface_Modify [-T] targetIdentifier\n"
	                "  [-k] entry1 [-k] entry2 ...\n\n"
	                "DESCRIPTION\n"
	                "  Use Network_IP_Interface_Modify to change the configuration of the existing \n"
	                "  network interface.\n\n"
	                "  The following options are required:\n"
	                "    -T    This must match an entry in the authorization file\n"
	                "    -k    A keyword=value item to be created in the directory.\n"
	                "          They may be specified in any order. Possible keywords are:\n"
	                "             tcpip_stack - The TCP/IP stack to which the new interface change\n"
	                "                           applies. This input parameter is required.\n\n"
	                "             interface_id - The identifier of the interface to be modified.\n"
                    "                            Note that this value cannot begin with a dash(-),\n"
	                "                            end with a colon(:),or contain a semicolon(;).\n"
		            "                            This input parameter is required.\n\n"
	                "             permanent - One of the following:\n"
	                "                YES - The changes to the interface configuration will be\n"
                    "                      permanent.\n"
	                "                NO  - The changes to the interface configuration will be\n"
                    "                      temporary(created only for the current session).\n"
                    "                      This is the default.\n\n"
	                "      You must specify exactly one of the next five modify input parameters\n"
                    "      (delete_ip=, add_ip=, change_mask=, change_mtu=. or change_p2p=).\n\n"
    	            "             delete_ip - The IPv4 or IPv6 address to be deleted.\n\n"
    	            "             add_ip -    The IPv4 or IPv6 address to be added.\n\n"
        	        "             change_mask - The subnet mask which will be associated with\n"
                    "                           interface. This value should be specified in\n"
                    "                           dot-decimal notation.\n"
            	    "             change_mtu - The maximum transmission unit (MTU) size that is to\n"
            	    "                          be used on the interface.\n\n"
                	"             change_p2p - Changes the peer IP address to the specified value.\n"
                	"                          This value should be specified in dot-decimal notation.\n");
                printRCheaderHelp();
                return 0;

            case '?':
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                if (isprint (optopt)) {
                    sprintf(tempStr,"%c", optopt);
                    if (strstr(argumentsRequired, tempStr)) {
                        printf("This option requires an argument: -%c\n", optopt);
                    } else {
                        printf("Unknown option -%c\n", optopt);
                    }
                } else {
                    printf("Unknown option character \\x%x\n", optopt);
                }
                return 1;
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
                break;
	    }

	if (!targetIdentifier ||  entryCount < 3)  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
	    printf("\nERROR: Missing required options\n");
	    return 1;
	}

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Modifying  Network IP Interface... ");

    rc = smNetwork_IP_Interface_Modify(vmapiContextP, "", 0, "", targetIdentifier, entryCount, entryArray, &output);
    if (rc) {
        printAndLogProcessingErrors("Network_IP_Interface_Modify", rc, vmapiContextP, strMsg, 0);
	} else {
	    // Handle SMAPI return code and reason code
	    rc = printAndLogSmapiReturnCodeReasonCodeDescriptionAndErrorBuffer("Network_IP_Interface_Modify", rc,
                output->common.returnCode, output->common.reasonCode, output->errorDataLength, output->errorData, vmapiContextP, strMsg);
	}
	return rc;
}

int networkIpInterfaceQuery(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Network_IP_Interface_Query";
	int rc;
	int i;
	int entryCount = 0;
	int option;
	int outPutVarCount = 0;
    char *token;
    char * buffer;  // Character pointer whose value is preserved between successive related calls to strtok_r
    const char * blank = " ";
	char * targetIdentifier = NULL;
	char * entryArray[3];
	vmApiNetworkIPInterfaceQueryOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];

	// Options that have arguments are followed by a : character
	while ((option = getopt(argC, argV, "T:k:h?")) != -1)
	    switch (option) {
	        case 'T':
	            targetIdentifier = optarg;
	            break;

            case 'k':
	            if (!optarg) {
                    DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
	                return INVALID_DATA;
	            }
	            if (entryCount < 3) {
	                entryArray[entryCount] = optarg;
	                entryCount++;
	            } else {
                    DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
	                printf(" Error Too many -k values entered.\n");
	                return INVALID_DATA;
	            }
                break;

	        case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
	                "  Network_IP_Interface_Query\n\n"
	                "SYNOPSIS\n"
	                "  smcli Network_IP_Interface_Query [-T] targetIdentifier\n"
	                "  [-k] entry1 [-k] entry2 ...\n\n"
	                "DESCRIPTION\n"
	                "  Use Network_IP_Interface_Query to obtain interface configurations for a\n"
	                "  specified TCP/IP stack virtual machine.\n\n"
	                "  The following options are required:\n"
	                "    -T    This must match an entry in the authorization file\n"
	                "    -k    A keyword=value item to be created in the directory.\n"
	                "          They may be specified in any order. Possible keywords are:\n"
	                "             tcpip_stack - The TCP/IP stack whose interfaces are to be queried.\n"
	                "                           This input parameter is required.\n\n"
	                "             interface_all - One of the following:\n"
	                "                YES - Return configurations of all interfaces.\n"
	                "                NO  - Return configurations of active interfaces only.\n"
	                "                      This is the default..\n\n"
	                "             interface_id - The identifier of the interface to be queried\n"
	                "                            Note that this value cannot begin with a dash(-),\n"
	                "                            end with a colon(:), or contain a semicolon(;).\n"
	                "                            If it is not specified, configurations for all\n"
                    "                            interfaces for the specified TCP/IP stack will be\n"
                    "                            returned.\n\n"
	                "       Note: You cannot specify both interface_all=YES and interface_id=value.\n");
                printRCheaderHelp();
                return 0;

            case '?':
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                if (isprint (optopt)) {
                    sprintf(tempStr,"%c", optopt);
                    if (strstr(argumentsRequired, tempStr)) {
                        printf("This option requires an argument: -%c\n", optopt);
                    } else {
                        printf("Unknown option -%c\n", optopt);
                    }
                } else {
                    printf("Unknown option character \\x%x\n", optopt);
                }
                return 1;
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
                break;
	    }

	if (!targetIdentifier ||  entryCount < 1)  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
	    printf("\nERROR: Missing required options\n");
	    return 1;
	}

    rc = smNetwork_IP_Interface_Query(vmapiContextP, "", 0, "", targetIdentifier, entryCount, entryArray, &output);
    if (rc) {
        printAndLogProcessingErrors("Network_IP_Interface_Query", rc, vmapiContextP, "", 0);
    } else if (output->common.returnCode || output->common.reasonCode) {
        // Handle SMAPI return code and reason code
        rc = printAndLogSmapiReturnCodeReasonCodeDescription("Network_IP_Interface_Query", output->common.returnCode,
                output->common.reasonCode, vmapiContextP, "");
    } else {
        DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
    	if (output->interfaceConfigArrayLength > 0) {
    		for (i = 0; i < output->interfaceConfigArrayCount; i++ ) {
    	        token = strtok_r(output->interfaceConfigArray[i].vmapiString, blank, &buffer);
    	        printf("%s\n", token);
                while (token != NULL) {
    	            token = strtok_r(NULL, blank, &buffer);
        	        printf("%s\n", token);
                }
    	    }
    	}
    }
	return rc;
}

int networkIpInterfaceRemove(int argC, char* argV[], struct _vmApiInternalContext* vmapiContextP) {
    const char * MY_API_NAME = "Network_IP_Interface_Remove";
	int rc;
	int i;
	int entryCount = 0;
	int option;
	char * targetIdentifier = NULL;
	char * entryArray[4];
	vmApiNetworkIPInterfaceRemoveOutput * output;

    opterr = 0; // 0 =>Tell getopt to not display a mesage
    const char * argumentsRequired = "Tk";
    char tempStr[1];
    char strMsg[250];

	// Options that have arguments are followed by a : character
	while ((option = getopt(argC, argV, "T:k:h?")) != -1)
	    switch (option) {
	        case 'T':
	            targetIdentifier = optarg;
	            break;

            case 'k':
	            if (!optarg) {
                    DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
	                return INVALID_DATA;
	            }
	            if (entryCount < 4) {
	                entryArray[entryCount] = optarg;
	                entryCount++;
	            } else {
                    DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
	                printf(" Error Too many -k values entered.\n");
	                return INVALID_DATA;
	            }
                break;

	        case 'h':
                DOES_CALLER_WANT_RC_HEADER_ALLOK(vmapiContextP);
                printf("NAME\n"
	                "  Network_IP_Interface_Remove\n\n"
	                "SYNOPSIS\n"
	                "  smcli Network_IP_Interface_Remove [-T] targetIdentifier\n"
	                "  [-k] entry1 [-k] entry2 ...\n\n"
	                "DESCRIPTION\n"
	                "  Use Network_IP_Interface_Remove to remove the existing network interface.\n\n"
	                "  The following options are required:\n"
	                "    -T    This must match an entry in the authorization file\n"
	                "    -k    A keyword=value item to be created in the directory.\n"
	                "          They may be specified in any order. Possible keywords are:\n"
	                "             tcpip_stack - The TCP/IP stack to which the new interface removal.\n"
	                "                           applies. This input parameter is required.\n\n"
	                "             interface_id - The identifier of the interface to be removed.\n"
                    "                            Note that this value cannot begin with a dash(-),\n"
	                "                            end with a colon(:),or contain a semicolon(;).\n"
		            "                            This input parameter is required.\n\n"
	                "             permanent - One of the following:\n"
	                "                YES - The changes to the interface configuration will be\n"
                    "                      permanent.\n"
	                "                NO  - The changes to the interface configuration will be\n"
                    "                      temporary(created only for the current session).\n"
                    "                      This is the default.\n");
                printRCheaderHelp();
                return 0;

            case '?':
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                if (isprint (optopt)) {
                    sprintf(tempStr,"%c", optopt);
                    if (strstr(argumentsRequired, tempStr)) {
                        printf("This option requires an argument: -%c\n", optopt);
                    } else {
                        printf("Unknown option -%c\n", optopt);
                    }
                } else {
                    printf("Unknown option character \\x%x\n", optopt);
                }
                return 1;
                break;

            default:
                DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
                return 1;
                break;
	    }

	if (!targetIdentifier ||  entryCount < 3)  {
        DOES_CALLER_WANT_RC_HEADER_SYNTAX_ERROR(vmapiContextP);
	    printf("\nERROR: Missing required options\n");
	    return 1;
	}

    // If they want special output header as first output, then we need to pass this
    // string on RC call so it is handled correctly for both cases.
    snprintf(strMsg, sizeof(strMsg), "Removing  Network IP Interface... ");

    rc = smNetwork_IP_Interface_Remove(vmapiContextP, "", 0, "", targetIdentifier, entryCount, entryArray, &output);
    if (rc) {
        printAndLogProcessingErrors("Network_IP_Interface_Remove", rc, vmapiContextP, strMsg, 0);
	} else {
	    // Handle SMAPI return code and reason code
	    rc = printAndLogSmapiReturnCodeReasonCodeDescriptionAndErrorBuffer("Network_IP_Interface_Remove", rc,
                output->common.returnCode, output->common.reasonCode, output->errorDataLength, output->errorData, vmapiContextP, strMsg);
	}
	return rc;
}
