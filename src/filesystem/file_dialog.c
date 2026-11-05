#include "file_dialog.h"
#include "path_session.h"
#include "../recording/foreground.h"
#include "../capture/capture_file.h"
#include "../printer/printer_device.h"
typedef unsigned short word;
typedef unsigned char byte;
#define TEXT __based(__segname("_CODE"))
typedef struct file_dialog_state {
 word cookie,active,phase,cursor,insert,full,rows,count,more,pending,started,claimed,error;
 char edit[65];
 file_find_entry entry;
 char lines[1560];
} file_dialog_state;
file_dialog_state TEXT terminal_file_dialog_state={0x4644};
typedef char dialog_layout[sizeof(file_dialog_state)==1676?1:-1];
#define S terminal_file_dialog_state
enum {EDIT=1,LOADING,PAGE,NOTICE};
extern word csi_column_count,ui_window_rows;
#pragma aux csi_column_count "csi_column_count";
#pragma aux ui_window_rows "ui_window_rows";
extern word __far __cdecl recording_ui_ready(void);
static const char TEXT title[]=" Enter FILE SPEC: (Carriage Return = *.*) ";
static const char TEXT heading[]="FILE NAME       SIZE    DATE    TIME";
static const char TEXT more[]="- MORE -";
static const char TEXT missing[]="File(s) not found";
static const char TEXT failed[]="File search failed";
static const char TEXT busy[]="Operation pending";
static const char TEXT unavailable[]="View unavailable";

