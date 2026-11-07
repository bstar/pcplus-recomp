#ifndef PCPLUS_META_LOADER_H
#define PCPLUS_META_LOADER_H
/* Foreground, DS=SS. Begin requires an exclusive retained-arena grant from
 * the parent. Each admitted step reads <=512 bytes or applies <=32 fixups.
 * READY alone permits enter; ACTIVE code/state remain until checked release.
 * HANDLE_OPEN means a close attempt remains; HELD may own an uncertain
 * descriptor even when that selector is zero. HELD is terminal until DOS exit. No allocation, implicit file search or UI. */
enum {META_LOAD_EMPTY,META_LOAD_READING,META_LOAD_FIXING,META_LOAD_READY,META_LOAD_ACTIVE,META_LOAD_FAILED,META_LOAD_HELD};
enum {META_LOAD_OK,META_LOAD_ARGUMENT,META_LOAD_BUSY,META_LOAD_IO,META_LOAD_IDENTITY,META_LOAD_FIXUP,META_LOAD_RECOVERY,META_LOAD_STATE};
enum {META_LOAD_PHASE,META_LOAD_REASON,META_LOAD_DOS_ERROR,META_LOAD_READ_AT,META_LOAD_FIX_AT,META_LOAD_HANDLE_OPEN,META_LOAD_BYTES,META_LOAD_RELOCATIONS,META_LOAD_BASE,META_LOAD_SEGMENT};
unsigned __far __cdecl meta_loader_begin(unsigned psp,unsigned granted);
unsigned __far __cdecl meta_loader_step(unsigned admitted);
unsigned __far __cdecl meta_loader_enter(void);
unsigned __far __cdecl meta_loader_release(void);
unsigned __far __cdecl meta_loader_cancel(void);
unsigned __far __cdecl meta_loader_hold(void);
unsigned __far __cdecl meta_loader_inspect(unsigned selector);
#endif
