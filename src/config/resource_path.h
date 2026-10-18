#ifndef PCPLUS_RESOURCE_PATH_H
#define PCPLUS_RESOURCE_PATH_H
#define RESOURCE_PATH_CAPACITY 64U
enum { RESOURCE_PATH_OK=0, RESOURCE_PATH_ARGUMENT, RESOURCE_PATH_ABSENT,
       RESOURCE_PATH_ENVIRONMENT, RESOURCE_PATH_SIZE };
/* DOS16 near-cdecl, DS=SS. Read PSP environment via its bounded MCB extent.
 * First exact uppercase PCPLUS= wins; empty/missing values are absent. The
 * value is one directory, not PATH syntax. Append backslash unless present.
 * Leaf is ASCII8.3 (letters/digits/_/-), output is a caller-owned64-byte buffer.
 * No DOS calls or file probes. Failures preserve output. Validate the complete
 * environment terminator before copying. Output cannot alias PSP/environment.
 * MCB shape/extent checks are not a complete DOS heap ownership proof. */
unsigned __cdecl resource_pcplus_path(unsigned psp,const char *leaf,char *output);
#endif
