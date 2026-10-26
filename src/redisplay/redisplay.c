/* Maintained redisplay over a frozen chronological native history snapshot.
 * DOS16 DS=SS; no heap, original resources, blocking input or UART ownership. */
#include <dos.h>
#include "../capture/capture_file.h"
#include "../clipboard/clipboard_ui.h"
#include "command_menu.h"
#ifdef TERMINAL_REFERENCE
#include "command_reference.h"
#endif
typedef unsigned short word;
typedef unsigned char byte;
typedef struct context {
 word source_off,source_seg,snapshot_off,snapshot_seg;
 word live_off,live_seg,view_off,view_seg;
 word start,end,head,wrapped;
} context;
unsigned redisplay_active=0;
/* Only event2 grants live video ownership; local frames revoke it before paint. */
unsigned redisplay_live_ready=0;
unsigned redisplay_search_pending=0;
unsigned redisplay_export_pending=0;
static byte __far *snapshot;
static word __far *live;
static word __far *view;
static word length,top,visible,position,shape,direct_clipboard;
static word query_size,query_edit,found,last_match;
static char query[40];
extern word __far redisplay_row_index[247];
#define checkpoints redisplay_row_index
static word search_start,search_cursor;
static word export_edit,export_phase,export_at,export_size,export_notice,oldest_skip;
static char export_path[64];
static byte export_bytes[256];
static void export_close(word notice)
{
 unsigned status=history_file_event(HISTORY_CLOSE,0,0);
 redisplay_export_pending=0;export_edit=0;
 export_notice=status?3:notice;
}
/* A foreground turn writes at most128 snapshot bytes, expanded to<=256 bytes.
 * The main loop services serial/keyboard again before the next kernel call. */
