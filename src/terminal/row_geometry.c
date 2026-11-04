/* Maintained offline BIOS/canonical/reset transaction around recovered services.
 * The inactive frozen-history workspace supplies rollback storage; no heap.
 * Geometry changes deliberately execute configured RIS, as native DISPLAY does.
 */
#include <dos.h>
#include "status_transition.h"
#include "row_geometry.h"
#include "../process/native_display_rows.h"
typedef unsigned short word;
typedef unsigned char byte;
#define TEXT __based(__segname("_CODE"))
unsigned terminal_row_geometry_active=0;
#ifdef TERMINAL_DISPLAY_SELECTOR
#include "../config/display_preferences.h"
unsigned terminal_display_selector=0xffff;
unsigned terminal_display_selector_ready=0;
unsigned terminal_display_fallback=0;
unsigned terminal_display_physical_result=0;
#endif
extern byte __far redisplay_snapshot[];
extern byte __far redisplay_snapshot_end[];
#pragma aux redisplay_snapshot "redisplay_snapshot";
#pragma aux redisplay_snapshot_end "redisplay_snapshot_end";
extern word reset_byte_addresses[],reset_byte_addresses_end[];
#pragma aux reset_byte_addresses "reset_byte_addresses";
#pragma aux reset_byte_addresses_end "reset_byte_addresses_end";
extern byte terminal_keymap[],terminal_tab_stops[],ansi_parameters[];
#pragma aux terminal_keymap "terminal_keymap";
#pragma aux terminal_tab_stops "terminal_tab_stops";
#pragma aux ansi_parameters "ansi_parameters";
extern word terminal_quit,terminal_exit_code,csi_unimplemented_service;
#pragma aux terminal_quit "terminal_quit";
#pragma aux terminal_exit_code "terminal_exit_code";
#pragma aux csi_unimplemented_service "csi_unimplemented_service";
extern word __far __cdecl notice_idle(void);
#pragma aux notice_idle "terminal_status_notice_idle_far";
extern word __far __cdecl recording_owned(void);
#pragma aux recording_owned "terminal_recording_owned_far";
extern word __far __cdecl defaults_resize(word rows);
#pragma aux defaults_resize "terminal_status_defaults_far";
extern word __far __cdecl status_refresh(void);
#pragma aux status_refresh "terminal_status_notice_refresh";
extern void __far __cdecl native_reset(void);
#pragma aux native_reset "terminal_control_reset_far";
extern void __far __cdecl native_cursor(word row,word column);
#pragma aux native_cursor "terminal_status_cursor_far";
#ifdef TERMINAL_ROW_MOUSE
extern word mouse_count;
#pragma aux mouse_count "mouse_count";
extern word __far __cdecl mouse_phase(void);
extern word __far __cdecl mouse_pause(void);
extern word __far __cdecl mouse_resume(void);
#pragma aux mouse_phase "terminal_rows_mouse_phase_far";
#pragma aux mouse_pause "_terminal_mouse_pause_far";
#pragma aux mouse_resume "terminal_rows_mouse_resume_far";
#endif
static word * const TEXT owners[]={
 &terminal_program_active,&terminal_program_pending,&terminal_aspect_active,
 &terminal_parser_active,&terminal_macro_active,&terminal_ansi_wait_active,
 &terminal_monitor_active,&terminal_snapshot_active,&terminal_screen_print_active,
 &terminal_controller_active,&terminal_transfer_active,&terminal_transfer_pending,
 &uart_break_hold,&terminal_tx_count,&_redisplay_active,&_redisplay_live_ready,
 &_redisplay_export_pending,&_redisplay_search_pending,&_command_menu_active,
 &_terminal_elapsed_view_active,&terminal_screen_pause_active,&terminal_manual_init_active,
 &_clipboard_ui_active,&_clipboard_ui_visible,&_clipboard_paste_pending,&terminal_menu_pending
};
/* Exclusive scratch regions, byte offsets within retained63000-byte snapshot. */
#define VIDEO 0
#define SHADOW 8000
#define FLAGS 16192
#define ATTRS 20288
#define LINES 24384
#define KEYS 24512
#define TABS 25460
#define PARAMS 25490
#define BACKUP_END 25522
static word legal(word rows){return rows==25 || rows==28 || rows==43 || rows==50;}
unsigned __far __cdecl terminal_row_status_layout(void)
{
 word rows=ui_window_rows;
 if(!legal(rows) || ui_flow_suppressed>1 || ui_flow_region_cells!=80 || screen_columns!=80)return 3;
 if(screen_video_row_bytes!=160 || text_video_segment!=0xb800)return 3;
 if(ui_flow_video_base!=(rows-1)*160 || ui_flow_coordinate_base!=(rows-1)*256)return 3;
 if(csi_row_count!=rows-(ui_flow_suppressed?0:1) || csi_last_row!=csi_row_count-1)return 3;
 return 0;
}
static word admit(native_display_rows_info *p)
{
 word flags=0,dsword=0,ssword=0,i,rows,rate=0;
 static const unsigned long TEXT rates[]={300,1200,2400,4800,9600,19200,38400,57600,115200};
 __asm {
 pushf
 pop ax
 mov flags,ax
 mov ax,ds
 mov dsword,ax
 mov ax,ss
 mov ssword,ax
 }
 if(dsword!=ssword || (flags&0x600)!=0x200 || terminal_row_geometry_active || terminal_status_toggle_active)return 3;
 if(reset_ready!=1)return 2;
 if(connection_state || terminal_row_status_layout())return 3;
 for(i=0;i<sizeof(owners)/sizeof(owners[0]);++i)if(*owners[i])return 3;
 if(terminal_browser_screen_owned || terminal_editor_screen_owned || reset_bank_busy || terminal_auto_answer_notice_active || terminal_script_overlay_visible)return 3;
 if(notice_idle() || recording_owned())return 3;
#ifdef TERMINAL_ROW_MOUSE
 if(mouse_phase()>1 || mouse_count)return 3;
#endif
 if(terminal_tab_wrap || terminal_parity>4 || terminal_data_bits<5 || terminal_data_bits>8 || terminal_stop_bits<1 || terminal_stop_bits>2)return 3;
 for(i=0;i<9;++i)if(rates[i]==(((unsigned long)terminal_baud_high<<16)|terminal_baud_low))rate=1;
 if(!rate)return 3;
 if(csi_terminal_id!=4 && csi_terminal_id!=6)return 3;
 if(screen_video_row_bytes!=160 || screen_attribute_row_bytes!=80 || screen_last_column!=79)return 3;
 if(screen_viewport_enabled || screen_viewport_active || screen_viewport_offset || screen_cursor_wrap || screen_attribute_checks || erase_protection_mode)return 3;
 if(text_video_segment!=0xb800 || text_cga_status_port || screen_attributes_base!=(word)screen_attribute_cells || erase_attribute_values_base!=(word)erase_attribute_values)return 3;
 if(erase_shadow_offset!=FP_OFF(erase_shadow_cells) || erase_shadow_segment!=FP_SEG(erase_shadow_cells))return 3;
 if(FP_SEG(redisplay_snapshot)!=FP_SEG(redisplay_snapshot_end) || FP_OFF(redisplay_snapshot_end)-FP_OFF(redisplay_snapshot)<BACKUP_END)return 3;
 rows=csi_row_count;
 if(erase_cell_count!=rows*80 || screen_first_row>screen_last_row || screen_last_row>=rows || csi_origin_row>csi_origin_bottom || csi_origin_bottom>=rows)return 3;
 if(screen_cursor_row>=rows || screen_cursor_column>=80 || screen_visible_column!=screen_cursor_column || csi_saved_row>=rows || csi_saved_column>=80)return 3;
 if(screen_previous_row!=screen_cursor_row || screen_previous_column!=screen_cursor_column || screen_video_offset!=screen_cursor_row*160+screen_cursor_column*2 || screen_attribute_offset!=screen_cursor_row*80+screen_cursor_column)return 3;
 if(native_display_rows_probe(p) || p->mode!=3 || p->rows!=ui_window_rows || p->segment!=0xb800)return 3;
 return 0;
}
static void save(word at,const byte *p,word count)
{word i;for(i=0;i<count;++i)redisplay_snapshot[at+i]=p[i];}
static void restore(word at,byte *p,word count)
{word i;for(i=0;i<count;++i)p[i]=redisplay_snapshot[at+i];}
static void layout(word physical,word hidden)
{
 ui_window_rows=physical;ui_flow_suppressed=hidden;
 ui_flow_video_base=(physical-1)*160;ui_flow_coordinate_base=(physical-1)*256;
}
static word mouse_restore(void)
{
#ifdef TERMINAL_ROW_MOUSE
 if(mouse_resume()){terminal_quit=1;terminal_exit_code=14;return 6;}
#endif
 return 0;
}
#ifdef TERMINAL_DISPLAY_SELECTOR
static unsigned geometry_request(word requested,word selector,word mode,word hidden)
#else
unsigned __far __cdecl terminal_row_geometry_set(unsigned requested)
#endif
{
 word values[128],baseline[128],ui[4],shape=0,xy=0,i,count,bytes,status,restore_status,old_physical;
 byte live_bytes[16];native_display_rows_info before,actual;
#ifdef TERMINAL_DISPLAY_SELECTOR
 native_display_selection selected,restored;word physical_status=0,preferred_rows=requested;
#endif
 byte __far *video=(byte __far *)MK_FP(0xb800,0);
#ifdef TERMINAL_DISPLAY_SELECTOR
 if(selector!=0xffff && selector>4)return 1;
 if(hidden>1)return 3;
#endif
#ifdef TERMINAL_DISPLAY_SELECTOR
 if(selector==0xffff && !legal(requested))return 1;
#else
 if(!legal(requested))return 1;
#endif
 status=admit(&before);if(status)return status;
#ifdef TERMINAL_DISPLAY_SELECTOR
 if(selector!=0xffff){
  if(selector==0)requested=before.rows;
  else if(selector==1 || selector==3 || ((selector==4) && ((signed short)mode<=0 || !before.font_capable)))requested=25;
  else if(!before.font_capable)requested=25;
  else if(before.scanline_capable){requested&=255;if(requested!=28 && requested!=43 && requested!=50)requested=25;}
  else requested=(requested&255)==43?43:25;
 }
#endif
 if(requested!=25 && (!before.font_capable || (!before.scanline_capable && requested!=43)))return 3;
 count=(word)(reset_word_addresses_end-reset_word_addresses);bytes=(word)(reset_byte_addresses_end-reset_byte_addresses);
 if(count>128 || bytes>16)return 3;
 for(i=0;i<count;++i){values[i]=*(word *)reset_word_addresses[i];baseline[i]=reset_words[i];}
 for(i=0;i<bytes;++i)live_bytes[i]=*(byte *)reset_byte_addresses[i];
 ui[0]=ui_window_rows;ui[1]=ui_flow_video_base;ui[2]=ui_flow_coordinate_base;ui[3]=ui_flow_suppressed;
#ifdef TERMINAL_DISPLAY_SELECTOR
 status=defaults_resize(requested-(hidden?0:1));if(status)return status;
#else
 status=defaults_resize(requested-(ui[3]?0:1));if(status)return status;
#endif
 terminal_row_geometry_active=1;old_physical=before.rows;
#ifdef TERMINAL_ROW_MOUSE
 if(mouse_pause()){
  for(i=0;i<count;++i)reset_words[i]=baseline[i];
  terminal_quit=1;terminal_exit_code=14;terminal_row_geometry_active=0;return 6;
 }
#endif
 __asm {
 mov ah,3
 xor bx,bx
 int 10h
 mov xy,dx
 mov shape,cx
 }
 for(i=0;i<8000;++i)redisplay_snapshot[VIDEO+i]=video[i];
 for(i=0;i<8192;++i)redisplay_snapshot[SHADOW+i]=((byte __far *)erase_shadow_cells)[i];
 save(FLAGS,screen_attribute_cells,4096);save(ATTRS,erase_attribute_values,4096);
 save(LINES,screen_line_flags,128);save(KEYS,terminal_keymap,948);
 save(TABS,terminal_tab_stops,30);save(PARAMS,ansi_parameters,32);
#ifdef TERMINAL_DISPLAY_SELECTOR
 if(selector!=0xffff){
  selected.geometry=before;selected.accepted_selector=0xffff;
  physical_status=native_display_select(selector,preferred_rows,mode,&selected);
  actual=selected.geometry;
  status=physical_status;
  if((status==0 || (status==DISPLAY_ROWS_FAILED && actual.fallback==1 && selected.accepted_selector==1)) &&
     actual.mode==3 && actual.segment==0xb800 && actual.columns==80 && actual.stride==160 && legal(actual.rows)){
   requested=actual.rows;status=defaults_resize(requested-(hidden?0:1));
  }else status=DISPLAY_ROWS_UNSUPPORTED;
 }else status=native_display_rows_set(requested,&actual);
#else
 status=native_display_rows_set(requested,&actual);
#endif
 if(!status && actual.rows==requested){
#ifdef TERMINAL_DISPLAY_SELECTOR
  layout(requested,hidden);native_reset();
#else
  layout(requested,ui[3]);native_reset();
#endif
  status=status_refresh();
  if(!status){
   for(i=0;i<4096;++i)erase_shadow_cells[i]=i<requested*80?((word __far *)video)[i]:0;
   native_cursor(screen_cursor_row,screen_cursor_column);
#ifdef TERMINAL_DISPLAY_SELECTOR
   if(selector==0xffff)terminal_display_selector_ready=0;
   else{
     terminal_display_selector=selected.accepted_selector;
     terminal_display_fallback=actual.fallback;
     terminal_display_physical_result=physical_status;
     terminal_display_selector_ready=1;
   }
#endif
   status=mouse_restore();terminal_row_geometry_active=0;return status;
  }
 }
 /* Restore BIOS first, then all canonical state/configured defaults and planes.
  * If hardware refuses the old geometry, request existing fatal shutdown;
  * never return to foreground parsing with a fabricated successful rollback. */
#ifdef TERMINAL_DISPLAY_SELECTOR
 /* A selected mono/alternate text mode cannot be repaired by a font request
  * alone. Restore our admitted mode3/B800 first, then the old physical rows. */
 restore_status=native_display_rows_probe(&actual);
 if(!restore_status && (actual.mode!=3 || actual.segment!=0xb800)){
  restored.geometry=actual;restored.accepted_selector=0xffff;
  restore_status=native_display_select(3,25,3,&restored);actual=restored.geometry;
 }
 if(!restore_status && actual.mode==3 && actual.segment==0xb800)restore_status=native_display_rows_set(old_physical,&actual);
 else restore_status=DISPLAY_ROWS_UNUSABLE;
#else
 restore_status=native_display_rows_set(old_physical,&actual);
#endif
 for(i=0;i<count;++i){*(word *)reset_word_addresses[i]=values[i];reset_words[i]=baseline[i];}
 for(i=0;i<bytes;++i)*(byte *)reset_byte_addresses[i]=live_bytes[i];
 ui_window_rows=ui[0];ui_flow_video_base=ui[1];ui_flow_coordinate_base=ui[2];ui_flow_suppressed=ui[3];
 for(i=0;i<8000;++i)video[i]=redisplay_snapshot[VIDEO+i];
 for(i=0;i<8192;++i)((byte __far *)erase_shadow_cells)[i]=redisplay_snapshot[SHADOW+i];
 restore(FLAGS,screen_attribute_cells,4096);restore(ATTRS,erase_attribute_values,4096);
 restore(LINES,screen_line_flags,128);restore(KEYS,terminal_keymap,948);
 restore(TABS,terminal_tab_stops,30);restore(PARAMS,ansi_parameters,32);
 if((restore_status==0 || restore_status==DISPLAY_ROWS_FAILED) && actual.rows==old_physical
#ifdef TERMINAL_DISPLAY_SELECTOR
    && actual.mode==3 && actual.segment==0xb800
#endif
 ){
  __asm {
  mov cx,shape
  mov ah,1
  push bp
  int 10h
  pop bp
  mov dx,xy
  xor bx,bx
  mov ah,2
  int 10h
  }
  status=mouse_restore();terminal_row_geometry_active=0;return status?status:4;
 }
 terminal_quit=1;terminal_exit_code=2;csi_unimplemented_service=0x6ef6;
 terminal_row_geometry_active=0;return 5;
}

