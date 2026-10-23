#include "hook_apply.h"
#include "hook_modem.h"
#include "hook_input.h"
#include "../terminal/hook_transaction.h"
#include "../terminal/register_owner.h"
#include "../terminal/session_projection.h"
#include "../terminal/session_baseline.h"
#include "../aspect/register_codec.h"
extern unsigned __far __cdecl terminal_register_context(void);
extern unsigned __far __cdecl hook_apply_uart_check(unsigned);
extern unsigned __far __cdecl hook_prepare_link(void);
extern unsigned __far __cdecl hook_port_move(const terminal_import_settings *);
extern unsigned __far __cdecl hook_port_check(const terminal_import_settings *);
extern void __far __cdecl hook_apply_display(const terminal_import_settings *);
extern unsigned __far __cdecl hook_xlt_check(unsigned,unsigned char *);
extern void __far __cdecl hook_xlt_publish(unsigned,unsigned char *);
extern unsigned __far __cdecl hook_xlt_offer(unsigned,unsigned char *);
extern unsigned __far __cdecl terminal_mouse_offer_far(const unsigned char *,unsigned);
extern unsigned __far __cdecl terminal_mouse_check_far(void);
extern void __far __cdecl terminal_mouse_publish_far(void);
extern void __far __cdecl terminal_mouse_discard_far(void);
extern unsigned __far terminal_hook_apply_epoch,terminal_hook_apply_seal;
extern unsigned __far terminal_hook_input_bound;
extern prm_dos_image __far terminal_hook_before;
extern unsigned terminal_program_active,terminal_program_kind,terminal_program_status;
extern unsigned terminal_parser_active,terminal_transfer_pending,terminal_transfer_active;
extern unsigned terminal_controller_active,terminal_monitor_active,process_busy,connection_state;
extern unsigned terminal_baud_low,terminal_baud_high,terminal_parity,terminal_data_bits,terminal_stop_bits;
extern unsigned uart_software_flow,uart_hardware_flow,uart_tx_paused,uart_rx_count;
extern unsigned char uart_flow_pending,uart_xoff_sent,uart_rts_lowered;
extern unsigned terminal_option_mask,terminal_modem_init_wait,terminal_break_delay_units;
extern unsigned terminal_translation_mode,terminal_translation_enabled,uart_rx_mask,csi_terminal_id;
extern unsigned terminal_setup_profile_ready,terminal_setup_profile_status,setup_profile_target,terminal_setup_link_status;
extern unsigned connection_baud_index,modem_response_cursors[11];
extern unsigned char terminal_dial_target[64],terminal_modem_pause,connection_init[129],connection_dial[129],connection_hangup[129];
extern unsigned char terminal_keymap[948],setup_profile_keymap[948],terminal_translation_table[256],modem_response_slots[176];
extern modem_import_settings terminal_modem_settings;
extern live_configuration_plan terminal_setup_plan;
extern transfer_import_settings terminal_transfer_preferences;
extern unsigned terminal_sound_enabled;
#pragma aux terminal_program_active "terminal_program_active";
#pragma aux terminal_program_kind "terminal_program_kind";
#pragma aux terminal_program_status "terminal_program_status";
#pragma aux terminal_parser_active "terminal_parser_active";
#pragma aux terminal_transfer_pending "terminal_transfer_pending";
#pragma aux terminal_transfer_active "terminal_transfer_active";
#pragma aux terminal_controller_active "terminal_controller_active";
#pragma aux terminal_monitor_active "terminal_monitor_active";
#pragma aux process_busy "process_busy";
#pragma aux connection_state "connection_state";
#pragma aux terminal_baud_low "terminal_baud_low";
#pragma aux terminal_baud_high "terminal_baud_high";
#pragma aux terminal_parity "terminal_parity";
#pragma aux terminal_data_bits "terminal_data_bits";
#pragma aux terminal_stop_bits "terminal_stop_bits";
#pragma aux uart_software_flow "uart_software_flow";
#pragma aux uart_hardware_flow "uart_hardware_flow";
#pragma aux uart_tx_paused "uart_tx_paused";
#pragma aux uart_rx_count "uart_rx_count";
#pragma aux uart_flow_pending "uart_flow_pending";
#pragma aux uart_xoff_sent "uart_xoff_sent";
#pragma aux uart_rts_lowered "uart_rts_lowered";
#pragma aux terminal_option_mask "terminal_option_mask";
#pragma aux terminal_modem_init_wait "terminal_modem_init_wait";
#pragma aux terminal_break_delay_units "terminal_break_delay_units";
#pragma aux terminal_translation_mode "terminal_translation_mode";
#pragma aux terminal_translation_enabled "terminal_translation_enabled";
#pragma aux uart_rx_mask "uart_rx_mask";
#pragma aux csi_terminal_id "csi_terminal_id";
#pragma aux terminal_setup_profile_ready "terminal_setup_profile_ready";
#pragma aux terminal_setup_profile_status "terminal_setup_profile_status";
#pragma aux setup_profile_target "setup_profile_target";
#pragma aux terminal_setup_link_status "terminal_setup_link_status";
#pragma aux connection_baud_index "connection_baud_index";
#pragma aux modem_response_cursors "modem_response_cursors";
#pragma aux terminal_dial_target "terminal_dial_target";
#pragma aux terminal_modem_pause "terminal_modem_pause";
#pragma aux connection_init "connection_init";
#pragma aux connection_dial "connection_dial";
#pragma aux connection_hangup "connection_hangup";
#pragma aux terminal_keymap "terminal_keymap";
#pragma aux setup_profile_keymap "setup_profile_keymap";
#pragma aux terminal_translation_table "terminal_translation_table";
#pragma aux modem_response_slots "modem_response_slots";
#pragma aux terminal_modem_settings "terminal_modem_settings";
#pragma aux terminal_setup_plan "terminal_setup_plan";
typedef char apply_result_abi[sizeof(hook_apply_result)==6?1:-1];
static unsigned equal(const void *a,const void __far *b,unsigned n)
{unsigned i;for(i=0;i<n;++i)if(((const unsigned char *)a)[i]!=((const unsigned char __far *)b)[i])return 0;return 1;}
static void copy(void *a,const void __far *b,unsigned n)
{unsigned i;for(i=0;i<n;++i)((unsigned char *)a)[i]=((const unsigned char __far *)b)[i];}
static unsigned current(void)
{
 prm_dos_image image;
 if(terminal_session_project_bound(&image) || !equal(&image,&terminal_hook_before,1264))return HOOK_APPLY_STALE;
 if(terminal_register_owner.epoch!=terminal_hook_apply_epoch || terminal_register_owner.seal!=terminal_hook_apply_seal ||
  !register_strings(terminal_register_owner.accepted) ||
  terminal_register_owner.seal!=register_seal(terminal_register_owner.accepted,terminal_register_owner.epoch))return HOOK_APPLY_STALE;
 return 0;
}
static unsigned data(void)
{
 prm_dos_image before,after;hook_return_plan settings;hook_return_result result;
 copy(&before,&terminal_hook_before,1264);copy(&after,&terminal_hook_proposal.image,1264);
 if(hook_return_validate(&before,&after,terminal_hook_proposal.settings.modem_active,&settings,&result) ||
  !equal(&settings,&terminal_hook_proposal.settings,490) || !register_strings(terminal_hook_proposal.integers))return HOOK_APPLY_DATA;
 return 0;
}
static unsigned modem(void)
{
 hook_return_plan settings;hook_modem_plan plan;hook_modem_result result;
 copy(&settings,&terminal_hook_proposal.settings,490);
 if(hook_modem_prepare(&settings,terminal_dial_target,terminal_modem_init_wait!=0,&plan,&result) ||
  !equal(&plan,&terminal_hook_modem_offer,1086))return HOOK_APPLY_MODEM;
 return 0;
}
static unsigned input(void)
{
 unsigned i,j,mode=terminal_hook_proposal.settings.serial.translation_mode;
 unsigned profile=terminal_hook_proposal.settings.serial.terminal_id;unsigned char table[256];
 if(terminal_hook_input_offer.profile!=profile || terminal_hook_input_offer.translation_mode!=mode ||
  terminal_hook_input_offer.profile_changed!=(profile!=csi_terminal_id) ||
  terminal_hook_input_offer.translation_changed!=(mode!=terminal_translation_mode))return HOOK_APPLY_INPUT;
 if(profile!=csi_terminal_id){
  if(terminal_setup_profile_ready!=1 || setup_profile_target!=profile ||
   !equal(setup_profile_keymap,terminal_hook_input_offer.keyboard,948))return HOOK_APPLY_INPUT;
 }else if(!equal(terminal_keymap,terminal_hook_input_offer.keyboard,948))return HOOK_APPLY_INPUT;
 for(i=0;i<79;++i){for(j=0;j<12 && terminal_hook_input_offer.keyboard[i*12+j];++j);if(j==12)return HOOK_APPLY_INPUT;}
 for(i=0;i<256;++i)table[i]=terminal_translation_table[i];
 if(mode!=terminal_translation_mode){
  if((terminal_option_mask&16384U) || hook_xlt_check(mode,terminal_translation_table) || hook_xlt_offer(mode,table))return HOOK_APPLY_INPUT;
 }
 return equal(table,terminal_hook_input_offer.translation,256)?0:HOOK_APPLY_INPUT;
}
static unsigned mouse(void)
{
 prm_dos_image image;unsigned status;
 copy(&image,&terminal_hook_proposal.image,1264);
 status=terminal_mouse_offer_far(image.bytes,1264);
 if((status!=0 && status!=16384U) || terminal_mouse_check_far())return HOOK_APPLY_MOUSE;
 return 0;
}
static unsigned state(void)
{
 if((terminal_hook_phase!=4 && terminal_hook_phase!=5) || terminal_hook_input_bound!=1 || terminal_program_active!=1 || terminal_program_kind!=5 || terminal_program_status!=4 ||
  terminal_parser_active || terminal_transfer_pending || terminal_transfer_active || terminal_controller_active || terminal_monitor_active ||
  process_busy || terminal_register_owner.phase || terminal_hook_owner.phase || terminal_hook_owner.segment ||
  (connection_state!=0 && connection_state!=6))return HOOK_APPLY_STATE;
 return 0;
}
static unsigned check(hook_apply_result *result)
{
 unsigned status;
 result->status=result->source_status=result->change_mask=0;
 status=state();if(status)goto done;
 status=current();if(status)goto done;
 status=data();if(status)goto done;
 status=modem();if(status)goto done;
 status=input();if(status)goto done;
 status=mouse();if(status)goto done;
 result->change_mask=terminal_hook_proposal.settings.change_mask;
 copy(&terminal_setup_plan.serial,&terminal_hook_proposal.settings.serial,44);
 if((result->change_mask&15) && hook_prepare_link()){status=HOOK_APPLY_UART;goto done;}
 if(hook_apply_uart_check(result->change_mask) || ((result->change_mask&1) && hook_port_check(&terminal_setup_plan.serial)))status=HOOK_APPLY_UART;
done:
 result->status=status;
 if(status)terminal_mouse_discard_far();
 return status;
}
unsigned __far __cdecl terminal_hook_apply_check(hook_apply_result *result)
{
 unsigned status;
 if(!terminal_register_context() || !result || (unsigned long)(unsigned)result+6>65536UL)return HOOK_APPLY_ARGUMENT;
 status=check(result);if(!status)terminal_hook_phase=5;return status;
}
static void baseline(void)
{prm_dos_image image;copy(&image,&terminal_hook_proposal.image,1264);hook_baseline_publish(&image,SESSION_BASELINE_HOOK);}
static void publish(unsigned mask)
{
 unsigned i,old_soft=uart_software_flow,token;const hook_return_plan __far *p=&terminal_hook_proposal.settings;
 terminal_mouse_publish_far();
 if(p->serial.translation_mode!=terminal_translation_mode)hook_xlt_publish(p->serial.translation_mode,terminal_translation_table);
 terminal_translation_mode=p->serial.translation_mode;terminal_translation_enabled=terminal_translation_mode==1;
 uart_rx_mask=terminal_translation_mode==2?127:255;
 if(p->modem_active){
  copy(&terminal_modem_settings,&p->modem,368);
  copy(connection_init,terminal_hook_modem_offer.commands[0],129);
  copy(connection_hangup,terminal_hook_modem_offer.commands[3],129);
  copy(connection_dial,terminal_hook_modem_offer.dial,129);
  copy(modem_response_slots,terminal_hook_modem_offer.responses,176);
  for(i=0;i<11;++i)modem_response_cursors[i]=(unsigned)(modem_response_slots+i*16);
 }
 terminal_modem_settings.command_pause_character=p->serial.mapping_pause_character;
 terminal_modem_settings.command_character_delay_units=p->serial.mapping_character_delay_units;
 terminal_modem_pause=(unsigned char)p->serial.mapping_pause_character;
 terminal_modem_settings.break_delay_units=terminal_break_delay_units=p->modem.break_delay_units;
 if(terminal_option_mask&96)connection_baud_index=terminal_hook_modem_offer.baud_index;
 terminal_baud_low=p->serial.baud_low;terminal_baud_high=p->serial.baud_high;
 terminal_parity=p->serial.parity;terminal_data_bits=p->serial.data_bits;terminal_stop_bits=p->serial.stop_bits;
 uart_software_flow=p->serial.software_flow;uart_hardware_flow=p->serial.hardware_flow;
 if(mask&15){
  if(!uart_software_flow){uart_tx_paused=0;uart_flow_pending=uart_xoff_sent=0;}
  else{
   if((mask&1) || !old_soft){uart_tx_paused=0;uart_flow_pending=0x11;}
   if(uart_rx_count>128){uart_xoff_sent=1;uart_flow_pending=0x13;}else uart_xoff_sent=0;
  }
  uart_rts_lowered=!uart_software_flow && uart_hardware_flow && uart_rx_count>128;
  terminal_setup_link_status=1;
 }
 copy(&terminal_transfer_preferences,&p->transfer,66);terminal_sound_enabled=p->sound_enabled;
 terminal_setup_profile_status=terminal_hook_input_offer.profile_changed?1:0;
 hook_apply_display(&terminal_setup_plan.serial);
 baseline();
 for(i=0;i<830;++i)terminal_register_owner.accepted[i]=((const unsigned char __far *)&terminal_hook_proposal)[i];
 token=terminal_register_owner.token+1;if(!token)++token;
 terminal_register_owner.token=terminal_register_owner.epoch=token;
 terminal_register_owner.seal=register_seal(terminal_register_owner.accepted,token);
 terminal_hook_phase=6;
}
unsigned __far __cdecl terminal_hook_apply(hook_apply_result *result)
{
 unsigned status;
 if(!terminal_register_context() || !result || (unsigned long)(unsigned)result+6>65536UL)return HOOK_APPLY_ARGUMENT;
 if(terminal_hook_phase!=5){result->status=HOOK_APPLY_STATE;return result->status;}
 status=check(result);if(status)return status;
 if((result->change_mask&1) && hook_port_move(&terminal_setup_plan.serial)){
  result->status=HOOK_APPLY_UART;terminal_mouse_discard_far();return result->status;
 }
 publish(result->change_mask);return 0;
}