static word export_step(void)
{
 word n=0,budget=128;byte b;unsigned status;
 if(!redisplay_export_pending)return 0;
 if(!export_phase){
  status=history_file_event(HISTORY_BEGIN,export_path,0);
  if(status){redisplay_export_pending=0;export_notice=4;return 1;}
  export_phase=1;return 1;
 }
 if(export_at==length){export_close(1);return 1;}
 while(export_at<length && budget--){b=snapshot[export_at++];export_bytes[n++]=b;if(b==13)export_bytes[n++]=10;}
 status=history_file_event(HISTORY_WRITE,export_bytes,n);
 if(status){export_close(3);return 1;}
 return 0;
}
static void copy(word __far *to,const word __far *from)
{word i;for(i=0;i<2000;++i)to[i]=from[i];}
static void cursor_get(void)
{
 word p=0,s=0;
 __asm {
 mov ah,3
 xor bh,bh
 int 10h
 mov p,dx
 mov s,cx 
}
 position=p;shape=s;
}
static void cursor_restore(void)
{
 word p=position,s=shape;
 __asm {
 mov ah,1
 mov cx,s
 int 10h
 mov ah,2
 xor bh,bh
 mov dx,p
 int 10h 
}
}
static void hide(void)
{__asm {
 mov ah,1
 mov cx,2000h
 int 10h 
}}
static byte fold(byte b)
{return b>='a' && b<='z'?b-32:b;}
static word next(word at)
{
 word col=0;byte b;
 while(at<length){b=snapshot[at++];if(b==13)return at;
  col+=b==9?8-(col&7):1;
  if(col>=80){if(at<length && snapshot[at]==13)++at;return at;}
 }
 return at;
}
static void index_rows(void)
{
 word p=0,n,block=0;
 while(p<length){n=next(p);while(block<247 && ((unsigned long)block<<8)<n)checkpoints[block++]=p;p=n;}
 while(block<247)checkpoints[block++]=0;
}
static word line_at(word at)
{
 word p,n;if(!length)return 0;if(at>=length)at=length-1;
 p=checkpoints[at>>8];
 while(p<at){n=next(p);if(n>at || n<=p)return p;p=n;}return p;
}
static word previous(word at)
{
 word p,n;if(!at)return 0;p=checkpoints[(at-1)>>8];
 while(p<at){n=next(p);if(n>=at || n<=p)return p;p=n;}return 0;
}
static void bottom(void)
{
 word i;top=line_at(length?length-1:0);for(i=1;i<23;++i)top=previous(top);
}
/* Keep fixed UI prose with CONFIG code, following command_menu.c. */
#define REDISPLAY_TEXT __based(__segname("_CODE"))
static const char REDISPLAY_TEXT redisplay_text_0[]="PCPLUS  Redisplay | Up/Down PgUp/PgDn Home/End / Search F3 W Write C Clip Esc";
static const char REDISPLAY_TEXT redisplay_text_1[]="File: ";
static const char REDISPLAY_TEXT redisplay_text_2[]="Append frozen history: Enter starts; Esc cancels. DOS 8.3 path, up to63 bytes.";
static const char REDISPLAY_TEXT redisplay_text_3[]="Appending history; incoming data continues. Esc cancels; written bytes remain.";
static const char REDISPLAY_TEXT redisplay_text_4[]="History appended. W writes again; Esc returns to the live screen.";
static const char REDISPLAY_TEXT redisplay_text_5[]="Export canceled. A partial append may remain. W retries; Esc returns.";
static const char REDISPLAY_TEXT redisplay_text_6[]="Export failed; partial output may remain. Check the file/disk before retrying.";
static const char REDISPLAY_TEXT redisplay_text_7[]="Cannot open history file. Check path, attributes and active file owners.";
static const char REDISPLAY_TEXT redisplay_text_8[]="History is empty; no file was created. Esc returns to the live screen.";
static const char REDISPLAY_TEXT redisplay_text_9[]="Search: ";
static const char REDISPLAY_TEXT redisplay_text_10[]="Searching... Incoming data continues; Esc returns to the live screen.";
static const char REDISPLAY_TEXT redisplay_text_11[]="History is empty. Incoming data continues; Esc returns to the live screen.";
static const char REDISPLAY_TEXT redisplay_text_12[]="No match. / changes search; F3 repeats. Incoming data continues.";
static const char REDISPLAY_TEXT redisplay_text_13[]="Frozen history; incoming data continues. / searches; Esc returns to live screen.";
static void label(word at,const char __far *s,word attribute)
{while(*s && at<2000)view[at++]=attribute|(byte)*s++;}
static void draw(void)
{
 word i,p=top,row,col;byte b;
 for(i=0;i<2000;++i)view[i]=0x0720;
 for(i=0;i<80;++i)view[i]=view[1920+i]=0x1f20;
 label(1,redisplay_text_0,0x1f00);
 for(row=1;row<24 && p<length;++row){col=0;
  while(p<length){b=snapshot[p++];if(b==13)break;
   if(b==9){col+=8-(col&7);}else{
    if(col<80)view[row*80+col]=0x0700|(b<32?'.':b);++col;
   }
   if(col>=80){if(p<length && snapshot[p]==13)++p;break;}
  }
 }
 if(export_edit){
  for(i=1840;i<1920;++i)view[i]=0x1f20;
  label(1841,redisplay_text_1,0x1f00);label(1847,export_path,0x1f00);
  label(1921,redisplay_text_2,0x1f00);
 }
 else if(redisplay_export_pending)label(1921,redisplay_text_3,0x1f00);
 else if(export_notice==1)label(1921,redisplay_text_4,0x1f00);
 else if(export_notice==2)label(1921,redisplay_text_5,0x1f00);
 else if(export_notice==3)label(1921,redisplay_text_6,0x1f00);
 else if(export_notice==4)label(1921,redisplay_text_7,0x1f00);
 else if(export_notice==5)label(1921,redisplay_text_8,0x1f00);
 else if(query_edit)label(1921,redisplay_text_9,0x1f00);
 else if(redisplay_search_pending)label(1921,redisplay_text_10,0x1f00);
 else if(!length)label(1921,redisplay_text_11,0x1f00);
 else if(!found)label(1921,redisplay_text_12,0x1f00);
 else label(1921,redisplay_text_13,0x1f00);
 if(query_edit && !export_edit && !redisplay_export_pending)label(1929,query,0x1f00);
 if(visible){copy((word __far *)MK_FP(0xb800,0),view);hide();}
}
static void search(void)
{
 if(!query_size || !length){found=0;redisplay_search_pending=0;return;}
 search_start=last_match==65535U?top:last_match+1;
 if(search_start>=length)search_start=0;
 search_cursor=search_start;redisplay_search_pending=1;
}
/* At most64 candidates per foreground turn; receive, flow and cancellation
 * resume between chunks, even for worst-case repeated-prefix searches. */
