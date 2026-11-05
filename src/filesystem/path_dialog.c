#include "path_dialog.h"
#include "path_session.h"
#include "../recording/foreground.h"
typedef unsigned short word;
typedef unsigned char byte;
#define TEXT __based(__segname("_CODE"))
typedef struct dialog_state {
 word cookie,active,full,cursor,insert,notice;
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
static void clear_editor(void)
{
 word i;
 S.full=S.cursor=S.insert=0;
 for(i=0;i<62;++i)S.edit[i]=' ';
 S.edit[62]=S.edit[63]=0;
}
static void text(word __far *frame,word at,const char __far *s,word attr,word limit)
{while(limit-- && *s)frame[at++]=attr|(byte)*s++;}
static void draw(word __far *frame)
{
 word row,col,n=0;
 if(!S.active || !frame)return;
 for(row=5;row<=9;++row)for(col=1;col<=76;++col)frame[row*80+col]=0x0320;
 for(col=2;col<76;++col)frame[5*80+col]=frame[9*80+col]=0x03cd;
 for(row=6;row<9;++row)frame[row*80+1]=frame[row*80+76]=0x03ba;
 frame[5*80+1]=0x03c9;frame[5*80+76]=0x03bb;
 frame[9*80+1]=0x03c8;frame[9*80+76]=0x03bc;
 frame[5*80+3]=0x03b5;text(frame,5*80+4,title,0x0300,14);
 while(n<56 && S.current[n]){frame[5*80+18+n]=0x0300|(byte)S.current[n];++n;}
 frame[5*80+18+n]=0x0320;frame[5*80+19+n]=0x03c6;
 text(frame,7*80+3,prompt,0x0300,9);
 for(col=0;col<62;++col)frame[7*80+13+col]=0x0d00|(byte)S.edit[col];
 if(S.notice&0x8000){
  for(row=8;row<=12;++row)for(col=30;col<=49;++col)frame[row*80+col]=0x0b20;
  for(col=31;col<49;++col)frame[8*80+col]=frame[12*80+col]=0x0bcd;
  for(row=9;row<12;++row)frame[row*80+30]=frame[row*80+49]=0x0bba;
  frame[8*80+30]=0x0bc9;frame[8*80+49]=0x0bbb;
  frame[12*80+30]=0x0bc8;frame[12*80+49]=0x0bbc;
  text(frame,10*80+33,missing,0x0a00,14);
  /* Original shadow visibly tints the underlying path border, preserving
   * characters. The rest is kept as an explicit inferred footprint. */
  for(row=9;row<=13;++row)for(col=50;col<=51;++col)frame[row*80+col]=(frame[row*80+col]&255)|0x0700;
  for(col=32;col<=51;++col)frame[13*80+col]=(frame[13*80+col]&255)|0x0700;
 }else if(S.notice==PATH_VERIFY)text(frame,8*80+3,restored,0x0f00,70);
 else if(S.notice==8)text(frame,8*80+3,busy,0x0f00,70);
 else if(S.notice==9)text(frame,8*80+3,unavailable,0x0f00,70);
 else if(S.notice==PATH_ROLLBACK)text(frame,8*80+3,uncertain,0x0f00,70);
 else if(S.notice)text(frame,8*80+3,missing,0x0f00,70);
}
word __far __cdecl path_dialog_event(word event,word key,word __far *frame)
{
 word i,status;byte ch=(byte)key;char request[64];path_result result;
 if(event==4){S.active=0;return 0;}
 if(event==0){
  S.active=1;S.notice=0;clear_editor();S.current[0]=0;
  if(refresh() || csi_column_count!=80)S.notice=9;
  else if(!ready())S.notice=8;
  draw(frame);return 1;
 }
 if(!S.active)return 0;
 if(event!=1){if(event==2)draw(frame);return 1;}
 if(S.notice&0x8000){S.notice=0;clear_editor();if(refresh())S.notice=9;draw(frame);return 1;}
 if(ch==27){S.active=0;return 0;}
 if(ch==0xe0){key&=0xff00;ch=0;}
 if(ch==13){
  i=62;while(i && S.edit[i-1]==' ')--i;
  if(!i){S.active=0;return 0;}
  if(!ready()){S.notice=8;draw(frame);return 1;}
  request[i]=0;while(i){--i;request[i]=S.edit[i];}
  status=path_session_change(request,&result);
  if(!status){S.active=0;return 0;}
  if(status==PATH_ROLLBACK || path_session_quarantined()){
   S.notice=PATH_ROLLBACK;terminal_quit=1;if(!terminal_exit_code)terminal_exit_code=17;
   S.active=0;return 0;
  }
  S.notice=status;
  if(status==PATH_ARGUMENT || status==PATH_DRIVE || status==PATH_CHANGE)S.notice|=0x8000;
  else clear_editor();
  if(refresh())S.notice=9;
 }else if(ch==8){
  /* Keep the decremented index local: Watcom's based-code optimizer otherwise
   * hoists the later cursor reload before its store and erases one cell late. */
  S.full=0;i=S.cursor;
  if(i){--i;S.cursor=i;for(;i<61;++i)S.edit[i]=S.edit[i+1];S.edit[61]=' ';}
 }else if(key==0x4b00){S.full=0;if(S.cursor)--S.cursor;}
 else if(key==0x4d00){if(S.cursor<61)++S.cursor;}
 else if(key==0x4700){S.cursor=S.full=0;}
 else if(key==0x4f00){S.full=0;i=62;while(i && S.edit[i-1]==' ')--i;S.cursor=i<62?i:61;}
 else if(key==0x5200)S.insert=!S.insert;
 else if(key==0x5300){S.full=0;for(i=S.cursor;i<61;++i)S.edit[i]=S.edit[i+1];S.edit[61]=' ';}
 else if(key==0x7500){S.full=0;for(i=S.cursor;i<62;++i)S.edit[i]=' ';}
 else if(ch>=32 && ch!=127){
  if(!S.full){
   if(S.insert)for(i=61;i>S.cursor;--i)S.edit[i]=S.edit[i-1];
   S.edit[S.cursor]=(char)ch;
   if(S.cursor==61)S.full=1;else ++S.cursor;
  }
 }
 draw(frame);return 1;
}
word __far __cdecl path_dialog_cursor(void)
{return !S.active?0xffff:(S.notice&0x8000)?0x64c8:(7U<<8)|(13U+S.cursor);}
word __far __cdecl path_dialog_shape(word saved)
{
 word end=saved&31;
 if(S.notice&0x8000)return (saved&0x1f1f)|0x2000;
 return S.insert?(word)((((end>>1)+1)<<8)|end):(saved&0x1f1f);
}
