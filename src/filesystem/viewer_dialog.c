#include "viewer_dialog.h"
#ifdef TERMINAL_EXTERNAL_VIEWER
#include "viewer_external_dialog.h"
#endif
#include "viewer_session.h"
#include "viewer_file.h"
#include "path_session.h"
#include "../recording/foreground.h"
#include "../capture/capture_file.h"
#include "../printer/printer_device.h"
#include <dos.h>
typedef unsigned short word;
typedef unsigned char byte;
#define TEXT __based(__segname("_CODE"))
typedef struct viewer_dialog_state {
 word cookie,active,phase,cursor,insert,full,started,bound,rows,error;
 char edit[44];byte __far *page;
} viewer_dialog_state;
volatile viewer_dialog_state TEXT terminal_viewer_dialog_state={0x5644};
typedef char dialog_layout[sizeof(viewer_dialog_state)==68?1:-1];
#define S terminal_viewer_dialog_state
enum {EDIT=1,LOADING,PAGE,NOTICE,CLEANUP,GUARD};
extern word csi_column_count,ui_window_rows,terminal_quit,terminal_exit_code,redisplay_active;
#pragma aux csi_column_count "csi_column_count";
#pragma aux ui_window_rows "ui_window_rows";
#pragma aux terminal_quit "terminal_quit";
#pragma aux terminal_exit_code "terminal_exit_code";
extern byte __far redisplay_snapshot[63000];
#pragma aux redisplay_snapshot "redisplay_snapshot";
extern word __far __cdecl recording_ui_ready(void);
static const char TEXT title[]=" VIEW A FILE ";
static const char TEXT prompt[]="Please enter filename:";
static const char TEXT missing[]="FILE NOT FOUND...";
static const char TEXT failed[]="Unable to view file";
static const char TEXT busy[]="Operation pending";
static const char TEXT unavailable[]="View unavailable";
static const char TEXT uncertain[]="File state uncertain. Returning to DOS.";
static const char TEXT loading[]="Loading file...";
static const char TEXT closing[]="Closing file...";
static const char TEXT footer[]=" Home: Top of file      PgUp: Previous page      PgDn: Next page      ESC: Exit ";
word __far __cdecl viewer_dialog_unsafe(void)
{
 viewer_file_snapshot f;viewer_session_snapshot s;
 return
#ifdef TERMINAL_EXTERNAL_VIEWER
        viewer_external_unsafe()||
#endif
        S.cookie!=0x5644||viewer_file_inspect(&f)||viewer_session_inspect(&s)||
        f.phase==VF_UNCERTAIN||s.phase==VS_UNCERTAIN;
}
word __far __cdecl viewer_dialog_owned(void)
{
 viewer_file_snapshot f;viewer_session_snapshot s;
 return
#ifdef TERMINAL_EXTERNAL_VIEWER
        viewer_external_owned()||
#endif
        S.cookie!=0x5644||S.active||viewer_file_inspect(&f)||viewer_session_inspect(&s)||
        f.handle!=0xffff||f.claimed||f.phase==VF_UNCERTAIN||s.owned||s.phase==VS_UNCERTAIN;
}
static void fatal(void)
{S.phase=GUARD;S.error=0xfffa;terminal_quit=1;if(!terminal_exit_code)terminal_exit_code=20;}
static word close(void)
{
 viewer_session_snapshot s;
 if(S.started)viewer_session_stop();
 if(viewer_session_inspect(&s)||(S.started&&s.owned)||viewer_dialog_unsafe()){fatal();return 1;}
 S.started=S.active=0;return 0;
}
word __far __cdecl viewer_dialog_shutdown(void)
{
#ifdef TERMINAL_EXTERNAL_VIEWER
 viewer_external_event(4,0,0);
#endif
 close();return viewer_dialog_owned();}
