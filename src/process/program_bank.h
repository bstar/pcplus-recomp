/* Explicit far adapters into the near CRT/platform segment. All near pointers
 * belong to the shared DGROUP, including C locals on the DS=SS stack. */
#ifndef PCPLUS_PROGRAM_BANK_H
#define PCPLUS_PROGRAM_BANK_H
unsigned __far __cdecl program_bank_native_display_probe(void);
unsigned __far __cdecl program_bank_native_display_capture(void);
unsigned __far __cdecl program_bank_native_display_restore(void);
void __far __cdecl program_bank_native_display_discard(void);
unsigned __far __cdecl program_bank_aspect_process_serial_pause(void);
unsigned __far __cdecl program_bank_aspect_process_serial_resume(void);
unsigned __far __cdecl program_bank_aspect_serial_poll(void);
unsigned __far __cdecl program_bank_program_ui_key_available(void);
unsigned __far __cdecl program_bank_program_ui_wait(void);
void __far __cdecl program_bank_program_ui_shape(void);
void __far __cdecl program_bank_program_ui_cursor(unsigned value);
void __far __cdecl program_bank_program_ui_clear(unsigned value);
void __far __cdecl program_bank_program_ui_mode(unsigned value);
void __far __cdecl program_bank_program_ui_scanlines(unsigned value);
unsigned __far __cdecl program_bank_native_process_search(const char *path,const char *tail,char **environment,native_process_result *result);
unsigned __far __cdecl program_bank_native_process_system(const char *command,char **environment,native_process_result *result);
int __far __cdecl program_bank_int86(int number,union REGS *in,union REGS *out);
void * __far __cdecl program_bank_memset(void *dest,int value,unsigned count);
#if defined(ASPECT_EXTERNAL_DIAGNOSTIC)
void __far __cdecl program_bank_phase(unsigned phase);
#endif
#ifndef PROGRAM_BANK_IMPLEMENTATION
#define native_display_probe program_bank_native_display_probe
#define native_display_capture program_bank_native_display_capture
#define native_display_restore program_bank_native_display_restore
#define native_display_discard program_bank_native_display_discard
#define aspect_process_serial_pause program_bank_aspect_process_serial_pause
#define aspect_process_serial_resume program_bank_aspect_process_serial_resume
#define aspect_serial_poll program_bank_aspect_serial_poll
#define program_ui_key_available program_bank_program_ui_key_available
#define program_ui_wait program_bank_program_ui_wait
#define program_ui_shape program_bank_program_ui_shape
#define program_ui_cursor program_bank_program_ui_cursor
#define program_ui_clear program_bank_program_ui_clear
#define program_ui_mode program_bank_program_ui_mode
#define program_ui_scanlines program_bank_program_ui_scanlines
#define native_process_search program_bank_native_process_search
#define native_process_system program_bank_native_process_system
#define int86 program_bank_int86
#define memset program_bank_memset
#if defined(ASPECT_EXTERNAL_DIAGNOSTIC)
#undef external_phase
#define external_phase(value) program_bank_phase(value)
#endif
#endif
#endif
