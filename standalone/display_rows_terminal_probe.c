/* Diagnostic only: raw BIOS service at startup, before UART enable/parsing.
 * Canonical terminal geometry deliberately stays24; restore BIOS25 before IO. */
#include <dos.h>
#include "native_display_rows.h"
typedef unsigned short word;
#define TEXT __based(__segname("_CODE"))
extern word csi_row_count,csi_last_row,ui_flow_suppressed;
#pragma aux csi_row_count "csi_row_count";
#pragma aux csi_last_row "csi_last_row";
#pragma aux ui_flow_suppressed "ui_flow_suppressed";
extern word __far __cdecl rows_probe_write(const char *,const void *,word);
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
}
unsigned __far __cdecl terminal_display_rows_probe(void)
{
 static const char TEXT leaf[]="DROWS.BIN";
 static const word TEXT requests[]={25,28,43,50,25};
 native_display_rows_info info;word records[3+6*18],i,status,failed=0;char name[10];
 records[0]=0x4452;records[1]=1;records[2]=6;
 status=native_display_rows_probe(&info);if(status)return 20;
 capture(records+3,0,status,&info);
 for(i=0;i<5;++i){
  status=native_display_rows_set(requests[i],&info);
  capture(records+3+(i+1)*18,requests[i],status,&info);
  if(status && status!=DISPLAY_ROWS_UNSUPPORTED)failed=21;
 }
 if(info.rows!=25 || status)failed=22;
 for(i=0;i<sizeof(leaf);++i)name[i]=leaf[i];
 if(rows_probe_write(name,records,sizeof(records)))return 23;
 return failed;
}
