#ifndef PCPLUS_KEY_ACTIONS_DOS_H
#define PCPLUS_KEY_ACTIONS_DOS_H
#define KEY_ACTIONS_RECORDS 10
#define KEY_ACTIONS_RECORD_SIZE 54
#define KEY_ACTIONS_TEXT_SIZE 52
#define KEY_ACTIONS_SIZE 540
typedef unsigned key_actions_dos_status;
enum {KEY_ACTIONS_DOS_OK=0,KEY_ACTIONS_DOS_ARGUMENT,KEY_ACTIONS_DOS_OPEN,
 KEY_ACTIONS_DOS_READ,KEY_ACTIONS_DOS_SIZE,KEY_ACTIONS_DOS_KIND,
 KEY_ACTIONS_DOS_TEXT,KEY_ACTIONS_DOS_CLOSE};
typedef struct key_actions_dos_result {
 key_actions_dos_status status;
 unsigned dos_error,close_error,bytes_processed;
} key_actions_dos_result;
/* Near C caller6, DS=SS, full16-bit unsigned AX. Explicit path1..63 bytes.
 * Exact540-byte EOF;10 records of kindWORD0..3 +52-byte NUL-terminated text.
 * Stage and close before committing raw540 bytes. Preserve opaque string tails.
 * Invalid/wrapping/overlapping near extents cause no IO/result mutation.
 * Result optional; otherwise disjoint from path and destination.
 * No implicit search, defaults, creation, writes, caret expansion or execution.
 * Schema-valid action kinds do not imply installed ASPECT/PROGRAM/HOOK handlers.
 */
key_actions_dos_status __cdecl key_actions_dos_read(const char *path,
 unsigned char *destination,key_actions_dos_result *result);
#endif
