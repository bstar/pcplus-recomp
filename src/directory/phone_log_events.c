/* Foreground session boundaries only. No log-file append/poll here.
 * Shutdown reports retained RAM records until the disk scheduler is supplied. */
#include "phone_log_lifecycle.h"
#include "phone_log_events.h"
#ifdef PHONE_LOG_DISK
#include "phone_log_disk.h"
#endif
#include "directory_live.h"
#include <dos.h>
extern unsigned terminal_option_mask,terminal_directory_mode,terminal_exit_code;
extern char terminal_dial_target[64];
extern directory_live_plan terminal_directory_plan;
#pragma aux terminal_option_mask "terminal_option_mask";
#pragma aux terminal_directory_mode "terminal_directory_mode";
#pragma aux terminal_exit_code "terminal_exit_code";
#pragma aux terminal_dial_target "terminal_dial_target";
#pragma aux terminal_directory_plan "terminal_directory_plan";
unsigned terminal_phone_log_event_status=0,terminal_phone_log_event_epoch=0;
static unsigned event_fault=0;
static unsigned publish(unsigned status)
{
 terminal_phone_log_event_status=status;
 ++terminal_phone_log_event_epoch;
 return status;
}
unsigned __cdecl terminal_phone_log_events_ready(void)
{
 unsigned status;
#ifdef PHONE_LOG_DISK
 if(terminal_phone_log_disk_status)return publish(terminal_phone_log_disk_status);
#endif
 status=phone_log_lifecycle_service();
 if(!status)status=phone_log_lifecycle_ready();
 return publish(status==PLQ_DISABLED?PLQ_OK:status);
}
unsigned __cdecl terminal_phone_log_events_connected(void)
{
 phone_log_queue_snapshot queue;phone_log_stamp stamp;char name[25];unsigned status,i;
 status=phone_log_queue_inspect(&queue);
 if(!status&&!queue.enabled)return publish(PLQ_OK);
 if(!status){
  status=phone_log_read_stamp(&stamp);if(status)status=PLQ_CLOCK;
  else{
   if(terminal_option_mask&64U){
    for(i=0;i<24 && terminal_directory_plan.name[i];++i)name[i]=(char)terminal_directory_plan.name[i];
    name[i]=0;
   }else{
    const char *label=terminal_directory_mode==1?"DIRECT":"MODEM";
    for(i=0;(name[i]=label[i])!=0;++i){}
   }
   status=phone_log_lifecycle_begin(name,terminal_dial_target,&stamp);
  }
 }
 if(status&&status!=PLQ_DUPLICATE)event_fault=status;
 return publish(status==PLQ_DUPLICATE?PLQ_OK:status);
}
unsigned __cdecl terminal_phone_log_events_disconnected(void)
{
 phone_log_lifecycle_snapshot state;phone_log_stamp stamp;unsigned status;
 status=phone_log_lifecycle_inspect(&state);
 if(!status){
  if(state.pending)status=PLL_PENDING;
  else if(state.active){
   status=phone_log_read_stamp(&stamp);if(status)status=PLQ_CLOCK;
   else status=phone_log_lifecycle_end(&stamp);
  }
 }
 if(status&&status!=PLL_PENDING)event_fault=status;
 return publish(status);
}
unsigned __cdecl terminal_phone_log_events_shutdown(void)
{
 phone_log_queue_snapshot queue;phone_log_lifecycle_snapshot state;
 union REGS in,out;unsigned status=terminal_phone_log_events_disconnected();
#ifdef PHONE_LOG_DISK
 if(status==PLL_PENDING)status=PLQ_OK;
 if(!status)status=phone_log_shutdown_drain();
#endif
 if(!status)status=phone_log_lifecycle_inspect(&state);
 if(!status&&(state.active||state.pending))status=PLL_PENDING;
 if(!status)status=phone_log_queue_inspect(&queue);
 if(!status&&queue.queued)status=PLE_UNSAVED;
 if(!status)status=event_fault;
 if(status){
  if(!terminal_exit_code)terminal_exit_code=12;
  in.h.ah=9;in.x.dx=(unsigned)"Call log pending; records were not saved.\r\n$";
  intdos(&in,&out);
 }
 return publish(status);
}

#ifdef PHONE_LOG_CONTROLS
unsigned __cdecl phone_log_event_fault(void){return event_fault;}
#endif
