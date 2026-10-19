/* Foreground-only invitation owner. Canonical wire recognition is separate;
 * ordinary delivery and admission remain resident services. Never unreceive
 * bytes into the UART ring. Initialization is explicit for the ASM entry. */
#include "zmodem_autostart.h"
#include "../config/transfer_import.h"
#include <string.h>
transfer_import_settings terminal_transfer_preferences={0,"."};
extern void __cdecl terminal_auto_deliver(unsigned);
extern unsigned __cdecl terminal_auto_allowed(void);
extern unsigned __cdecl terminal_auto_start(void);
extern unsigned long __cdecl terminal_auto_ticks(void);
static za_state invitation;
static unsigned char output[20];
static unsigned emitting;
static unsigned long last_tick;
static void emit(unsigned count)
{unsigned i;emitting=1;for(i=0;i<count;++i)terminal_auto_deliver(output[i]);emitting=0;}
void __cdecl terminal_autostart_initialize(void)
{za_reset(&invitation);emitting=0;last_tick=0;}
void __cdecl terminal_autostart_flush(void)
{unsigned n;if(emitting || !invitation.count)return;n=za_flush(&invitation,output);emit(n);}
void __cdecl terminal_autostart_poll(void)
{
 unsigned long now,elapsed;
 if(!invitation.count)return;
 now=terminal_auto_ticks();
 /* BIOS ticks restart at midnight; preserve the same inactivity interval
  * across that boundary. A backwards clock adjustment expires safely. */
 elapsed=now>=last_tick?now-last_tick:now+0x1800b0UL-last_tick;
 if(!terminal_auto_allowed() || elapsed>=36UL)terminal_autostart_flush();
}
void __cdecl terminal_autostart_input(unsigned value)
{
 unsigned n,status;
 if(!terminal_auto_allowed()){
  terminal_autostart_flush();terminal_auto_deliver(value);return;
 }
 status=za_feed(&invitation,value,output,&n);
 if(invitation.count)last_tick=terminal_auto_ticks();
 emit(n);
 if(status==ZA_START && !terminal_auto_start()){
  /* The admission check can refuse a transfer. The validated invitation is
   * still in held[], so refusal never manufactures or discards UART bytes. */
  memcpy(output,invitation.held,20);emit(20);
 }
}
