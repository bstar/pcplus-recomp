#ifndef PCPLUS_KEY_EDITOR_FILE_H
#define PCPLUS_KEY_EDITOR_FILE_H
#include "key_actions_dos.h"
#include "../directory/directory_replace.h"
/* Synchronous near-cdecl DOS boundary, DS=SS; record buffers are explicit far
 * nonwrapping540-byte spans. Caller owns file/EXEC admission and buffer lifetime.
 * Explicit absolute ASCII DOS83 paths<=63 bytes; recovery parent<=53 bytes.
 * No implicit lookup, filename prompt, auto-create, defaults or live adoption.
 */
unsigned __cdecl key_editor_file_paths(const char *,char *,char *);
/* Strict reader reused: no destination commit before checked close. Optional
 * result has the existing8-byte KEY ABI. Bad arguments leave it untouched. */
unsigned __cdecl key_editor_file_load(const char *,unsigned char __far *,key_actions_dos_result *);
/* expected0 explicitly requests creation of an absent target. Otherwise every
 * old byte must match, including opaque tails; rechecked after staging. Valid
 * replacement schema required. Exclusive KEYSTG.$$$/KEYBAK.$$$ in same parent.
 * Check all20-byte result flags, including on failure. Uncertain close retains
 * recovery and requires owner quarantine/DOS recovery, not a blind retry.
 * Not crash-atomic, externally locked or attribute/timestamp preserving.
 * Readonly targets refused; no overwrite on create. No original data inputs. */
unsigned __cdecl key_editor_file_save(const char *,const unsigned char __far *,const unsigned char __far *,directory_replace_result *);
#endif
