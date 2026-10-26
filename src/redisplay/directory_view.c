/* Foreground component. No UART, BIOS, direct video, dialing, writes or active
 * selection mutation. The command screen owner supplies its private frame.
 * Its empty history snapshot lends two far pages; the startup browser lends
 * near scratch. Both leases end before another screen owner can enter. */
#include "directory_view.h"
#include "../directory/directory_reader.h"
typedef unsigned short word;
typedef unsigned char byte;
extern byte __far redisplay_snapshot[63000];
extern byte directory_view_scratch[512];
extern char terminal_directory_path[64];
extern word terminal_directory_entry;
extern byte terminal_browser_screen_owned,terminal_editor_screen_owned;
#pragma aux redisplay_snapshot "redisplay_snapshot";
#pragma aux terminal_directory_path "terminal_directory_path";
#pragma aux terminal_directory_entry "terminal_directory_entry";
#pragma aux terminal_browser_screen_owned "terminal_browser_screen_owned";
#pragma aux terminal_editor_screen_owned "terminal_editor_screen_owned";
static directory_reader reader;
static char path[128];
static word size,selected,phase,active,last_status;
static word __far *view;
#define STAGE ((directory_dos_page_data __far *)redisplay_snapshot)
#define PAGE ((directory_dos_page_data __far *)(redisplay_snapshot+1394))
enum {PATH=0,LOADING,READY,ERROR,CANCELING};
#define CONST __based(__segname("_CODE"))
#define TEXT(n,s) static const char CONST n[]=s
TEXT(title,"PCPLUS // DIALING DIRECTORY");
TEXT(file_label,"File: ");
TEXT(columns,"No.   Name                        Number");
TEXT(prompt,"Enter: open directory  Backspace: edit  Esc: return");
TEXT(loading,"Reading directory... serial input continues. Esc: cancel");
TEXT(keys,"Arrows PgUp/PgDn Home/End: browse  F2: file  F5: reload  Esc: return");
TEXT(read_only,"Read-only view. The current target and connection are retained.");
TEXT(closing,"Closing directory... returning to the current session.");
TEXT(failed,"Could not load the directory. F2 changes the file; Esc returns.");
TEXT(uncertain,"Close uncertain. Directory loading is held until the session ends.");
TEXT(codes,"Status:       DOS:       Close:");
TEXT(default_path,"PCPLUS.DIR");
static byte character(byte c){return c<32 || c==127?'.':c;}
static void text(word at,const char __far *p,word attribute)
{while(*p && at<2000)view[at++]=attribute|(byte)*p++;}
static void number(word at,word value,word attribute)
{char digits[5];word n=0;do{digits[n++]=(char)('0'+value%10);value/=10;}while(value);
 while(n)view[at++]=attribute|(byte)digits[--n];}
