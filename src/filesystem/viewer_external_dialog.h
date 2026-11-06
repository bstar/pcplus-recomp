#ifndef PCPLUS_VIEWER_EXTERNAL_DIALOG_H
#define PCPLUS_VIEWER_EXTERNAL_DIALOG_H
#include "../process/dos_exec.h"
#define VIEWER_EXTERNAL_ACTION 0xf600U
unsigned __far __cdecl viewer_external_select(void);
unsigned __far __cdecl viewer_external_event(unsigned,unsigned,unsigned short __far *);
unsigned __far __cdecl viewer_external_cursor(void);
unsigned __far __cdecl viewer_external_shape(unsigned);
unsigned __far __cdecl viewer_external_owned(void);
unsigned __far __cdecl viewer_external_unsafe(void);
unsigned __far __cdecl viewer_external_queued(void);
unsigned __far __cdecl viewer_external_start(void);
unsigned __far __cdecl viewer_external_execute(process_result *);
void __far __cdecl viewer_external_cancel(void);
#endif
