#ifndef PCPLUS_DIRECTORY_SCRIPT_H
#define PCPLUS_DIRECTORY_SCRIPT_H
enum { DSCRIPT_NONE=0,DSCRIPT_COMPILED,DSCRIPT_SOURCE };
enum { DSCRIPT_OK=0,DSCRIPT_ARGUMENT,DSCRIPT_OPEN,DSCRIPT_READ,DSCRIPT_HEADER,DSCRIPT_RANGE,DSCRIPT_CLOSE };
typedef struct directory_script_fingerprint {
 unsigned kind,header;
 unsigned long bytes,crc32;
} directory_script_fingerprint;
typedef struct directory_script_result {
 unsigned status,dos_error,close_error,handle;
} directory_script_result;
/* Near-cdecl DOS16 DS=SS. Read an absolute canonical DOS83 path (<=63 bytes)
 * using non-inheritable IO, streaming256-byte chunks through a32-bit length
 * and CRC32/IEEE fingerprint. Compiled files require a first byte<=128; this
 * is the loader header check, not validation of every bytecode instruction.
 * Source files are fingerprinted, never compiled/executed or called ready to
 * apply. Empty source is allowed for the compiler to diagnose later. Signed
 * 32-bit file-position limits match ASPECT; no64KiB file-size restriction.
 * Caller owns canonical reservations/quiescence. Success closes before output
 * publication. Any read/header/close error preserves the entire fingerprint.
 * Close uncertainty reports the handle; caller retains its claim and refuses
 * EXEC/reset/retry. Argument errors preserve both output and result. Path,
 * fingerprint12 and result8 must be disjoint nonwrapping near extents.
 */
unsigned __cdecl directory_script_read(const char *,unsigned,
 directory_script_fingerprint *,directory_script_result *);
#endif
