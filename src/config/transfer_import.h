#ifndef PCPLUS_TRANSFER_IMPORT_H
#define PCPLUS_TRANSFER_IMPORT_H
#include "prm_dos.h"
/* Proved 2.01 fields; see ZMODEM_AUTOSTART_NATIVE.md. Near cdecl, DS=SS.
 * No filesystem or transport access. Unknown image bytes remain opaque.
 * Enabled is normalized from the original zero/nonzero word. Empty saved
 * prefix becomes "." at decode time; current-directory resolution is deferred
 * until transfer start. Nonempty paths retain their spelling and separators.
 */
typedef struct transfer_import_settings {
 unsigned auto_download;
 char download_directory[64];
} transfer_import_settings;
enum { TRANSFER_IMPORT_OK=0,TRANSFER_IMPORT_ARGUMENT,TRANSFER_IMPORT_PATH };
/* Bounded DOS83 directory syntax only, including roots, drive-relative paths,
 * an optional trailing separator and empty/current directory. No disk probe.
 * Reject parent traversal, devices, UNC, wildcards and unterminated input. */
unsigned __cdecl transfer_import_path(const char *path,unsigned capacity);
/* Image and destination must be disjoint, nonwrapping near objects. Failure
 * leaves destination unchanged. This neither identifies PRM version nor proves
 * directory existence, free space, destination fit or file-owner availability.
 */
unsigned __cdecl transfer_import_decode(const prm_dos_image *,transfer_import_settings *);
#endif
