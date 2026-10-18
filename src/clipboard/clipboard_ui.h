#ifndef PCPLUS_CLIPBOARD_UI_H
#define PCPLUS_CLIPBOARD_UI_H
/* CONFIG_CODE-local UI, sharing the redisplay owner's frozen frame.
 * event0 opens,1 handles a BIOS key,3 polls/paints,4 cancels and closes.
 * Returns whether the clipboard still owns the local view. */
unsigned __cdecl clipboard_ui_event(unsigned event,unsigned key,
 const unsigned short __far *underlay);
extern unsigned clipboard_ui_active,clipboard_paste_pending,clipboard_ui_visible;
/* Resident transport callback:0 queues a whole packet only on empty TX,
 * 1 probes remaining actual UART writes,2 removes the unsent owned prefix.
 * Queue returns0 on success,ffff on refusal; probe returns0..196. */
unsigned __cdecl clipboard_transport(unsigned operation,
 const unsigned char *bytes,unsigned size);
#endif
