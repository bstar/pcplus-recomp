#include "phone_log_controls.h"
#include "phone_log_disk.h"
#include "phone_log_events.h"
#include "phone_log_lifecycle.h"
#include "phone_log_file.h"
#include <dos.h>
extern unsigned command_menu_active,redisplay_active;
extern unsigned short __far redisplay_view[2000];
#pragma aux redisplay_view "redisplay_view";
static unsigned confirming=0,note=0;
#define UI_TEXT __based(__segname("_CODE"))
#define TEXT(n,s) static const char UI_TEXT n[]=s
TEXT(title,"Telephone call log");
TEXT(footer,"R: retry   F5: refresh   Esc: back   Alt-X: exit");
TEXT(state_label,"State:");TEXT(path_label,"Fixed destination:");
TEXT(queued_label,"Queued:");TEXT(committed_label,"Committed:");TEXT(generation_label,"Generation:");
TEXT(status_label,"Scheduler:");TEXT(file_label,"File:");TEXT(dos_label,"DOS:");TEXT(close_label,"Close:");
TEXT(pending_label,"Retained END:");TEXT(rollback_label,"Rollback:");
TEXT(ready,"Ready");TEXT(active,"Call active");TEXT(disabled,"Logging is disabled");
TEXT(retry,"Retry required");TEXT(recovery,"Recovery required");TEXT(fault,"Event clock/input fault");
TEXT(confirm,"Retry retained records? Y/N");
TEXT(accepted,"Retry acknowledged; close to resume");TEXT(cancelled,"Retry canceled");
TEXT(nothing,"No retry is pending");TEXT(blocked,"Call log busy; try again when idle");
TEXT(unsafe,"Recovery required: exit and inspect the log.");
TEXT(protected,"Retained records and uncertain file ownership stay protected.");
TEXT(clock_fault,"Uncaptured events cannot be repaired by a disk retry.");
static void text(unsigned short __far *frame,unsigned at,const char __far *s,unsigned attr)
{while(*s && at<2000)frame[at++]=attr|(unsigned char)*s++;}
static void near_text(unsigned short __far *frame,unsigned at,const char *s)
{unsigned i;for(i=0;i<64 && s[i] && at+i<2000;++i)frame[at+i]=0x0700|(unsigned char)s[i];}
static void number(unsigned short __far *frame,unsigned at,unsigned long value)
{char digits[10];unsigned n=0;do{digits[n++]=(char)('0'+value%10);value/=10;}while(value);while(n && at<2000)frame[at++]=0x0700|(unsigned char)digits[--n];}
static unsigned context(unsigned short __far *frame)
{return command_menu_active==1 && redisplay_active==1 && frame &&
 FP_SEG(frame)==FP_SEG(redisplay_view) && FP_OFF(frame)==FP_OFF(redisplay_view);}
static unsigned eligibility(phone_log_queue_snapshot *queue)
{
 unsigned status=phone_log_queue_inspect(queue),file;
 if(status)return status;
 file=phone_log_file_initialize();
 if(queue->recovery_required || file==PLF_RECOVERY || phone_log_file_result.handle_uncertain || phone_log_file_result.recovery_required)return PLQ_RECOVERY;
 if(file)return PLQ_BUSY;
 if(!queue->enabled)return PLQ_DISABLED;
 if(phone_log_event_fault())return PLQ_CLOCK;
 return queue->retry_required || terminal_phone_log_disk_status?PLQ_OK:PLQ_STATE;
}
unsigned __cdecl phone_log_controls_event(unsigned event,unsigned key,unsigned short __far *frame)
{
 phone_log_queue_snapshot queue;phone_log_lifecycle_snapshot life;
 unsigned status,i;unsigned char c=(unsigned char)key;char path[64];
 if(!context(frame))return 0;
 if(event==4){confirming=note=0;return 0;}
 if(event>2)return 1;
 status=eligibility(&queue);
 if(event==0)confirming=note=0;
 else if(event==1){
  if(confirming){
   if(c=='y'||c=='Y'){
    note=phone_log_disk_retry()?3:1;confirming=0;status=eligibility(&queue);
   }else if(c=='n'||c=='N'||c==27){confirming=0;note=2;}
  }else if(c==27)return 0;
  else if(c=='r'||c=='R'){
   if(status==PLQ_OK){confirming=1;note=0;}
   else note=3;
  }
 }
 for(i=0;i<2000;++i)frame[i]=0x0720;
 for(i=0;i<80;++i)frame[i]=frame[1920+i]=0x1f20;
 text(frame,2,title,0x1f00);text(frame,1922,footer,0x1f00);
 if(phone_log_queue_inspect(&queue) || phone_log_lifecycle_inspect(&life)){
  text(frame,322,blocked,0x0f00);return 1;
 }
 text(frame,242,state_label,0x0700);
 if(!queue.enabled)text(frame,250,disabled,0x0f00);
 else if(status==PLQ_RECOVERY)text(frame,250,recovery,0x0f00);
 else if(phone_log_event_fault())text(frame,250,fault,0x0f00);
 else if(queue.retry_required || terminal_phone_log_disk_status)text(frame,250,retry,0x0f00);
 else if(life.active)text(frame,250,active,0x0f00);
 else text(frame,250,ready,0x0f00);
 text(frame,402,path_label,0x0700);
 if(!phone_log_queue_destination(path,sizeof(path)))near_text(frame,482,path);
 text(frame,642,queued_label,0x0700);number(frame,650,queue.queued);
 text(frame,662,committed_label,0x0700);number(frame,673,queue.committed_events);
 text(frame,687,generation_label,0x0700);number(frame,699,life.generation);
 text(frame,802,status_label,0x0700);number(frame,813,terminal_phone_log_disk_status);
 text(frame,826,file_label,0x0700);number(frame,832,phone_log_file_result.status);
 text(frame,842,dos_label,0x0700);number(frame,847,phone_log_file_result.dos_error);
 text(frame,858,close_label,0x0700);number(frame,865,phone_log_file_result.close_error);
 text(frame,962,pending_label,0x0700);number(frame,976,life.pending);
 text(frame,990,rollback_label,0x0700);number(frame,1000,phone_log_file_result.rollback_error);
 if(confirming)text(frame,1282,confirm,0x0f00);
 else if(note==1)text(frame,1282,accepted,0x0f00);
 else if(note==2)text(frame,1282,cancelled,0x0f00);
 else if(status==PLQ_RECOVERY){text(frame,1282,unsafe,0x0f00);text(frame,1442,protected,0x0700);}
 else if(status==PLQ_CLOCK)text(frame,1282,clock_fault,0x0f00);
 else if(status==PLQ_DISABLED)text(frame,1282,disabled,0x0f00);
 else if(note){if(status==PLQ_STATE)text(frame,1282,nothing,0x0f00);else text(frame,1282,blocked,0x0f00);}
 return 1;
}
