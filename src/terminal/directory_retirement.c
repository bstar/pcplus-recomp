#include "directory_retirement.h"
#include "directory_identity.h"
#include "../config/live_setup_owner.h"
#include "../directory/directory_replace.h"
#include "../config/resource_path.h"
#include <string.h>
extern unsigned __far __cdecl directory_retire_queue(void);
extern unsigned __far __cdecl directory_retire_flush(void);
extern unsigned __far __cdecl directory_setup_queue(void);
extern unsigned __far __cdecl hook_apply_uart_check(unsigned);
extern unsigned __cdecl directory_accounting_patch(const unsigned char *,unsigned char *,unsigned,unsigned,unsigned,unsigned);
extern unsigned terminal_program_active,terminal_program_pending,terminal_program_kind,terminal_program_status;
extern unsigned connection_state,terminal_parser_active,terminal_transfer_pending,terminal_transfer_active;
extern unsigned terminal_controller_active,terminal_monitor_active,process_busy,terminal_quit,terminal_exit_code;
extern unsigned redisplay_active,command_menu_active,uart_rx_count,uart_rx_dropped,terminal_tx_count;
extern unsigned terminal_directory_context_valid,directory_pending_count,directory_pending_year,directory_pending_month,directory_pending_day;
extern unsigned char directory_pending;
extern directory_live_context terminal_directory_context;
extern directory_live_plan terminal_directory_plan;
extern directory_replace_result directory_account_result;
extern unsigned directory_account_status;
extern unsigned process_psp,terminal_option_mask,terminal_macro_active,terminal_setup_status;
extern char terminal_setup_tail[68],program_setup_executable[64];
#pragma aux process_psp "process_psp";
#pragma aux terminal_option_mask "terminal_option_mask";
#pragma aux terminal_macro_active "terminal_macro_active";
#pragma aux terminal_setup_status "terminal_setup_status";
#pragma aux terminal_setup_tail "terminal_setup_tail";
#pragma aux program_setup_executable "program_setup_executable";
#pragma aux terminal_program_active "terminal_program_active";
#pragma aux terminal_program_pending "terminal_program_pending";
#pragma aux terminal_program_kind "terminal_program_kind";
#pragma aux terminal_program_status "terminal_program_status";
#pragma aux connection_state "connection_state";
#pragma aux terminal_parser_active "terminal_parser_active";
#pragma aux terminal_transfer_pending "terminal_transfer_pending";
#pragma aux terminal_transfer_active "terminal_transfer_active";
#pragma aux terminal_controller_active "terminal_controller_active";
#pragma aux terminal_monitor_active "terminal_monitor_active";
#pragma aux process_busy "process_busy";
#pragma aux terminal_quit "terminal_quit";
#pragma aux terminal_exit_code "terminal_exit_code";
#pragma aux uart_rx_count "uart_rx_count";
#pragma aux uart_rx_dropped "uart_rx_dropped";
#pragma aux terminal_tx_count "terminal_tx_count";
#pragma aux terminal_directory_context_valid "terminal_directory_context_valid";
#pragma aux terminal_directory_context "terminal_directory_context";
#pragma aux terminal_directory_plan "terminal_directory_plan";
#pragma aux directory_pending "directory_pending";
#pragma aux directory_pending_count "directory_pending_count";
#pragma aux directory_pending_year "directory_pending_year";
#pragma aux directory_pending_month "directory_pending_month";
#pragma aux directory_pending_day "directory_pending_day";
#pragma aux directory_account_result "directory_account_result";
#pragma aux directory_account_status "directory_account_status";
directory_retirement_snapshot terminal_directory_retirement;
unsigned directory_retire_armed=0xd910;
static unsigned cookie=0xd911;
typedef char retirement_abi[sizeof(directory_retirement_snapshot)==10?1:-1];
static void initialize(void)
{
 if(cookie==0xd911){
  memset(&terminal_directory_retirement,0,sizeof(terminal_directory_retirement));
  if(directory_retire_armed==0xd910)directory_retire_armed=0;
  cookie=0xd912;
 }
}
unsigned __far __cdecl terminal_setup_frozen_start(void)
{
 char executable[64],tail[68];unsigned status;
 status=1;
 memset(executable,0,sizeof(executable));
 if(!(terminal_option_mask&16))goto done;
 if(terminal_macro_active){status=2;goto done;}
 if(live_setup_frozen_command(tail) || resource_program_path(process_psp,"PRMEDIT.EXE",executable))goto done;
 if(directory_setup_queue()){status=2;goto done;}
 memcpy(program_setup_executable,executable,64);memcpy(terminal_setup_tail,tail,68);status=0;
done:
 terminal_setup_status=status;return status;
}
static unsigned occupied(void)
{return terminal_quit || terminal_parser_active || terminal_transfer_pending || terminal_transfer_active ||
 terminal_controller_active || terminal_monitor_active || process_busy || redisplay_active || command_menu_active ||
 uart_rx_count || uart_rx_dropped || terminal_tx_count || connection_state;}
