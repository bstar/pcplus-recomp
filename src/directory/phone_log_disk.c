#include "phone_log_disk.h"
#include "phone_log_events.h"
#include "phone_log_lifecycle.h"
#include "phone_log_file.h"
#include <dos.h>
extern unsigned terminal_quit,terminal_aspect_active,terminal_program_active,terminal_program_pending;
extern unsigned terminal_parser_active,terminal_transfer_pending,terminal_transfer_active;
extern unsigned terminal_controller_active,terminal_monitor_active,terminal_macro_active,terminal_ansi_wait_active;
extern unsigned process_busy,redisplay_active,command_menu_active,connection_state;
extern volatile unsigned uart_rx_count,uart_rx_dropped;
extern unsigned terminal_tx_count,uart_break_hold;
extern unsigned uart_hardware_flow,uart_software_flow,uart_port_mcr,uart_port_lsr,uart_port_thr;
extern volatile unsigned char hardware_active,uart_flow_pending,uart_xoff_sent,uart_rts_lowered;
#pragma aux terminal_quit "terminal_quit";
#pragma aux terminal_aspect_active "terminal_aspect_active";
#pragma aux terminal_program_active "terminal_program_active";
#pragma aux terminal_program_pending "terminal_program_pending";
#pragma aux terminal_parser_active "terminal_parser_active";
#pragma aux terminal_transfer_pending "terminal_transfer_pending";
#pragma aux terminal_transfer_active "terminal_transfer_active";
#pragma aux terminal_controller_active "terminal_controller_active";
#pragma aux terminal_monitor_active "terminal_monitor_active";
#pragma aux terminal_macro_active "terminal_macro_active";
#pragma aux terminal_ansi_wait_active "terminal_ansi_wait_active";
#pragma aux process_busy "process_busy";
#pragma aux connection_state "connection_state";
#pragma aux uart_rx_count "uart_rx_count";
#pragma aux uart_rx_dropped "uart_rx_dropped";
#pragma aux terminal_tx_count "terminal_tx_count";
#pragma aux uart_break_hold "uart_break_hold";
#pragma aux uart_hardware_flow "uart_hardware_flow";
#pragma aux uart_software_flow "uart_software_flow";
#pragma aux uart_port_mcr "uart_port_mcr";
#pragma aux uart_port_lsr "uart_port_lsr";
#pragma aux uart_port_thr "uart_port_thr";
#pragma aux hardware_active "hardware_active";
#pragma aux uart_flow_pending "uart_flow_pending";
#pragma aux uart_xoff_sent "uart_xoff_sent";
#pragma aux uart_rts_lowered "uart_rts_lowered";
extern unsigned __far __cdecl connection_alive(void);
#pragma aux connection_alive "terminal_connection_flow_alive";
extern void __cdecl phone_log_disk_notify(const char *);
static unsigned read_flags(void);
#pragma aux read_flags = "pushf" "pop ax" value [ax] modify exact [];
static void disable_irq(void);
#pragma aux disable_irq = "cli" modify exact [];
static void enable_irq(void);
#pragma aux enable_irq = "sti" modify exact [];
static unsigned input_port(unsigned);
#pragma aux input_port = "xor ax,ax" "in al,dx" parm [dx] value [ax] modify exact [];
static void output_port(unsigned,unsigned);
#pragma aux output_port = "out dx,al" parm [dx] [ax] modify exact [];
unsigned terminal_phone_log_disk_attempts=0,terminal_phone_log_disk_status=0;
static unsigned busy=0,last_notice=0;
static unsigned tick(void)
{return *(volatile unsigned __far *)MK_FP(0x40,0x6c);}
static unsigned occupied(void)
{
 return !hardware_active || terminal_quit || terminal_aspect_active ||
 terminal_program_active || terminal_program_pending || process_busy || terminal_parser_active ||
 terminal_transfer_pending || terminal_transfer_active || terminal_controller_active || terminal_monitor_active ||
 terminal_macro_active || terminal_ansi_wait_active || redisplay_active || command_menu_active ||
 uart_rx_count || uart_rx_dropped || terminal_tx_count || uart_break_hold ||
 (connection_state!=0 && connection_state!=6);
}
static unsigned report(unsigned status,unsigned force)
{
 unsigned notice=status==PLQ_FILE?PLQ_RETRY:status;
 if(force || terminal_phone_log_disk_status!=status){
  terminal_phone_log_event_status=status;++terminal_phone_log_event_epoch;
 }
 terminal_phone_log_disk_status=status;
 if(notice && notice!=last_notice){
  phone_log_disk_notify(notice==PLQ_RECOVERY?"Call log recovery required":
      notice==PLQ_RETRY?"Call log retry required":"Call log blocked");
 }
 last_notice=notice;return status;
}
unsigned __cdecl terminal_phone_log_disk_poll(void)
{
 phone_log_queue_snapshot queue;
 unsigned status,start,n,hard=0,soft=0,alive=0,mcr,attempted=0,flags;
 if(busy || !(read_flags()&0x200U) || occupied())return PLQ_OK;
 busy=1;
 if(terminal_phone_log_disk_status){status=terminal_phone_log_disk_status;goto failed;}
 status=phone_log_lifecycle_service();
 if(status && status!=PLQ_FULL)goto failed;
 status=phone_log_queue_inspect(&queue);if(status)goto failed;
 if(queue.recovery_required){status=PLQ_RECOVERY;goto failed;}
 if(queue.retry_required){status=PLQ_RETRY;goto failed;}
 if(!queue.queued){busy=0;return PLQ_OK;}
 /* Without peer flow, keep online event capture in RAM. Idle/offline and
  * shutdown can drain it; do not promise unbounded disk-latency protection. */
 if(connection_state==6 && !uart_hardware_flow && !uart_software_flow){busy=0;return PLQ_OK;}
 if(uart_flow_pending || uart_xoff_sent || uart_rts_lowered){busy=0;return PLQ_OK;}
 alive=connection_state==6?connection_alive():0;
 mcr=input_port(uart_port_mcr);
 if(uart_hardware_flow && (mcr&2U)){
  output_port(uart_port_mcr,mcr&~2U);hard=1;
 }
 /* Wait for current physical TX without consuming RX/parser bytes. Any RX
  * arrival cancels this opportunity. Tick wrap can shorten, not extend, it. */
 start=tick();
 for(n=0;n<65535U;++n){
  if(uart_rx_count || (unsigned)(tick()-start)>=2U)goto deferred;
  if((input_port(uart_port_lsr)&0x60U)==0x60U)break;
 }
 if(n==65535U)goto deferred;
 if(uart_software_flow && alive){
  output_port(uart_port_thr,0x13);soft=1;
  for(n=0;n<65535U;++n){
   if(uart_rx_count || (unsigned)(tick()-start)>=2U)goto deferred;
   if((input_port(uart_port_lsr)&0x60U)==0x60U)break;
  }
  if(n==65535U)goto deferred;
 }
 if(occupied())goto deferred;
 ++terminal_phone_log_disk_attempts;attempted=1;
 status=phone_log_queue_poll();
 if(!status){unsigned retained=phone_log_lifecycle_service();if(retained && retained!=PLQ_FULL)status=retained;}
 goto released;
deferred:
 status=PLQ_OK;
released:
 /* Driver watermark ownership may have arisen while DOS/IRQs ran. Never
  * raise its RTS or replace its pending XOFF. Transfer our XON to the normal
  * driver poll; shutdown already drains that pending control byte. */
 alive=connection_alive();
 flags=read_flags();disable_irq();
 if(hard && !uart_rts_lowered)output_port(uart_port_mcr,input_port(uart_port_mcr)|2U);
 if(soft && alive && !uart_xoff_sent && !uart_flow_pending)uart_flow_pending=0x11;
 if(flags&0x200U)enable_irq();
 if(status || attempted)status=report(status,attempted);
 busy=0;return status;
failed:
 status=report(status,0);busy=0;return status;
}
unsigned __cdecl phone_log_shutdown_drain(void)
{
 phone_log_queue_snapshot queue;unsigned status,retained,i;
 if(busy)return PLQ_BUSY;
 if(terminal_phone_log_disk_status)return terminal_phone_log_disk_status;
 busy=1;
 for(i=0;i<PHONE_LOG_QUEUE_CAPACITY+2U;++i){
  retained=phone_log_lifecycle_service();
  if(retained && retained!=PLQ_FULL){busy=0;return retained;}
  status=phone_log_queue_inspect(&queue);
  if(status || queue.retry_required || queue.recovery_required){
   busy=0;return status?status:queue.recovery_required?PLQ_RECOVERY:PLQ_RETRY;
  }
  if(!queue.queued){busy=0;return retained;}
  ++terminal_phone_log_disk_attempts;
  status=phone_log_queue_poll();if(status){busy=0;return status;}
 }
 busy=0;return PLE_UNSAVED;
}

