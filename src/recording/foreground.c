#include "foreground.h"
#include "dos_backend.h"
#include <string.h>
#include <stddef.h>
/* The banked wire callback reads this field without entering the owner. */
typedef char recording_state_offset_check[offsetof(recording_file,state)==136?1:-1];
typedef char recording_claimed_offset_check[offsetof(recording_file,claimed)==156?1:-1];
recording_file recording_terminal_owner;
unsigned recording_terminal_cookie=0x5243;
unsigned recording_terminal_replay,recording_terminal_unread_pointer;
char recording_terminal_path[64];
#ifdef __WATCOMC__
static const char __based(__segname("_CODE")) default_path[]="PCPLUS.ASP";
#else
static const char default_path[]="PCPLUS.ASP";
#endif
unsigned AR_FAR AR_CALL recording_terminal_initialize(void)
{
 unsigned i;
 if(recording_terminal_cookie==0x5243){
  memset(&recording_terminal_owner,0,sizeof(recording_terminal_owner));memset(recording_terminal_path,0,sizeof(recording_terminal_path));
  for(i=0;i<sizeof(default_path);++i)recording_terminal_path[i]=default_path[i];
  recording_terminal_cookie=0x5244;
  recording_terminal_replay=recording_terminal_unread_pointer=0;
 }else if(recording_terminal_cookie!=0x5244)return RF_STATE;
 if(recording_terminal_owner.state==RF_RECOVERY_STATE)return RF_RECOVERY;
 return recording_terminal_owner.claimed||recording_terminal_owner.handle_state||recording_terminal_owner.state==RF_RECORDING?RF_BUSY:RF_OK;
}
const recording_file * AR_FAR AR_CALL recording_terminal_inspect(void)
{return recording_terminal_cookie==0x5244?&recording_terminal_owner:0;}
unsigned AR_FAR AR_CALL recording_terminal_begin(unsigned mode,unsigned timeout)
{
 unsigned status=recording_terminal_initialize();
 if(status)return status;
 recording_terminal_replay=0;
 return recording_file_begin(&recording_terminal_owner,&recording_dos_ops,0,recording_terminal_path,mode,timeout);
}
unsigned AR_FAR AR_CALL recording_terminal_transmit(unsigned character)
{
 unsigned char byte=(unsigned char)character;
 return recording_terminal_cookie==0x5244?recording_file_transmit(&recording_terminal_owner,&byte,1):RF_STATE;
}
unsigned AR_FAR AR_CALL recording_terminal_receive(unsigned character)
{
 unsigned char byte=(unsigned char)character;
 return recording_terminal_cookie==0x5244?recording_file_receive(&recording_terminal_owner,&byte,1):RF_STATE;
}
unsigned AR_FAR AR_CALL recording_terminal_stop(void)
{
 unsigned status;
 if(recording_terminal_cookie!=0x5244)return RF_STATE;
 status=recording_file_stop(&recording_terminal_owner);
 if(recording_terminal_owner.state!=RF_RECORDING)recording_terminal_replay=0;
 return status;
}
unsigned AR_FAR AR_CALL recording_terminal_cancel(void)
{
 unsigned status;
 if(recording_terminal_cookie!=0x5244)return RF_STATE;
 status=recording_file_cancel(&recording_terminal_owner);
 if(recording_terminal_owner.state!=RF_RECORDING)recording_terminal_replay=0;
 return status;
}
unsigned AR_FAR AR_CALL recording_terminal_cleanup(void)
{return recording_terminal_cookie==0x5244?recording_file_cleanup(&recording_terminal_owner):RF_STATE;}
unsigned AR_FAR AR_CALL recording_terminal_shutdown(void)
{
 unsigned status;
 if(recording_terminal_cookie!=0x5244)return RF_STATE;
 if(recording_terminal_owner.busy)return RF_BUSY;
 recording_terminal_replay=0;
 status=recording_terminal_owner.status;
 if(recording_terminal_owner.state==RF_RECORDING)status=recording_file_cancel(&recording_terminal_owner);
 if(recording_terminal_owner.claimed||recording_terminal_owner.handle_state||recording_terminal_owner.stage_owned||recording_terminal_owner.backup_owned)return RF_RECOVERY;
 return status>=RF_WRITE&&status!=RF_CANCELLED?status:RF_OK;
}
