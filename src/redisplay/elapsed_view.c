/* Serviced integration of native DB04's display contract; not its blocking UI.
 * Native rectangle/field positions are recovered facts. Serial/parser/frame
 * ownership remains with redisplay_event; original220 timer bytes stay live. */
#include <dos.h>
#include "elapsed_view.h"
typedef unsigned short word;
extern word terminal_call_timer_running,elapsed_hours,elapsed_minutes,elapsed_secs;
extern char elapsed_duration[9];
#pragma aux terminal_call_timer_running "terminal_call_timer_running";
#pragma aux elapsed_hours "elapsed_hours";
#pragma aux elapsed_minutes "elapsed_minutes";
#pragma aux elapsed_secs "elapsed_secs";
#pragma aux elapsed_duration "elapsed_duration";
extern void __far __cdecl call_timer_refresh(void);
#pragma aux call_timer_refresh "terminal_call_timer_refresh_far";
unsigned terminal_elapsed_view_active=0;
static word online,tick,wall_hm,wall_sh,date_y,date_md;
#define TEXT __based(__segname("_CODE"))
static const char TEXT this_call[]="ELAPSED TIME THIS CALL:";
static const char TEXT last_call[]="ELAPSED TIME LAST CALL:";
static void wall(void)
{
 word hm=0,sh=0;
 __asm {
 mov ah,2ch
 int 21h
 mov hm,cx
 mov sh,dx
 }
 wall_hm=hm;wall_sh=sh;
 call_timer_refresh();
}
void __cdecl elapsed_view_open(void)
{
 word year=0,md=0;
 online=terminal_call_timer_running!=0;
 __asm {
 mov ah,2ah
 int 21h
 mov year,cx
 mov md,dx
 }
 date_y=year;date_md=md;
 tick=*(volatile word __far *)MK_FP(0x40,0x6c);
 terminal_elapsed_view_active=1;
 wall();
}
unsigned __cdecl elapsed_view_poll(void)
{
 word now=*(volatile word __far *)MK_FP(0x40,0x6c);
 if((word)(now-tick)<18)return 0;
 tick=now;wall();return 1;
}
static void pair(word __far *frame,word at,word value)
{frame[at]=0x1f30+value/10;frame[at+1]=0x1f30+value%10;}
static void caption(word __far *frame,const char __far *label)
{word i;for(i=0;label[i];++i)frame[12*80+27+i]=0x1f00|(unsigned char)label[i];}
void __cdecl elapsed_view_draw(word __far *frame)
{
 word row,col,i,at;
 for(row=9;row<=15;++row)frame[row*80+61]=(frame[row*80+61]&255)|0x0800;
 for(col=26;col<=61;++col)frame[15*80+col]=(frame[15*80+col]&255)|0x0800;
 for(row=8;row<=14;++row)for(col=25;col<=60;++col)frame[row*80+col]=0x1f20;
 for(col=26;col<60;++col)frame[8*80+col]=frame[14*80+col]=0x1fcd;
 for(row=9;row<14;++row)frame[row*80+25]=frame[row*80+60]=0x1fba;
 frame[8*80+25]=0x1fc9;frame[8*80+60]=0x1fbb;
 frame[14*80+25]=0x1fc8;frame[14*80+60]=0x1fbc;
 at=10*80+30;pair(frame,at,wall_hm>>8);frame[at+2]=0x1f3a;
 pair(frame,at+3,wall_hm&255);frame[at+5]=0x1f3a;pair(frame,at+6,wall_sh>>8);
 at=10*80+47;pair(frame,at,date_md>>8);frame[at+2]=0x1f2f;
 pair(frame,at+3,date_md&255);frame[at+5]=0x1f2f;pair(frame,at+6,date_y%100);
 if(online)caption(frame,this_call);else caption(frame,last_call);
 for(i=0;i<8;++i)frame[12*80+51+i]=0x1f00|(unsigned char)elapsed_duration[i];
}
void __cdecl elapsed_view_close(void){terminal_elapsed_view_active=0;}
