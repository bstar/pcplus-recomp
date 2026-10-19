#ifndef PCPLUS_KEYBOARD_API_H
#define PCPLUS_KEYBOARD_API_H
/* Near caller-cleanup wrappers around the recovered RET2 normalizers.
 * DS must equal SS. This layer neither reads BIOS nor owns the key queue. */
unsigned __cdecl keyboard_key_from_bios(unsigned key);
unsigned __cdecl keyboard_key_for_extended(unsigned key);
#endif
