#ifndef PCPLUS_BATCH_HEADER_H
#define PCPLUS_BATCH_HEADER_H
/* Maintained bounded metadata codec, NOT a transfer engine or native recovery.
 * Forsberg1988 YMODEM section5: length decimal; date/mode/serial octal;
 * later fields opaque. https://android.googlesource.com/platform/external/syslinux/+/refs/heads/oreo-m6-s2-release/com32/libupload/ymodem.txt
 * Safe local-platform policy: basename DOS8.3 only, case preserved, no devices.
 * No file IO, timestamp/mode application, framing, CRC or protocol callbacks.
 * DOS small-model near cdecl, DS=SS. Outputs atomic; overlapping spans rejected.
 */
#ifdef __WATCOMC__
typedef unsigned long batch_header_u32;
#else
#include <stdint.h>
typedef uint32_t batch_header_u32;
#ifndef __cdecl
#define __cdecl
#endif
#endif
enum { BH_OK=0,BH_ARGUMENT,BH_NAME,BH_FORMAT,BH_OVERFLOW,BH_UNSUPPORTED };
enum { BH_FILE=1,BH_END=2 };
enum { BH_LENGTH=1,BH_MTIME=2,BH_MODE=4,BH_SERIAL=8,BH_EXTENSION=16 };
typedef struct batch_header_result {
 char name[13];unsigned char kind;unsigned short flags;
 batch_header_u32 size,mtime,mode,serial;
 unsigned short extension_offset,extension_length;
} batch_header_result;
/* Encoder always128 bytes, minimal decimal DWORD size and NUL padding.
 * name_capacity1..64 includes accessible NUL; basename max12. */
unsigned __cdecl batch_header_encode(const char *name,unsigned name_capacity,
 batch_header_u32 size,unsigned char *block,unsigned block_capacity);
unsigned __cdecl batch_header_end(unsigned char *block,unsigned block_capacity);
/* Decoder accepts exactly128 or1024 bytes; every string bounded by that span.
 * Optional known fields form consecutive prefix; absent length != zero length.
 * Printable future metadata remains in input at returned offset/length;
 * caller must retain input to inspect it. Result has fixed36-byte ABI.
 * Signs, tabs, repeated/leading/trailing separators, overflow and nonzero
 * post-terminator padding reject. Unknown extensions cannot contain controls.
 */
unsigned __cdecl batch_header_decode(const unsigned char *block,
 unsigned block_capacity,batch_header_result *result);
#endif
