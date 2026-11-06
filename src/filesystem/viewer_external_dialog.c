#include "viewer_external_dialog.h"
#include "viewer_external.h"
#include "viewer_dialog.h"
#include "path_session.h"
#include "../terminal/session_baseline.h"
#include <dos.h>
typedef unsigned word;
typedef unsigned char byte;
#define TEXT __based(__segname("_CODE"))
typedef struct external_dialog {
 word cookie,active,pending,cursor,insert,full,error;
 char configured[65],edit[49];
#ifdef TERMINAL_EXTERNAL_EDITOR
 word editor;
#endif
} external_dialog;
#ifdef TERMINAL_EXTERNAL_EDITOR
typedef char external_dialog_layout[sizeof(external_dialog)==130?1:-1];
#else
typedef char external_dialog_layout[sizeof(external_dialog)==128?1:-1];
#endif
volatile external_dialog TEXT terminal_external_viewer_state={0x5658};
#define S terminal_external_viewer_state
extern word csi_column_count,ui_window_rows;
#pragma aux csi_column_count "csi_column_count";
#pragma aux ui_window_rows "ui_window_rows";
extern word __far __cdecl recording_ui_ready(void);
extern word __far __cdecl external_program_queue(void);
static const char TEXT parameters[]="Enter parameters:";
static const char TEXT suffix[]=" Parameters ";
static const char TEXT unavailable[]="External viewer unavailable";
#ifdef TERMINAL_EXTERNAL_EDITOR
static const char TEXT editor_unavailable[]="External editor unavailable";
#define CONFIG_OFFSET (S.editor?EDITOR_EXTERNAL_PRM_OFFSET:VIEWER_EXTERNAL_PRM_OFFSET)
#else
#define CONFIG_OFFSET VIEWER_EXTERNAL_PRM_OFFSET
#endif
word __far __cdecl viewer_external_unsafe(void){return S.cookie!=0x5658;}
word __far __cdecl viewer_external_owned(void){return viewer_external_unsafe()||S.active;}
word __far __cdecl viewer_external_queued(void){return !viewer_external_unsafe()&&S.pending;}
void __far __cdecl viewer_external_cancel(void){S.pending=0;}
#ifdef TERMINAL_EXTERNAL_EDITOR
static word select(void)
#else
word __far __cdecl viewer_external_select(void)
#endif
{
 prm_dos_image image;word i,status;
 S.error=1;
 if(viewer_external_unsafe()||S.active||S.pending)return 2;
 status=hook_baseline_copy(&image);
 if(status==SESSION_BASELINE_MISSING)return 0;
 if(status)return 2;
 for(i=0;i<65&&image.bytes[CONFIG_OFFSET+i];++i){}
 if(!i)return 0;if(i==65)return 2;
 for(i=0;i<65;++i)S.configured[i]=(char)image.bytes[CONFIG_OFFSET+i];
 S.error=0;return 1;
}
#ifdef TERMINAL_EXTERNAL_EDITOR
word __far __cdecl viewer_external_select(void)
{if(viewer_external_unsafe()||S.active||S.pending)return 2;S.editor=0;return select();}
word __far __cdecl editor_external_select(void)
{if(viewer_external_unsafe()||S.active||S.pending)return 2;S.editor=1;return select();}
#endif
static void text(unsigned short __far *f,word at,const char __far *s,word count,word attr)
{while(count--&&*s)f[at++]=attr|(byte)*s++;}
static void draw(unsigned short __far *f)
{
 word r,c,i,at,base=0;
 for(r=10;r<=14;++r)for(c=5;c<=75;++c)f[r*80+c]=0x0b20;
 for(c=6;c<75;++c)f[10*80+c]=f[14*80+c]=0x0bcd;
 for(r=11;r<14;++r)f[r*80+5]=f[r*80+75]=0x0bba;
 f[10*80+5]=0x0bc9;f[10*80+75]=0x0bbb;f[14*80+5]=0x0bc8;f[14*80+75]=0x0bbc;
 for(i=0;i<64&&S.configured[i];++i)if(S.configured[i]=='\\')base=i+1;
 if(!base)for(i=0;i<64&&S.configured[i];++i)if(S.configured[i]==':')base=i+1;
 at=10*80+9;f[at++]=0x0bb5;f[at++]=0x0b20;
 for(i=base;i<64&&S.configured[i]&&at<10*80+62;++i)f[at++]=0x0b00|(byte)S.configured[i];
 text(f,at,suffix,12,0x0b00);for(i=0;i<12&&suffix[i];++i){}at+=i;
 if(at<10*80+75)f[at]=0x0bc6;
 if(S.error){
#ifdef TERMINAL_EXTERNAL_EDITOR
  if(S.editor){text(f,12*80+7,editor_unavailable,66,0x0b00);return;}
#endif
  text(f,12*80+7,unavailable,66,0x0b00);return;}
 text(f,12*80+7,parameters,17,0x0b00);
 for(i=0;i<48;++i)f[12*80+25+i]=0x0a00|(byte)S.edit[i];
}
word __far __cdecl viewer_external_event(word event,word key,unsigned short __far *frame)
{
 word i,n;byte ch=(byte)key;
 if(event==4){S.active=S.pending=0;return 0;}
 if(!frame)return 0;
 if(event==0){
  S.error=S.error||viewer_external_unsafe()||viewer_dialog_owned()||path_session_quarantined()||!recording_ui_ready()||csi_column_count!=80||ui_window_rows<25;
  S.active=1;S.pending=S.cursor=S.insert=S.full=0;
  for(i=0;i<48;++i)S.edit[i]=' ';S.edit[48]=0;
  draw(frame);return 1;
 }
 if(!S.active)return 0;
 if(event==1){
  if(ch==27||S.error){S.active=S.pending=0;return 0;}
  if(ch==0xe0){key&=0xff00;ch=0;}
  if(ch==13){
   n=48;while(n&&S.edit[n-1]==' ')--n;S.edit[n]=0;
   S.active=0;S.pending=1;return 0;
  }
  if(ch==8){S.full=0;if(S.cursor){--S.cursor;for(i=S.cursor;i<47;++i)S.edit[i]=S.edit[i+1];S.edit[47]=' ';}}
  else if(key==0x4b00){S.full=0;if(S.cursor)--S.cursor;}
  else if(key==0x4d00){if(S.cursor<47)++S.cursor;}
  else if(key==0x4700){S.full=S.cursor=0;}
  else if(key==0x4f00){S.full=0;i=48;while(i&&S.edit[i-1]==' ')--i;S.cursor=i<48?i:47;}
  else if(key==0x5200)S.insert=!S.insert;
  else if(key==0x5300){S.full=0;for(i=S.cursor;i<47;++i)S.edit[i]=S.edit[i+1];S.edit[47]=' ';}
  else if(key==0x7500){S.full=0;for(i=S.cursor;i<48;++i)S.edit[i]=' ';}
  else if(ch>=32&&ch!=127&&!S.full){if(S.insert)for(i=47;i>S.cursor;--i)S.edit[i]=S.edit[i-1];S.edit[S.cursor]=(char)ch;if(S.cursor==47)S.full=1;else ++S.cursor;}
 }
 if(event==3)return 2;
 if(event==1){for(i=0;i<48;++i)frame[12*80+25+i]=0x0a00|(byte)S.edit[i];return 1;}
 draw(frame);return 1;
}
word __far __cdecl viewer_external_cursor(void){return S.active?(12U<<8)|(25+S.cursor):0xffff;}
word __far __cdecl viewer_external_shape(word saved)
{word end=saved&31;return S.active&&S.insert?(word)((((end>>1)+1)<<8)|end):(saved&0x1f1f);}
word __far __cdecl viewer_external_start(void)
{
 word status;
 if(viewer_external_unsafe()||!S.pending||S.active)return PROCESS_ARGUMENT;
 status=external_program_queue();if(status)S.pending=0;return status;
}
static word build(char *command)
{
 prm_dos_image image;word i,length;
 if(hook_baseline_copy(&image))return PROCESS_ARGUMENT;
 for(i=0;i<65;++i)if(image.bytes[CONFIG_OFFSET+i]!=(byte)S.configured[i])return PROCESS_ARGUMENT;
#ifdef TERMINAL_EXTERNAL_EDITOR
 /* Reuse the checked literal builder after validating the editor's own field.
  * This is a transient copy, never a write to the accepted baseline or PRM. */
 if(S.editor)for(i=0;i<65;++i)image.bytes[VIEWER_EXTERNAL_PRM_OFFSET+i]=image.bytes[EDITOR_EXTERNAL_PRM_OFFSET+i];
#endif
 return viewer_external_build((const byte __far *)&image,(const char __far *)S.edit,(char __far *)command,114,(word __far *)&length)?PROCESS_ARGUMENT:0;
}
word __far __cdecl viewer_external_execute(process_result *result)
{
 char command[114];word status;
 if(viewer_external_unsafe()||!S.pending||S.active)return PROCESS_ARGUMENT;
 S.pending=0;status=build(command);if(status)return status;
 return program_execute_external(command,result);
}