extern unsigned __far __cdecl capture_before_program(void);
#pragma aux capture_before_program "phone_capture_before_program_resident";
unsigned __cdecl phone_log_disk_before_program(void)
{
 if(phone_log_file_initialize() || phone_log_file_result.handle_open || phone_log_file_result.handle_uncertain || phone_log_file_result.recovery_required){
  phone_log_disk_notify("Call log recovery required");return 1;
 }
 return capture_before_program();
}

#ifdef PHONE_LOG_CONTROLS
unsigned terminal_phone_log_retry_acks=0;
unsigned __cdecl phone_log_disk_retry(void)
{
 phone_log_queue_snapshot queue;unsigned status,file;
 if(busy || !(read_flags()&0x200U) || terminal_quit || terminal_aspect_active ||
    terminal_program_active || terminal_program_pending || process_busy || terminal_parser_active ||
    terminal_transfer_pending || terminal_transfer_active || terminal_controller_active || terminal_monitor_active ||
    terminal_macro_active || terminal_ansi_wait_active || uart_break_hold)return PLQ_BUSY;
 busy=1;
 status=phone_log_queue_inspect(&queue);
 if(status){busy=0;return status;}
 file=phone_log_file_initialize();
 if(queue.recovery_required || file==PLF_RECOVERY || phone_log_file_result.handle_uncertain || phone_log_file_result.recovery_required){busy=0;return PLQ_RECOVERY;}
 if(file){busy=0;return PLQ_BUSY;}
 if(!queue.enabled){busy=0;return PLQ_DISABLED;}
 if(phone_log_event_fault()){busy=0;return PLQ_CLOCK;}
 if(!queue.retry_required && !terminal_phone_log_disk_status){busy=0;return PLQ_STATE;}
 if(queue.retry_required){status=phone_log_queue_retry();if(status){busy=0;return status;}}
 terminal_phone_log_disk_status=last_notice=0;
 terminal_phone_log_event_status=0;++terminal_phone_log_retry_acks;
 busy=0;++terminal_phone_log_event_epoch;return PLQ_OK;
}
#endif
