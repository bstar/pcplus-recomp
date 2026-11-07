/* Owned VGA/keyboard/file probe; not a PCPlus launcher or terminal. */
#include <dos.h>
#include <bios.h>
#include <stdio.h>
#include <string.h>
#include "meta_editor.h"
extern meta_editor __far editor;
extern unsigned char __far live[540];
static unsigned saved[2000],frame[2000];
static unsigned char table[540];
static char name[64]="TEST.KEY",path[64]="C:\\LAB\\TEST.KEY",out_name[64],out_path[64];
static void cursor(unsigned position,unsigned shape)
{union REGS r;r.h.ah=1;r.x.cx=shape;int86(0x10,&r,&r);r.h.ah=2;r.h.bh=0;r.x.dx=position==0xffff?0:position;int86(0x10,&r,&r);}
int main(void)
{
 union REGS r;unsigned i,row,position,shape,key,status,phase,dirty=1;unsigned long started;volatile unsigned long __far *ticks=MK_FP(0x40,0x6c);FILE *f;unsigned __far *video=MK_FP(0xb800,0);
 r.h.ah=0x0f;int86(0x10,&r,&r);if(r.h.al!=3 || r.h.ah!=80 || r.h.bh || *(unsigned char __far *)MK_FP(0x40,0x84)!=24)return 2;
 r.h.ah=3;r.h.bh=0;int86(0x10,&r,&r);position=r.x.dx;shape=r.x.cx;for(i=0;i<2000;++i)saved[i]=video[i];
 memset(table,0xa5,540);for(row=0;row<10;++row){i=row*54;table[i]=3;table[i+1]=0;table[i+2]='R';table[i+3]='O';table[i+4]='W';table[i+5]='0'+row;table[i+6]=0;}_fmemcpy(live,table,540);
 if(meta_editor_open(&editor,0,live,name,path,shape))return 3;
 started=*ticks;
 while(editor.phase!=META_EDITOR_CLOSED){
  if(*ticks-started>270UL){f=fopen("C:\\DEBUG.BIN","wb");if(f){_fmemcpy(table,&editor,16);fwrite(table,1,16,f);fclose(f);}for(i=0;i<2000;++i)video[i]=saved[i];cursor(position,shape);return 10;}
  phase=editor.phase;status=meta_editor_step(&editor,1);if(status==META_EDITOR_RECOVERY || status==META_EDITOR_ARGUMENT)return 4;if(phase!=editor.phase)dirty=1;
  if(dirty){memcpy(frame,saved,4000);if(meta_editor_draw(&editor,frame,0x1f))return 5;for(i=0;i<2000;++i)if(video[i]!=frame[i])video[i]=frame[i];cursor(meta_editor_cursor(&editor),meta_editor_shape(&editor));dirty=0;}
  if(_bios_keybrd(1)){key=_bios_keybrd(0);if(key&255){if((key&255)==0xe0 && (key>>8))key&=0xff00;else key&=255;}status=meta_editor_key(&editor,key);if(status==META_EDITOR_RECOVERY || status==META_EDITOR_ARGUMENT)return 6;dirty=1;}
 }
 if(meta_editor_proposal(&editor,table,out_name,out_path))return 7;
 for(i=0;i<2000;++i)if(video[i]!=saved[i])video[i]=saved[i];cursor(position,shape);
 f=fopen("C:\\RESULT.BIN","wb");if(!f)return 8;i=fwrite(table,1,540,f);i+=fwrite(out_name,1,64,f);i+=fwrite(out_path,1,64,f);if(fclose(f) || i!=668)return 9;return 0;
}