word __far __cdecl viewer_dialog_bind(byte __far *page)
{
 viewer_session_snapshot s;
 if(viewer_dialog_owned()||viewer_session_inspect(&s)||
    (s.phase!=VS_IDLE&&s.phase!=VS_CLOSED))return 1;
 if(FP_SEG(page)!=FP_SEG(redisplay_snapshot)||FP_OFF(page)!=FP_OFF(redisplay_snapshot)||FP_OFF(page)>65535U-3920U)return 1;
 S.page=page;S.bound=1;return 0;
}
static word ready(void)
{
 viewer_file_snapshot f;const recording_file *r;word i;
 if(!S.bound||!recording_ui_ready()||path_session_quarantined())return 0;
 if(viewer_file_inspect(&f)||f.handle!=0xffff||f.claimed||f.phase==VF_UNCERTAIN)return 0;
 r=recording_terminal_inspect();if(r&&(r->claimed||r->handle_state||r->stage_owned||r->backup_owned))return 0;
 for(i=0;i<4;i++)if(capture_file_child_handle(i)==0xfffe)return 0;
 return printer_device_child_handle()!=0xfffe;
}
static void text(word __far *f,word at,const char __far *s,word attr,word n)
{while(n--&&*s)f[at++]=attr|(byte)*s++;}
static void draw(word __far *f)
{
 word r,c,i;const char __far *message;
 if(!S.active||!f)return;
 if(S.phase==PAGE||S.phase==LOADING||S.phase==CLEANUP){
  for(i=0;i<S.rows*80;i++)f[i]=0x0720;
  if(S.phase==PAGE)for(i=0;i<(S.rows-1)*80;i++)f[i]=0x0700|S.page[i];
  else if(S.phase==LOADING)text(f,0,loading,0x0700,80);
  else text(f,0,closing,0x0700,80);
  for(i=(S.rows-1)*80;i<S.rows*80;i++)f[i]=0x7120;
  text(f,(S.rows-1)*80,footer,0x7100,80);return;
 }
 for(r=10;r<=14;r++)for(c=5;c<=75;c++)f[r*80+c]=0x0b20;
 for(c=6;c<75;c++)f[10*80+c]=f[14*80+c]=0x0bcd;
 for(r=11;r<14;r++)f[r*80+5]=f[r*80+75]=0x0bba;
 f[10*80+5]=0x0bc9;f[10*80+75]=0x0bbb;f[14*80+5]=0x0bc8;f[14*80+75]=0x0bbc;
 f[10*80+9]=0x0bb5;text(f,10*80+10,title,0x0b00,13);f[10*80+23]=0x0bc6;
 if(S.phase==EDIT){
  text(f,12*80+7,prompt,0x0b00,23);
  for(i=0;i<43;i++)f[12*80+30+i]=0x0a00|(byte)S.edit[i];
 }else{
  message=(const char __far *)failed;
  if(S.error==2||S.error==3)message=(const char __far *)missing;
  else if(S.error==0xfffc)message=(const char __far *)busy;
  else if(S.error==0xfffb)message=(const char __far *)unavailable;
  else if(S.error==0xfffa)message=(const char __far *)uncertain;
  text(f,12*80+7,message,0x0b00,66);
 }
}
static word step(void)
{
 viewer_session_snapshot s;viewer_file_snapshot f;word status;
 if(S.phase==CLEANUP){
  viewer_session_stop();
  if(viewer_dialog_unsafe()||viewer_session_inspect(&s)||s.owned){fatal();return 1;}
  S.started=0;
  if(!viewer_file_inspect(&f)&&f.dos_error)S.error=f.dos_error;
  S.phase=NOTICE;return 1;
 }
 if(S.phase!=LOADING)return 0;
 status=viewer_session_step();
 if(status||viewer_session_inspect(&s)){S.error=0xfff9;S.phase=CLEANUP;return 1;}
 if(s.phase==VS_READY){S.phase=PAGE;return 1;}
 return 0;
}
word __far __cdecl viewer_dialog_event(word event,word key,word __far *frame)
{
 word i,n,status,cursor;byte ch=(byte)key;char request[64];
 if(event==4){close();return 0;}
 if(event==0){
  if(S.active){draw(frame);return 1;}
  S.active=1;S.phase=EDIT;S.cursor=S.insert=S.full=S.started=S.error=0;S.rows=ui_window_rows;
  for(i=0;i<43;i++)S.edit[i]=' ';S.edit[43]=0;
  if(csi_column_count!=80||(S.rows!=25&&S.rows!=28&&S.rows!=43&&S.rows!=50)){S.error=0xfffb;S.phase=GUARD;}
  else if(!ready()){S.error=0xfffc;S.phase=GUARD;}
  draw(frame);return 1;
 }
 if(!S.active)return 0;
 if(event==3){if(!step())return 2;draw(frame);return 1;}
 if(event==1){
  if(S.phase==NOTICE){S.phase=EDIT;S.cursor=S.full=0;draw(frame);return 1;}
  if(S.phase==GUARD||ch==27){if(close()){draw(frame);return 1;}return 0;}
  if(S.phase==PAGE){
   if(ch==0xe0)key&=0xff00;
   if(key==0x4700||key==0x4900||key==0x5100){
    status=viewer_session_move(key==0x4700?VS_HOME:key==0x4900?VS_PREVIOUS:VS_NEXT);
    if(!status)S.phase=LOADING;
    else if(status!=VS_TOP&&status!=VS_END){S.error=0xfff9;S.phase=CLEANUP;}
   }
  }else if(S.phase==EDIT){
   if(ch==0xe0){key&=0xff00;ch=0;}
   if(ch==13){
    n=43;while(n&&S.edit[n-1]==' ')--n;
    if(!n){close();return 0;}
    if(!ready()){S.error=0xfffc;S.phase=GUARD;}
    else{
     for(i=0;i<64;i++)request[i]=0;for(i=0;i<n;i++)request[i]=S.edit[i];
     status=viewer_session_begin(request,(void *)&redisplay_active,S.page,3920,80,S.rows-1);
     S.started=1;
     if(status){S.error=0xfff9;S.phase=CLEANUP;}else S.phase=LOADING;
    }
   }else if(ch==8){
    S.full=0;cursor=S.cursor;
    if(cursor){--cursor;S.cursor=cursor;for(i=cursor;i<42;i++)S.edit[i]=S.edit[i+1];S.edit[42]=' ';}
   }else if(key==0x4b00){S.full=0;if(S.cursor)--S.cursor;}
   else if(key==0x4d00){if(S.cursor<42)++S.cursor;}
   else if(key==0x4700){S.full=S.cursor=0;}
   else if(key==0x4f00){S.full=0;i=43;while(i&&S.edit[i-1]==' ')--i;S.cursor=i<43?i:42;}
   else if(key==0x5200)S.insert=!S.insert;
   else if(key==0x5300){S.full=0;for(i=S.cursor;i<42;i++)S.edit[i]=S.edit[i+1];S.edit[42]=' ';}
   else if(key==0x7500){S.full=0;for(i=S.cursor;i<43;i++)S.edit[i]=' ';}
   else if(ch>=32&&ch!=127&&!S.full){
    if(S.insert)for(i=42;i>S.cursor;i--)S.edit[i]=S.edit[i-1];
    S.edit[S.cursor]=(char)ch;if(S.cursor==42)S.full=1;else ++S.cursor;
   }
  }
 }
 draw(frame);return 1;
}
word __far __cdecl viewer_dialog_cursor(void)
{return S.active?(S.phase==EDIT?(12U<<8)|(30U+S.cursor):0x64c8):0xffff;}
word __far __cdecl viewer_dialog_shape(word saved)
{word end=saved&31;return S.phase==EDIT&&S.insert?(word)((((end>>1)+1)<<8)|end):(saved&0x1f1f);}
word __far __cdecl viewer_dialog_pending(void)
{return S.active&&(S.phase==LOADING||S.phase==CLEANUP);}
word __far __cdecl viewer_dialog_fullscreen(void)
{return S.active&&(S.phase==LOADING||S.phase==CLEANUP||S.phase==PAGE);}
