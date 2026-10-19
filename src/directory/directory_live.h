#ifndef PCPLUS_DIRECTORY_LIVE_H
#define PCPLUS_DIRECTORY_LIVE_H
#include "directory_dos.h"
#include "terminal_import.h"
#include "modem_import.h"
/* Maintained live subset, not the complete original directory application. */
typedef struct directory_live_plan {
 unsigned entry_number,dialing_mode,protocol_index,duplex,codes;
 unsigned char name[25];
 unsigned char target[64];
 unsigned char reserved;
 unsigned char record[114];
} directory_live_plan;
typedef struct directory_live_result {
 unsigned status,source_status,dos_error,close_error,bytes_processed;
} directory_live_result;
/* Retained logical selection identity and original header/record. Paths are
 * request spellings, not canonical filesystem identities or namespace locks. */
typedef struct directory_live_context {
 directory_dos_selection selection;
 unsigned codes;
 char prm_path[64],directory_path[64];
} directory_live_context;
typedef unsigned directory_live_status;
enum {
 DIRECTORY_LIVE_OK=0,DIRECTORY_LIVE_ARGUMENT,DIRECTORY_LIVE_PRM_IO,
 DIRECTORY_LIVE_DIRECTORY_IO,DIRECTORY_LIVE_SERIAL,DIRECTORY_LIVE_MODEM,
 DIRECTORY_LIVE_RECORD,DIRECTORY_LIVE_BINDING,DIRECTORY_LIVE_TARGET,
 DIRECTORY_LIVE_MODE,DIRECTORY_LIVE_DUPLEX
};
/* Pure version of the same three-plan transaction over a caller-owned raw PRM
 * and selected header/record. No DOS/UART/BIOS, no mutation of source images.
 * Sources and all outputs/results must have disjoint nonwrapping DS extents;
 * output plans remain unchanged on failure. Initial global serial validation
 * precedes record overrides, preserving read() compatibility policy. */
directory_live_status __cdecl directory_live_decode(const prm_dos_image *image,
 const directory_dos_selection *selection,unsigned codes,
 terminal_import_settings *serial,modem_import_settings *modem,
 directory_live_plan *plan,directory_live_result *result);
/* One PRM read and one strict directory read, then atomic three-plan commit.
 * Explicit paths1..63bytes; output/IO near extents disjoint and nonwrapping.
 * Unknown directory bytes remain untouched on disk. This API never writes.
 * codes0 preserves literal network targets; codes1 uses original A..J semantics.
 * Protocol selection is retained as metadata until transfer UI is implemented.
 * Supported compiled-script names are retained for post-connect execution.
 * Unsupported script spellings, KEY/META bindings and HALF fail before UART. Stored
 * password bytes remain metadata; they are never automatically transmitted.
 * DIRECT accepts an empty number and needs no modem command configuration.
 */
directory_live_status __cdecl directory_live_read(const char *prm_path,
 const char *directory_path,unsigned entry,unsigned codes,
 terminal_import_settings *serial,modem_import_settings *modem,
 directory_live_plan *plan,directory_live_result *result);
/* Same read order/status policy, plus optional496-byte context. On failure
 * context and all three plans stay unchanged. The context must not overlap
 * paths, plans or result. Paths may otherwise alias ordinary output plans:
 * path spelling is captured before any commit. NULL context preserves read().
 * A reader-selection tag inconsistent with requested entry rejects as RECORD. */
directory_live_status __cdecl directory_live_read_context(const char *prm_path,
 const char *directory_path,unsigned entry,unsigned codes,
 terminal_import_settings *serial,modem_import_settings *modem,
 directory_live_plan *plan,directory_live_result *result,
 directory_live_context *context);
/* Pure logical request match: same entry/codes and ASCII case-insensitive path
 * spellings. No alias/dot/CWD canonicalization or record integrity proof.
 * Read-only arguments may alias each other; invalid extents/strings return0. */
unsigned __cdecl directory_live_context_matches(const directory_live_context *context,
 const char *prm_path,const char *directory_path,unsigned entry,unsigned codes);
/* Convert a NUL-terminated stored9-byte script field to an uppercase DOS8.3
 * path, appending .ASX when absent. Blank first byte/space means no script.
 * Output13bytes and input9bytes must be disjoint valid near extents.
 * Returns0 on success;1 for malformed/unsupported name. Does not open files. */
unsigned __cdecl directory_script_name(const unsigned char *stored,char *output);
#endif
