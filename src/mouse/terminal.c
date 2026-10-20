/* Maintained terminal policy around the recovered producer/consumer. */
#include "owner.h"
extern void __cdecl mouse_owner_bootstrap(void);
extern unsigned __cdecl mouse_terminal_release_unused(void);
/* Source-owned fallback for an explicit command line without a PRM. */
static mouse_settings selected={8,8,{1,1,1,1,1,1}};
static mouse_settings offered;
static unsigned offered_valid;
void __cdecl terminal_mouse_bootstrap(void){mouse_owner_bootstrap();offered_valid=0;}
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
/* Internal CONFIG policy: success returns0 or change bit16384; failure15.
 * Staging and publication perform no reset/init or heap replacement. */
unsigned __cdecl terminal_mouse_offer(const unsigned char *image,unsigned bytes)
{
 unsigned phase=mouse_owner_phase(),i,changed=0;
 offered_valid=0;
 if(phase!=MOUSE_CLOSED&&phase!=MOUSE_SUSPENDED)return 15;
 if(mouse_settings_decode(image,bytes,&offered)!=MOUSE_OK)return 15;
 for(i=0;i<sizeof(selected);++i)if(((unsigned char *)&selected)[i]!=((unsigned char *)&offered)[i])changed=1;
 offered_valid=changed?2:1;return changed?16384U:0;
}
void __cdecl terminal_mouse_discard(void){offered_valid=0;}
unsigned __cdecl terminal_mouse_commit(void)
{
 unsigned i,status;
 if(offered_valid==2){
  if(mouse_owner_phase()==MOUSE_SUSPENDED){
   status=mouse_owner_reconfigure(&offered);
   if(status){offered_valid=0;return status;}
  }else if(mouse_owner_phase()!=MOUSE_CLOSED){offered_valid=0;return MOUSE_STATE;}
  for(i=0;i<sizeof(selected);++i)((unsigned char *)&selected)[i]=((unsigned char *)&offered)[i];
 }
 offered_valid=0;return 0;
}
