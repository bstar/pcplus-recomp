#ifndef PCPLUS_COMPILER_LEASE_H
#define PCPLUS_COMPILER_LEASE_H
/* Maintained experimental component, not a recovered original API.
 * The parent alone initializes its trusted resident boundary. Resident code
 * and storage lie below it. The optional bank can live in the lent tail;
 * preparation returns before shrink; finalization follows verified restore.
 * The integration/linker must prove placement and prohibit other consumers.
 * Begin/end execute on the checked immediate child's DS=SS stack. No caller
 * pointer survives a call. No parent tail consumer may run while lent.
 * Any failed end keeps the lease: callers MUST NOT resume tail consumers.
 * DOS4+ exclusive no-inherit files; source-only component, not enabled in app. */
enum {CL_OK,CL_STATE,CL_IDENTITY,CL_ARGUMENT,CL_IO,CL_RESIZE,CL_RESTORE,CL_CORRUPT,CL_UNSUPPORTED};
enum {CL_IDLE,CL_BACKING,CL_LENT,CL_RESTORING,CL_CLEANUP,CL_PREPARED};
unsigned __far __cdecl compiler_lease_init(unsigned,unsigned,unsigned);
unsigned __far __cdecl compiler_lease_begin(unsigned,unsigned);
unsigned __far __cdecl compiler_lease_end(unsigned,unsigned);
/* 0 phase,1 full paras,2 keep,3 memory valid,4 DOS error,5 checksum,
 *6 parent PSP,7 child PSP,8 no-inherit handle,9 next filename sequence;
 * diagnostic/owner use only. DOS error is the last captured failure. */
unsigned __far __cdecl compiler_lease_info(unsigned);
#endif
