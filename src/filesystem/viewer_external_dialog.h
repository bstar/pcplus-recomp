#ifndef PCPLUS_VIEWER_EXTERNAL_DIALOG_H
#define PCPLUS_VIEWER_EXTERNAL_DIALOG_H
#include "../process/dos_exec.h"
/* F600 belongs to browser redial; keep the private viewer action distinct. */
#define VIEWER_EXTERNAL_ACTION 0xf300U
unsigned __far __cdecl viewer_external_select(void);
#ifdef TERMINAL_EXTERNAL_EDITOR
#define FILE_EDITOR_ACTION 124U
#define EDITOR_EXTERNAL_PRM_OFFSET 0x39e
unsigned __far __cdecl editor_external_select(void);
#endif
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
