#ifndef PCPLUS_PHONE_LOG_CONTROLS_H
#define PCPLUS_PHONE_LOG_CONTROLS_H
/* Borrow the exact admitted redisplay frame. All actions are RAM-only.
 * 0=open,1=key,2=redraw,4=close. Return1 retains pane,0 returns to menu. */
unsigned __cdecl phone_log_controls_event(unsigned,unsigned,unsigned short __far *);
#endif
