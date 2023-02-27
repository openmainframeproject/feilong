/**
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
#include <stdlib.h>
#include "smPublic.h"

int quantum = 64;

int smMemoryGroupInitialize(struct _vmApiInternalContext* vmapiContextP) {
    smMemoryGroupContext * context = vmapiContextP->memContext;
    // Set up a tracking array with no allocated chunks yet
    context->arraySize = quantum;
    context->chunks = (void **) malloc(context->arraySize * sizeof(void *));
    if (context->chunks == 0) {
        errorLine(vmapiContextP, "smMemoryGroupInitialize: out of memory");
        return MEMORY_ERROR;
    }
    context->lastChunk = -1;

    // Return successfully
    return 0;
}

void * smMemoryGroupAlloc(struct _vmApiInternalContext* vmapiContextP, size_t size) {
    int rc;
    smMemoryGroupContext * context = vmapiContextP->memContext;

    // Check that memory structure is initialized, if not then call to init
    if (context->arraySize < quantum || context->chunks == 0) {
        rc = smMemoryGroupInitialize(vmapiContextP);
        if (rc != 0)
            return 0;  // Return of 0 is error in this case
    }
    // Increment to the next unused entry in the tracking array
    context->lastChunk = context->lastChunk + 1;

    // If we're past the end of the array, enlarge it by the quantum
    if (context->lastChunk == context->arraySize) {
        context->arraySize = context->arraySize + quantum;
        void ** reallocated = (void **) realloc(context->chunks, context->arraySize * sizeof(void *));
        if (NULL == reallocated) {
            errorLine(vmapiContextP, "smMemory realloc: out of memory");
            return NULL;
        } else {
            context->chunks = reallocated;
        }
    }

    // Obtain the memory and record it in the tracking array
    context->chunks[context->lastChunk] = malloc(size);

    // clear out the memory chunk if obtained
    if (context->chunks[context->lastChunk]) {
        memset(context->chunks[context->lastChunk], 0, size);
    }

    // Return the pointer
    return context->chunks[context->lastChunk];
}

void * smMemoryGroupRealloc(struct _vmApiInternalContext* vmapiContextP, void * chunk, size_t size) {
    smMemoryGroupContext * context = vmapiContextP->memContext;
    // Variables
    int i;
    int rc;
    void * newChunk;

    // Check that memory structure is initialized, if not then call to init
    if (context->arraySize < quantum || context->chunks == 0) {
        rc = smMemoryGroupInitialize(vmapiContextP);
        if (rc != 0)
            return 0;  // Return of 0 is error in this case
    }

    // Find this chunk in the tracking array and reallocate it
    newChunk = NULL;
    for (i = 0; (i <= context->lastChunk) && (newChunk == NULL); i++) {
        if (context->chunks[i] == chunk) {
            char *reallocated = realloc(context->chunks[i], size);
            if (NULL == reallocated) {
                errorLine(vmapiContextP, "smMemory group realloc: out of memory");
                return NULL;
            } else {
                context->chunks[i] = reallocated;
            }
            newChunk = context->chunks[i];
        }
    }

    // Return the new pointer
    return newChunk;
}

int smMemoryGroupFreeAll(struct _vmApiInternalContext* vmapiContextP) {
    smMemoryGroupContext * context = vmapiContextP->memContext;
    int i;

    // Check that memory structure is initialized, if not then just return
    if (context->arraySize < quantum || context->chunks == 0) {
        return 0;
    }

    // Free all the memory recorded in the tracking array
    for (i = 0; i <= context->lastChunk; i++) {
        if (context->chunks[i])
            FREE_MEMORY(context->chunks[i]);
    }

    // Reset the tracking array to empty
    if (context->arraySize != quantum) {
        context->arraySize = quantum;
        context->chunks = (void **) realloc(context->chunks, context->arraySize * sizeof(void *));
    }

    context->lastChunk = -1;

    // Return successfully
    return 0;
}

int smMemoryGroupTerminate(struct _vmApiInternalContext* vmapiContextP) {
    smMemoryGroupContext * context = vmapiContextP->memContext;

    // Check that memory structure is initialized, if not then just return
    if (context->arraySize < quantum || context->chunks == 0) {
        return 0;
    }

    // Free the tracking array
    FREE_MEMORY(context->chunks);

    // Return successfully
    return 0;
}
