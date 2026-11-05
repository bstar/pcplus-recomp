#include "gateway_front.h"
#include "gateway_uart.h"
#include "program_display.h"
#include "status_transition.h"
#include "row_geometry.h"
#include "../process/gateway_files.h"
#include "../filesystem/path_session.h"
#include "../capture/capture_file.h"
#include "../printer/printer_device.h"
#include "../directory/phone_log_file.h"
extern unsigned terminal_quit,terminal_exit_code,terminal_program_kind,terminal_program_status,terminal_macro_tx_epoch;
extern unsigned terminal_printer_count,terminal_printer_closing,terminal_printer_fault_epoch;
extern unsigned uart_rx_dropped;
extern unsigned char hardware_active,vector_active;
#pragma aux hardware_active "hardware_active";
#pragma aux vector_active "vector_active";
extern process_result terminal_program_result;
#pragma aux terminal_quit "terminal_quit";
#pragma aux terminal_exit_code "terminal_exit_code";
#pragma aux terminal_program_kind "terminal_program_kind";
#pragma aux terminal_program_status "terminal_program_status";
#pragma aux terminal_macro_tx_epoch "terminal_macro_tx_epoch";
#pragma aux terminal_printer_count "terminal_printer_count";
#pragma aux terminal_printer_closing "terminal_printer_closing";
#pragma aux terminal_printer_fault_epoch "terminal_printer_fault_epoch";
#pragma aux uart_rx_dropped "uart_rx_dropped";
#pragma aux terminal_program_result "terminal_program_result";
extern unsigned __far __cdecl gateway_files_context(void);
extern unsigned __far __cdecl gateway_clock_ready(void);
extern unsigned __far __cdecl gateway_video_ready(void);
extern unsigned long __far __cdecl gateway_ticks(void);
extern void __far __cdecl gateway_notice(const char *);
extern void __far __cdecl gateway_connection_poll(void);
extern void __far __cdecl notice_restore(void);
#pragma aux notice_restore "connection_notice_restore_resident";
extern unsigned __far __cdecl recording_owned(void);
#pragma aux recording_owned "terminal_recording_owned_far";
extern unsigned __far __cdecl autostart_busy(void);
#pragma aux autostart_busy "_terminal_autostart_busy";
#ifdef TERMINAL_MOUSE
extern unsigned __far __cdecl gateway_mouse_pause(void);
extern unsigned __far __cdecl gateway_mouse_resume(void);
#pragma aux gateway_mouse_pause "_terminal_mouse_pause_far";
#pragma aux gateway_mouse_resume "_terminal_mouse_resume_far";
#endif
typedef struct gateway_front_state {
 unsigned cookie,phase,status,notice,quarantine,epoch,printer_count,printer_epoch;
 unsigned long progress;
} gateway_front_state;
gateway_front_state __based(__segname("_CODE")) gateway_front_storage={0x4747};
#define F gateway_front_storage
#define TEXT __based(__segname("_CODE"))
static const status_word * const TEXT owners[]={
 &terminal_aspect_active,&terminal_parser_active,&terminal_macro_active,&terminal_ansi_wait_active,
 &terminal_monitor_active,&terminal_snapshot_active,&terminal_screen_print_active,&terminal_controller_active,
 &terminal_transfer_active,&terminal_transfer_pending,&uart_break_hold,
 &_redisplay_active,&_redisplay_live_ready,&_redisplay_export_pending,&_redisplay_search_pending,
 &_command_menu_active,&_terminal_elapsed_view_active,&terminal_screen_pause_active,&terminal_manual_init_active,
 &_clipboard_ui_active,&_clipboard_ui_visible,&_clipboard_paste_pending,&terminal_menu_pending
};
static unsigned idle(void)
{
 unsigned i;
 if(terminal_quit || hardware_active!=1 || vector_active!=1 || (connection_state!=0 && connection_state!=6))return 0;
 if(terminal_status_toggle_active || terminal_row_geometry_active || program_display_ready)return 0;
 for(i=0;i<sizeof(owners)/sizeof(owners[0]);++i)if(*owners[i])return 0;
 if(terminal_browser_screen_owned || terminal_editor_screen_owned || reset_bank_busy || terminal_auto_answer_notice_active || terminal_script_overlay_visible)return 0;
 return !recording_owned() && !autostart_busy() && gateway_video_ready();
}
static unsigned files_ready(void)
{
 unsigned i;
 if(gateway_files_owned() || path_session_quarantined() || !phone_log_file_child_ready())return 0;
 for(i=0;i<4;++i)if(capture_file_child_handle(i)==0xfffe)return 0;
 return printer_device_child_handle()!=0xfffe;
}
static void notify(void)
{
 static const char TEXT messages[5][32]={"Gateway busy","Gateway could not run","Gateway timed out","Gateway serial error","Gateway carrier changed"};
 char message[32];unsigned i,n=F.notice;
 if(!n || n>5 || !idle() || terminal_program_pending || terminal_program_active)return;
 for(i=0;i<32;++i)message[i]=messages[n-1][i];
 F.notice=0;gateway_notice(message);
}
static void cancel(unsigned status,unsigned notice)
{
 if(terminal_program_kind==9 && !terminal_program_active){terminal_program_pending=0;terminal_program_kind=0;}
 F.phase=0;F.status=status;F.notice=notice;
}
static void fatal(unsigned code,unsigned files)
{
 F.phase=3;F.quarantine=files;F.status=code;
 terminal_program_pending=0;terminal_exit_code=code;terminal_quit=1;
}
unsigned __far __cdecl gateway_quarantined(void)
{return F.cookie!=0x4747 || F.quarantine || gateway_files_owned();}
unsigned __far __cdecl gateway_start(void)
{
 if(!gateway_files_context() || !gateway_clock_ready())return 2;
 if(F.cookie!=0x4747 || F.quarantine || F.phase>1)return 2;
 if(F.phase==1 && terminal_program_pending==1 && terminal_program_kind==9)return 0;
 if(!idle() || terminal_program_pending || terminal_program_active || program_display_ready || !files_ready()){
  F.status=2;F.notice=1;return 2;
 }
 F.phase=1;F.status=1;F.notice=0;F.progress=gateway_ticks();
 F.epoch=terminal_macro_tx_epoch;F.printer_count=terminal_printer_count;F.printer_epoch=terminal_printer_fault_epoch;
 terminal_program_kind=9;terminal_program_pending=1;terminal_program_status=1;return 0;
}
void __far __cdecl gateway_poll(void)
{
 unsigned long now,elapsed;unsigned status,serial,display;
 if(!gateway_files_context())return;
 if(F.cookie!=0x4747){fatal(18,1);return;}
 if(F.phase==0){
  if(terminal_program_kind==9 && terminal_program_pending && !terminal_program_active){fatal(18,1);return;}
  notify();return;
 }
 if(F.phase!=1)return;
 if(terminal_program_kind!=9 || terminal_program_pending!=1 || terminal_program_active){cancel(3,0);return;}
 if(!idle() || !files_ready() || !gateway_clock_ready() || F.printer_epoch!=terminal_printer_fault_epoch){cancel(2,1);notify();return;}
 if(uart_rx_dropped){cancel(5,0);fatal(6,0);return;}
 now=gateway_ticks();
 if(F.epoch!=terminal_macro_tx_epoch || terminal_printer_count<F.printer_count){F.epoch=terminal_macro_tx_epoch;F.printer_count=terminal_printer_count;F.progress=now;}
 elapsed=now>=F.progress?now-F.progress:0x1800b0UL-F.progress+now;
 if(now>=0x1800b0UL || F.progress>=0x1800b0UL || elapsed>=36){cancel(7,3);terminal_program_status=8;notify();return;}
 if(terminal_tx_count || terminal_printer_count || terminal_printer_closing)return;
 notice_restore();
 if(program_display_save()){cancel(2,1);notify();return;}
#ifdef TERMINAL_MOUSE
 if(gateway_mouse_pause()){program_display_restore();cancel(14,0);fatal(14,0);return;}
#endif
 terminal_program_pending=0;terminal_program_active=1;terminal_program_status=2;F.phase=2;
 serial=gateway_uart_begin();
 if(serial){status=4;F.notice=serial==7?1:4;if(serial!=5)serial=0;}
 else{status=gateway_files_run(&terminal_program_result);serial=gateway_uart_end();}
 if(F.cookie!=0x4747 || F.phase!=2 || status==GATEWAY_FILES_RECOVERY || gateway_files_owned()){fatal(18,1);return;}
 display=program_display_restore();
 if(display){fatal(2,0);return;}
#ifdef TERMINAL_MOUSE
 if(gateway_mouse_resume()){fatal(14,0);return;}
#endif
 terminal_program_active=0;terminal_program_kind=0;F.phase=0;F.status=status;
 terminal_program_status=status || serial?5:4;
 if(serial==5 || uart_rx_dropped){fatal(6,0);return;}
 if(serial){fatal(19,0);return;}
 gateway_connection_poll();
 if(status)F.notice=2;
 notify();
}
