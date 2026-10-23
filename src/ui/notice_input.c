#include "notice.h"
#include "notice_input.h"
#ifdef NOTICE_INPUT_EXIT_GUARD
#include "notice_input_exit.h"
#endif
static unsigned owned;
#ifdef ASPECT_NOTICE_HELP
#include "notice_help.h"
#include "notice_window.h"
#include "../help/notice_content.h"
static unsigned help_enabled,help_generation;
static void __far *help_identity;
unsigned __far __cdecl notice_help_active(void){return help_view_active();}
unsigned __far __cdecl notice_help_configure(unsigned enabled)
{
 if(enabled>1||!owned||notice_active()||help_view_active())return MOUSE_STATE;
 help_enabled=enabled;return MOUSE_OK;
}
unsigned __far __cdecl notice_help_close(void)
{
 if(!help_view_active())return MOUSE_OK;
 if(!notice_window_phase()||notice_window_generation()!=help_generation||notice_window_identity()!=help_identity)return MOUSE_STATE;
 return help_view_close()?MOUSE_STATE:MOUSE_OK;
}
#endif
#ifdef NOTICE_INPUT_BIOS_FALLBACK
extern unsigned __cdecl notice_input_bios_peek(void),notice_input_bios_read(void);
static unsigned input_context(void);
#pragma aux input_context = "mov ax,ds" "mov dx,ss" "cmp ax,dx" "jne bad" "pushf" "pop ax" "and ax,0x200" "jmp done" "bad: xor ax,ax" "done:" value [ax] modify [dx];
static unsigned fallback_key(unsigned *key,unsigned read)
{
 unsigned value;
 if(!input_context()||!key||(unsigned long)(unsigned)key+sizeof(*key)>65536UL)return MOUSE_ARGUMENT;
 if(mouse_owner_phase()!=MOUSE_CLOSED)return MOUSE_STATE;
 value=notice_input_bios_peek();if(!value)return MOUSE_PENDING;
 *key=read?notice_input_bios_read():value;return MOUSE_OK;
}
#endif
unsigned __far __cdecl notice_input_open(const mouse_settings *settings)
{
 unsigned status;
 if(notice_active()||owned||mouse_owner_phase()!=MOUSE_CLOSED)return MOUSE_STATE;
#ifdef ASPECT_NOTICE_HELP
 help_enabled=0;
#endif
#ifdef NOTICE_INPUT_EXIT_GUARD
 if(notice_input_exit_prepare())return MOUSE_STATE;
#endif
 /* Publish before the first driver mutation: an outer nonlocal unwind may
  * abandon mouse_owner_open after it has acquired quarantined storage. */
 owned=1;status=mouse_owner_open(settings);
 if(mouse_owner_phase()==MOUSE_CLOSED)owned=0;
#ifdef NOTICE_INPUT_BIOS_FALLBACK
 if(status==MOUSE_DRIVER&&!owned){owned=2;return MOUSE_OK;}
#endif
 return status;
}
unsigned __far __cdecl notice_input_close(void)
{
 unsigned status;
 if(notice_active())return MOUSE_STATE;
#ifdef ASPECT_NOTICE_HELP
 if(notice_help_close())return MOUSE_STATE;
#endif
 if(!owned)return mouse_owner_phase()==MOUSE_CLOSED?MOUSE_OK:MOUSE_STATE;
#ifdef NOTICE_INPUT_BIOS_FALLBACK
 if(owned==2){if(mouse_owner_phase()!=MOUSE_CLOSED)return MOUSE_STATE;owned=0;return MOUSE_OK;}
#endif
 status=mouse_owner_close();if(!status&&mouse_owner_phase()==MOUSE_CLOSED)owned=0;
 return status;
}
#ifdef ASPECT_NOTICE_HELP
static unsigned raw_peek(unsigned *key)
#else
unsigned __far __cdecl notice_input_peek(unsigned *key)
#endif
{
#ifdef NOTICE_INPUT_BIOS_FALLBACK
 if(owned==2)return fallback_key(key,0);
#endif
 return owned?mouse_owner_peek(key):MOUSE_STATE;
}
#ifdef ASPECT_NOTICE_HELP
unsigned __far __cdecl notice_input_peek(unsigned *key)
{
 unsigned value,status;
 if(!input_context()||!key||(unsigned long)(unsigned)key+sizeof(*key)>65536UL)return MOUSE_ARGUMENT;
 status=raw_peek(&value);
 if(status==MOUSE_PENDING&&help_view_active())return help_view_key(0)?MOUSE_STATE:MOUSE_PENDING;
 if(status)return status;
 if(help_view_active()){
  status=notice_input_read(&value);if(status)return status;
  if(notice_window_generation()!=help_generation||notice_window_identity()!=help_identity)return MOUSE_STATE;
  status=help_view_key(value);return status?MOUSE_STATE:MOUSE_PENDING;
 }
 if(help_enabled&&notice_active()&&value==0x2c00){
  status=notice_input_read(&value);if(status)return status;
  if(value!=0x2c00)return MOUSE_STATE;
  help_generation=notice_window_generation();help_identity=notice_window_identity();
  status=help_view_open(notice_help_pages,2,0);
  return status?(status==HELP_VIEW_MEMORY?MOUSE_MEMORY:MOUSE_STATE):MOUSE_PENDING;
 }
 *key=value;return MOUSE_OK;
}
#endif
unsigned __far __cdecl notice_input_read(unsigned *key)
{
#ifdef NOTICE_INPUT_BIOS_FALLBACK
 if(owned==2)return fallback_key(key,1);
#endif
 return owned?mouse_owner_key(key):MOUSE_STATE;
}
unsigned __far __cdecl notice_input_active(void){return owned;}
