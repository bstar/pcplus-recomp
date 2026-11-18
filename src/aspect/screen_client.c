/* Scalar screen RPC client: overlay-local code, resident private admission. */
#include "resident_render.h"
#include "runtime.h"
#ifdef ASPECT_SCREEN_PARENT
extern unsigned __far __cdecl aspect_render_screen_ready(void);
extern unsigned __far __cdecl screen_wire_request(unsigned,unsigned);
extern unsigned __far __cdecl screen_client_check(void);
#pragma code_seg("SCRIPT_SCREEN_CODE","FARCODE")
unsigned __far __cdecl aspect_render_screen_scalar(unsigned operation,unsigned value)
{
 unsigned result;
 if(operation<32 || operation>36)return ASPECT_RUN_OPERAND;
 result=aspect_render_screen_ready();
 if(result)return result;
 result=screen_wire_request(operation,value);
 if(screen_client_check())return ASPECT_RUN_STATE;
 return result<=ASPECT_RUN_SERIAL || (result&0xff00U)==0xf000U?result:ASPECT_RUN_STATE;
}
#pragma code_seg()
#endif
