#ifndef PCPLUS_KBD_EDITOR_FILE_H
#define PCPLUS_KBD_EDITOR_FILE_H
#include "../directory/directory_replace.h"
#define KBD_EDITOR_BYTES 31284
#define KBD_EDITOR_MEMORY 16
#define KBD_EDITOR_SCHEMA 17
/* Synchronous DOS16 small-model DS=SS API, explicit far nonwrapping images.
 * All33*79 slots require a terminator, with opaque suffixes preserved.
 * Absolute ASCII8.3 path<=63; exclusive same-parent KBDSTG/KBDBAK recovery.
 * Load commits after exact EOF/schema/close. Save compares all old bytes,
 * verifies stage after close, rechecks source, then installs with rollback.
 * Check recovery flags even on error. Uncertain close retains recovery.
 * Not crash-atomic/externally locked; attributes/timestamps not preserved.
 * source_bytes saturates at65535, bytes_processed is exact written count.
 */
unsigned kbd_editor_file_paths(const char *,char *,char *);
unsigned kbd_editor_file_load(const char *,unsigned char __far *,directory_replace_result *);
unsigned kbd_editor_file_save(const char *,const unsigned char __far *,const unsigned char __far *,directory_replace_result *);
#endif
