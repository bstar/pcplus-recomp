/* Maintained terminal policy around the recovered producer/consumer. */
#include "owner.h"
extern void __cdecl mouse_owner_bootstrap(void);
extern unsigned __cdecl mouse_terminal_release_unused(void);
/* Source-owned fallback for an explicit command line without a PRM. */
static mouse_settings selected={8,8,{1,1,1,1,1,1}};
void __cdecl terminal_mouse_bootstrap(void){mouse_owner_bootstrap();}
unsigned __cdecl terminal_mouse_stage(const unsigned char *image,unsigned bytes)
{
 if(mouse_owner_phase()!=MOUSE_CLOSED)return 15;
 return mouse_settings_decode(image,bytes,&selected)==MOUSE_OK?0:15;
}
unsigned __cdecl terminal_mouse_start(void)
{
 unsigned status;
 if(mouse_terminal_release_unused())return 15;
 status=mouse_owner_open(&selected);
 /* Missing/unsupported storage API with no acquired owner permits BIOS input. */
 if(status==MOUSE_DRIVER&&mouse_owner_phase()==MOUSE_CLOSED)return 0;
 return status==MOUSE_OK?0:15;
}
unsigned __cdecl terminal_mouse_pause(void)
{return mouse_owner_phase()==MOUSE_CLOSED?0:mouse_owner_suspend();}
unsigned __cdecl terminal_mouse_resume(void)
{return mouse_owner_phase()==MOUSE_CLOSED?0:mouse_owner_resume();}
unsigned __cdecl terminal_mouse_stop(void){return mouse_owner_close();}
