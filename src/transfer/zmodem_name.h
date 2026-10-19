#ifndef PCPLUS_ZMODEM_NAME_H
#define PCPLUS_ZMODEM_NAME_H
#include "batch_header.h"
#define ZM_WIRE_NAME_MAX 255
/* Separate remote identity from the local DOS basename. Valid DOS83 names
 * retain their spelling. Other bounded leaf names use eight CRC32 hex digits
 * (ASCII case folded) and a safe1..3-character extension, otherwise DAT.
 * Slashes, drive separators, controls, empty/dot paths and >255 bytes reject.
 * High bytes are opaque identity bytes, never filesystem path bytes.
 * Scratch is a disjoint1024-byte caller workspace. Result is atomic; extension
 * offsets still identify the original input. No IO or collision overwrite.
 * Existing local aliases follow the storage owner's checked skip policy. */
unsigned __cdecl zm_name_decode(const unsigned char *block,unsigned count,
 unsigned char *scratch,batch_header_result *result);
#endif
