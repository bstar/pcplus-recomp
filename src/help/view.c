#include "view.h"
#include <dos.h>
extern void __far * __cdecl mouse_platform_allocate(unsigned);
extern unsigned __cdecl mouse_platform_release(void __far *);
extern void __cdecl help_view_cursor(unsigned,unsigned);
static struct {
 unsigned phase,ready,restored,topic,count,cursor,shape;
 const help_page *pages;
 unsigned char __far *block;
} held;
#ifdef HELP_VIEW_DIAGNOSTIC
unsigned help_view_fail_allocate,help_view_fail_release;
void __far __cdecl help_view_damage_guard(void){if(held.block)held.block[0]^=1;}
#endif
static unsigned context(void);
#pragma aux context = "mov ax,ds" "mov dx,ss" "cmp ax,dx" "jne bad" "pushf" "pop ax" "and ax,0x200" "jmp done" "bad: xor ax,ax" "done:" value [ax] modify [dx];
static unsigned extent(const void *p,unsigned bytes)
{return p&&(unsigned long)(unsigned)p+bytes<=65536UL;}
static unsigned geometry(void)
{
 return *(unsigned char __far *)MK_FP(0x40,0x49)==3&&
  *(unsigned __far *)MK_FP(0x40,0x4a)==80&&
  *(unsigned char __far *)MK_FP(0x40,0x62)==0&&
  *(unsigned char __far *)MK_FP(0x40,0x84)==24&&
  *(unsigned __far *)MK_FP(0x40,0x63)==0x3d4;
}
static unsigned text_valid(const char *text)
{
 unsigned i;
 if(!text)return 1;
 for(i=0;i<=74;++i){if(!extent(text+i,1))return 0;if(!text[i])return 1;}
 return 0;
}
static unsigned guards(void)
{
 unsigned i;if(!held.block)return 0;
 for(i=0;i<16;++i)if(held.block[i]!=0xa5||held.block[4016+i]!=0x5a)return 0;
 return 1;
}
static void line(unsigned row,const char *text,unsigned attribute)
{
 unsigned i;unsigned __far *screen=MK_FP(0xb800,row*160+6);
 if(text)for(i=0;i<74&&text[i];++i)screen[i]=(attribute<<8)|(unsigned char)text[i];
}
static void paint(void)
{
 unsigned i;unsigned __far *screen=MK_FP(0xb800,0);
 for(i=0;i<2000;++i)screen[i]=0x1720;
 for(i=0;i<80;++i){screen[i]=0x1fcd;screen[1920+i]=0x1fcd;}
 line(1,"PCPlus // CONTEXT HELP",0x1f);
 line(3,held.pages[held.topic].title,0x1e);
 for(i=0;i<17;++i)line(5+i,held.pages[held.topic].lines[i],0x17);
 line(23,"Left/Right: topic   Home/End: first/last   Esc or Enter: return",0x1f);
 help_view_cursor(0,0x2000);
}
unsigned __far __cdecl help_view_active(void){return held.phase;}
unsigned __far __cdecl help_view_topic(void){return held.topic;}
unsigned __far __cdecl help_view_open(const help_page *pages,unsigned count,unsigned topic)
{
 unsigned i,j;unsigned char __far *screen=MK_FP(0xb800,0);
 if(!context())return HELP_VIEW_STATE;
 if(held.phase)return HELP_VIEW_STATE;
 if(!count||count>255||topic>=count||!extent(pages,count*sizeof(*pages)))return HELP_VIEW_ARGUMENT;
 for(i=0;i<count;++i){
  if(!pages[i].title||!text_valid(pages[i].title))return HELP_VIEW_ARGUMENT;
  for(j=0;j<17;++j)if(!text_valid(pages[i].lines[j]))return HELP_VIEW_ARGUMENT;
 }
 if(!geometry())return HELP_VIEW_STATE;
#ifdef HELP_VIEW_DIAGNOSTIC
 if(help_view_fail_allocate)return HELP_VIEW_MEMORY;
#endif
 held.block=mouse_platform_allocate(4032);
 if(!held.block)return HELP_VIEW_MEMORY;
 held.phase=1;held.ready=held.restored=0;
 for(i=0;i<16;++i){held.block[i]=0xa5;held.block[4016+i]=0x5a;}
 for(i=0;i<4000;++i)held.block[16+i]=screen[i];
 held.cursor=*(unsigned __far *)MK_FP(0x40,0x50);
 held.shape=*(unsigned __far *)MK_FP(0x40,0x60);
 held.ready=1;held.pages=pages;held.count=count;held.topic=topic;
 paint();held.phase=2;return HELP_VIEW_OK;
}
static unsigned close_view(unsigned discard)
{
 unsigned i,status;unsigned char __far *screen=MK_FP(0xb800,0);
 if(!context())return HELP_VIEW_STATE;
 if(!held.phase)return HELP_VIEW_OK;
 if(!guards()){held.phase=3;return HELP_VIEW_GUARD;}
 if(discard)held.restored=1;
 if(!held.restored&&held.ready){
  if(!geometry()){held.phase=3;return HELP_VIEW_STATE;}
  for(i=0;i<4000;++i)screen[i]=held.block[16+i];
  help_view_cursor(held.cursor,held.shape);held.restored=1;
 }
#ifdef HELP_VIEW_DIAGNOSTIC
 if(help_view_fail_release){held.phase=3;return HELP_VIEW_STATE;}
#endif
 status=mouse_platform_release(held.block);
 if(status){held.phase=3;return HELP_VIEW_STATE;}
 held.block=0;held.pages=0;held.count=held.ready=held.restored=held.phase=0;
 return HELP_VIEW_OK;
}
unsigned __far __cdecl help_view_close(void){return close_view(0);}
unsigned __far __cdecl help_view_discard(void){return close_view(1);}
unsigned __far __cdecl help_view_key(unsigned key)
{
 unsigned topic;
 if(!context()||held.phase!=2||!geometry()||!guards())return HELP_VIEW_STATE;
 topic=held.topic;
 if(key==27||key==13||key==0x2c00)return help_view_close();
 if(key==0x4700)topic=0;
 else if(key==0x4f00)topic=held.count-1;
 else if(key==0x4b00||key==0x4800||key==0x4900){if(topic)--topic;}
 else if(key==0x4d00||key==0x5000||key==0x5100||key=='t'||key=='T'){
  if(topic+1<held.count)++topic;else topic=0;
 }
 if(topic!=held.topic){held.topic=topic;paint();}
 return HELP_VIEW_OK;
}
