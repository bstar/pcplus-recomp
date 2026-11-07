#ifndef PCPLUS_KBD_EDITOR_PREFIX_H
#define PCPLUS_KBD_EDITOR_PREFIX_H
#include "kbd_editor_file.h"
/* Maintained compatibility extension:1..33 complete948-byte profiles.
 * Load publishes a zero-filled full-capacity RAM image only after EOF/schema/
 * close; bytes_processed reports the exact original file length on success.
 * Save compares and writes exactly that explicit length, including EOF checks.
 * No missing profiles/defaults are invented or appended to the file. */
unsigned kbd_editor_prefix_load(const char *,unsigned char __far *,directory_replace_result *);
unsigned kbd_editor_prefix_save(const char *,const unsigned char __far *,const unsigned char __far *,unsigned,directory_replace_result *);
#endif
