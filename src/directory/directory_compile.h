#ifndef PCPLUS_DIRECTORY_COMPILE_H
#define PCPLUS_DIRECTORY_COMPILE_H
#include "directory_resources.h"
#include "../process/dos_exec.h"
enum { DC_IDLE=0,DC_ACTIVE,DC_HELD,DC_DONE,DC_FAILED };
enum { DC_OK=0,DC_ARGUMENT,DC_STATE,DC_PATH,DC_CLAIM,DC_SOURCE,DC_CHANGED,DC_TARGET,DC_PROCESS,DC_OUTPUT,DC_RELEASE };
typedef struct directory_compile_owner {
 unsigned state,status,source_status,dos_error,close_error,release_status,attempts,installed;
 process_result child;
 char source[64],target[64],compiler[64];
 directory_script_fingerprint before,compiled;
 unsigned char reserved[16];
} directory_compile_owner;
extern directory_compile_owner __far directory_compile_storage;
unsigned __cdecl directory_compile_initialize(void);
unsigned __cdecl directory_compile_exec_allowed(void);
/* Caller owns quiesced foreground PROGRAM and stable disjoint bundle2024.
 * Only a SOURCE candidate is accepted. Paths/claims survive in independent
 * far storage, never in the lent history allocation or a returning stack.
 * Fresh source fingerprint must match before and after actual direct ASPCOMP.
 * Existing targets refuse before EXEC. Claim includes source/target/compiler
 * and sibling LPC?????.TMP/BAK names. No shell or interpreter execution.
 * Publish only script path/fingerprint after successful child, checked output
 * read and release. Failures preserve bundle. Ambiguous close/release or an
 * unexpected installed output retains ownership and blocks every later EXEC.
 */
unsigned __cdecl directory_compile_run(unsigned,directory_resource_bundle __far *);
#endif
