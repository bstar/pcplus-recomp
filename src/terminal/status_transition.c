/* Maintained offline live row transaction around recovered cursor/scroll/status.
 * Narrow unprotected BIOS text; composed full-frame owners admit larger rows.
 * The caller retires notices first; active/pending leases cause a clean refusal.
 */
#include <dos.h>
#include "status_transition.h"
typedef status_word word;
typedef unsigned char byte;
#define TEXT __based(__segname("_CODE"))
#if defined(TERMINAL_LARGE_VIEW_FRAMES) && defined(TERMINAL_PROGRAM_DISPLAY)
#define STATUS_LARGE_ROWS
#endif
unsigned terminal_status_toggle_active=0;
extern unsigned __far __cdecl notice_idle(void);
#pragma aux notice_idle "terminal_status_notice_idle_far";
extern unsigned __far __cdecl recording_owned(void);
#pragma aux recording_owned "terminal_recording_owned_far";
extern unsigned __far __cdecl defaults_resize(unsigned rows);
#pragma aux defaults_resize "terminal_status_defaults_far";
extern unsigned __far __cdecl status_refresh(void);
#pragma aux status_refresh "terminal_status_notice_refresh";
extern void __far __cdecl native_scroll(void);
#pragma aux native_scroll "terminal_status_scroll_far";
extern void __far __cdecl native_cursor(unsigned row,unsigned column);
#pragma aux native_cursor "terminal_status_cursor_far";
static word * const TEXT fields[]={
 &ui_flow_suppressed,&csi_row_count,&csi_last_row,&erase_cell_count,
 &screen_first_row,&screen_last_row,&csi_origin_row,&csi_origin_bottom,
 &screen_cursor_row,&screen_cursor_column,&screen_visible_column,
 &screen_previous_row,&screen_previous_column,&screen_video_offset,
 &screen_attribute_offset,&csi_saved_row,&csi_saved_column,&csi_wrap_pending
};
#define FIELD_COUNT (sizeof(fields)/sizeof(fields[0]))
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
static word mode_info(void)
{
 word mode=0,page=0;
 __asm {
 mov ah,0fh
 int 10h
 mov mode,ax
 mov page,bx
 }
 if((mode&255)!=2 && (mode&255)!=3)return 3;
 if((mode>>8)!=80 || (page>>8)!=0)return 3;
 return 0;
}
static word cursor_get(void)
{
 word xy=0;
 __asm {
 mov ah,3
 xor bx,bx
 int 10h
 mov xy,dx
 }
 return xy;
}
static void cursor_restore(word xy)
{
 __asm {
 mov dx,xy
 mov ah,2
 xor bx,bx
 int 10h
 }
}
static word preflight(void)
{
 word i,rows,rate=0,flags=0,dsword=0,ssword=0;
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
 if(dsword!=ssword || (flags&0x600)!=0x200 || terminal_status_toggle_active)return 3;
 if(reset_ready!=1)return 2;
 /* Until the Linux bridge has a matching size contract, online requests refuse. */
 if(connection_state)return 3;
 for(i=0;i<sizeof(owners)/sizeof(owners[0]);++i)if(*owners[i])return 3;
 if(terminal_browser_screen_owned || terminal_editor_screen_owned || reset_bank_busy || terminal_auto_answer_notice_active || terminal_script_overlay_visible)return 3;
 if(notice_idle() || recording_owned())return 3;
 if(csi_terminal_id!=4 && csi_terminal_id!=6)return 3;
 if(ui_flow_suppressed>1 || ui_flow_region_cells!=80)return 3;
#ifdef STATUS_LARGE_ROWS
 if(ui_window_rows!=25 && ui_window_rows!=28 && ui_window_rows!=43 && ui_window_rows!=50)return 3;
#else
 if(ui_window_rows!=25)return 3;
#endif
 if(ui_flow_video_base!=(ui_window_rows-1)*160 || ui_flow_coordinate_base!=(ui_window_rows-1)*256)return 3;
 if(screen_columns!=80 || screen_video_row_bytes!=160 || screen_attribute_row_bytes!=80 || screen_last_column!=79)return 3;
 if(screen_viewport_enabled || screen_viewport_active || screen_viewport_offset || screen_cursor_wrap || screen_attribute_checks || erase_protection_mode)return 3;
 if(text_video_segment!=0xb800 || text_cga_status_port || screen_attributes_base!=(word)screen_attribute_cells || erase_attribute_values_base!=(word)erase_attribute_values)return 3;
 if(erase_shadow_offset!=FP_OFF(erase_shadow_cells) || erase_shadow_segment!=FP_SEG(erase_shadow_cells))return 3;
 rows=ui_window_rows-(ui_flow_suppressed?0:1);
 if(csi_row_count!=rows || csi_last_row!=rows-1 || erase_cell_count!=rows*80)return 3;
 if(screen_first_row>screen_last_row || screen_last_row>=rows || csi_origin_row>csi_origin_bottom || csi_origin_bottom>=rows)return 3;
 if(screen_cursor_row>=rows || screen_cursor_column>=80 || screen_visible_column!=screen_cursor_column)return 3;
 if(screen_previous_row!=screen_cursor_row || screen_previous_column!=screen_cursor_column || csi_saved_row>=rows || csi_saved_column>=80)return 3;
 if(screen_video_offset!=screen_cursor_row*160+screen_cursor_column*2 || screen_attribute_offset!=screen_cursor_row*80+screen_cursor_column)return 3;
 if(terminal_tab_wrap || terminal_parity>4 || terminal_data_bits<5 || terminal_data_bits>8 || terminal_stop_bits<1 || terminal_stop_bits>2)return 3;
 for(i=0;i<9;++i)if(rates[i]==(((unsigned long)terminal_baud_high<<16)|terminal_baud_low))rate=1;
 if(!rate || mode_info())return 3;
 i=*(byte __far *)MK_FP(0x40,0x84);
 if((i?i+1:25)!=ui_window_rows)return 3;
 return 0;
}
unsigned __far __cdecl terminal_status_toggle(void)
{
 word old[FIELD_COUNT],baseline[128],i,j,count,rows,last,oldlast,hw,rc,scroll,attribute,cells;
 byte lines[128];word __far *video=(word __far *)MK_FP(0xb800,0);
 rc=preflight();if(rc)return rc;
 cells=ui_window_rows*80;
 rows=ui_window_rows-(ui_flow_suppressed?1:0);last=rows-1;oldlast=csi_last_row;
 /* Native toggle preserves custom margins. Refuse a contraction that would
  * invalidate one, instead of inventing a new custom scroll region. */
 if(screen_first_row>(screen_last_row==oldlast?last:screen_last_row) ||
    csi_origin_row>(csi_origin_bottom==oldlast?last:csi_origin_bottom))return 3;
 count=(word)(reset_word_addresses_end-reset_word_addresses);if(count>128)return 3;
 for(i=0;i<FIELD_COUNT;++i)old[i]=*fields[i];
 for(i=0;i<count;++i)baseline[i]=reset_words[i];
 rc=defaults_resize(rows);if(rc)return rc;
 terminal_status_toggle_active=1;hw=cursor_get();
 for(i=0;i<128;++i)lines[i]=screen_line_flags[i];
 /* Quiescent exclusive loans: EXEC/live/view frames never overlap. */
 for(i=0;i<cells;++i){program_screen[i]=video[i];redisplay_live[i]=erase_shadow_cells[i];
  redisplay_view[i]=screen_attribute_cells[i]|((word)erase_attribute_values[i]<<8);}
 scroll=rows==ui_window_rows-1 && screen_cursor_row>=rows;
 attribute=(attributes_monochrome?attributes_current:attributes_normal_value)&255;
 if(scroll){
  /* Run the real helper while its old complete geometry is still admitted. */
  native_scroll();
  for(i=screen_first_row;i<screen_last_row;++i){
   for(j=0;j<80;++j){screen_attribute_cells[i*80+j]=screen_attribute_cells[(i+1)*80+j];erase_attribute_values[i*80+j]=erase_attribute_values[(i+1)*80+j];}
   screen_line_flags[i]=screen_line_flags[i+1];
  }
  for(j=0;j<80;++j){screen_attribute_cells[screen_last_row*80+j]=0;erase_attribute_values[screen_last_row*80+j]=(byte)attribute;}
  screen_line_flags[screen_last_row]=0;
 }
 ui_flow_suppressed=rows==ui_window_rows;csi_row_count=rows;csi_last_row=last;erase_cell_count=rows*80;
 if(screen_last_row==oldlast)screen_last_row=last;
 if(csi_origin_bottom==oldlast)csi_origin_bottom=last;
 if(screen_cursor_row>last)screen_cursor_row=last;
 /* Previous row/column are the native cursor offset cache. Retain the old
  * cache until native_cursor applies the signed delta to both offsets. */
 if(csi_saved_row>last)csi_saved_row=last;
 /* Keep a pending deferred wrap unless the real scroll helper cleared it. */
 if(rows==ui_window_rows){
  attribute=ui_flow_attribute&255;
  for(i=cells-80;i<cells;++i){video[i]=(attribute<<8)|32;screen_attribute_cells[i]=0;erase_attribute_values[i]=(byte)attribute;}
  screen_line_flags[ui_window_rows-1]=0;
 }else{
  rc=status_refresh();
  if(rc){
   for(i=0;i<FIELD_COUNT;++i)*fields[i]=old[i];
   for(i=0;i<count;++i)reset_words[i]=baseline[i];
   for(i=0;i<cells;++i){video[i]=program_screen[i];erase_shadow_cells[i]=redisplay_live[i];screen_attribute_cells[i]=(byte)redisplay_view[i];erase_attribute_values[i]=(byte)(redisplay_view[i]>>8);}
   for(i=0;i<128;++i)screen_line_flags[i]=lines[i];
   cursor_restore(hw);terminal_status_toggle_active=0;return 4;
  }
 }
 /* Rebuild the narrow shadow from actual physical cells, not a stale pane. */
 for(i=0;i<cells;++i)erase_shadow_cells[i]=video[i];
 native_cursor(screen_cursor_row,screen_cursor_column);
 terminal_status_toggle_active=0;return 0;
}
