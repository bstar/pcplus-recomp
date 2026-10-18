/* Maintained serviced filename clipboard UI. Original list/packet semantics
 * live in clipboard.c; this screen and keyboard layout are source-owned. */
#include <dos.h>
#include "clipboard.h"
#include "clipboard_ui.h"
typedef unsigned short word;
typedef unsigned char byte;
clipboard_state clipboard_list;
unsigned clipboard_ui_active=0,clipboard_paste_pending=0,clipboard_ui_visible=0;
static unsigned painted;
static word initialized,selected,phase,field_size,scan,match,mode,notice;
static unsigned first,past;
static char field[13];
static byte row[80],packet[196];
static const word __far *frame;
static void text(word at,const char *s,word attribute)
{word __far *v=(word __far *)MK_FP(0xb800,0);while(*s && at<2000)v[at++]=attribute|(byte)*s++;}
static void number(word at,word n)
{char s[4];s[0]='0'+n/100;s[1]='0'+n/10%10;s[2]='0'+n%10;s[3]=0;text(at,s,0x1f00);}
static void paint(void)
{
 word i,r;word __far *v=(word __far *)MK_FP(0xb800,0);
 if(!clipboard_ui_visible)return;painted=1;
 for(i=0;i<2000;++i)v[i]=frame[i];
 if(phase==3){
  for(i=0;i<80;++i)v[1920+i]=0x1f20;
  text(1921,"Cut: Left/Right or Tab selects; Enter adds; Esc returns to list.",0x1f00);
  if(match)for(i=first;i<past;++i)v[i]=(v[i]&255)|0x7000;
 }else{
  for(r=2;r<23;++r)for(i=8;i<73;++i)v[r*80+i]=0x1f20;
  text(171,"PCPLUS  Filename Clipboard",0x1f00);
  for(r=0;r<clipboard_list.count;++r){
   i=(r+4)*80+12;v[i-2]=(r==selected?0x7020:0x1f20);v[i-1]=0x1f00|(clipboard_list.tags[r]?'*':' ');
   text(i,clipboard_list.names[r],r==selected?0x7000:0x1f00);
  }
  text(1610,"A Add  E Edit  D Delete  U Purge  Space Tag  C Cut",0x1f00);
  text(1690,"P Paste all  S Single  T Tagged  R Separator  Esc",0x1f00);
  if(phase==1 || phase==2){text(1770,phase==1?"Add: ":"Edit: ",0x1f00);text(1776,field,0x1f00);}
  else if(phase==4){text(1770,"Separator (decimal0..255): ",0x1f00);text(1797,field,0x1f00);}
  else if(phase==5)text(1770,"Purge all entries? Y confirms; any other key cancels.",0x1f00);
  else if(clipboard_paste_pending)text(1770,"Pasting; Esc cancels unsent bytes. Input continues.",0x1f00);
  else if(notice==1)text(1770,"Paste delivered to UART. Remote receipt is not confirmed.",0x1f00);
  else if(notice==2)text(1770,"Canceled; a prefix may have been sent. Entry retained.",0x1f00);
  else if(notice==3)text(1770,"Cannot paste now; wait for pending output to drain.",0x1f00);
  else if(notice==4)text(1770,"List full, duplicate, empty or invalid name.",0x1f00);
  else if(notice==5)text(1770,"No selected filenames to paste.",0x1f00);
  else if(notice==6)text(1770,"No filename found on this screen.",0x1f00);
  else {text(1770,"Separator byte: ",0x1f00);number(1786,clipboard_list.separator);}
 }
 __asm {
 mov ah,1
 mov cx,2000h
 int 10h
 }
}
static void finish(void)
{
 word status;if(!clipboard_paste_pending)return;status=clipboard_transport(1,0,0);
 if(status==65535U){clipboard_transport(2,0,0);clipboard_paste_pending=0;notice=2;painted=0;return;}
 if(!status){
  if(mode==CLIP_SINGLE)clip_change(&clipboard_list,CLIP_DELETE,0,0);
  clipboard_paste_pending=0;notice=1;painted=0;
  if(selected>=clipboard_list.count)selected=clipboard_list.count?clipboard_list.count-1:0;
 }
}
static void cancel(void)
{if(clipboard_paste_pending){clipboard_transport(2,0,0);clipboard_paste_pending=0;notice=2;}}
static void find(word backwards)
{
 word i,col,start=scan;
 match=0;
 for(i=0;i<2000;++i){
  scan=backwards?(scan?scan-1:1999):(scan==1999?0:scan+1);
  if((frame[scan]&255)!='.')continue;
  start=scan/80*80;for(col=0;col<80;++col)row[col]=(byte)frame[start+col];
  if(!clip_extract(row,80,scan%80,field,&first,&past)){
   first+=start;past+=start;match=1;return;
  }
 }
 notice=6;
}
static void paste(word selection)
{
 unsigned n;mode=selection;
 if(clip_prepare(&clipboard_list,mode,packet,sizeof(packet),&n) || !n){notice=5;return;}
 if(clipboard_transport(0,packet,n)){notice=3;return;}
 clipboard_paste_pending=1;notice=0;
}
unsigned __cdecl clipboard_ui_event(unsigned event,unsigned key,const word __far *underlay)
{
 word i,n;byte ch=(byte)key;
 if(event==0){
  if(!initialized){clip_initialize(&clipboard_list);initialized=1;}
  frame=underlay;painted=0;clipboard_ui_active=1;phase=notice=0;selected=0;paint();return 1;
 }
 if(!clipboard_ui_active)return 0;
 finish();
 if(event==4 || (event==1 && key==0x2d00)){cancel();clipboard_ui_active=0;return 0;}
 if(event==2){painted=0;return 1;}
 if(event==3){if(!painted)paint();return 1;}
 if(event!=1)return 1;
 if(clipboard_paste_pending){if(key==27)cancel();paint();return 1;}
 if(key==27){if(phase)phase=0;else clipboard_ui_active=0;}
 else if(phase==5){if(ch=='y' || ch=='Y'){clip_change(&clipboard_list,CLIP_PURGE,0,0);selected=0;}phase=0;}
 else if(phase==3){
  if(ch==13 && match){notice=clip_change(&clipboard_list,CLIP_ADD,0,field)?4:0;find(0);}
  else if(ch==9 || key==0x4d00 || key==0x4de0 || key==0x5000 || key==0x50e0)find(0);
  else if(key==0x4b00 || key==0x4be0 || key==0x4800 || key==0x48e0)find(1);
 }else if(phase){
  if(ch==13){
   if(phase==4){n=0;for(i=0;i<field_size;++i)n=n*10+field[i]-'0';if(!field_size || n>255){paint();return 1;}clip_change(&clipboard_list,CLIP_SEPARATOR,n,0);}
   else notice=clip_change(&clipboard_list,phase==1?CLIP_ADD:CLIP_EDIT,selected,field)?4:0;
   phase=0;
  }else if(ch==8){if(field_size)field[--field_size]=0;}
  else if(ch>=32 && ch<127 && field_size<(phase==4?3:12) && (phase!=4 || (ch>='0' && ch<='9'))){field[field_size++]=ch;field[field_size]=0;}
 }else{
  notice=0;
  if(key==0x4800 || key==0x48e0){if(selected)--selected;}
  else if(key==0x5000 || key==0x50e0){if(selected+1<clipboard_list.count)++selected;}
  else if(key==0x4700 || key==0x47e0)selected=0;
  else if(key==0x4f00 || key==0x4fe0)selected=clipboard_list.count?clipboard_list.count-1:0;
  else switch(ch){
   case 'a':case 'A':phase=1;field_size=0;field[0]=0;break;
   case 'e':case 'E':if(clipboard_list.count){phase=2;for(i=0;(field[i]=clipboard_list.names[selected][i])!=0;++i);field_size=i;}break;
   case 'd':case 'D':if(clipboard_list.count){clip_change(&clipboard_list,CLIP_DELETE,selected,0);if(selected>=clipboard_list.count)selected=clipboard_list.count?clipboard_list.count-1:0;}break;
   case 'u':case 'U':phase=5;break;
   case ' ':if(clipboard_list.count)clip_change(&clipboard_list,CLIP_TAG,selected,0);break;
   case 'c':case 'C':phase=3;scan=1999;find(0);break;
   case 'r':case 'R':phase=4;field_size=0;field[0]=0;break;
   case 'p':case 'P':paste(CLIP_ALL);break;
   case 's':case 'S':paste(CLIP_SINGLE);break;
   case 't':case 'T':paste(CLIP_TAGGED);break;
  }
 }
 if(clipboard_ui_active)paint();return clipboard_ui_active;
}
