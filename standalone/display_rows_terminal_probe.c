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
