#ifndef PCPLUS_DIRECTORY_VIEW_H
#define PCPLUS_DIRECTORY_VIEW_H
/* Serviced read-only directory view, DIRECTORY_CODE far cdecl, DS=SS.
 * event0 open,1 key,2 redraw,3 foreground idle,4 force stop.
 * Return1 retains the view;0 returns to its caller. Only event3 reads data.
 * A key can open a file or request cancel; stop closes at most once.
 * TERMINAL_DIRECTORY_PREVIEW adds idle-only pure selection preparation and
 * bounded public-field preview. It does not adopt settings or dial. */
unsigned __far __cdecl directory_view_event(unsigned short,unsigned short,unsigned short __far *);
#endif