static void field(word at,const byte __far *p,word length,word attribute)
{word i,ended=0;byte c;for(i=0;i<length;++i){c=p[i];if(!c)ended=1;view[at+i]=attribute|(ended?' ':character(c));}}
static void draw(void)
{
 word i,row,entry,attribute;
 const byte __far *record;
 for(i=0;i<2000;++i)view[i]=0x0720;
 for(i=0;i<80;++i)view[i]=view[1920+i]=0x1f20;
 text(2,title,0x1f00);text(162,file_label,0x0700);
 for(i=0;i<size && i<72;++i)view[168+i]=0x0700|character((byte)path[i]);
 if(phase==PATH){text(1921,prompt,0x1f00);return;}
 if(phase==LOADING){text(402,loading,0x0700);number(562,reader.bytes_processed,0x0700);return;}
 if(phase==CANCELING){text(402,closing,0x0700);return;}
 if(phase==ERROR){
  /* Keep each based code-string conversion explicit. A conditional array
   * expression loses the code-segment provenance in this small-model ABI. */
  if(reader.phase==DIRECTORY_READER_RECOVERY)text(402,uncertain,0x0f00);
  else text(402,failed,0x0f00);
  text(562,codes,0x0700);number(570,last_status,0x0700);number(582,reader.dos_error,0x0700);number(594,reader.close_error,0x0700);
  text(1921,keys,0x1f00);return;}
 text(242,columns,0x1f00);
 for(row=0;row<PAGE->count && row<10;++row){entry=PAGE->first_entry+row;
  attribute=entry==selected+1?0x7000:0x0700;
  for(i=0;i<76;++i)view[(row+4)*80+2+i]=attribute|' ';
  number((row+4)*80+2,entry,attribute);record=PAGE->records[row];
  field((row+4)*80+8,record,24,attribute);field((row+4)*80+36,record+25,20,attribute);
 }
 text(1762,read_only,0x0700);text(1921,keys,0x1f00);
}
static void begin(void)
{
 word status;
 if(terminal_browser_screen_owned || terminal_editor_screen_owned){last_status=DIRECTORY_READER_BUSY;phase=ERROR;draw();return;}
 status=directory_reader_initialize(&reader);
 if(!status)status=directory_reader_begin(&reader,path,(selected/10)*10+1,STAGE,PAGE,directory_view_scratch);
 last_status=status;phase=status==DIRECTORY_READER_PENDING?LOADING:ERROR;draw();
}
static void stop(void)
{
 if(reader.handle_open && reader.phase!=DIRECTORY_READER_RECOVERY){
  directory_reader_cancel(&reader);directory_reader_step(&reader);
 }
 active=0;
}
unsigned __far __cdecl directory_view_event(word event,word key,word __far *frame)
{
 word i,next,status;byte c=(byte)key;
 if(event==0){
  view=frame;active=1;phase=PATH;selected=0;last_status=reader.status;
  if(terminal_directory_entry>=1 && terminal_directory_entry<=200)selected=terminal_directory_entry-1;
  for(size=0;size<63 && terminal_directory_path[size];++size)path[size]=terminal_directory_path[size];
  if(!size){for(i=0;default_path[i];++i)path[size++]=default_path[i];}path[size]=0;
  if(reader.phase==DIRECTORY_READER_RECOVERY)phase=ERROR;
  draw();return 1;
 }
 if(event==4){stop();return 0;}
 if(!active)return 0;
 if(event==2){draw();return 1;}
 if(event==3){
  if(phase!=LOADING && phase!=CANCELING)return 1;
  status=directory_reader_step(&reader);
  if(status!=DIRECTORY_READER_PENDING){
   if(phase==CANCELING){active=0;return 0;}
   last_status=status;phase=status?ERROR:READY;
  }
  draw();return 1;
 }
 if(event!=1)return 1;
 if(c==27){
  if(phase==LOADING || phase==CANCELING){directory_reader_cancel(&reader);phase=CANCELING;draw();return 1;}
  active=0;return 0;
 }
 if(phase==LOADING || phase==CANCELING)return 1;
 if(key==0x3c00){if(reader.phase!=DIRECTORY_READER_RECOVERY)phase=PATH;draw();return 1;}
 if(phase==PATH){
  if(c==13){if(size)begin();return 1;}
  if(c==8){if(size)path[--size]=0;}
  else if(c>=32 && c<127 && size<127){path[size++]=c;path[size]=0;}
  draw();return 1;
 }
 if(phase==ERROR)return 1;
 if(key==0x3f00){begin();return 1;}
 if((key&255)==0xe0)key&=0xff00;
 next=selected;
 if(key==0x4800){if(next)--next;}
 else if(key==0x5000){if(next<199)++next;}
 else if(key==0x4900)next=next<10?0:next-10;
 else if(key==0x5100)next=next>189?199:next+10;
 else if(key==0x4700)next=0;
 else if(key==0x4f00)next=199;
 else return 1;
 if(next!=selected){selected=next;
  if(selected+1<PAGE->first_entry || selected+1>=PAGE->first_entry+PAGE->count){begin();return 1;}
 }
 draw();return 1;
}