#ifdef TERMINAL_DISPLAY_SELECTOR
unsigned __far __cdecl terminal_row_geometry_set(unsigned rows)
{return geometry_request(rows,0xffff,0,ui_flow_suppressed);}
unsigned __far __cdecl terminal_display_select(unsigned selector,unsigned rows,unsigned mode)
{if(selector>4)return 1;return geometry_request(rows,selector,mode,ui_flow_suppressed);}
unsigned __far __cdecl terminal_display_apply_saved(void)
{
 if(terminal_display_preferences_ready!=1)return 7;
 if(terminal_display_preferences.selector>4)return 1;
 return geometry_request(terminal_display_preferences.rows,terminal_display_preferences.selector,
  terminal_display_preferences.video_mode,terminal_display_preferences.status_hidden?1:0);
}
unsigned __far __cdecl terminal_display_cycle(void)
{
 word choices;
 if(terminal_display_preferences_ready!=1 || terminal_display_selector_ready!=1)return 7;
 if(terminal_display_selector>4)return 1;
 choices=terminal_display_preferences.video_mode?4:2;
 return terminal_display_select(terminal_display_selector%choices+1,
  terminal_display_preferences.rows,terminal_display_preferences.video_mode);
}
#ifdef TERMINAL_DISPLAY_STARTUP
unsigned __far __cdecl terminal_display_startup(void)
{
 /* No import means the admitted source-owned baseline remains in force.
  * Do not manufacture saved preferences or selector readiness in that case. */
 if(!terminal_display_preferences_ready)return 0;
 return terminal_display_apply_saved();
}
#endif
#endif
