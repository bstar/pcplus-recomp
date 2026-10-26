#ifndef PCPLUS_DIRECTORY_RESOURCES_H
#define PCPLUS_DIRECTORY_RESOURCES_H
#include "../key_mapping/keymap_dos.h"
#include "../key_mapping/key_actions_dos.h"
#define DIRECTORY_RESOURCE_KBD 512U
#define DIRECTORY_RESOURCE_KEY 4096U
enum { DR_OK=0,DR_ARGUMENT,DR_STATE,DR_BUSY,DR_CANONICAL,DR_PATH,
 DR_LOOKUP,DR_CLAIM,DR_KEYMAP,DR_ACTIONS,DR_RELEASE,DR_RECOVERY };
enum { DR_IDLE=0,DR_ACTIVE,DR_RESOLVED,DR_HELD };
enum { DR_DEFAULT=0,DR_CLI,DR_DIRECTORY,DR_FALLBACK };
typedef struct directory_resource_request {
 unsigned char record[114];
 unsigned profile,cli_mask,psp;
 char cli_keyboard[64],cli_actions[64];
} directory_resource_request;
typedef struct directory_resource_bundle {
 unsigned profile,mask,keyboard_source,actions_source;
 char keyboard_path[64],actions_path[64];
 unsigned char keyboard[KEYMAP_PROFILE_SIZE],actions[KEY_ACTIONS_SIZE];
} directory_resource_bundle;
typedef struct directory_resource_snapshot {
 unsigned state,status,source_status,dos_error,close_error,claim_status,release_status;
 char keyboard_path[64],actions_path[64];
} directory_resource_snapshot;
extern directory_resource_snapshot directory_resource_result;
/* DOS16 small model, DS=SS. Caller may inspect, never modify owner state.
 * Once-only initialization preserves active/uncertain ownership. */
unsigned __cdecl directory_resources_initialize(void);
unsigned __far __cdecl directory_resources_exec_allowed(void);
/* Stage only KEY/KBD resources; no live settings, UART, screen or user-file
 * writes. Call under the future adopting owner's UART quiescence boundary.
 * cli_mask is ORIGINAL CLI provenance (only512/4096), never the subsequently
 * augmented terminal_option_mask. Present CLI paths must be previously bound
 * absolute DOS identities, not relative startup spellings. profile4/6 only.
 * Both stored binding names are validated even under CLI overrides.
 * Directory lookup: CWD, then PCPLUS environment; named missing META tries
 * PCPLUS.KBD through the same search. Blank META does not request fallback.
 * Missing/blank directory resources RESET to caller-supplied valid default
 * keyboard and disabled actions(kind3), never carry the old board's bindings.
 * Explicit missing CLI resources fail. No fallback after IO/schema failures.
 * Resolve all present canonical DOS83 names before shared reservation/read.
 * Strict reads use non-inheritable DOS3+ handles. Close/release uncertainty
 * retains the claim and inhibits EXEC/reinitialization until process exit.
 * On failure the entire far bundle is unchanged. It is published only after
 * both reads/close/release succeed. Caller owns a stable, disjoint, nonwrapping
 * request248, default948 and far bundle1624 (including physical far aliases).
 * Default slots must each contain a NUL within12. No source resource is kept
 * open on success; bundle bytes may be used without rereading those files.
 * This does not stage translation/scripts, bind CLI at startup, acquire an
 * output-buffer lease, lock external writers or commit a directory selection.
 */
unsigned __cdecl directory_resources_stage(const directory_resource_request *,
 const unsigned char *default_keyboard,directory_resource_bundle __far *);
#endif
