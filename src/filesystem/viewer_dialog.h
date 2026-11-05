#ifndef PCPLUS_VIEWER_DIALOG_H
#define PCPLUS_VIEWER_DIALOG_H
#define FILE_VIEWER_ACTION 123U
/* Shared serviced modal frame;0=open,1=key,2=draw,3=one step,4=stop.
 * Return1 retains/paints,2 retains without paint,0 closes. Bind only the
 * checked inactive redisplay snapshot before opening. No extra page allocation.
 * Shutdown resolves known ownership once; uncertainty remains owned to DOS exit.
 */
unsigned short __far __cdecl viewer_dialog_bind(unsigned char __far *);
unsigned short __far __cdecl viewer_dialog_event(unsigned short,unsigned short,unsigned short __far *);
unsigned short __far __cdecl viewer_dialog_cursor(void);
unsigned short __far __cdecl viewer_dialog_shape(unsigned short);
unsigned short __far __cdecl viewer_dialog_pending(void);
unsigned short __far __cdecl viewer_dialog_fullscreen(void);
unsigned short __far __cdecl viewer_dialog_owned(void);
unsigned short __far __cdecl viewer_dialog_unsafe(void);
unsigned short __far __cdecl viewer_dialog_shutdown(void);
#endif
