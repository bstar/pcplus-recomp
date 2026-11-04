/* Startup diagnostics before UART enable/parsing. Raw mode keeps canonical24;
 * geometry mode runs the offline BIOS/canonical/RIS owner and captures pixels. */
#include <dos.h>
#include "native_display_rows.h"
typedef unsigned short word;
#ifdef TERMINAL_ROW_GEOMETRY_PROBE
#include "../src/terminal/row_geometry.h"
#define RECORD_WORDS 21
#define RECORD_VERSION 2
extern word attributes_current,ui_flow_video_base,ui_flow_coordinate_base;
extern word __far erase_shadow_cells[];
#pragma aux attributes_current "attributes_current";
#pragma aux ui_flow_video_base "ui_flow_video_base";
#pragma aux ui_flow_coordinate_base "ui_flow_coordinate_base";
#pragma aux erase_shadow_cells "erase_shadow_cells";
#else
#define RECORD_WORDS 18
#define RECORD_VERSION 1
#endif
#define TEXT __based(__segname("_CODE"))
extern word csi_row_count,csi_last_row,ui_flow_suppressed;
#pragma aux csi_row_count "csi_row_count";
#pragma aux csi_last_row "csi_last_row";
#pragma aux ui_flow_suppressed "ui_flow_suppressed";
extern word __far __cdecl rows_probe_write(const char *,const void *,word);
#ifdef TERMINAL_ROW_GEOMETRY_PROBE
extern word __far __cdecl rows_probe_far(const char *,const void __far *,word);
static word images(word phase,word rows)
{
 char name[8]={'G','V','0','.', 'B','I','N',0};
 name[2]+=(char)phase;
 if(rows_probe_far(name,MK_FP(0xb800,0),rows*160))return 1;
 name[1]='W';return rows_probe_far(name,erase_shadow_cells,8192);
}
#endif
#ifdef TERMINAL_DISPLAY_PREFERENCES
#include "../src/config/display_preferences.h"
/* Raw selector diagnostics deliberately leave canonical geometry24 while the
 * UART/foreground mouse owner is not enabled; final selector restores BIOS25. */
static word selector_images(void)
{
 static const word TEXT requests[8][3]={{1,50,0},{2,43,0},{0,50,3},{3,50,3},
  {4,50,3},{3,50,0},{4,50,0},{3,50,0x12}};
 char name[9]={'D','S','E','L','.','B','I','N',0};word records[3+8*16],i,j;
 native_display_selection result;
 records[0]=0x4453;records[1]=1;records[2]=8;
 for(i=0;i<8;++i){
  for(j=0;j<3;++j)records[3+i*16+j]=requests[i][j];
  records[3+i*16+3]=native_display_select(requests[i][0],requests[i][1],requests[i][2],&result);
  for(j=0;j<12;++j)records[3+i*16+4+j]=((word *)&result)[j];
 }
 return rows_probe_write(name,records,sizeof(records));
}
#include "../src/terminal/status_transition.h"
static word transaction_image(word *r,word phase,word selector,word rows,word mode,word status)
{
 native_display_rows_info info;char name[8]={'S','V','0','.','B','I','N',0};
 if(native_display_rows_probe(&info))return 1;
 r[0]=selector;r[1]=rows;r[2]=mode;r[3]=status;r[4]=info.rows;
 r[5]=csi_row_count;r[6]=ui_flow_suppressed;r[7]=terminal_display_selector;
 r[8]=terminal_display_selector_ready;r[9]=terminal_display_fallback;r[10]=terminal_display_physical_result;
 name[2]+=(char)phase;
 if(rows_probe_far(name,MK_FP(0xb800,0),info.rows*160))return 1;
 name[1]='W';return rows_probe_far(name,erase_shadow_cells,8192);
}
static word selector_transaction_images(void)
{
 static const word TEXT requests[8][3]={{1,50,0},{2,43,0},{0,50,3},{3,50,3},
  {4,50,3},{3,50,0},{4,50,0},{3,50,0x12}};
 char name[9]={'T','S','E','L','.','B','I','N',0};word records[3+9*11],i,status;
 records[0]=0x5453;records[1]=1;records[2]=9;
 for(i=0;i<8;++i){
  status=terminal_display_select(requests[i][0],requests[i][1],requests[i][2]);
  if(transaction_image(records+3+i*11,i,requests[i][0],requests[i][1],requests[i][2],status))return 1;
 }
 status=terminal_display_apply_saved();
 if(transaction_image(records+3+8*11,8,terminal_display_preferences.selector,
   terminal_display_preferences.rows,terminal_display_preferences.video_mode,status))return 1;
 /* Synthetic saved preferences hide status. Retire that state through the real
  * owner so the existing canonical-row diagnostic still starts visible24. */
 if(terminal_status_toggle())return 1;
 return rows_probe_write(name,records,sizeof(records));
}
static word preferences_image(void)
{
 char name[10]={'D','P','R','E','F','.','B','I','N',0};word values[5];
 values[0]=terminal_display_preferences_ready;
 values[1]=terminal_display_preferences.status_hidden;values[2]=terminal_display_preferences.selector;
 values[3]=terminal_display_preferences.rows;values[4]=terminal_display_preferences.video_mode;
 return rows_probe_write(name,values,sizeof(values));
}
#endif
#if defined(TERMINAL_LARGE_VIEW_FRAMES) && defined(TERMINAL_ROW_GEOMETRY_PROBE)
extern word __far __cdecl rows_view_key(word key);
extern word redisplay_active;
/* Diagnostic key adapter enters the genuine far owner. It supplies a normalized
 * key explicitly, not a BIOS keystroke or a remote terminal response. */
