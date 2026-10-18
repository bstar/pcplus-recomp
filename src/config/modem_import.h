#ifndef PCPLUS_MODEM_IMPORT_H
#define PCPLUS_MODEM_IMPORT_H
#include "prm_dos.h"
/* Maintained, partial2.01 decoder; no defaults or automatic initialization.
 * DOS8086 small model: DS=SS, near pointers, cdecl, unsigned16-bit status.
 * Six command fields retain caret notation; response fields ALREADY contain
 * expanded bytes. No transmission, timer, DOS write or mutation of raw PRM.
 * Array bytes after their first NUL are preserved in the decoded plan. */
#define MODEM_IMPORT_RESPONSE_COUNT 11U
#define MODEM_IMPORT_RESPONSE_SIZE 16U
#define MODEM_IMPORT_SIZE 368U

typedef struct modem_import_settings {
 unsigned dial_timeout_seconds;
 unsigned redial_pause_seconds;
 unsigned autobaud;
 unsigned abort_drop_dtr;
 unsigned initialize_while_connected;
 unsigned dial_cycle_limit;
 unsigned command_character_delay_units;
 unsigned command_pause_character;
 unsigned dial_abort_character;
 unsigned char initialization[47];
 unsigned char dial_prefix[25];
 unsigned char dial_suffix[25];
 unsigned char hangup[25];
 unsigned char answer_on[25];
 unsigned char answer_off[25];
 unsigned char responses[MODEM_IMPORT_RESPONSE_COUNT][MODEM_IMPORT_RESPONSE_SIZE];
 unsigned break_delay_units; /* Raw PRM01A4h, nominal1/55 BIOS tick. */
} modem_import_settings;
typedef unsigned modem_import_status;
enum {
 MODEM_IMPORT_OK=0, MODEM_IMPORT_ARGUMENT, MODEM_IMPORT_BOOLEAN,
 MODEM_IMPORT_RANGE, MODEM_IMPORT_COMMAND, MODEM_IMPORT_RESPONSE,
 MODEM_IMPORT_IO
};
/* Exact numeric policy: timeout accepts1..32767; redial/cycle limits and delay units
 * accept0..32767 for the maintained32-bit deadline engine. This does not
 * reproduce the legacy increment-before-signed-compare overflow at32767.
 * Three flags accept0/1. Empty bounded strings are legal. Dangling caret is
 * rejected in commands only. BREAK delay retains all16-bit values as nominal1/55-tick units; no
 * additional bounds reject a legacy PRM. Unknown fields are never validated/applied.
 * Nonoverlapping DS extents must fit below64KiB; destination unchanged error. */
modem_import_status __cdecl modem_import_decode(const prm_dos_image *image,
 modem_import_settings *destination);
/* Explicit read-only path, no repair/create fallback. Destination unchanged on
 * load/decode failure. Optional IO detail refers to loading, not decoding.
 * Needs roughly3.3KiB nested staging stack including prm_dos_load buffers. */
modem_import_status __cdecl modem_import_read(const char *path,
 modem_import_settings *destination,prm_dos_result *io);
#endif
