#ifndef PCPLUS_FILE_DIALOG_H
#define PCPLUS_FILE_DIALOG_H
#include "find_owner.h"
#define FILE_DIRECTORY_ACTION 122U
/* Serviced modal frame. Events0=open,1=key,2=draw,3=one search step,4=stop.
 * Foreground DS=SS. A step performs at most one DOS enumeration call.
 * Return1 retains/paints,2 retains without paint,0 closes the dialog.
 * All persistent state is FILE_CODE. Pending prevents BIOS-tick sleep between
 * bounded search steps; UART/keyboard service still runs on every main turn. */
unsigned short __far __cdecl file_dialog_event(unsigned short,unsigned short,unsigned short __far *);
unsigned short __far __cdecl file_dialog_cursor(void);
unsigned short __far __cdecl file_dialog_pending(void);
unsigned short __far __cdecl file_dialog_shape(unsigned short);
/* Bounded38-column row; output requires39 bytes including NUL. Input near. */
void __far __cdecl file_dialog_format(const file_find_entry *,char __far *);
#endif
