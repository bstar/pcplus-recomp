#ifndef PCPLUS_COMMAND_MENU_H
#define PCPLUS_COMMAND_MENU_H
/* CONFIG_CODE-local foreground view. The redisplay owner supplies the frame;
 * ordinary commands return to the dispatcher. Recorder dialogs use the checked
 * far file owner only after a serviced byte-owner/boundary admission check.
 * event0 opens,1 handles a BIOS key,4 stops. A selected existing local command
 * is returned through command_menu_action only after releasing the view. */
extern unsigned command_menu_active,command_menu_action;
unsigned __cdecl command_menu_event(unsigned short event,unsigned short key,
 unsigned short __far *frame);
#endif
