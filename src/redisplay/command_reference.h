#ifndef PCPLUS_COMMAND_REFERENCE_H
#define PCPLUS_COMMAND_REFERENCE_H
/* Separate code/constant bank. No BIOS/DOS/UART access; the shared foreground
 * screen owner passes its frame. 0=open,1=key,2=redraw.
 * Return 0=remain,1=close,0x200=browser,0x100+item=run,0x300+item=help. */
unsigned __far __cdecl command_reference_event(unsigned short event,
 unsigned short key,unsigned short __far *frame);
unsigned __far __cdecl command_reference_unavailable(unsigned short key);
#endif