static word ready(void)
{
 const recording_file *r;
#ifdef TERMINAL_GATEWAY_HANDLES
 word i;
#endif
 if(!recording_ui_ready()||path_session_quarantined())return 0;
 r=recording_terminal_inspect();
 if(r&&(r->claimed||r->handle_state||r->stage_owned||r->backup_owned))return 0;
#ifdef TERMINAL_GATEWAY_HANDLES
 for(i=0;i<4;i++)if(capture_file_child_handle(i)==0xfffe)return 0;
 if(printer_device_child_handle()==0xfffe)return 0;
#endif
 return 1;
}
static void text(word __far *frame,word at,const char __far *s,word attr,word limit)
{while(limit--&&*s)frame[at++]=attr|(byte)*s++;}
static void box(word __far *f,word top,word bottom,word left,word right,word attr)
{
 word r,c;
 for(r=top;r<=bottom;r++)for(c=left;c<=right;c++)f[r*80+c]=attr|32;
 for(c=left+1;c<right;c++)f[top*80+c]=f[bottom*80+c]=attr|205;
 for(r=top+1;r<bottom;r++)f[r*80+left]=f[r*80+right]=attr|186;
 f[top*80+left]=attr|201;f[top*80+right]=attr|187;
 f[bottom*80+left]=attr|200;f[bottom*80+right]=attr|188;
}
static void draw(word __far *frame)
{
 word i;const char __far *message;
 if(!S.active||!frame)return;
 if(S.phase==EDIT){
  box(frame,10,14,5,75,0x0b00);frame[10*80+6]=0x0bb5;
  text(frame,10*80+7,title,0x0b00,42);frame[10*80+49]=0x0bc6;
  for(i=0;i<64;i++)frame[12*80+8+i]=0x0a00|(byte)S.edit[i];
 }else if(S.phase==NOTICE){
  box(frame,8,12,29,51,0x0b00);
  message=(const char __far *)failed;
  if(S.error==0xfffc)message=(const char __far *)busy;
  else if(S.error==0xfffb)message=(const char __far *)unavailable;
  else if(S.error==2||S.error==3||S.error==18)message=(const char __far *)missing;
  text(frame,10*80+32,message,0x0a00,18);
 }else{
  box(frame,1,S.rows-4,20,60,0x0700);
  text(frame,2*80+22,heading,0x0700,37);
  if(S.phase==PAGE)for(i=0;i<S.count;i++)text(frame,(4+i)*80+22,((const char __far *)S.lines)+i*39,0x0700,38);
  if(S.phase==PAGE&&S.more)text(frame,(S.rows-5)*80+37,more,0x0700,8);
 }
}
static word digits(unsigned long value,char *out)
{
 char reverse[10];word n=0,i,bit,high=(word)(value>>16),low=(word)value,qhigh,qlow,remainder;
 /* Small-model32-bit division would near-call the resident CRT from this
  * bank. Divide two16-bit halves explicitly, with no cross-bank RTL call. */
 do{
  qhigh=high/10;remainder=high%10;qlow=0;
  for(bit=0;bit<16;bit++){
   remainder=(word)(remainder*2+(low>>15));low<<=1;qlow<<=1;
   if(remainder>=10){remainder-=10;qlow|=1;}
  }
  reverse[n++]=(char)('0'+remainder);high=qhigh;low=qlow;
 }while(high||low);
 for(i=0;i<n;i++)out[i]=reverse[n-i-1];
 return n;
}
static void pair(char __far *out,word at,word value,word zero)
{out[at]=value<10&&!zero?' ':(char)('0'+value/10);out[at+1]=(char)('0'+value%10);}
void __far __cdecl file_dialog_format(const file_find_entry *entry,char __far *out)
{
 word i,n=0,at=22,year=(entry->date>>9)+80;char number[10];
 for(i=0;i<38;i++)out[i]=' ';out[38]=0;
 for(i=0;i<12&&entry->name[i];i++)out[i]=entry->name[i];
 if(entry->attributes==0x10){out[15]='<';out[16]='D';out[17]='I';out[18]='R';out[19]='>';}
 else{
  n=digits(entry->size,number);
  /* Large32-bit sizes keep all digits in a compact row, inside the border. */
  if(n>6){for(i=0;i<n;i++)out[23-n+i]=number[i];at=24;}
  else for(i=0;i<n;i++)out[20-n+i]=number[i];
 }
 while(year>=100)year-=100;
 pair(out,at,(entry->date>>5)&15,0);out[at+2]='-';
 pair(out,at+3,entry->date&31,1);out[at+5]='-';pair(out,at+6,year,1);
 i=at==22?32:33;pair(out,i,entry->time>>11,1);out[i+2]=':';
 pair(out,i+3,(entry->time>>5)&63,1);
}
static void close(void)
{if(S.claimed)file_find_close();S.claimed=S.active=0;}
static word step(void)
{
 char request[68];file_find_entry entry;word i,n,status;
 if(S.phase!=LOADING||!ready())return 0;
 if(!S.started){
  n=64;while(n&&S.edit[n-1]==' ')--n;
  for(i=0;i<n;i++)request[i]=S.edit[i];
  if(!n||request[n-1]==':'||request[n-1]=='\\'){
   request[n++]='*';request[n++]='.';request[n++]='*';
  }
  request[n]=0;status=file_find_begin(request,0x10,&entry);
  S.claimed=status!=FILE_FIND_BUSY&&file_find_storage.active;S.started=1;
 }else if(S.pending){
  /* Copy out of the bank before giving a near argument to the formatter. */
  /* Cast the fixed based-array root before adding the variable row offset.
   * Watcom loses the bank segment when a two-dimensional subarray decays. */
  entry=S.entry;file_dialog_format(&entry,((char __far *)S.lines)+S.count*39);
  ++S.count;S.pending=0;return 0;
 }else status=file_find_next(&entry);
 if(status){
  S.error=status;
  if(status==18&&S.count){S.more=0;S.phase=PAGE;}
  else S.phase=NOTICE;
  return 1;
 }else{
  S.entry=entry;S.pending=1;
  if(S.count==S.rows-10){S.more=1;S.phase=PAGE;return 1;}
 }
 return 0;
}
word __far __cdecl file_dialog_event(word event,word key,word __far *frame)
{
 word i,cursor;byte ch=(byte)key;
 if(event==4){close();return 0;}
 if(event==0){
  if(S.active){draw(frame);return 1;}
  S.active=1;S.phase=EDIT;S.cursor=S.insert=S.full=S.count=S.more=S.pending=S.started=S.claimed=S.error=0;
  S.rows=ui_window_rows;
  for(i=0;i<64;i++)S.edit[i]=' ';S.edit[64]=0;
  if(csi_column_count!=80||(S.rows!=25&&S.rows!=28&&S.rows!=43&&S.rows!=50))S.error=0xfffb;
  else if(!ready()||file_find_storage.active)S.error=0xfffc;
  if(S.error)S.phase=NOTICE;
  draw(frame);return 1;
 }
 if(!S.active)return 0;
 /* Use the step's explicit repaint result. A cached based-code phase reload
  * across the call can otherwise miss the LOADING-to-PAGE transition. */
 if(event==3&&!step())return 2;
 if(event==1){
  if(ch==27||S.phase==NOTICE||(S.phase==PAGE&&!S.more)){close();return 0;}
  if(S.phase==PAGE){S.count=0;S.more=0;S.phase=LOADING;}
  else if(S.phase==EDIT){
   if(ch==0xe0){key&=0xff00;ch=0;}
   if(ch==13){S.phase=LOADING;}
   else if(ch==8){
    S.full=0;cursor=S.cursor;
    if(cursor){--cursor;S.cursor=cursor;for(i=cursor;i<63;i++)S.edit[i]=S.edit[i+1];S.edit[63]=' ';}
   }else if(key==0x4b00){S.full=0;if(S.cursor)--S.cursor;}
   else if(key==0x4d00){if(S.cursor<63)++S.cursor;}
   else if(key==0x4700){S.full=S.cursor=0;}
   else if(key==0x4f00){S.full=0;i=64;while(i&&S.edit[i-1]==' ')--i;S.cursor=i<64?i:63;}
   else if(key==0x5200)S.insert=!S.insert;
   else if(key==0x5300){S.full=0;for(i=S.cursor;i<63;i++)S.edit[i]=S.edit[i+1];S.edit[63]=' ';}
   else if(key==0x7500){S.full=0;for(i=S.cursor;i<64;i++)S.edit[i]=' ';}
   else if(ch>=32&&ch!=127&&!S.full){
    if(S.insert)for(i=63;i>S.cursor;i--)S.edit[i]=S.edit[i-1];
    S.edit[S.cursor]=(char)ch;if(S.cursor==63)S.full=1;else ++S.cursor;
   }
  }
 }
 draw(frame);return 1;
}
word __far __cdecl file_dialog_cursor(void)
{return !S.active?0xffff:S.phase==EDIT?(12U<<8)|(8U+S.cursor):0x64c8;}
word __far __cdecl file_dialog_pending(void)
{return S.active&&S.phase==LOADING;}
word __far __cdecl file_dialog_shape(word saved)
{
 word end=saved&31;
 if(S.phase!=EDIT)return (saved&0x1f1f)|0x2000;
 return S.insert?(word)((((end>>1)+1)<<8)|end):(saved&0x1f1f);
}
