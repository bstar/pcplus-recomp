/* Foreground selection publication. IRQ stays quiesced until PROGRAM returns. */
#include "directory_resource_owner.h"
#include "session_baseline.h"
#include "../config/hook_modem.h"
#include "../capture/capture_file.h"
#include <string.h>
extern unsigned __far __cdecl directory_adopt_setup(const directory_live_context *,const directory_live_context *,const prm_dos_image *,unsigned);
extern unsigned __far __cdecl directory_adopt_xlt_check(unsigned,const char *,const unsigned char *,unsigned char *);
extern unsigned __far __cdecl directory_adopt_xlt_publish(unsigned,const char *,const unsigned char *,unsigned char *);
extern unsigned __far __cdecl directory_adopt_script_read(const char *,unsigned,directory_script_fingerprint *,directory_script_result *);
extern unsigned __far __cdecl directory_adopt_carrier_check(void);
extern unsigned __far __cdecl hook_prepare_link(void);
extern unsigned __far __cdecl hook_apply_uart_check(unsigned);
extern unsigned __far __cdecl hook_port_check(const terminal_import_settings *);
extern unsigned __far __cdecl hook_port_move(const terminal_import_settings *);
extern void __far __cdecl hook_apply_display(const terminal_import_settings *);
extern unsigned char __far redisplay_snapshot[63000];
#pragma aux redisplay_snapshot "redisplay_snapshot";
#define MODEM ((hook_modem_plan __far *)(redisplay_snapshot+8724))
typedef struct script_binding {unsigned bound,held;char path[64];directory_script_fingerprint fingerprint;} script_binding;
extern script_binding __far directory_adopt_script_storage;
#pragma aux directory_adopt_script_storage "directory_adopt_script_storage";
#define SCRIPT (&directory_adopt_script_storage)
typedef char script_binding_abi[sizeof(script_binding)==80?1:-1];
extern unsigned terminal_program_active;
#pragma aux terminal_program_active "terminal_program_active";
extern unsigned terminal_program_kind;
#pragma aux terminal_program_kind "terminal_program_kind";
extern unsigned terminal_program_status;
#pragma aux terminal_program_status "terminal_program_status";
extern unsigned terminal_program_pending;
#pragma aux terminal_program_pending "terminal_program_pending";
extern unsigned connection_state;
#pragma aux connection_state "connection_state";
extern unsigned terminal_parser_active;
#pragma aux terminal_parser_active "terminal_parser_active";
extern unsigned terminal_tx_count;
#pragma aux terminal_tx_count "terminal_tx_count";
extern unsigned uart_rx_count;
#pragma aux uart_rx_count "uart_rx_count";
extern unsigned uart_rx_dropped;
#pragma aux uart_rx_dropped "uart_rx_dropped";
extern unsigned terminal_transfer_pending;
#pragma aux terminal_transfer_pending "terminal_transfer_pending";
extern unsigned terminal_transfer_active;
#pragma aux terminal_transfer_active "terminal_transfer_active";
extern unsigned terminal_controller_active;
#pragma aux terminal_controller_active "terminal_controller_active";
extern unsigned terminal_monitor_active;
#pragma aux terminal_monitor_active "terminal_monitor_active";
extern unsigned process_busy;
#pragma aux process_busy "process_busy";
extern unsigned terminal_macro_active;
#pragma aux terminal_macro_active "terminal_macro_active";
extern unsigned terminal_directory_context_valid;
#pragma aux terminal_directory_context_valid "terminal_directory_context_valid";
extern unsigned terminal_directory_entry;
#pragma aux terminal_directory_entry "terminal_directory_entry";
extern unsigned terminal_directory_codes;
#pragma aux terminal_directory_codes "terminal_directory_codes";
extern unsigned terminal_directory_mode;
#pragma aux terminal_directory_mode "terminal_directory_mode";
extern unsigned terminal_directory_protocol;
#pragma aux terminal_directory_protocol "terminal_directory_protocol";
extern unsigned terminal_option_mask;
#pragma aux terminal_option_mask "terminal_option_mask";
extern unsigned terminal_modem_init_wait;
#pragma aux terminal_modem_init_wait "terminal_modem_init_wait";
extern unsigned terminal_break_delay_units;
#pragma aux terminal_break_delay_units "terminal_break_delay_units";
extern unsigned terminal_baud_low;
#pragma aux terminal_baud_low "terminal_baud_low";
extern unsigned terminal_baud_high;
#pragma aux terminal_baud_high "terminal_baud_high";
extern unsigned terminal_parity;
#pragma aux terminal_parity "terminal_parity";
extern unsigned terminal_data_bits;
#pragma aux terminal_data_bits "terminal_data_bits";
extern unsigned terminal_stop_bits;
#pragma aux terminal_stop_bits "terminal_stop_bits";
extern unsigned uart_software_flow;
#pragma aux uart_software_flow "uart_software_flow";
extern unsigned uart_hardware_flow;
#pragma aux uart_hardware_flow "uart_hardware_flow";
extern unsigned uart_tx_paused;
#pragma aux uart_tx_paused "uart_tx_paused";
extern unsigned terminal_translation_mode;
#pragma aux terminal_translation_mode "terminal_translation_mode";
extern unsigned terminal_translation_enabled;
#pragma aux terminal_translation_enabled "terminal_translation_enabled";
extern unsigned uart_rx_mask;
#pragma aux uart_rx_mask "uart_rx_mask";
extern unsigned csi_terminal_id;
#pragma aux csi_terminal_id "csi_terminal_id";
extern unsigned terminal_setup_profile_ready;
#pragma aux terminal_setup_profile_ready "terminal_setup_profile_ready";
extern unsigned terminal_setup_profile_status;
#pragma aux terminal_setup_profile_status "terminal_setup_profile_status";
extern unsigned setup_profile_target;
#pragma aux setup_profile_target "setup_profile_target";
extern unsigned terminal_setup_link_status;
#pragma aux terminal_setup_link_status "terminal_setup_link_status";
extern unsigned connection_baud_index;
#pragma aux connection_baud_index "connection_baud_index";
extern unsigned terminal_quit;
#pragma aux terminal_quit "terminal_quit";
extern unsigned terminal_exit_code;
#pragma aux terminal_exit_code "terminal_exit_code";
extern unsigned char uart_flow_pending;
#pragma aux uart_flow_pending "uart_flow_pending";
extern unsigned char uart_xoff_sent;
#pragma aux uart_xoff_sent "uart_xoff_sent";
extern unsigned char uart_rts_lowered;
#pragma aux uart_rts_lowered "uart_rts_lowered";
extern unsigned char connection_enabled;
#pragma aux connection_enabled "connection_enabled";
extern unsigned char connection_carrier_seen;
#pragma aux connection_carrier_seen "connection_carrier_seen";
extern unsigned char terminal_modem_pause;
#pragma aux terminal_modem_pause "terminal_modem_pause";
extern directory_live_context terminal_directory_context;
#pragma aux terminal_directory_context "terminal_directory_context";
extern directory_live_plan terminal_directory_plan;
#pragma aux terminal_directory_plan "terminal_directory_plan";
extern modem_import_settings terminal_modem_settings;
#pragma aux terminal_modem_settings "terminal_modem_settings";
extern transfer_import_settings terminal_transfer_preferences;
extern unsigned modem_response_cursors[11];
#pragma aux modem_response_cursors "modem_response_cursors";
extern unsigned char terminal_dial_target[64];
#pragma aux terminal_dial_target "terminal_dial_target";
extern char terminal_directory_path[64];
#pragma aux terminal_directory_path "terminal_directory_path";
extern char terminal_keyboard_path[64];
#pragma aux terminal_keyboard_path "terminal_keyboard_path";
extern char terminal_actions_path[64];
#pragma aux terminal_actions_path "terminal_actions_path";
extern unsigned char connection_init[129];
#pragma aux connection_init "connection_init";
extern unsigned char connection_dial[129];
#pragma aux connection_dial "connection_dial";
extern unsigned char connection_hangup[129];
#pragma aux connection_hangup "connection_hangup";
extern unsigned char terminal_keymap[948];
#pragma aux terminal_keymap "terminal_keymap";
extern unsigned char setup_profile_keymap[948];
#pragma aux setup_profile_keymap "setup_profile_keymap";
extern unsigned char terminal_action_definitions[540];
#pragma aux terminal_action_definitions "terminal_action_definitions";
extern unsigned char terminal_translation_table[256];
#pragma aux terminal_translation_table "terminal_translation_table";
extern unsigned char modem_response_slots[176];
#pragma aux modem_response_slots "modem_response_slots";
extern char command_menu_script[64];
static void read(void *to,const void __far *from,unsigned bytes)
{unsigned i;for(i=0;i<bytes;++i)((unsigned char *)to)[i]=((const unsigned char __far *)from)[i];}
static void write(void __far *to,const void __far *from,unsigned bytes)
{unsigned i;for(i=0;i<bytes;++i)((unsigned char __far *)to)[i]=((const unsigned char __far *)from)[i];}
static void zero(void *p,unsigned bytes)
{unsigned i;for(i=0;i<bytes;++i)((unsigned char *)p)[i]=0;}
static unsigned context(const directory_selection_proposal __far *p,unsigned action)
{
 prm_dos_image image;directory_live_context before,next;
 if(hook_baseline_copy(&image))return 1;
 read(&next,&p->context,sizeof(next));
 if(terminal_directory_context_valid)memcpy(&before,&terminal_directory_context,sizeof(before));
 return directory_adopt_setup(terminal_directory_context_valid?&before:0,&next,&image,action);
}
static unsigned modem(const directory_selection_proposal __far *p)
{
 hook_return_plan settings;hook_modem_plan plan;hook_modem_result result;unsigned char target[64];
 zero(&settings,sizeof(settings));read(&settings.serial,&p->configuration.serial,44);
 read(&settings.modem,&p->configuration.modem,368);settings.modem_active=!p->configuration.directory.dialing_mode;
 read(target,p->configuration.directory.target,64);
 if(hook_modem_prepare(&settings,target,terminal_modem_init_wait!=0,&plan,&result))return 1;
 write(MODEM,(const void __far *)&plan,sizeof(plan));return 0;
}
static unsigned translation(const directory_resource_bundle __far *b,unsigned publish)
{
 char path[64];unsigned char table[256];
 read(path,b->translation_path,64);read(table,b->translation,256);
 return publish?directory_adopt_xlt_publish(b->translation_mode,path,table,terminal_translation_table):
  directory_adopt_xlt_check(b->translation_mode,path,table,terminal_translation_table);
}
static unsigned state(void)
{
 return terminal_directory_adopt_requested!=1 || terminal_program_active!=1 || terminal_program_pending ||
  terminal_program_kind!=8 || terminal_program_status!=2 || connection_state || terminal_parser_active ||
  terminal_tx_count || uart_rx_count || uart_rx_dropped || terminal_transfer_pending || terminal_transfer_active ||
  terminal_controller_active || terminal_monitor_active || process_busy || terminal_macro_active || terminal_directory_context_valid>1 || SCRIPT->held;
}
unsigned __far __cdecl directory_adopt_exec_allowed(void)
{return !SCRIPT->held;}
unsigned __far __cdecl terminal_directory_adopt(const directory_selection_proposal __far *p,const directory_resource_bundle __far *b)
{
 terminal_import_settings serial;unsigned i,j,profile_changed,old_soft=uart_software_flow;
 if(state())return 1;
 if(context(p,0))return 2;
 if(b->profile!=p->configuration.serial.terminal_id || b->translation_mode!=p->configuration.serial.translation_mode ||
  b->script.kind>DSCRIPT_COMPILED)return 4;
 for(i=0;i<79;++i){for(j=0;j<12 && b->keyboard[i*12+j];++j){}if(j==12)return 4;}
 if(modem(p))return 3;
 if(translation(b,0))return 4;
 read(&serial,&p->configuration.serial,44);
 if(hook_prepare_link() || hook_apply_uart_check(15) || directory_adopt_carrier_check())return 5;
 if((p->configuration.change_mask&LIVE_CHANGE_PORT) && hook_port_check(&serial))return 5;
 if(context(p,0) || translation(b,0) || state())return 2;
 /* The final fallible hardware step repeats its own late arrival checks. */
 if((p->configuration.change_mask&LIVE_CHANGE_PORT) && hook_port_move(&serial))return 5;
 /* No callbacks/IO/foreground scheduling intervene after validation. A broken
  * invariant after resource transfer must stop instead of resuming mixed state. */
 if(context(p,1) || translation(b,1)){
  terminal_quit=1;if(!terminal_exit_code)terminal_exit_code=7;return 6;
 }
 profile_changed=serial.terminal_id!=csi_terminal_id;
 terminal_setup_profile_status=profile_changed?1:0;terminal_setup_profile_ready=profile_changed;
 setup_profile_target=serial.terminal_id;
 write((void __far *)(profile_changed?setup_profile_keymap:terminal_keymap),b->keyboard,948);
 write((void __far *)terminal_action_definitions,b->actions,540);
 write((void __far *)terminal_keyboard_path,b->keyboard_path,64);write((void __far *)terminal_actions_path,b->actions_path,64);
 terminal_option_mask=(terminal_option_mask&~(512U|4096U))|(b->mask&(512U|4096U))|64;
 write((void __far *)&terminal_directory_context,&p->context,sizeof(terminal_directory_context));
 write((void __far *)&terminal_directory_plan,&p->configuration.directory,sizeof(terminal_directory_plan));
 write((void __far *)terminal_directory_path,p->context.directory_path,64);
 write((void __far *)terminal_dial_target,p->configuration.directory.target,64);
 terminal_directory_entry=p->context.selection.entry_number;terminal_directory_codes=p->context.codes;
 terminal_directory_mode=p->configuration.directory.dialing_mode;terminal_directory_protocol=p->configuration.directory.protocol_index;
 terminal_directory_context_valid=1;
 write((void __far *)&terminal_transfer_preferences,&p->transfer,sizeof(terminal_transfer_preferences));
 write((void __far *)&terminal_modem_settings,&p->configuration.modem,368);
 if(MODEM->active){
  write((void __far *)connection_init,MODEM->commands[0],129);write((void __far *)connection_dial,MODEM->dial,129);
  write((void __far *)connection_hangup,MODEM->commands[3],129);write((void __far *)modem_response_slots,MODEM->responses,176);
  for(i=0;i<11;++i)modem_response_cursors[i]=(unsigned)(modem_response_slots+16*i);
 }
 terminal_modem_pause=(unsigned char)serial.mapping_pause_character;
 terminal_break_delay_units=terminal_modem_settings.break_delay_units;
 connection_baud_index=MODEM->baud_index;connection_enabled=1;connection_carrier_seen=0;
 terminal_baud_low=serial.baud_low;terminal_baud_high=serial.baud_high;terminal_parity=serial.parity;
 terminal_data_bits=serial.data_bits;terminal_stop_bits=serial.stop_bits;
 uart_software_flow=serial.software_flow;uart_hardware_flow=serial.hardware_flow;
 if(!uart_software_flow){uart_tx_paused=0;uart_flow_pending=uart_xoff_sent=0;}
 else if(!old_soft || (p->configuration.change_mask&LIVE_CHANGE_PORT)){uart_tx_paused=0;uart_flow_pending=0x11;uart_xoff_sent=0;}
 uart_rts_lowered=0;terminal_setup_link_status=1;
 terminal_translation_mode=b->translation_mode;terminal_translation_enabled=b->translation_mode==1;uart_rx_mask=b->translation_mode==2?127:255;
 write(SCRIPT->path,b->script_path,64);write(&SCRIPT->fingerprint,&b->script,12);SCRIPT->bound=1;
 hook_apply_display(&serial);return 0;
}
unsigned __far __cdecl directory_adopt_script_name(void)
{
 if(!SCRIPT->bound)return 0;
 if(SCRIPT->held || !SCRIPT->path[0])return 1;
 read(command_menu_script,SCRIPT->path,64);return 2;
}
static unsigned __far __cdecl script_probe(const char *path,void *context_pointer)
{
 unsigned i;if(context_pointer!=&terminal_directory_adopt_requested)return 1;
 for(i=0;i<64;++i){if(path[i]!=SCRIPT->path[i])return 0;if(!path[i])return 1;}return 0;
}
unsigned __far __cdecl directory_adopt_script_check(const char *name)
{
 char path[64];directory_script_fingerprint now;directory_script_result io;unsigned i,status;
 if(SCRIPT->held)return 1;
 if(!SCRIPT->bound || !SCRIPT->path[0])return 0;
 for(i=0;i<64;++i){if(name[i]!=SCRIPT->path[i])return 0;if(!name[i])break;}
 read(path,SCRIPT->path,64);
 if(capture_file_reserve(script_probe,&terminal_directory_adopt_requested))return 1;
 zero(&io,sizeof(io));status=directory_adopt_script_read(path,DSCRIPT_COMPILED,&now,&io);
 if(io.close_error){SCRIPT->held=1;return 1;}
 if(!status)for(i=0;i<12;++i)if(((unsigned char *)&now)[i]!=((unsigned char __far *)&SCRIPT->fingerprint)[i]){status=1;break;}
 if(capture_file_release(script_probe,&terminal_directory_adopt_requested)){SCRIPT->held=1;return 1;}
 return status;
}
