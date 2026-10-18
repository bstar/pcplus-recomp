#ifndef PCPLUS_PRM_REPLACE_H
#define PCPLUS_PRM_REPLACE_H
#include "prm_dos.h"
/* Maintained failure-aware replacement, not a crash-atomic FAT transaction.
 * Paths must be distinct ASCII 8.3 leaf names in the current DOS directory.
 * Stage and backup must not exist. Existing read-only/directory targets fail.
 * Successful replacement removes the backup; cleanup errors retain it.
 * Check installed/original_in_backup even on failure. Never blindly retry a
 * failed operation over its recovery files. No user/config defaults embedded. */
typedef enum prm_replace_status {
 PRM_REPLACE_OK=0, PRM_REPLACE_ARGUMENT, PRM_REPLACE_CONFLICT,
 PRM_REPLACE_INSPECT, PRM_REPLACE_STAGE_OPEN, PRM_REPLACE_WRITE,
 PRM_REPLACE_CLOSE, PRM_REPLACE_MOVE_OLD, PRM_REPLACE_INSTALL,
 PRM_REPLACE_CLEANUP
} prm_replace_status;
typedef struct prm_replace_result {
 prm_replace_status status;
 unsigned dos_error,close_error,cleanup_error,rollback_error,bytes_processed;
 unsigned installed,original_in_backup,stage_exists;
} prm_replace_result;
prm_replace_status __cdecl prm_dos_replace(const char *target,const char *stage,
 const char *backup,const prm_dos_image *image,prm_replace_result *result);
#endif
