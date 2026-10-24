#ifndef PCPLUS_SHADOW_OWNER_H
#define PCPLUS_SHADOW_OWNER_H
/* Foreground DOS controller for the admitted native 80/132 shadow geometry.
 * No UART/UI ownership or arbitrary asynchronous-fault recovery is supplied. */
#define SHADOW_OK 0
#define SHADOW_STATE 1
#define SHADOW_MEMORY 2
#define SHADOW_NATIVE 3
#define SHADOW_GUARD 4
#define SHADOW_RELEASE 5
unsigned __cdecl shadow_request(unsigned wide);
unsigned __cdecl shadow_close(void);
unsigned __cdecl shadow_owned_blocks(void);
unsigned __cdecl shadow_last_error(void);
void __far *__cdecl shadow_allocate(unsigned bytes);
void __cdecl shadow_release_request(void __far *pointer);
void __cdecl shadow_native_error(void);
#ifdef SHADOW_DIAGNOSTIC
extern unsigned shadow_fail_allocation,shadow_abort_after_allocation,shadow_fail_release;
extern unsigned shadow_abort_after_reset,shadow_reenter,shadow_reenter_result,shadow_foreign_release;
extern unsigned shadow_allocations,shadow_releases,shadow_native_errors;
#endif
#endif
