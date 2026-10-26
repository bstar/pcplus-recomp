#ifndef PCPLUS_COMMAND_MENU_H
#define PCPLUS_COMMAND_MENU_H
/* Foreground view. The reference variant uses a separate code bank and a far
 * cdecl entry; older variants retain the CONFIG_CODE-local near entry.
 * The redisplay owner supplies the frame;
 * ordinary commands return to the dispatcher. Recorder dialogs use the checked
 * far file owner only after a serviced byte-owner/boundary admission check.
 * event0 opens,1 handles a BIOS key,4 stops. A selected existing local command
 * is returned through command_menu_action only after releasing the view. */
extern unsigned command_menu_active,command_menu_action;
#ifdef TERMINAL_REFERENCE
#define COMMAND_MENU_CALL __far __cdecl
#else
#define COMMAND_MENU_CALL __cdecl
#endif
unsigned COMMAND_MENU_CALL command_menu_event(unsigned short event,unsigned short key,
 unsigned short __far *frame);
#endif
