#ifndef PCPLUS_VIEWER_EXTERNAL_H
#define PCPLUS_VIEWER_EXTERNAL_H
/* Foreground DOS16 DS=SS. Native PRM035Dh stores at most64 command bytes
 * plus NUL. External parameter input allows48 bytes plus NUL. Build the
 * literal COMSPEC command: configured bytes, one space, parameters bytes.
 * No quote insertion, TEXT expansion, path resolution or execution here.
 * The native80-byte temporary is replaced by a checked114-byte maximum.
 * All spans must fit their segment and20-bit address space. Output/length
 * must not overlap inputs or one another. Errors/disabled change nothing.
 */
#define VIEWER_EXTERNAL_PRM_OFFSET 0x35d
#define VIEWER_EXTERNAL_CONFIG_BYTES 65
#define VIEWER_EXTERNAL_PARAMETER_BYTES 49
#define VIEWER_EXTERNAL_COMMAND_BYTES 114
enum { VEXT_OK=0,VEXT_DISABLED,VEXT_ARGUMENT,VEXT_CONFIG,VEXT_PARAMETERS,VEXT_CAPACITY };
unsigned __far __cdecl viewer_external_build(const unsigned char __far *,
 const char __far *,char __far *,unsigned,unsigned __far *);
#endif