void __far __cdecl terminal_directory_retire_poll(void)
{
 initialize();
 if(directory_retire_armed!=1 || !directory_pending || terminal_directory_context_valid!=1 ||
  terminal_program_pending || terminal_program_active || occupied() ||
  terminal_directory_retirement.state==DRET_QUEUED || terminal_directory_retirement.state==DRET_RUNNING)return;
 if(directory_retire_queue())return;
 directory_retire_armed=0;terminal_directory_retirement.state=DRET_QUEUED;
 terminal_directory_retirement.status=terminal_directory_retirement.detail=terminal_directory_retirement.installed=0;
}
void __far __cdecl terminal_directory_retire_cancel(void)
{
 initialize();if(terminal_directory_retirement.state==DRET_QUEUED){
  terminal_directory_retirement.state=DRET_IDLE;terminal_directory_retirement.status=DRET_CANCELED;
 }
}
unsigned __far __cdecl terminal_directory_retire_run(void)
{
 directory_live_context next;
 unsigned char before[114],expected[114];
 unsigned i,status,count,year,month,day;
 directory_retirement_snapshot *r=&terminal_directory_retirement;
 initialize();
 if(r->state!=DRET_QUEUED || terminal_program_active!=1 || terminal_program_pending || terminal_program_kind!=7 ||
  terminal_program_status!=2)return DRET_CONTEXT;
 r->state=DRET_RUNNING;++r->attempts;
 if(occupied() || !directory_pending || !terminal_directory_account_identity() || hook_apply_uart_check(15)){
  r->status=DRET_CONTEXT;goto failed;
 }
 memcpy(&next,&terminal_directory_context,sizeof(next));memcpy(before,terminal_directory_plan.record,114);
 for(i=0;i<114;++i)if((i<61 || i>=72) && before[i]!=next.selection.record[i]){r->status=DRET_DATA;goto failed;}
 status=live_setup_reconcile_accounting(&next,0);
 if(status){r->status=DRET_SETUP;r->detail=status;goto failed;}
 count=directory_pending_count;year=directory_pending_year;month=directory_pending_month;day=directory_pending_day;
 if(directory_accounting_patch(before,expected,year,month,day,count)){r->status=DRET_DATA;goto failed;}
 status=directory_retire_flush();r->detail=directory_account_status;r->installed=directory_account_result.installed;
 if(memcmp(&next,&terminal_directory_context,sizeof(next)))goto inconsistent;
 if(r->installed){
  if(directory_pending || directory_pending_count || memcmp(expected,terminal_directory_plan.record,114))goto inconsistent;
  memcpy(next.selection.record,expected,114);
  if(live_setup_reconcile_accounting(&next,1))goto inconsistent;
  memcpy(terminal_directory_context.selection.record+61,expected+61,11);
 }else if(!status || !directory_pending || directory_pending_count!=count || memcmp(before,terminal_directory_plan.record,114))goto inconsistent;
 if(status){r->status=DRET_IO;goto failed;}
 r->state=DRET_DONE;return 0;
inconsistent:
 terminal_quit=1;if(!terminal_exit_code)terminal_exit_code=7;r->status=DRET_DATA;
failed:
 r->state=DRET_FAILED;return r->status;
}
