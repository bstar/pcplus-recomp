/* Diagnostic only: four live application file owners across direct COMSPEC. */
#include "../src/process/gateway_files.h"
#include "../src/capture/capture_session.h"
#include "../src/filesystem/path_session.h"
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
} report;
typedef char report_size[sizeof(report)==116?1:-1];
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
 r.status=gateway_files_run(&terminal_program_result);r.result=terminal_program_result;
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
 return gateway_probe_report(&r,sizeof(r));
}
