#ifndef PCPLUS_NATIVE_FILE_BRIDGE_H
#define PCPLUS_NATIVE_FILE_BRIDGE_H
/* Maintained opaque FILE-token adapter for recovered receiver call sites.
 * Prepare transfer_download_begin(target,stage) first; pass the normalized stage
 * as native filename, with empty native download prefix/path-test false.
 * Token1 is not a CRT FILE object and must never enter native CRT internals.
 * Only these fwrite/fclose/open callbacks may consume it. Near cdecl, DS=SS.
 * Native return1 and prior wireACK do not establish durable file success:
 * owner must check storage failure state, then explicitly finish/install.
 * Any owner failure must abort; close only seals and never installs a partial.
 */
unsigned __cdecl transfer_native_open(const char *path,const char *mode);
unsigned __cdecl transfer_native_write(const void *data,unsigned size,unsigned count,unsigned file);
unsigned __cdecl transfer_native_close(unsigned file);
#endif