static word view_frame_images(void)
{
 static const word TEXT heights[]={25,28,43,50};
 static const word TEXT keys[]={0x2c00,0x8400,0x8300,0x1400};
 word records[3+16*7],r,v,i,n=3,opened,open_active,closed,restored;
 word __far *video=(word __far *)MK_FP(0xb800,0);
 char name[9]={'L','V','0','0','.', 'B','I','N',0};
 char leaf[12]={'V','F','R','A','M','E','S','.', 'B','I','N',0};
 records[0]=0x5646;records[1]=1;records[2]=16;
 for(r=0;r<4;++r){
  if(terminal_row_geometry_set(heights[r]))return 1;
  for(v=0;v<4;++v){
   for(i=0;i<4000;++i)video[i]=i<heights[r]*80?0x0700+65+i%26:0x5a5a;
   opened=rows_view_key(keys[v]);open_active=redisplay_active;
   name[1]='V';name[2]='0'+r;name[3]='0'+v;
   if(rows_probe_far(name,video,8000))return 1;
   closed=rows_view_key(27);restored=1;
   for(i=0;i<4000;++i)if(video[i]!=(i<heights[r]*80?0x0700+65+i%26:0x5a5a))restored=0;
   records[n++]=heights[r];records[n++]=keys[v];records[n++]=opened;
   records[n++]=open_active;records[n++]=closed;records[n++]=redisplay_active;records[n++]=restored;
   name[1]='A';if(rows_probe_far(name,video,8000))return 1;
   if(opened!=1 || open_active!=1 || closed!=1 || redisplay_active || !restored)return 1;
  }
 }
 if(terminal_row_geometry_set(25))return 1;
 return rows_probe_write(leaf,records,sizeof(records));
}
#endif
#if defined(TERMINAL_PROGRAM_DISPLAY) && defined(TERMINAL_ROW_GEOMETRY_PROBE)
#include "../src/terminal/program_display.h"
extern word __far __cdecl rows_program_run(const char *command);
extern word terminal_quit;
#pragma aux terminal_quit "terminal_quit";
extern word terminal_program_result[];
#pragma aux terminal_program_result "terminal_program_result";
static word program_frame_images(void)
{
 static const word TEXT heights[]={25,28,43,50};
 word records[3+4*8],r,i,n=3,status;native_display_rows_info actual;
 word __far *video=(word __far *)MK_FP(0xb800,0);
 char name[8]={'P','B','0','.', 'B','I','N',0};
 char leaf[10]={'P','R','O','W','S','.', 'B','I','N',0};
 char command[11]={'P','C','H','I','L','D','.', 'C','O','M',0};
 records[0]=0x5052;records[1]=2;records[2]=4;
 for(r=0;r<4;++r){
  if(terminal_row_geometry_set(heights[r]))return 1;
  for(i=0;i<4000;++i)video[i]=0x0700+65+i%26;
  name[1]='B';name[2]='0'+r;if(rows_probe_far(name,video,8000))return 1;
  status=rows_program_run(command);
  if(native_display_rows_probe(&actual))return 1;
  records[n++]=heights[r];records[n++]=status;records[n++]=program_display_ready;
  records[n++]=terminal_quit;records[n++]=actual.mode;records[n++]=actual.rows;records[n++]=csi_row_count;records[n++]=terminal_program_result[2];
  name[1]='A';if(rows_probe_far(name,video,8000))return 1;
  if(status!=4 || program_display_ready || terminal_quit || actual.mode!=3 || actual.rows!=heights[r] || terminal_program_result[2])return 1;
  for(i=0;i<heights[r]*80;++i)if(video[i]!=0x0700+65+i%26)return 1;
 }
 if(terminal_row_geometry_set(25))return 1;
 return rows_probe_write(leaf,records,sizeof(records));
}
#endif
#ifdef TERMINAL_PROFILE_DISPLAY_PROBE
extern word __far __cdecl rows_setup_run(void);
extern word terminal_setup_profile_status,terminal_setup_profile_ready,csi_terminal_id,ui_window_rows;
#pragma aux terminal_setup_profile_status "terminal_setup_profile_status";
#pragma aux terminal_setup_profile_ready "terminal_setup_profile_ready";
#pragma aux csi_terminal_id "csi_terminal_id";
#pragma aux ui_window_rows "ui_window_rows";
extern word __far terminal_keymap[];
#pragma aux terminal_keymap "terminal_keymap";
static word profile_keys(word target)
{
 static const word TEXT keys[]={0x5100,0x4700,0x5300,0,0x4400,0x011b,0x1579,0x1c0d};
 word i,pending=0,key,status=0;
 for(i=0;i<16;++i){
  __asm { mov ah,1
 push bp
 int 16h
 pop bp
 mov pending,0
 jz empty
 mov pending,1
 empty: }
  if(!pending)break;
  __asm { mov ah,0
 push bp
 int 16h
 pop bp }
 }
 for(i=0;i<8;++i){
  key=i==3?(target==4?0x0534:0x0736):keys[i];
  __asm { mov cx,key
 mov ax,0500h
 push bp
 int 16h
 pop bp
 mov status,ax }
  if(status&255)return 1;
 }
 return 0;
}
static word profile_frame_images(void)
{
 static const word TEXT heights[]={25,28,43,50};
 native_display_rows_info actual;word records[3+8*16],r,t,target,status,n=3;
 char name[9]={'P','V','0','0','.', 'B','I','N',0};
 char leaf[13]={'P','R','O','F','I','L','E','S','.', 'B','I','N',0};
 records[0]=0x5054;records[1]=1;records[2]=8;
 for(r=0;r<4;++r){
  if(terminal_row_geometry_set(heights[r]))return 1;
  for(t=0;t<2;++t){
   target=t?6:4;if(profile_keys(target))return 1;
   status=rows_setup_run();if(native_display_rows_probe(&actual))return 1;
   records[n++]=heights[r];records[n++]=target;records[n++]=status;
   records[n++]=terminal_setup_profile_status;records[n++]=terminal_setup_profile_ready;
   records[n++]=csi_terminal_id;records[n++]=csi_row_count;records[n++]=csi_last_row;
   records[n++]=ui_window_rows;records[n++]=ui_flow_suppressed;records[n++]=terminal_quit;
   records[n++]=terminal_program_result[2];records[n++]=actual.mode;records[n++]=actual.rows;
   records[n++]=program_display_ready;records[n++]=attributes_current;
   name[1]='V';name[2]='0'+r;name[3]='0'+t;
   if(rows_probe_far(name,MK_FP(0xb800,0),heights[r]*160))return 1;
   name[1]='K';if(rows_probe_far(name,terminal_keymap,948))return 1;
   if(status!=4 || terminal_setup_profile_status!=1 || terminal_setup_profile_ready ||
    csi_terminal_id!=target || csi_row_count!=heights[r]-1 || csi_last_row!=heights[r]-2 ||
    ui_window_rows!=heights[r] || ui_flow_suppressed || terminal_quit || terminal_program_result[2] ||
    actual.mode!=3 || actual.rows!=heights[r] || program_display_ready)return 1;
  }
 }
 if(terminal_row_geometry_set(25))return 1;
 return rows_probe_write(leaf,records,sizeof(records));
}
#endif
#ifdef TERMINAL_XLT_DISPLAY_PROBE
extern word __far __cdecl rows_xlt_run(void);
extern word terminal_translation_edit_status,terminal_translation_reload_status;
extern word terminal_translation_mode,terminal_translation_enabled,uart_rx_mask,ui_window_rows;
extern unsigned char terminal_translation_table[];
#pragma aux terminal_translation_edit_status "terminal_translation_edit_status";
#pragma aux terminal_translation_reload_status "terminal_translation_reload_status";
#pragma aux terminal_translation_mode "terminal_translation_mode";
#pragma aux terminal_translation_enabled "terminal_translation_enabled";
#pragma aux uart_rx_mask "uart_rx_mask";
#pragma aux ui_window_rows "ui_window_rows";
#pragma aux terminal_translation_table "terminal_translation_table";
static word xlt_keys(word target)
{
 static const word TEXT keys[]={0x1c0d,0x4700,0x5300,0x5300,0,0x0938,0x1c0d,0x3b00,0x011b,0x1579};
 word i,pending=0,key,status=0;
 for(i=0;i<16;++i){
  __asm { mov ah,1
 push bp
 int 16h
 pop bp
 mov pending,0
 jz empty
 mov pending,1
 empty: }
  if(!pending)break;
  __asm { mov ah,0
 push bp
 int 16h
 pop bp }
 }
 for(i=0;i<10;++i){
  if(i==5 && !target)continue;
  key=i==4?(target?0x0938:0x0b30):keys[i];
  __asm { mov cx,key
 mov ax,0500h
 push bp
 int 16h
 pop bp
 mov status,ax }
  if(status&255)return 1;
 }
 return 0;
}
static word xlt_frame_images(void)
{
 static const word TEXT heights[]={25,28,43,50};
 native_display_rows_info actual;word records[3+8*16],r,t,target,status,n=3;
 char name[9]={'X','B','0','0','.', 'B','I','N',0};
 char leaf[13]={'X','L','T','R','O','W','S','.', 'B','I','N',0};
 records[0]=0x5854;records[1]=1;records[2]=8;
 for(r=0;r<4;++r){
  if(terminal_row_geometry_set(heights[r]))return 1;
  for(t=0;t<2;++t){
   target=t?0:88;
   name[1]='B';name[2]='0'+r;name[3]='0'+t;
   if(rows_probe_far(name,MK_FP(0xb800,0),heights[r]*160))return 1;
   if(xlt_keys(target))return 1;
   status=rows_xlt_run();if(native_display_rows_probe(&actual))return 1;
   records[n++]=heights[r];records[n++]=target;records[n++]=status;
   records[n++]=terminal_translation_edit_status;records[n++]=terminal_translation_reload_status;
   records[n++]=actual.mode;records[n++]=actual.rows;records[n++]=csi_row_count;
   records[n++]=ui_window_rows;records[n++]=ui_flow_suppressed;records[n++]=terminal_quit;
   records[n++]=program_display_ready;records[n++]=terminal_program_result[2];
   records[n++]=terminal_translation_table[0];records[n++]=terminal_translation_enabled;records[n++]=uart_rx_mask;
   name[1]='V';if(rows_probe_far(name,MK_FP(0xb800,0),heights[r]*160))return 1;
   name[1]='K';if(rows_probe_write(name,terminal_translation_table,256))return 1;
   if(status!=4 || terminal_translation_edit_status!=2 || terminal_translation_reload_status!=2 ||
    actual.mode!=3 || actual.rows!=heights[r] || csi_row_count!=heights[r]-1 || ui_window_rows!=heights[r] ||
    ui_flow_suppressed || terminal_quit || program_display_ready || terminal_program_result[2] ||
    terminal_translation_table[0]!=target || terminal_translation_mode!=1 || terminal_translation_enabled!=1 || uart_rx_mask!=255)return 1;
  }
 }
 if(terminal_row_geometry_set(25))return 1;
 return rows_probe_write(leaf,records,sizeof(records));
}
#endif
#ifdef TERMINAL_ASPECT_ADMISSION_PROBE
extern word __far __cdecl rows_aspect_admission(word operation);
static word aspect_admission_images(void)
{
 static const word TEXT heights[]={25,28,43,50};
 char leaf[13]={'A','R','R','O','W','S','.', 'B','I','N',0};
 native_display_rows_info actual;word records[3+4*7],r,n=3,a,b,c;
 records[0]=0x4152;records[1]=1;records[2]=4;
 for(r=0;r<4;++r){
  if(terminal_row_geometry_set(heights[r]) || native_display_rows_probe(&actual))return 1;
  a=rows_aspect_admission(0);b=rows_aspect_admission(1);c=rows_aspect_admission(2);
  records[n++]=heights[r];records[n++]=actual.rows;records[n++]=csi_row_count;
  records[n++]=ui_flow_suppressed;records[n++]=a;records[n++]=b;records[n++]=c;
  if(actual.rows!=heights[r] || csi_row_count!=heights[r]-1 || ui_flow_suppressed || a || b || c)return 1;
 }
 if(terminal_row_geometry_set(25))return 1;
 return rows_probe_write(leaf,records,sizeof(records));
}
#endif
static void capture(word *r,word request,word status,native_display_rows_info *p)
{
 word axword=0,bxword=0;
 __asm {
 mov ah,0fh
 int 10h
 mov axword,ax
 mov bxword,bx
 }
 r[0]=request;r[1]=status;r[2]=p->mode;r[3]=p->columns;r[4]=p->rows;
 r[5]=p->segment;r[6]=p->stride;r[7]=p->cells;r[8]=p->font_capable;
 r[9]=p->scanline_capable;r[10]=p->extended_mode;r[11]=p->fallback;
 r[12]=axword;r[13]=bxword;r[14]=*(unsigned char __far *)MK_FP(0x40,0x84);
 r[15]=csi_row_count;r[16]=csi_last_row;r[17]=ui_flow_suppressed;
#ifdef TERMINAL_ROW_GEOMETRY_PROBE
 r[18]=attributes_current;r[19]=ui_flow_video_base;r[20]=ui_flow_coordinate_base;
#endif
}
unsigned __far __cdecl terminal_display_rows_probe(void)
{
#ifdef TERMINAL_ROW_GEOMETRY_PROBE
 static const char TEXT leaf[]="GROWS.BIN";
#else
 static const char TEXT leaf[]="DROWS.BIN";
#endif
 static const word TEXT requests[]={25,28,43,50,25};
 native_display_rows_info info;word records[3+6*RECORD_WORDS],i,status,failed=0;char name[10];
 records[0]=0x4452;records[1]=RECORD_VERSION;records[2]=6;
#ifdef TERMINAL_DISPLAY_PREFERENCES
 if(preferences_image())return 26;
 if(selector_images())return 27;
 if(selector_transaction_images())return 28;
#endif
#if defined(TERMINAL_LARGE_VIEW_FRAMES) && defined(TERMINAL_ROW_GEOMETRY_PROBE)
 if(view_frame_images())return 29;
#endif
#if defined(TERMINAL_PROGRAM_DISPLAY) && defined(TERMINAL_ROW_GEOMETRY_PROBE)
 if(program_frame_images())return 30;
#endif
#ifdef TERMINAL_PROFILE_DISPLAY_PROBE
 if(profile_frame_images())return 31;
#endif
#ifdef TERMINAL_XLT_DISPLAY_PROBE
 if(xlt_frame_images())return 32;
#endif
#ifdef TERMINAL_ASPECT_ADMISSION_PROBE
 if(aspect_admission_images())return 33;
#endif
 status=native_display_rows_probe(&info);if(status)return 20;
 capture(records+3,0,status,&info);
#ifdef TERMINAL_ROW_GEOMETRY_PROBE
 if(images(0,info.rows))return 24;
#endif
 for(i=0;i<5;++i){
#ifdef TERMINAL_ROW_GEOMETRY_PROBE
  status=terminal_row_geometry_set(requests[i]);
  if(native_display_rows_probe(&info))return 25;
#else
  status=native_display_rows_set(requests[i],&info);
#endif
  capture(records+3+(i+1)*RECORD_WORDS,requests[i],status,&info);
#ifdef TERMINAL_ROW_GEOMETRY_PROBE
  if(images(i+1,info.rows))return 24;
#endif
  if(status && status!=DISPLAY_ROWS_UNSUPPORTED)failed=21;
 }
 if(info.rows!=25 || status)failed=22;
 for(i=0;i<sizeof(leaf);++i)name[i]=leaf[i];
 if(rows_probe_write(name,records,sizeof(records)))return 23;
 return failed;
}
