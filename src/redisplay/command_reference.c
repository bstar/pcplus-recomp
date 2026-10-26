/* Authored terminal-command reference. Functional names/shortcut arrangement
 * follow the identified 2.01 reference data; navigation/refusal is maintained.
 * This entire module and its constants live in REFERENCE_CODE. */
#include "command_reference.h"
typedef unsigned short word;
typedef unsigned char byte;
typedef struct reference_item {
 const char __far *label;const char __far *shortcut;
 word key;byte row,column,action;
} reference_item;
#define CONST __based(__segname("_CODE"))
#define LABEL(n,s) static const char CONST n[]=s
#define NAME(n,s,k) LABEL(n##_label,s);LABEL(n##_key,k)
NAME(directory,"Dialing Directory","Alt-D");NAME(script,"Script Files","Alt-F5");
NAME(meta,"Meta Keys","Alt-M");NAME(history,"Redisplay","Alt-F6");
NAME(clear,"Clear Screen","Alt-C");NAME(linebreak,"Break Key","Alt-B");
NAME(elapsed,"Elapsed Time","Alt-T");NAME(chat,"Chat Mode","Alt-O");
NAME(host,"Host Mode","Alt-Q");NAME(answer,"Auto Answer","Alt-Y");
NAME(initialize,"Init Modem","Alt-J");NAME(reset,"Reset Terminal","Alt-U");
NAME(hangup,"Hang Up","Alt-H");NAME(exit,"Exit","Alt-X");
NAME(send,"Send Files","PgUp");NAME(receive,"Receive Files","PgDn");
NAME(capture,"Log File On/Off","Alt-F1");NAME(hold,"Log File Pause","Alt-F2");
NAME(snapshot,"Screen Snapshot","Alt-G");NAME(printer,"Printer On/Off","Alt-L");
NAME(record,"Record Mode","Alt-R");NAME(duplex,"Duplex Toggle","Alt-E");
NAME(crlf,"CR-CR/LF Toggle","Alt-F3");NAME(kermit,"Kermit Server Cmd","Alt-K");
NAME(pause,"Screen Pause","Alt-N");NAME(setup,"Setup Facility","Alt-S");
NAME(port,"Line/Port Setup","Alt-P");NAME(translate,"Translate Table","Alt-W");
NAME(mapping,"Key Mapping","Alt-F8");NAME(files,"File Directory","Alt-F");
NAME(cwd,"Change Directory","Alt-F7");NAME(viewfile,"View a File","Alt-V");
NAME(editor,"Editor","Alt-A");NAME(dos,"DOS Gateway","Alt-F4");
NAME(info,"Program Info","Alt-I");NAME(clipboard,"Clipboard","Alt-=");
NAME(monitor,"Monitor Mode","Ctrl-\\");NAME(status,"Toggle Status","Ctrl-]");
NAME(lines,"Toggle Lines","Ctrl--");
#define ITEM(n,k,r,c,a) {n##_label,n##_key,k,r,c,a}
#define UNAVAILABLE 255
static const reference_item CONST items[]={
 ITEM(directory,0x2000,4,0,255),ITEM(script,0x6c00,7,0,3),
 ITEM(meta,0x3200,8,0,255),ITEM(history,0x6d00,9,0,11),
 ITEM(clear,0x2e00,10,0,255),ITEM(linebreak,0x3000,11,0,10),
 ITEM(elapsed,0x1400,12,0,255),ITEM(chat,0x1800,14,0,255),
 ITEM(host,0x1000,15,0,255),ITEM(answer,0x1500,16,0,255),
 ITEM(initialize,0x2400,17,0,255),ITEM(reset,0x1600,18,0,255),
 ITEM(hangup,0x2300,4,1,9),ITEM(exit,0x2d00,5,1,7),
 ITEM(send,0x4900,7,1,1),ITEM(receive,0x5100,8,1,0),
 ITEM(capture,0x6800,9,1,4),ITEM(hold,0x6900,10,1,5),
 ITEM(snapshot,0x2200,11,1,2),ITEM(printer,0x2600,12,1,14),
 ITEM(record,0x1300,14,1,21),ITEM(duplex,0x1200,15,1,255),
 ITEM(crlf,0x6a00,16,1,6),ITEM(kermit,0x2500,17,1,255),
 ITEM(pause,0x3100,18,1,255),ITEM(setup,0x1f00,3,2,15),
 ITEM(port,0x1900,4,2,15),ITEM(translate,0x1100,5,2,17),
 ITEM(mapping,0x6f00,6,2,255),ITEM(files,0x2100,8,2,255),
 ITEM(cwd,0x6e00,9,2,255),ITEM(viewfile,0x2f00,10,2,255),
 ITEM(editor,0x1e00,11,2,255),ITEM(dos,0x6b00,12,2,255),
 ITEM(info,0x1700,13,2,20),ITEM(clipboard,0x8300,14,2,12),
 ITEM(monitor,0x2b1c,15,2,13),ITEM(status,0x1b1d,16,2,255),
 ITEM(lines,0x0c1f,17,2,255)};
