/* Diagnostic only: four live application file owners across direct COMSPEC. */
#include "../src/process/gateway_files.h"
#include "../src/capture/capture_session.h"
#include "../src/filesystem/path_session.h"
#if defined(TERMINAL_GATEWAY_UART_PROBE)
#include "../src/terminal/gateway_uart.h"
extern unsigned __far __cdecl gateway_probe_rx_report(const void *,unsigned);
extern unsigned terminal_program_kind,terminal_program_pending,terminal_program_active;
extern unsigned uart_rx_count,uart_rx_dropped,uart_rx_read,uart_rx_write;
extern unsigned char uart_rx_buffer[],uart_flow_pending,uart_xoff_sent,uart_rts_lowered;
extern unsigned __cdecl gateway_probe_receive(void);
extern unsigned __cdecl gateway_probe_poll(void);
extern unsigned __cdecl gateway_probe_mcr(void);
#pragma aux gateway_probe_receive "uart_receive_byte";
#pragma aux gateway_probe_poll "uart_poll_flow";
#pragma aux terminal_program_kind "terminal_program_kind";
#pragma aux terminal_program_pending "terminal_program_pending";
#pragma aux terminal_program_active "terminal_program_active";
#pragma aux uart_rx_count "uart_rx_count";
#pragma aux uart_rx_dropped "uart_rx_dropped";
#pragma aux uart_rx_read "uart_rx_read";
#pragma aux uart_rx_write "uart_rx_write";
#pragma aux uart_rx_buffer "uart_rx_buffer";
#pragma aux uart_flow_pending "uart_flow_pending";
#pragma aux uart_xoff_sent "uart_xoff_sent";
#pragma aux uart_rts_lowered "uart_rts_lowered";
#endif
extern unsigned __far __cdecl gateway_probe_near(unsigned,unsigned,unsigned,unsigned);
extern unsigned __far __cdecl gateway_probe_report(const void *,unsigned);
extern process_result terminal_program_result;
#pragma aux terminal_program_result "terminal_program_result";
extern unsigned terminal_sink_398a_enabled,terminal_sink_398c_disabled;
#pragma aux terminal_sink_398a_enabled "terminal_sink_398a_enabled";
#pragma aux terminal_sink_398c_disabled "terminal_sink_398c_disabled";
#define CALL0(fn) gateway_probe_near((unsigned)(fn),0,0,0)
#define CALL1(fn,a) gateway_probe_near((unsigned)(fn),(unsigned)(a),0,0)
#define CALL2(fn,a,b) gateway_probe_near((unsigned)(fn),(unsigned)(a),(unsigned)(b),0)
#define CALL3(fn,a,b,c) gateway_probe_near((unsigned)(fn),(unsigned)(a),(unsigned)(b),(unsigned)(c))
typedef struct report {
 process_result result;
 unsigned status,flags_before,flags_after,owned_before,owned_after,flush_before,flush_after;
 unsigned before[4],after[4],closed[4],current_status;
 char current[68];
#if defined(TERMINAL_GATEWAY_UART_PROBE)
 unsigned uart_begin,uart_end,rx_count,rx_dropped,flow_pending,xoff,rts,head,tail,diagnostic;
#endif
} report;
#if defined(TERMINAL_GATEWAY_UART_PROBE)
typedef char report_size[sizeof(report)==136?1:-1];
#else
typedef char report_size[sizeof(report)==116?1:-1];
#endif
unsigned __far __cdecl gateway_files_probe(void)
{
 static const char __based(__segname("_CODE")) paths[4][16]={"D:\\CAPTURE.DAT","D:\\SNAP.DAT","D:\\MONITOR.DAT","D:\\HISTORY.DAT"};
 report r;unsigned i,j;char path[16],value;
 for(i=0;i<sizeof(r);++i)((unsigned char *)&r)[i]=0;
 if(CALL0(capture_session_initialize) || CALL0(snapshot_file_initialize) || CALL0(monitor_file_initialize))return 1;
 for(i=0;i<4;++i){
  for(j=0;j<16;++j)path[j]=paths[i][j];
  if(i==0){if(CALL3(capture_session_begin,path,0,0))return 2;}
  else if(i==1){if(CALL2(snapshot_file_begin,path,CF_NEW))return 2;}
  else if(i==2){if(CALL2(monitor_file_begin,path,CF_NEW))return 2;}
  else if(CALL3(history_file_event,HISTORY_BEGIN,path,0))return 2;
  value='A';
  if(i==0){if(CALL2(capture_session_put,'A',0)!= 'A')return 3;}
  else if(i==1){if(CALL2(snapshot_file_append,&value,1))return 3;}
  else if(i==2){if(CALL2(monitor_file_append,&value,1))return 3;}
  else if(CALL3(history_file_event,HISTORY_WRITE,&value,1))return 3;
  r.before[i]=capture_file_child_handle(i);
 }
#if defined(GATEWAY_PROBE_HOLD)
 if(CALL0(capture_session_pause))return 4;
#endif
 r.flags_before=terminal_sink_398a_enabled+2*terminal_sink_398c_disabled;
 r.flush_before=capture_session_buffered;r.owned_before=gateway_files_owned();
#if defined(TERMINAL_GATEWAY_UART_PROBE)
 terminal_program_kind=9;terminal_program_active=1;terminal_program_pending=0;
 r.uart_begin=gateway_uart_begin();if(r.uart_begin)return 9;
#endif
 r.status=gateway_files_run(&terminal_program_result);r.result=terminal_program_result;
#if defined(TERMINAL_GATEWAY_UART_PROBE)
 r.uart_end=gateway_uart_end();terminal_program_active=terminal_program_kind=0;
 r.rx_count=uart_rx_count;r.rx_dropped=uart_rx_dropped;r.flow_pending=uart_flow_pending;
 r.xoff=uart_xoff_sent;r.rts=uart_rts_lowered;
 r.head=uart_rx_read-(unsigned)uart_rx_buffer;r.tail=uart_rx_write-(unsigned)uart_rx_buffer;
#endif
 r.owned_after=gateway_files_owned();r.flush_after=capture_session_buffered;
 r.flags_after=terminal_sink_398a_enabled+2*terminal_sink_398c_disabled;
 if(r.status==GATEWAY_FILES_RECOVERY || r.owned_after)return 8;
 for(i=0;i<4;++i)r.after[i]=capture_file_child_handle(i);
#if defined(GATEWAY_PROBE_HOLD)
 if(CALL0(capture_session_pause))return 4;
#endif
 value='B';
 if(CALL2(capture_session_put,'B',0)!='B' || CALL0(capture_session_flush) || CALL0(capture_session_stop))return 5;
 if(CALL2(snapshot_file_append,&value,1) || CALL1(snapshot_file_close,0))return 5;
 if(CALL2(monitor_file_append,&value,1) || CALL1(monitor_file_close,0))return 5;
 if(CALL3(history_file_event,HISTORY_WRITE,&value,1) || CALL3(history_file_event,HISTORY_CLOSE,0,0))return 5;
 for(i=0;i<4;++i)r.closed[i]=capture_file_child_handle(i);
 r.current_status=path_session_current(r.current);
#if defined(TERMINAL_GATEWAY_UART_PROBE)
 if(gateway_probe_rx_report(uart_rx_buffer,4096))return 10;
 while(uart_rx_count){if(CALL0(gateway_probe_receive)==0xffff)return 11;CALL0(gateway_probe_poll);}
 CALL0(gateway_probe_poll);
 r.diagnostic=(CALL0(gateway_probe_mcr)<<8) | (uart_rx_count?1:0) | (uart_rts_lowered?2:0) | (uart_xoff_sent?4:0) | (uart_flow_pending?8:0);
#endif
 return gateway_probe_report(&r,sizeof(r));
}
