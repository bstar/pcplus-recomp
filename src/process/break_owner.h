#ifndef PCPLUS_BREAK_OWNER_H
#define PCPLUS_BREAK_OWNER_H
/* Foreground DS=SS=DGROUP, IF1. Raw native routines remain callee-cleaned;
 * callers use this C owner, not their unguarded entry points. Keep code/data
 * resident while phase != CLOSED, including quarantine. */
#if defined(NATIVE_BREAK_FAR)
#define NATIVE_BREAK_CODE __far
#else
#define NATIVE_BREAK_CODE
#endif
enum { BREAK_OK=0,BREAK_ARGUMENT,BREAK_STATE,BREAK_QUARANTINE };
enum { BREAK_CLOSED=0,BREAK_READY,BREAK_SUSPENDED,BREAK_TRANSITION,BREAK_HELD };
unsigned NATIVE_BREAK_CODE __cdecl native_break_open(unsigned disable_extended);
unsigned NATIVE_BREAK_CODE __cdecl native_break_suspend(void);
unsigned NATIVE_BREAK_CODE __cdecl native_break_resume(void);
unsigned NATIVE_BREAK_CODE __cdecl native_break_close(void);
unsigned NATIVE_BREAK_CODE __cdecl native_break_recover(void);
unsigned NATIVE_BREAK_CODE __cdecl native_break_phase(void);
#endif