#define COUNT (sizeof(items)/sizeof(items[0]))
LABEL(title,"P R O C O M M   P L U S   C O M M A N D   M E N U");
LABEL(communications,"COMMUNICATIONS");LABEL(setup_title,"SET UP");
LABEL(other,"OTHER FUNCTIONS");LABEL(before," BEFORE ");
LABEL(after," AFTER ");LABEL(during," DURING ");LABEL(other_group," OTHER ");
LABEL(footer,"Arrows/Tab: select  Enter: run  F1: help  `: command browser  Esc: return");
LABEL(dim,"Dim commands are unavailable. Assigned BBS page keys remain unchanged.");
LABEL(refused,"Not available in this build: ");
static word selected,refusal;
static word __far *view;
static word normalize(word key)
{
 if((key&255)==0xe0)key&=0xff00;
 if((key&255)==28)key=0x2b1c;
 else if((key&255)==29)key=0x1b1d;
 else if((key&255)==31)key=0x0c1f;
 return key;
}
unsigned __far __cdecl command_reference_unavailable(word key)
{
 word i;key=normalize(key);
 for(i=0;i<COUNT;++i)if(key==items[i].key)return items[i].action==UNAVAILABLE;
 return 0;
}
static word length(const char __far *s){word n=0;while(s[n])++n;return n;}
static void text(word at,const char __far *s,word attribute)
{while(*s && at<2000)view[at++]=attribute|(byte)*s++;}
static void rule(word row,word left,word right,word glyph)
{word i;for(i=left;i<=right;++i)view[row*80+i]=0x1f00|glyph;}
static void draw(void)
{
 word i,row,start,end,attribute,at;
 for(i=0;i<2000;++i)view[i]=0x0720;
 rule(1,1,78,205);rule(2,1,78,205);rule(19,1,78,205);
 for(row=2;row<19;++row){view[row*80+1]=view[row*80+78]=0x1fba;view[row*80+52]=0x1fba;}
 view[81]=0x1fc9;view[158]=0x1fbb;view[1521]=0x1fc8;view[1598]=0x1fbc;
 view[161]=0x1fcc;view[212]=0x1fcb;view[238]=0x1fb9;view[1572]=0x1fca;
 text(95,title,0x1f00);text(178,communications,0x1f00);text(222,setup_title,0x1f00);
 rule(3,3,51,196);text(249,before,0x1f00);text(276,after,0x1f00);
 rule(6,3,51,196);text(490,during,0x1f00);
 rule(13,3,51,196);text(1050,other_group,0x1f00);
 rule(7,52,78,205);view[612]=0x1fcc;view[638]=0x1fb9;text(617,other,0x1f00);
 for(i=0;i<COUNT;++i){
  row=items[i].row;start=items[i].column==0?3:items[i].column==1?28:54;end=start+23;
  attribute=i==selected?0x7000:items[i].action==UNAVAILABLE?0x0800:0x0700;
  for(at=start;at<=end;++at)view[row*80+at]=attribute|'.';
  text(row*80+start,items[i].label,attribute);
  text(row*80+end+1-length(items[i].shortcut),items[i].shortcut,attribute);
 }
 text(1762,footer,0x1f00);
 if(refusal){text(1842,refused,0x4f00);text(1870,items[selected].label,0x4f00);}
 else text(1842,dim,0x0700);
}
static void vertical(word down)
{
 word i,want=selected,best=255,delta,row=items[selected].row;
 for(i=0;i<COUNT;++i)if(i!=selected && items[i].column==items[selected].column){
  delta=down?(items[i].row+25-row)%25:(row+25-items[i].row)%25;
  if(delta<best){best=delta;want=i;}}
 selected=want;
}
static void horizontal(word right)
{
 word i,want=selected,best=255,delta,col=(items[selected].column+(right?1:2))%3;
 for(i=0;i<COUNT;++i)if(items[i].column==col){
  delta=items[i].row>items[selected].row?items[i].row-items[selected].row:items[selected].row-items[i].row;
  if(delta<best){best=delta;want=i;}}
 selected=want;
}
unsigned __far __cdecl command_reference_event(word event,word key,word __far *frame)
{
 word i;view=frame;
 if(!event){selected=refusal=0;key=normalize(key);
  for(i=0;i<COUNT;++i)if(key==items[i].key){selected=i;refusal=items[i].action==UNAVAILABLE;break;}
  draw();return 0;}
 if(event==2){draw();return 0;}
 if((key&255)==27 || key==0x2c00)return 1;
 if((key&255)=='`')return 0x200;
 key=normalize(key);
 refusal=0;
 if(key==0x4800)vertical(0);
 else if(key==0x5000)vertical(1);
 else if(key==0x4b00 || key==0x0f00)horizontal(0);
 else if(key==0x4d00 || (key&255)==9)horizontal(1);
 else if(key==0x4700 || key==0x4f00){
  for(i=0;i<COUNT;++i)if(items[i].column==items[selected].column &&
   (key==0x4700?items[i].row<items[selected].row:items[i].row>items[selected].row))selected=i;
 }else{
  if((key&255)!=13 && key!=0x3b00){
   for(i=0;i<COUNT && key!=items[i].key;++i){}
   if(i==COUNT){draw();return 0;}selected=i;
  }
  if(items[selected].action==UNAVAILABLE)refusal=1;
  else return (key==0x3b00?0x300:0x100)+items[selected].action;
 }
 draw();return 0;
}
