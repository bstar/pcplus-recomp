#ifndef PCPLUS_ELAPSED_VIEW_H
#define PCPLUS_ELAPSED_VIEW_H
/* Same serviced live/view frame owner as Redisplay; no private borrowed frame. */
extern unsigned terminal_elapsed_view_active;
void __cdecl elapsed_view_open(void);
unsigned __cdecl elapsed_view_poll(void);
void __cdecl elapsed_view_draw(unsigned short __far *);
void __cdecl elapsed_view_close(void);
#endif
