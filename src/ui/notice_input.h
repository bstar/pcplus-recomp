#ifndef PCPLUS_NOTICE_INPUT_H
#define PCPLUS_NOTICE_INPUT_H
#include "../mouse/owner.h"
/* Foreground DS=SS/IF1. Separate executing-child mouse owner, never the
 * suspended parent's callback. Close only after notice retirement/unwind;
 * quarantine retains driver storage and requires repair before process exit. */
unsigned __far __cdecl notice_input_open(const mouse_settings *);
unsigned __far __cdecl notice_input_close(void);
unsigned __far __cdecl notice_input_peek(unsigned *);
unsigned __far __cdecl notice_input_read(unsigned *);
#endif
