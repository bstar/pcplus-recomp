#ifndef PCPLUS_ASPECT_SCREEN_RUNTIME_H
#define PCPLUS_ASPECT_SCREEN_RUNTIME_H
/* Native data words: normal, configured-wide, rows, last-row, last-col,stride. */
extern unsigned runtime_screen_values[6];
void __cdecl runtime_screen_enter(void);
void __cdecl runtime_screen_scroll(unsigned,unsigned,unsigned,unsigned);
void __cdecl runtime_screen_box(unsigned,unsigned,unsigned);
unsigned __cdecl runtime_screen_reset_attribute(void);
void __cdecl runtime_screen_clear(void);
void __cdecl runtime_screen_locate(unsigned,unsigned);
unsigned __cdecl runtime_screen_read(unsigned);
void __cdecl runtime_screen_write(unsigned,unsigned);
void __cdecl runtime_screen_home(void);
#endif
