#!/usr/bin/env python3
"""Compile pure renderer policy and source-owned DOS state matrix; no originals."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-renderer-policy'
C=r'''
#include <dos.h>
#include <stdio.h>
#include <string.h>
#include "renderer_policy.h"
#include "capture_file.h"
#include "capture_session.h"
#include "printer_device.h"
#include "download_file.h"
#include "upload_file.h"
#include "batch_download.h"
#define WORD(name) unsigned name;
ASPECT_RENDER_WORDS(WORD)
ASPECT_RENDER_DISPLAY_WORDS(WORD)
#undef WORD
unsigned redisplay_active,command_menu_active;
unsigned char terminal_history_pending;
unsigned terminal_history_pointer[2],ansi_parameters[16];
unsigned char screen_attribute_cells[4096],erase_attribute_values[4096],terminal_keymap[948],screen_line_flags[128];
/* Far planes are separate ASMsegments, exactly like actualparent. */
capture_file_snapshot capture_file_result,snapshot_file_result,monitor_file_result,history_file_result;
printer_device_snapshot printer_device_result;
transfer_file_result transfer_download_result;
upload_file_result upload_source_result;
batch_download_snapshot batch_download_result;
unsigned capture_session_notice,capture_session_failed,capture_session_buffered;
static unsigned long checks,failures;
static void ck(unsigned ok){++checks;if(!ok){++failures;if(failures<8)printf("FAIL %lu\n",checks);}}
static unsigned digest(void){unsigned h=0,i;
#define HASH(name) h=(h*31)^name;
ASPECT_RENDER_WORDS(HASH)
ASPECT_RENDER_DISPLAY_WORDS(HASH)
#undef HASH
for(i=0;i<16;++i)h=(h*31)^ansi_parameters[i];
h^=screen_attribute_cells[0]^screen_attribute_cells[4095]^erase_attribute_values[0]^erase_attribute_values[4095];
h^=terminal_keymap[0]^terminal_keymap[947];
return h;}
void __cdecl fixture_valid(void){
#define ZERO(name) name=0;
ASPECT_RENDER_WORDS(ZERO)
ASPECT_RENDER_DISPLAY_WORDS(ZERO)
#undef ZERO
redisplay_active=command_menu_active=0;terminal_history_pending=0;
memset(&capture_file_result,0,sizeof(capture_file_result));memset(&snapshot_file_result,0,sizeof(snapshot_file_result));
memset(&monitor_file_result,0,sizeof(monitor_file_result));memset(&history_file_result,0,sizeof(history_file_result));
memset(&printer_device_result,0,sizeof(printer_device_result));memset(&transfer_download_result,0,sizeof(transfer_download_result));
memset(&batch_download_result,0,sizeof(batch_download_result));memset(&upload_source_result,0,sizeof(upload_source_result));
capture_session_buffered=capture_session_failed=0;
memset(screen_attribute_cells,0,sizeof(screen_attribute_cells));memset(erase_attribute_values,0,sizeof(erase_attribute_values));
memset(terminal_keymap,0,sizeof(terminal_keymap));memset(screen_line_flags,0,sizeof(screen_line_flags));memset(ansi_parameters,0,sizeof(ansi_parameters));
terminal_program_active=1;terminal_program_kind=4;reset_ready=1;csi_terminal_id=6;connection_state=6;
screen_columns=csi_column_count=screen_attribute_row_bytes=80;screen_video_row_bytes=160;
csi_last_column=79;csi_last_row=screen_last_row=csi_origin_bottom=24;csi_row_count=25;
text_video_segment=0xb800;erase_cell_count=2000;
screen_attributes_base=(unsigned)screen_attribute_cells;erase_attribute_values_base=(unsigned)erase_attribute_values;
erase_shadow_segment=FP_SEG(erase_shadow_cells);erase_shadow_offset=FP_OFF(erase_shadow_cells);
terminal_history_start=terminal_history_pointer[0]=FP_OFF(terminal_history_buffer);terminal_history_end=terminal_history_start+63000;
terminal_history_pointer[1]=FP_SEG(terminal_history_buffer);
}
static void admit(unsigned expected){unsigned h=digest();ck(aspect_render_admit()==expected);ck(digest()==h);}
#define BAD(name,value) fixture_valid();name=value;admit(3)
int main(void){unsigned i,k,setting,priv,prefix,v,h,result;FILE *f;
fixture_valid();admit(0);csi_terminal_id=4;admit(0);
/* Native-compatible edgecursor, scrolled origin, pending history and resolved
 * historicerrors are admitted; no requirement for an empty BBS screen. */
fixture_valid();screen_cursor_row=24;screen_cursor_column=screen_visible_column=79;screen_attribute_offset=1999;screen_video_offset=3998;
screen_first_row=3;csi_origin_row=3;terminal_history_pointer[0]=terminal_history_end-1;
terminal_history_pending=2;terminal_history_wrapped=1;capture_file_result.state=CF_CLOSED;capture_file_result.first_status=CF_WRITE;admit(0);
'''
BAD={
 'terminal_program_active':0,'terminal_program_kind':3,'terminal_program_pending':1,'terminal_parser_active':1,'terminal_ansi_wait_active':1,
 'terminal_monitor_active':1,'terminal_snapshot_active':1,'terminal_screen_print_active':1,'terminal_controller_active':1,
 'terminal_macro_active':1,'terminal_transfer_active':1,'terminal_transfer_pending':1,'redisplay_active':1,'command_menu_active':1,
 'connection_state':2,'reset_ready':0,'csi_terminal_id':3,'terminal_ansi_m_policy':2,
 'terminal_sink_3988_enabled':1,'terminal_sink_398a_enabled':1,'terminal_sink_398c_disabled':1,'terminal_printer_count':1,
 'terminal_printer_closing':1,'csi_printer_ready':1,'capture_session_buffered':1,
 'screen_columns':81,'screen_video_row_bytes':162,'screen_attribute_row_bytes':81,'csi_last_column':80,'csi_column_count':81,
 'csi_last_row':25,'csi_row_count':26,'text_video_segment':0xb000,'text_cga_status_port':0x3da,
 'screen_viewport_active':2,'screen_viewport_enabled':1,'screen_viewport_offset':1,'screen_attribute_checks':2,'terminal_mode_372c':1,
 'render_translation_enabled':1,'erase_protection_mode':2,'erase_cell_count':2001,'screen_cursor_row':25,'screen_cursor_column':80,
 'screen_first_row':25,'screen_last_row':25,'csi_origin_row':25,'csi_origin_bottom':25,'screen_attribute_offset':1,'screen_video_offset':2,
 'screen_attributes_base':0xffff,'erase_attribute_values_base':0xffff,'erase_shadow_segment':0xffff,'erase_shadow_offset':0xffff,
 'terminal_history_start':0xffff,'terminal_history_end':0xffff,'terminal_history_pointer[0]':0xffff,'terminal_history_pointer[1]':0xffff,
 'terminal_history_pending':3,'terminal_history_wrapped':2}
for owner in ['capture_file_result','snapshot_file_result','monitor_file_result','history_file_result','printer_device_result','transfer_download_result','batch_download_result.file','upload_source_result']:
 for field in ['handle_open','handle_uncertain']:BAD[owner+'.'+field]=1
BAD['upload_source_result.discovery_open']=1;BAD['upload_source_result.binary_open']=1
C+='\n'.join(f'BAD({n},{v});' for n,v in BAD.items())+'\n'
C+=r'''
fixture_valid();
for(i=0;i<2000;++i){screen_attribute_cells[i]=0x80;admit(0);screen_attribute_cells[i]=0;}
for(i=0;i<25;++i){screen_line_flags[i]=0x40;admit(3);screen_line_flags[i]=0;}
for(i=0;i<79;++i){memset(terminal_keymap+i*12,'X',12);admit(3);memset(terminal_keymap+i*12,0,12);}
/* Every row count, both panes, both status policies, both supported profiles,
 * and all field mode combinations. Cursor caches describe the last visible
 * cell; pane0 is the right pane, pane1 the left pane. */
for(k=1;k<=25;++k)for(setting=0;setting<2;++setting)for(priv=0;priv<2;++priv)
for(prefix=0;prefix<2;++prefix)for(v=0;v<16;++v){
 fixture_valid();csi_terminal_id=prefix?4:6;
 screen_attribute_row_bytes=csi_column_count=132;csi_last_column=131;
 csi_row_count=k;csi_last_row=screen_last_row=csi_origin_bottom=k-1;
 erase_cell_count=k*132;screen_cursor_row=k-1;
 screen_viewport_enabled=1;screen_viewport_left=52;screen_viewport_right=79;
 screen_viewport_active=setting;screen_viewport_offset=setting?0:52;
 screen_cursor_column=screen_viewport_offset+79;screen_visible_column=79;
 screen_attribute_offset=(k-1)*132+screen_cursor_column;
 screen_video_offset=(k-1)*160+158;
 ui_flow_suppressed=priv;ui_flow_region_cells=80;ui_flow_video_base=3840;ui_flow_coordinate_base=0x1800;
 screen_cursor_wrap=v&1;screen_attribute_checks=(v>>1)&1;
 erase_protection_mode=(v>>2)&1;attributes_color_mode=(v>>3)&1;
 screen_attribute_cells[screen_attribute_offset]=0x81;
 result=(!priv&&k==25)||(screen_cursor_wrap&&erase_protection_mode&&!attributes_color_mode)?3:0;
 admit(result);
 terminal_aspect_active=1;terminal_parser_active=1;
 for(i=0;i<3;++i){
  ansi_command=i==0?'J':i==1?'K':'P';h=digest();
  ck(aspect_render_preflight_command()==(result||(i<2&&screen_cursor_wrap&&screen_attribute_checks)?3:0));
  ck(digest()==h);
 }
}
fixture_valid();ansi_parameter_count=17;ck(aspect_render_preflight_modes(1)==3);ansi_parameter_count=16;
ck(aspect_render_preflight_modes(2)==3);
/* Frozen supported/unsupported classes, every position in a16-mode list.
 * A later unsupported entry must reject before earlier valid7/25 mutation. */
for(setting=0;setting<2;++setting)for(priv=0;priv<2;++priv)for(prefix=0;prefix<2;++prefix){
 ansi_private=priv;csi_report_private_prefix=prefix;
 for(i=0;i<16;++i)ansi_parameters[i]=7;
 for(i=0;i<16;++i)for(v=0;v<33;++v){
  ansi_parameters[i]=v;h=digest();
  result=0;
  if(!prefix && ((!priv&&v==4)||(priv&&v==3)||(v==12&&(setting||!priv))||(!setting&&priv&&v==2)))result=3;
  ck(aspect_render_preflight_modes(setting)==result);ck(digest()==h);ansi_parameters[i]=7;
 }
}
/* CAN/SUB reject before unsafe branches; VT9026 continuation is explicitly
 * accepted, as are ordinary DEC linefeeds and inactive unsupported branches. */
for(k=0;k<64;++k){
 fixture_valid();terminal_aspect_active=1;terminal_parser_active=1;terminal_tab_wrap=k&1;terminal_control_mode_9026=(k>>1)&1;
 terminal_control_mode_1fb0=(k>>2)&1;terminal_newline_mode_9020=(k>>3)&1;terminal_dec_keys=(k>>4)&1;
 csi_terminal_id=(k&32)?4:6;
 for(i=0;i<256;++i){
  result=0;
  if((i==24||i==26) && (terminal_tab_wrap||terminal_control_mode_9026||(!terminal_newline_mode_9020&&terminal_control_mode_1fb0)))result=3;
  if(i==11&&!terminal_control_mode_9026&&!terminal_dec_keys&&terminal_newline_mode_9020)result=3;
  ck(aspect_render_preflight_control(i)==result);
 }
}
fixture_valid();terminal_aspect_active=1;terminal_parser_active=1;terminal_printer_count=1;ck(aspect_render_preflight_control('A')==3);
fixture_valid();terminal_aspect_active=1;terminal_parser_active=1;screen_video_offset=2;ck(aspect_render_preflight_control('A')==3);
printf("POLICY checks=%lu failures=%lu\n",checks,failures);
f=fopen("SUMMARY.TXT","w");if(!f)return 2;fprintf(f,"checks=%lu failures=%lu\n",checks,failures);fclose(f);
return failures?1:0;
}
'''
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'driver.c').write_text(C)
 (OUT/'planes.asm').write_text('BITS 16\nCPU 8086\nSEGMENT SHADOW public align=16 class=FAR_DATA use16\nglobal erase_shadow_cells\nerase_shadow_cells: resb 8192\nSEGMENT HISTORY public align=16 class=FAR_DATA use16\nglobal terminal_history_buffer\nterminal_history_buffer: resb 63000\n')
 subprocess.run(['nasm','-fobj',str(OUT/'planes.asm'),'-o',str(OUT/'planes.obj')],check=True)
 subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-s','-w4','-we','-nt=ASPECT_CODE','-fo='+str(OUT/'policy.obj'),str(ROOT/'src/aspect/renderer_policy.c')],check=True)
 subprocess.run(['wdis','-l='+str(OUT/'policy.dis'),str(OUT/'policy.obj')],check=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-nt=ASPECT_CODE','-k8192','-fm=POLICY.MAP',
  *['-I'+str(ROOT/'src'/p) for p in ['aspect','capture','printer','transfer']],'-fe=POLICY.EXE',str(OUT/'driver.c'),str(OUT/'policy.obj'),str(OUT/'planes.obj')],cwd=OUT,check=True)
 manifest=dict(binary_sha256=sha(OUT/'POLICY.EXE'),sources={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'src/aspect/renderer_policy.c',ROOT/'src/aspect/renderer_policy.h',ROOT/'src/capture/capture_file.h',ROOT/'src/capture/capture_session.h',ROOT/'src/printer/printer_device.h',ROOT/'src/transfer/download_file.h',ROOT/'src/transfer/upload_file.h',ROOT/'src/transfer/batch_download.h',ROOT/'src/transfer/batch_header.h']},original_inputs=[])
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
