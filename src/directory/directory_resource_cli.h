#ifndef PCPLUS_DIRECTORY_RESOURCE_CLI_H
#define PCPLUS_DIRECTORY_RESOURCE_CLI_H
#include "directory_resources.h"
enum { DRC_OK=0,DRC_ARGUMENT,DRC_STATE,DRC_CANONICAL,DRC_PATH };
enum { DRC_IDLE=0,DRC_BINDING,DRC_BOUND,DRC_FAILED };
typedef struct directory_resource_cli_snapshot {
 unsigned state,original_mask,status,dos_error,failed_resource;
 char keyboard[64],actions[64];
} directory_resource_cli_snapshot;
extern directory_resource_cli_snapshot directory_resource_cli;
/* Startup-only DOS16 near-cdecl, DS=SS. Snapshot is inspect-only. Once bound
 * or failed, no later bind may replace the original command-line provenance.
 * initialize is idempotent and never resets an attempted bind. */
unsigned __cdecl directory_resource_cli_initialize(void);
/* Call immediately after successful option parsing, before directory lookup or
 * any working-directory change. Preserve all original mask bits. Resolve only
 * explicit /K(512) and /T(4096) paths to uppercase absolute DOS83 <=63 bytes.
 * Inputs are64-byte near arrays, disjoint from owner state, allowed to alias
 * each other. Resolve both before publishing either; no probes/content opens.
 * Unused path contents are ignored. Failure records FAILED and no partial
 * identities; every subsequent bind refuses, including after initialize. */
unsigned __cdecl directory_resource_cli_bind(unsigned mask,const char *keyboard,
 const char *actions);
/* Build the248-byte resource request using ONLY bound original CLI identities.
 * record114 and request248 must be valid disjoint near spans outside ownership;
 * profile4/6 and nonzero PSP required. No IO or output mutation on failure.
 * Stored binding syntax is checked by directory_resources_stage, even under
 * CLI overrides. Caller must supply the actual selected record/profile. */
unsigned __cdecl directory_resource_cli_request(const unsigned char *record,
 unsigned profile,unsigned psp,directory_resource_request *request);
#endif
