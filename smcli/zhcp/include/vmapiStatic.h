/**
 * IBM (C) Copyright 2013 Eclipse Public License
 * http://www.eclipse.org/org/documents/epl-v10.html
 */
#ifndef _VMAPI_STATIC_H
#define _VMAPI_STATIC_H
#include <stddef.h>
#include "smPublic.h"
#include "smapiTableParser.h"


#ifdef __cplusplus
extern "C" {
#endif

/* Static_Image_Changes_Activate_DM */
typedef struct _vmApiStaticImageChangesActivateDmOutput  {
    commonOutputFields common;
} vmApiStaticImageChangesActivateDmOutput;

/* Parser table for Static_Image_Changes_Activate_DM */
static tableLayout Static_Image_Changes_Activate_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiStaticImageChangesActivateDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiStaticImageChangesActivateDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiStaticImageChangesActivateDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiStaticImageChangesActivateDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smStatic_Image_Changes_Activate_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, vmApiStaticImageChangesActivateDmOutput ** outData);

/* Static_Image_Changes_Deactivate_DM */
typedef struct _vmApiStaticImageChangesDeactivateDmOutput {
    commonOutputFields common;
} vmApiStaticImageChangesDeactivateDmOutput;

/* Parser table for Static_Image_Changes_Deactivate_DM */
static tableLayout Static_Image_Changes_Deactivate_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiStaticImageChangesDeactivateDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiStaticImageChangesDeactivateDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiStaticImageChangesDeactivateDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiStaticImageChangesDeactivateDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smStatic_Image_Changes_Deactivate_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, vmApiStaticImageChangesDeactivateDmOutput ** outData);

/* Static_Image_Changes_Immediate_DM */
typedef struct _vmApiStaticImageChangesImmediateDmOutput {
    commonOutputFields common;
} vmApiStaticImageChangesImmediateDmOutput;

/* Parser table for Static_Image_Changes_Immediate_DM */
static tableLayout Static_Image_Changes_Immediate_DM_Layout = {
    { APITYPE_BASE_STRUCT_LEN, 4, 4, STRUCT_INDX_0, NEST_LEVEL_0, sizeof(vmApiStaticImageChangesImmediateDmOutput) },
    { APITYPE_INT4,            4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiStaticImageChangesImmediateDmOutput, common.requestId) },
    { APITYPE_RC_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiStaticImageChangesImmediateDmOutput, common.returnCode) },
    { APITYPE_RS_INT4,         4, 4, STRUCT_INDX_0, NEST_LEVEL_0, offsetof(vmApiStaticImageChangesImmediateDmOutput, common.reasonCode) },
    { APITYPE_END_OF_TABLE, 0, 0, 0, 0 }
};

int smStatic_Image_Changes_Immediate_DM(struct _vmApiInternalContext* vmapiContextP, char * userid, int passwordLength,
        char * password, char * targetIdentifier, vmApiStaticImageChangesImmediateDmOutput ** outData);

#ifdef __cplusplus
}
#endif

#endif
