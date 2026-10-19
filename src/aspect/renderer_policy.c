/* Maintained shared-renderer rejection policy. This does not recover a native
 * admission function. Existing renderer/mode/control instructions execute only
 * after these pure checks. A rejected list cannot mutate any earlier mode.
 */
#include <dos.h>
#include "renderer_policy.h"
#include "../capture/capture_file.h"
#include "../capture/capture_session.h"
#include "../printer/printer_device.h"
#include "../transfer/download_file.h"
#include "../transfer/upload_file.h"
#include "../transfer/batch_download.h"

static unsigned near_span(unsigned offset,unsigned bytes)
{ return bytes && offset<=65535U-bytes+1U; }
static unsigned capture_closed(const capture_file_snapshot *owner)
{ return !owner->handle_open && !owner->handle_uncertain; }

/* O(1) lease invariants: foreground owners are suspended, parser mutation
 * passes guarded modes/controls/edit helpers. Recheck dynamic state per byte. */
static unsigned render_live_state(unsigned scoped)
{
 unsigned cell,start,end,segment;
 volatile unsigned char __far *bda=(volatile unsigned char __far *)MK_FP(0x40,0);
 if(terminal_program_active!=1 || terminal_program_kind!=4 || terminal_program_pending ||
    terminal_ansi_wait_active || terminal_monitor_active ||
    terminal_snapshot_active || terminal_screen_print_active || terminal_controller_active ||
    terminal_macro_active || terminal_transfer_active || terminal_transfer_pending ||
    redisplay_active || command_menu_active || (connection_state && connection_state!=6))return 3;
 if(scoped){
  if(terminal_aspect_active!=1 || !terminal_parser_active || terminal_parser_active>16)return 3;
 }else if(terminal_aspect_active || terminal_parser_active)return 3;
 if(reset_ready!=1 || (csi_terminal_id!=4 && csi_terminal_id!=6) ||
    terminal_ansi_m_policy>1)return 3;
 if(!capture_closed(&capture_file_result) || !capture_closed(&snapshot_file_result) ||
    !capture_closed(&monitor_file_result) || !capture_closed(&history_file_result) ||
    printer_device_result.handle_open || printer_device_result.handle_uncertain ||
    transfer_download_result.handle_open || transfer_download_result.handle_uncertain ||
    batch_download_result.file.handle_open || batch_download_result.file.handle_uncertain ||
    upload_source_result.handle_open || upload_source_result.handle_uncertain ||
    upload_source_result.discovery_open || upload_source_result.binary_open)return 3;
 /* Disabled logger branches must not admit queued writes or ambiguous owners.
  * sink398c is a disabled/hold flag; require0 as the owned normal baseline. */
 if(terminal_sink_3988_enabled || terminal_sink_398a_enabled || terminal_sink_398c_disabled ||
    terminal_printer_count || terminal_printer_closing || csi_printer_ready ||
    capture_session_buffered)return 3;
 if(bda[0x49]!=3 || *(volatile unsigned __far *)(bda+0x4a)!=80 || bda[0x62] ||
    (bda[0x84] && bda[0x84]!=24))return 3;
 if(screen_columns!=80 || screen_video_row_bytes!=160 || screen_attribute_row_bytes!=80 ||
    csi_last_column!=79 || csi_column_count!=80 || csi_last_row!=24 || csi_row_count!=25 ||
    text_video_segment!=0xb800 || text_cga_status_port ||
    screen_viewport_active || screen_viewport_enabled || screen_viewport_offset ||
    screen_attribute_checks || terminal_mode_372c || render_translation_enabled ||
    erase_protection_mode || erase_cell_count!=2000)return 3;
 if(screen_cursor_row>24 || screen_cursor_column>79 || screen_first_row>screen_last_row ||
    screen_last_row>24 || csi_origin_row>csi_origin_bottom || csi_origin_bottom>24)return 3;
 cell=screen_cursor_row*80+screen_cursor_column;
 if(screen_attribute_offset!=cell || screen_video_offset!=cell*2)return 3;
 if(!near_span((unsigned)screen_attribute_cells,4096) ||
    !near_span((unsigned)erase_attribute_values,4096) ||
    !near_span((unsigned)terminal_keymap,948) ||
    screen_attributes_base!=(unsigned)screen_attribute_cells ||
    erase_attribute_values_base!=(unsigned)erase_attribute_values)return 3;
 if(erase_shadow_segment!=FP_SEG(erase_shadow_cells) || erase_shadow_offset!=FP_OFF(erase_shadow_cells) ||
    !near_span(erase_shadow_offset,8192))return 3;
 start=FP_OFF(terminal_history_buffer);segment=FP_SEG(terminal_history_buffer);
 if(!near_span(start,63000))return 3;
 end=start+63000;
 if(terminal_history_start!=start || terminal_history_end!=end ||
    terminal_history_pointer[1]!=segment || terminal_history_pointer[0]<start ||
    terminal_history_pointer[0]>=end || terminal_history_pending>2 || terminal_history_wrapped>1)return 3;
 return 0;
}

unsigned __cdecl aspect_render_admit(void)
{
 unsigned i,j;
 if(render_live_state(0))return 3;
 /* Admission-only contents. The suspended parent has no outside writer;
  * supported guarded commands retain these bounds/cleared complex metadata. */
 /* Reject unsupported metadata providers before render/scroll mutates video. */
 for(i=0;i<2000;++i)if(screen_attribute_cells[i]&0x80)return 3;
 for(i=0;i<25;++i)if(screen_line_flags[i]&0x40)return 3;
 for(i=0;i<79;++i){
  for(j=0;j<12 && terminal_keymap[i*12+j];++j){}
  if(j==12)return 3;
 }
 return 0;
}

unsigned __cdecl aspect_render_preflight_modes(unsigned setting)
{
 unsigned i,value;
 if(setting>1 || ansi_parameter_count>16)return 3;
 /* Native report-prefix mode causes the entire handler to return unchanged. */
 if(csi_report_private_prefix)return 0;
 for(i=0;i<ansi_parameter_count;++i){
  value=ansi_parameters[i];
  if((!ansi_private && value==4) || (ansi_private && value==3) ||
     (value==12 && (setting || !ansi_private)) ||
     (!setting && ansi_private && value==2))return 3;
 }
 return 0;
}

unsigned __cdecl aspect_render_preflight_control(unsigned character)
{
 if(render_live_state(1))return 3;
 character&=255;
 if(character==0x18 || character==0x1a){
  if(terminal_tab_wrap || terminal_control_mode_9026 ||
     (!terminal_newline_mode_9020 && terminal_control_mode_1fb0))return 3;
 }
 /* VT's raw continuation under9026 is legitimate and must use child read.
  * Otherwise DEC keys selects the existing linefeed; only ba33 is rejected. */
 if(character==11 && csi_terminal_id<20 && !terminal_control_mode_9026 &&
    !terminal_dec_keys && terminal_newline_mode_9020)return 3;
 return 0;
}
