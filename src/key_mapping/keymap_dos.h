#ifndef PCPLUS_KEYMAP_DOS_H
#define PCPLUS_KEYMAP_DOS_H
#define KEYMAP_PROFILE_SIZE 948
#define KEYMAP_SLOT_SIZE 12
#define KEYMAP_SLOTS 79
typedef unsigned keymap_dos_status;
enum {KEYMAP_DOS_OK=0,KEYMAP_DOS_ARGUMENT,KEYMAP_DOS_OPEN,KEYMAP_DOS_SEEK,
 KEYMAP_DOS_SIZE,KEYMAP_DOS_READ,KEYMAP_DOS_SLOT,KEYMAP_DOS_CLOSE};
typedef struct keymap_dos_result {
 keymap_dos_status status;
 unsigned dos_error,close_error;
 unsigned long bytes_read,file_bytes;
} keymap_dos_result;
/* Near C, caller8, DS=SS, full16-bit unsigned AX. Explicit path1..63 bytes.
 * Require positive whole948-byte blocks; no maximum block count inferred.
 * Selected zero-based profile must exist; all79 selected strings NUL within12.
 * Stage/close before commit; failures preserve destination. FF remains storedFF.
 * No IO for invalid/wrapping/overlapping caller extents. Optional result is
 * disjoint from path/destination and unchanged on argument rejection.
 * No implicit file search/default import, no writes, no concurrent-writer lock.
 */
keymap_dos_status __cdecl keymap_dos_read(const char *path,unsigned profile,
 unsigned char *destination,keymap_dos_result *result);
#endif
