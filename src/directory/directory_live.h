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
} directory_live_plan;
typedef struct directory_live_result {
 unsigned status,source_status,dos_error,close_error,bytes_processed;
} directory_live_result;
typedef unsigned directory_live_status;
enum {
 DIRECTORY_LIVE_OK=0,DIRECTORY_LIVE_ARGUMENT,DIRECTORY_LIVE_PRM_IO,
 DIRECTORY_LIVE_DIRECTORY_IO,DIRECTORY_LIVE_SERIAL,DIRECTORY_LIVE_MODEM,
 DIRECTORY_LIVE_RECORD,DIRECTORY_LIVE_BINDING,DIRECTORY_LIVE_TARGET,
 DIRECTORY_LIVE_MODE,DIRECTORY_LIVE_DUPLEX
};
/* One PRM read and one strict directory read, then atomic three-plan commit.
 * Explicit paths1..63bytes; output/IO near extents disjoint and nonwrapping.
 * Unknown directory bytes remain untouched on disk. This API never writes.
 * codes0 preserves literal network targets; codes1 uses original A..J semantics.
 * Protocol selection is retained as metadata until transfer UI is implemented.
 * Unsupported script/password/KEY/META bindings and HALF fail before UART.
 * DIRECT accepts an empty number and needs no modem command configuration.
 */
directory_live_status __cdecl directory_live_read(const char *prm_path,
 const char *directory_path,unsigned entry,unsigned codes,
 terminal_import_settings *serial,modem_import_settings *modem,
 directory_live_plan *plan,directory_live_result *result);
#endif
