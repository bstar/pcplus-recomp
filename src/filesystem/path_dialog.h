#ifndef PCPLUS_PATH_DIALOG_H
#define PCPLUS_PATH_DIALOG_H
#define PATH_CONTROL_ACTION 120U
/* The shared serviced viewer owns the frame and serial/parser scheduling.
 * Events0=open,1=key,2=draw,4=stop. Return1 keeps the dialog,0 closes it. */
unsigned short __far __cdecl path_dialog_event(unsigned short,unsigned short,unsigned short __far *);
/* BIOS row/column while the dialog owns the visible frame, otherwiseFFFF. */
unsigned short __far __cdecl path_dialog_cursor(void);
/* Original Insert cursor: start=floor(saved end/2)+1, unchanged end. */
unsigned short __far __cdecl path_dialog_shape(unsigned short saved);
#endif
