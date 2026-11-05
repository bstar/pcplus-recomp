#include "path_dialog.h"
#include "path_session.h"
#include "../recording/foreground.h"
typedef unsigned short word;
typedef unsigned char byte;
#define TEXT __based(__segname("_CODE"))
typedef struct dialog_state {
 word cookie,active,length,cursor,insert,notice;
 char edit[64],current[68];
} dialog_state;
dialog_state TEXT terminal_path_dialog_state={0x5044};
typedef char dialog_layout[sizeof(dialog_state)==144?1:-1];
#define S terminal_path_dialog_state
extern word terminal_quit,terminal_exit_code,csi_column_count;
#pragma aux terminal_quit "terminal_quit";
#pragma aux terminal_exit_code "terminal_exit_code";
#pragma aux csi_column_count "csi_column_count";
extern word __far __cdecl recording_ui_ready(void);
static const char TEXT title[]=" CURRENT DIR: ";
static const char TEXT prompt[]="NEW PATH:";
static const char TEXT missing[]="Path not found";
static const char TEXT busy[]="Operation pending. Try again when idle.";
static const char TEXT unavailable[]="Directory unavailable in this view.";
static const char TEXT restored[]="Change failed; previous directory restored.";
static const char TEXT uncertain[]="Directory state uncertain. Returning to DOS.";
static word ready(void)
{
 const recording_file *r;
 if(csi_column_count!=80 || !recording_ui_ready() || path_session_quarantined())return 0;
 r=recording_terminal_inspect();
 return !r || !(r->claimed || r->handle_state || r->stage_owned || r->backup_owned);
}
static word refresh(void)
{
 char current[68];word i,status=path_session_current(current);
 if(!status)for(i=0;i<68;++i){S.current[i]=current[i];if(!current[i])break;}
 return status;
}
static void text(word __far *frame,word at,const char __far *s,word attr,word limit)
{while(limit-- && *s)frame[at++]=attr|(byte)*s++;}
static void draw(word __far *frame)
{
 word row,col,n=0;
 if(!S.active || !frame)return;
 for(row=5;row<=9;++row)for(col=2;col<=77;++col)frame[row*80+col]=0x0320;
 for(col=3;col<77;++col)frame[5*80+col]=frame[9*80+col]=0x03cd;
 for(row=6;row<9;++row)frame[row*80+2]=frame[row*80+77]=0x03ba;
 frame[5*80+2]=0x03c9;frame[5*80+77]=0x03bb;
 frame[9*80+2]=0x03c8;frame[9*80+77]=0x03bc;
 frame[5*80+4]=0x03b5;text(frame,5*80+5,title,0x0300,14);
 while(n<56 && S.current[n]){frame[5*80+19+n]=0x0300|(byte)S.current[n];++n;}
 frame[5*80+19+n]=0x0320;frame[5*80+20+n]=0x03c6;
 text(frame,7*80+4,prompt,0x0300,9);
 for(col=0;col<62;++col)frame[7*80+14+col]=0x0d00|(col<S.length?(byte)S.edit[col]:32);
 if(S.notice==PATH_VERIFY)text(frame,8*80+4,restored,0x0f00,70);
 else if(S.notice==8)text(frame,8*80+4,busy,0x0f00,70);
 else if(S.notice==9)text(frame,8*80+4,unavailable,0x0f00,70);
 else if(S.notice==PATH_ROLLBACK)text(frame,8*80+4,uncertain,0x0f00,70);
 else if(S.notice)text(frame,8*80+4,missing,0x0f00,70);
}
word __far __cdecl path_dialog_event(word event,word key,word __far *frame)
{
 word i,status;byte ch=(byte)key;char request[64];path_result result;
 if(event==4){S.active=0;return 0;}
 if(event==0){
  S.active=1;S.length=S.cursor=S.notice=0;S.insert=1;S.edit[0]=S.current[0]=0;
  if(refresh() || csi_column_count!=80)S.notice=9;
  else if(!ready())S.notice=8;
  draw(frame);return 1;
 }
 if(!S.active)return 0;
 if(event!=1){if(event==2)draw(frame);return 1;}
 if(ch==27){S.active=0;return 0;}
 if(ch==0xe0){key&=0xff00;ch=0;}
 if(ch==13){
  if(!S.length){S.active=0;return 0;}
  if(!ready()){S.notice=8;draw(frame);return 1;}
  for(i=0;i<=S.length;++i)request[i]=S.edit[i];
  status=path_session_change(request,&result);
  if(!status){S.active=0;return 0;}
  if(status==PATH_ROLLBACK || path_session_quarantined()){
   S.notice=PATH_ROLLBACK;terminal_quit=1;if(!terminal_exit_code)terminal_exit_code=17;
   S.active=0;return 0;
  }
  S.notice=status;S.length=S.cursor=0;S.edit[0]=0;
  if(refresh())S.notice=9;
 }else if(ch==8){
  if(S.cursor){--S.cursor;for(i=S.cursor;i<S.length;++i)S.edit[i]=S.edit[i+1];--S.length;}
 }else if(key==0x4b00){if(S.cursor)--S.cursor;}
 else if(key==0x4d00){if(S.cursor<S.length)++S.cursor;}
 else if(key==0x4700)S.cursor=0;
 else if(key==0x4f00)S.cursor=S.length;
 else if(key==0x5200)S.insert=!S.insert;
 else if(key==0x5300){if(S.cursor<S.length){for(i=S.cursor;i<S.length;++i)S.edit[i]=S.edit[i+1];--S.length;}}
 else if(ch>=32 && ch!=127){
  if(S.insert || S.cursor==S.length){
   if(S.length<62){for(i=S.length+1;i>S.cursor;--i)S.edit[i]=S.edit[i-1];S.edit[S.cursor++]=(char)ch;++S.length;}
  }else S.edit[S.cursor++]=(char)ch;
 }
 draw(frame);return 1;
}
word __far __cdecl path_dialog_cursor(void)
{return S.active?(7U<<8)|(14U+(S.cursor<62?S.cursor:61)):0xffff;}