static word search_step(void)
{
 word p,i,budget=64;
 if(!redisplay_search_pending)return 0;
 while(budget--){p=search_cursor;
  if(query_size<=length-p){for(i=0;i<query_size;++i)if(fold(snapshot[p+i])!=fold((byte)query[i]))break;
   if(i==query_size){top=line_at(p);last_match=p;found=1;redisplay_search_pending=0;return 1;}
  }
  if(++search_cursor==length)search_cursor=0;
  if(search_cursor==search_start){found=0;redisplay_search_pending=0;return 1;}
 }
 return 0;
}
/* event0=open,1=key,2=before receive,3=idle paint,4=stop.
 * Caller validates resource/geometry ownership before open and supplies the
 * fixed relocated extents. Return1 consumes a key,0 allows normal dispatch. */
unsigned __cdecl redisplay_event(word event,word key,const context *c)
{
 word i,p=0,mode=0;byte __far *source;
 if(event==0){
  if(redisplay_active)return 1;
  __asm {
 mov ah,0fh
 int 10h
 mov mode,ax
 mov p,bx 
}
  if((mode&255)!=3 || mode>>8!=80 || p>>8 || c->end<=c->start ||
   c->end-c->start!=63000U || c->head<c->start || c->head>=c->end || c->wrapped>1)return 1;
  if(*(byte __far *)MK_FP(0x40,0x84)!=0 && *(byte __far *)MK_FP(0x40,0x84)!=24)return 1;
  source=(byte __far *)MK_FP(c->source_seg,0);
  snapshot=(byte __far *)MK_FP(c->snapshot_seg,c->snapshot_off);
  live=(word __far *)MK_FP(c->live_seg,c->live_off);
  view=(word __far *)MK_FP(c->view_seg,c->view_off);
#ifdef TERMINAL_ORIGINAL_KEYS
  direct_clipboard=(key==0x2c00 || key==0x1300
#ifdef TERMINAL_REFERENCE
   || (key&255)=='`' || key==0x6c00 || key==0x1700 || command_reference_unavailable(key)
#endif
   )?2:key==0x8300;
#else
  direct_clipboard=key==0x2c00?2:key==0x8300;
#endif
  length=direct_clipboard?0:(c->wrapped?63000U:c->head-c->start);p=c->wrapped?c->head:c->start;
  for(i=0;i<length;++i){snapshot[i]=source[p];if(++p==c->end)p=c->start;}
  cursor_get();copy(live,(word __far *)MK_FP(0xb800,0));
  redisplay_search_pending=redisplay_export_pending=0;export_edit=export_notice=0;oldest_skip=c->wrapped && length && snapshot[0]==13;query_size=query_edit=0;query[0]=0;found=1;last_match=65535U;visible=1;redisplay_live_ready=0;clipboard_ui_visible=1;redisplay_active=1;index_rows();bottom();
  if(direct_clipboard==2){command_menu_event(0,
#ifdef TERMINAL_ORIGINAL_KEYS
   key,
#else
   0,
#endif
   view);copy((word __far *)MK_FP(0xb800,0),view);hide();}
  else if(direct_clipboard){copy(view,live);clipboard_ui_event(0,0,view);}else draw();return 1;
 }
 if(!redisplay_active)return 0;
 if(command_menu_active && (event==1 || event==4)){
  if(command_menu_event(event,key,view)){if(visible){copy((word __far *)MK_FP(0xb800,0),view);hide();}return 1;}
  if(visible){copy((word __far *)MK_FP(0xb800,0),live);cursor_restore();}
  redisplay_search_pending=redisplay_export_pending=0;redisplay_active=visible=redisplay_live_ready=0;
  return command_menu_action?0:1;
 }
 if(clipboard_ui_active && (event==1 || event==4)){
  if(clipboard_ui_event(event,key,view))return 1;
  if(!direct_clipboard && event==1 && key!=0x2d00){if(visible){copy((word __far *)MK_FP(0xb800,0),view);hide();}return 1;}
  key=key==0x2d00?key:27;
 }
 if(event==1 && key==27 && (export_edit || redisplay_export_pending)){
  if(redisplay_export_pending)export_close(2);else{export_edit=0;export_notice=0;}
  draw();return 1;
 }
 if(event==4 || (event==1 && (key==27 || key==0x2d00))){
  if(event==1 && query_edit && key==27){query_edit=0;draw();return 1;}
  if(redisplay_export_pending)export_close(2);
  if(visible){copy((word __far *)MK_FP(0xb800,0),live);cursor_restore();}
  export_edit=0;redisplay_search_pending=0;redisplay_active=visible=redisplay_live_ready=0;return key==0x2d00?0:1;
 }
 if(event==2){if(visible){copy((word __far *)MK_FP(0xb800,0),live);cursor_restore();visible=0;redisplay_live_ready=1;clipboard_ui_visible=0;if(clipboard_ui_active)clipboard_ui_event(2,0,view);}return 0;}
 if(event==3){if(export_step() || search_step())draw();if(!visible){cursor_get();copy(live,(word __far *)MK_FP(0xb800,0));redisplay_live_ready=0;visible=1;copy((word __far *)MK_FP(0xb800,0),view);hide();}
  clipboard_ui_visible=visible;if(clipboard_ui_active)clipboard_ui_event(3,0,view);return 0;}
 if(event!=1)return 0;
 if(redisplay_export_pending)return 1;
 if(export_edit){
  if((byte)key==13){
   export_edit=0;
   if(export_size){export_at=oldest_skip;export_phase=0;redisplay_export_pending=1;}
  }else if((byte)key==8){if(export_size)export_path[--export_size]=0;}
  else if((byte)key>=32 && (byte)key<127 && export_size<63){export_path[export_size++]=(byte)key;export_path[export_size]=0;}
  draw();return 1;
 }
 if(query_edit){
  if((byte)key==13){query_edit=0;search();}
  else if((byte)key==8){if(query_size)query[--query_size]=0;}
  else if((byte)key>=32 && (byte)key<127 && query_size<39){query[query_size++]=(byte)key;query[query_size]=0;}
 }else{
  if(key!=0x3d00){redisplay_search_pending=0;last_match=65535U;}
  switch(key){
  case 0x4800:case 0x48e0:top=previous(top);break;
  case 0x5000:case 0x50e0:if(next(top)<length)top=next(top);break;
  case 0x4900:case 0x49e0:for(i=0;i<23;++i)top=previous(top);break;
  case 0x5100:case 0x51e0:for(i=0;i<23 && next(top)<length;++i)top=next(top);break;
  case 0x4700:case 0x47e0:top=0;break;
  case 0x4f00:case 0x4fe0:bottom();break;
  case 'c':case 'C':clipboard_ui_event(0,0,view);return 1;
  case 'w':case 'W':
   if(length){export_edit=1;export_size=0;export_path[0]=0;export_notice=0;}else export_notice=5;
   break;
  case '/':export_notice=0;redisplay_search_pending=0;query_edit=1;query_size=0;query[0]=0;last_match=65535U;break;
  case 0x3d00:export_notice=0;search();break;
  }
 }
 search_step();draw();return 1;
}
