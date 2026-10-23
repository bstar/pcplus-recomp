#include "notice.h"
#include "notice_input.h"
static unsigned owned;
unsigned __far __cdecl notice_input_open(const mouse_settings *settings)
{
 unsigned status;
 if(notice_active()||owned||mouse_owner_phase()!=MOUSE_CLOSED)return MOUSE_STATE;
 /* Publish before the first driver mutation: an outer nonlocal unwind may
  * abandon mouse_owner_open after it has acquired quarantined storage. */
 owned=1;status=mouse_owner_open(settings);
 if(mouse_owner_phase()==MOUSE_CLOSED)owned=0;
 return status;
}
unsigned __far __cdecl notice_input_close(void)
{
 unsigned status;
 if(notice_active())return MOUSE_STATE;
 if(!owned)return mouse_owner_phase()==MOUSE_CLOSED?MOUSE_OK:MOUSE_STATE;
 status=mouse_owner_close();if(!status&&mouse_owner_phase()==MOUSE_CLOSED)owned=0;
 return status;
}
unsigned __far __cdecl notice_input_peek(unsigned *key)
{return owned?mouse_owner_peek(key):MOUSE_STATE;}
unsigned __far __cdecl notice_input_read(unsigned *key)
{return owned?mouse_owner_key(key):MOUSE_STATE;}
