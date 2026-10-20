#ifndef PCPLUS_BREAK_OWNER_H
#define PCPLUS_BREAK_OWNER_H
/* Foreground DS=SS=DGROUP, IF1. Raw native routines remain callee-cleaned;
 * callers use this C owner, not their unguarded entry points. Keep code/data
 * resident while phase != CLOSED, including quarantine. */
enum { BREAK_OK=0,BREAK_ARGUMENT,BREAK_STATE,BREAK_QUARANTINE };
enum { BREAK_CLOSED=0,BREAK_READY,BREAK_SUSPENDED,BREAK_TRANSITION,BREAK_HELD };
unsigned __cdecl native_break_open(unsigned disable_extended);
unsigned __cdecl native_break_suspend(void);
unsigned __cdecl native_break_resume(void);
unsigned __cdecl native_break_close(void);
unsigned __cdecl native_break_recover(void);
unsigned __cdecl native_break_phase(void);
#endif
