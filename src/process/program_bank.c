/* The adapters themselves stay in _TEXT so their near platform calls use
 * the correct CS. PROGRAMCODE calls only these declared far entries. */
#include "native_process.h"
#include "native_display.h"
#include "process_serial.h"
#include <dos.h>
#include <i86.h>
#include <string.h>
#define PROGRAM_BANK_IMPLEMENTATION
#include "program_bank.h"
unsigned __far __cdecl program_bank_native_display_probe(void)
{return native_display_probe();}
unsigned __far __cdecl program_bank_native_display_capture(void)
{return native_display_capture();}
unsigned __far __cdecl program_bank_native_display_restore(void)
{return native_display_restore();}
void __far __cdecl program_bank_native_display_discard(void)
{native_display_discard();}
unsigned __far __cdecl program_bank_aspect_process_serial_pause(void)
{return aspect_process_serial_pause();}
unsigned __far __cdecl program_bank_aspect_process_serial_resume(void)
{return aspect_process_serial_resume();}
unsigned __far __cdecl program_bank_aspect_serial_poll(void)
{return aspect_serial_poll();}
extern unsigned __cdecl program_ui_key_available(void);
unsigned __far __cdecl program_bank_program_ui_key_available(void)
{return program_ui_key_available();}
extern unsigned __cdecl program_ui_wait(void);
unsigned __far __cdecl program_bank_program_ui_wait(void)
{return program_ui_wait();}
extern void __cdecl program_ui_shape(void);
void __far __cdecl program_bank_program_ui_shape(void)
{program_ui_shape();}
extern void __cdecl program_ui_cursor(unsigned value);
void __far __cdecl program_bank_program_ui_cursor(unsigned value)
{program_ui_cursor(value);}
extern void __cdecl program_ui_clear(unsigned value);
void __far __cdecl program_bank_program_ui_clear(unsigned value)
{program_ui_clear(value);}
extern void __cdecl program_ui_mode(unsigned value);
void __far __cdecl program_bank_program_ui_mode(unsigned value)
{program_ui_mode(value);}
extern void __cdecl program_ui_scanlines(unsigned value);
void __far __cdecl program_bank_program_ui_scanlines(unsigned value)
{program_ui_scanlines(value);}
unsigned __far __cdecl program_bank_native_process_search(const char *path,const char *tail,char **environment,native_process_result *result)
{return native_process_search(path,tail,environment,result);}
unsigned __far __cdecl program_bank_native_process_system(const char *command,char **environment,native_process_result *result)
{return native_process_system(command,environment,result);}
int __far __cdecl program_bank_int86(int number,union REGS *in,union REGS *out)
{return int86(number,in,out);}
void * __far __cdecl program_bank_memset(void *dest,int value,unsigned count)
{return memset(dest,value,count);}
#if defined(ASPECT_EXTERNAL_DIAGNOSTIC)
extern void __cdecl runtime_external_phase(unsigned);
void __far __cdecl program_bank_phase(unsigned phase){runtime_external_phase(phase);}
#endif
