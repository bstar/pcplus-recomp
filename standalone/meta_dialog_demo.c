/* Owned DOS/VGA probe only. File commands report failure; no KEY IO backend. */
#include <dos.h>
#include <stdio.h>
#include <string.h>
#include "meta_dialog.h"
extern meta_dialog_state __far external_state;
#define state external_state
static unsigned saved[2000],frame[2000];
static unsigned char table[540];
static char name[64]="DEMO.KEY";
static void cursor(unsigned position,unsigned shape)
{union REGS r;r.h.ah=1;r.x.cx=shape;int86(0x10,&r,&r);r.h.ah=2;r.h.bh=0;r.x.dx=position;int86(0x10,&r,&r);}
int main(void)
{
 union REGS r;unsigned i,row,position,shape,key,status;FILE *f;unsigned __far *video=MK_FP(0xb800,0);
 r.h.ah=0x0f;int86(0x10,&r,&r);
 if(r.h.al!=3 || r.h.ah!=80 || r.h.bh || *(unsigned char __far *)MK_FP(0x40,0x84)!=24)return 2;
 r.h.ah=3;r.h.bh=0;int86(0x10,&r,&r);position=r.x.dx;shape=r.x.cx;
 for(i=0;i<2000;++i)saved[i]=video[i];
 memset(table,0xa5,540);
 for(row=0;row<10;++row){i=row*54;table[i]=3;table[i+1]=0;table[i+2]='R';table[i+3]='O';table[i+4]='W';table[i+5]='0'+row;table[i+6]=0;}
 if(meta_dialog_open(&state,table,name,shape))return 3;
 while(state.phase!=META_DIALOG_CLOSED){
  memcpy(frame,saved,4000);if(meta_dialog_draw(&state,frame,0x1f))break;
  for(i=0;i<2000;++i)if(video[i]!=frame[i])video[i]=frame[i];
  cursor(meta_dialog_cursor(&state),meta_dialog_shape(&state));
  r.h.ah=0;int86(0x16,&r,&r);key=r.h.al?r.h.al:r.x.ax;
  if(r.h.al==0xe0 && r.h.ah)key=r.x.ax&0xff00;
  status=meta_dialog_key(&state,key);
  if(status==META_DIALOG_LOAD || status==META_DIALOG_SAVE)meta_dialog_complete(&state,1,0,0);
  else if(status==META_DIALOG_ARGUMENT)break;
 }
 for(i=0;i<2000;++i)if(video[i]!=saved[i])video[i]=saved[i];cursor(position,shape);
 if(state.phase!=META_DIALOG_CLOSED)return 4;
 _fmemcpy(table,state.records,540);f=fopen("RESULT.BIN","wb");if(!f)return 5;i=fwrite(table,1,540,f);if(fclose(f) || i!=540)return 6;
 return 0;
}
