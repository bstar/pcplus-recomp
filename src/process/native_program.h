#ifndef PCPLUS_NATIVE_PROGRAM_H
#define PCPLUS_NATIVE_PROGRAM_H
#include "native_process.h"
#if defined(NATIVE_PROGRAM_FAR)
#define NATIVE_PROGRAM_CODE __far
#else
#define NATIVE_PROGRAM_CODE
#endif
/* Composed component, not yet a published ASPECT/terminal application service.
 * Text page0 with standard BIOS font geometry; caller must reconcile renderer,
 * mouse and VM/parent leases before using it in the application. */
enum { NATIVE_PROGRAM_OK,NATIVE_PROGRAM_ARGUMENT,NATIVE_PROGRAM_BUSY,
 NATIVE_PROGRAM_DISPLAY,NATIVE_PROGRAM_SERIAL,NATIVE_PROGRAM_PROCESS,NATIVE_PROGRAM_BREAK };
typedef struct native_program_result {
 unsigned status,display_status,serial_status,view_reset,wait_key;
 native_process_result process;
} native_program_result;
unsigned NATIVE_PROGRAM_CODE __cdecl native_program_execute(const char *program,const char *tail,
 unsigned processor,unsigned wait,unsigned save_screen,native_program_result *result);
extern unsigned native_program_busy,native_program_waiting;
#if defined(ASPECT_EXTERNAL_UNWIND)
unsigned NATIVE_PROGRAM_CODE __cdecl native_program_recover(unsigned *view_reset);
#endif
#endif
