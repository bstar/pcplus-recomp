/* Foreground component. No UART, BIOS, direct video, dialing, writes or active
 * selection mutation. The command screen owner supplies its private frame.
 * Its empty history snapshot lends two far pages; the startup browser lends
 * near scratch. Both leases end before another screen owner can enter. */
#include "directory_view.h"
#include "../directory/directory_reader.h"
#ifdef TERMINAL_DIRECTORY_PREVIEW
#include "../terminal/directory_preview.h"
#endif
#ifdef TERMINAL_DIRECTORY_RESOURCE_OWNER
#include "../terminal/directory_resource_owner.h"
static unsigned resource_notice;
#endif
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
#ifdef TERMINAL_DIRECTORY_PREVIEW
#define PROPOSAL ((directory_selection_proposal __far *)(redisplay_snapshot+2788))
#define PREPARING 5
#define PREVIEW 6
#define REJECTED 7
static word preview_status;
#endif
#define CONST __based(__segname("_CODE"))
#define TEXT(n,s) static const char CONST n[]=s
TEXT(title,"PCPLUS // DIALING DIRECTORY");
TEXT(file_label,"File: ");
TEXT(columns,"No.   Name                        Number");
TEXT(prompt,"Enter: open directory  Backspace: edit  Esc: return");
TEXT(loading,"Reading directory... serial input continues. Esc: cancel");
#ifdef TERMINAL_DIRECTORY_PREVIEW
TEXT(keys,"Arrows/PgUp/PgDn/Home/End: browse  Enter: preview  F2: file  Esc: return");
#else
TEXT(keys,"Arrows PgUp/PgDn Home/End: browse  F2: file  F5: reload  Esc: return");
#endif
TEXT(read_only,"Read-only view. The current target and connection are retained.");
TEXT(closing,"Closing directory... returning to the current session.");
TEXT(failed,"Could not load the directory. F2 changes the file; Esc returns.");
TEXT(uncertain,"Close uncertain. Directory loading is held until the session ends.");
TEXT(codes,"Status:       DOS:       Close:");
TEXT(default_path,"PCPLUS.DIR");
#ifdef TERMINAL_DIRECTORY_PREVIEW
TEXT(preparing,"Checking the selected entry...");
TEXT(preview_title,"SELECTED ENTRY // PROPOSED SETTINGS");
TEXT(name_label,"Name: ");
TEXT(target_label,"Target: ");
TEXT(mode_label,"Connection: ");
TEXT(modem_label,"MODEM");
TEXT(direct_label,"DIRECT");
TEXT(serial_label,"Port: COM    IRQ:     I/O: ");
TEXT(baud_label,"DTE speed: ");
TEXT(rate115200,"115200");
TEXT(line_label,"Data:    Parity:    Stop: ");
TEXT(flow_label,"Flow: ");
TEXT(hard_label,"RTS/CTS");
TEXT(soft_label,"XON/XOFF");
TEXT(none_label,"NONE");
TEXT(profile_label,"Terminal profile: ");
TEXT(protocol_label,"Saved transfer protocol: ");
TEXT(download_label,"Download path: ");
TEXT(auto_label,"Automatic download: ");
TEXT(on_label,"ON");
TEXT(off_label,"OFF");
#ifdef TERMINAL_DIRECTORY_RESOURCE_OWNER
#ifdef DIRECTORY_SCRIPT_RESOURCES
TEXT(preview_keys,"R: check resources/script  Esc: directory. Settings unchanged.");
#else
#ifdef DIRECTORY_TRANSLATION_RESOURCES
TEXT(preview_keys,"R: check KEY/KBD/XLT resources  Esc: directory. Settings have not been applied.");
#else
TEXT(preview_keys,"R: check KEY/KBD resources  Esc: directory. Settings have not been applied.");
#endif
#endif
TEXT(resource_busy,"Resource check unavailable. Disconnect first or release other owners.");
#else
TEXT(preview_keys,"Preview only. Settings have not been applied. Esc: directory");
#endif
TEXT(rejected,"This entry could not be prepared. Settings have not been applied.");
TEXT(baseline_error,"Accepted PRM settings unavailable. Load valid settings before previewing.");
TEXT(capture_error,"The current session could not be captured.");
TEXT(page_error,"The selected entry is outside the published directory page.");
TEXT(argument_error,"A path is empty/over63 bytes, or the preview arguments are invalid.");
TEXT(transfer_error,"The saved download directory is invalid.");
TEXT(serial_error,"The selected serial settings or terminal profile are invalid.");
TEXT(modem_error,"The saved modem commands or responses are invalid.");
TEXT(record_error,"The selected directory record contains an unterminated field.");
TEXT(binding_error,"The saved script, keyboard or macro name is unsupported.");
TEXT(target_error,"The selected dialing target is empty or invalid.");
TEXT(mode_error,"The saved connection mode is unsupported.");
TEXT(duplex_error,"The saved half-duplex setting is unsupported.");
TEXT(active_error,"The current session's serial configuration is invalid.");
#endif
static byte character(byte c){return c<32 || c==127?'.':c;}
static void text(word at,const char __far *p,word attribute)
{while(*p && at<2000)view[at++]=attribute|(byte)*p++;}
static void number(word at,word value,word attribute)
{char digits[5];word n=0;do{digits[n++]=(char)('0'+value%10);value/=10;}while(value);
 while(n)view[at++]=attribute|(byte)digits[--n];}
static void field(word at,const byte __far *p,word length,word attribute)
{word i,ended=0;byte c;for(i=0;i<length;++i){c=p[i];if(!c)ended=1;view[at+i]=attribute|(ended?' ':character(c));}}
#ifdef TERMINAL_DIRECTORY_PREVIEW
static void hex(word at,word value)
{word i,c;for(i=0;i<4;++i){c=(value>>((3-i)*4))&15;view[at+i]=0x0700|(c<10?'0'+c:'A'+c-10);}}
static void proposal_draw(void)
{
 word status=preview_status&15,detail=(preview_status>>8)&15;
 const terminal_import_settings __far *serial=&PROPOSAL->configuration.serial;
#ifdef TERMINAL_DIRECTORY_RESOURCE_OWNER
 if(resource_notice)text(22*80+2,resource_busy,0x0700);
#endif
 if(phase==PREPARING){text(402,preparing,0x0700);return;}
 if(phase==REJECTED){
  text(322,rejected,0x0f00);
  if(preview_status&0x1000)text(482,baseline_error,0x0700);
  else if(preview_status&0x2000)text(482,capture_error,0x0700);
  else if(status==DIRECTORY_SELECTION_ARGUMENT)text(482,argument_error,0x0700);
  else if(status==DIRECTORY_SELECTION_PAGE)text(482,page_error,0x0700);
  else if(status==DIRECTORY_SELECTION_TRANSFER)text(482,transfer_error,0x0700);
  else if((preview_status&0xf0)==0x50)text(482,active_error,0x0700);
  else if(detail==DIRECTORY_LIVE_SERIAL)text(482,serial_error,0x0700);
  else if(detail==DIRECTORY_LIVE_MODEM)text(482,modem_error,0x0700);
  else if(detail==DIRECTORY_LIVE_RECORD)text(482,record_error,0x0700);
  else if(detail==DIRECTORY_LIVE_BINDING)text(482,binding_error,0x0700);
  else if(detail==DIRECTORY_LIVE_TARGET)text(482,target_error,0x0700);
  else if(detail==DIRECTORY_LIVE_MODE)text(482,mode_error,0x0700);
  else if(detail==DIRECTORY_LIVE_DUPLEX)text(482,duplex_error,0x0700);
  text(1921,preview_keys,0x1f00);return;
 }
 text(242,preview_title,0x1f00);
 text(322,name_label,0x0700);field(330,PROPOSAL->configuration.directory.name,24,0x0f00);
 text(482,target_label,0x0700);field(490,PROPOSAL->configuration.directory.target,63,0x0f00);
 text(642,mode_label,0x0700);
 if(PROPOSAL->configuration.directory.dialing_mode)text(654,direct_label,0x0700);
 else text(654,modem_label,0x0700);
 text(802,serial_label,0x0700);number(811,serial->port_number,0x0700);
 number(819,serial->irq,0x0700);hex(828,serial->io_base);
 text(962,baud_label,0x0700);
 if(serial->baud_high)text(973,rate115200,0x0700);else number(973,serial->baud_low,0x0700);
 text(1002,line_label,0x0700);number(1008,serial->data_bits,0x0700);
 view[1019]=0x0700|(byte)(serial->parity==0?'N':serial->parity==1?'O':serial->parity==2?'E':serial->parity==3?'M':'S');
 number(1027,serial->stop_bits,0x0700);
 text(1122,flow_label,0x0700);
 if(serial->hardware_flow)text(1128,hard_label,0x0700);
 if(serial->software_flow)text(1140,soft_label,0x0700);
 if(!serial->hardware_flow && !serial->software_flow)text(1128,none_label,0x0700);
 text(1282,profile_label,0x0700);number(1300,serial->terminal_id,0x0700);
 text(1362,protocol_label,0x0700);number(1387,PROPOSAL->configuration.directory.protocol_index,0x0700);
 text(1522,download_label,0x0700);field(1537,(const byte __far *)PROPOSAL->transfer.download_directory,63,0x0700);
 text(1682,auto_label,0x0700);
 if(PROPOSAL->transfer.auto_download)text(1702,on_label,0x0700);else text(1702,off_label,0x0700);
 text(1921,preview_keys,0x1f00);
}
#endif
static void draw(void)
{
 word i,row,entry,attribute;
 const byte __far *record;
 for(i=0;i<2000;++i)view[i]=0x0720;
 for(i=0;i<80;++i)view[i]=view[1920+i]=0x1f20;
 text(2,title,0x1f00);text(162,file_label,0x0700);
 for(i=0;i<size && i<72;++i)view[168+i]=0x0700|character((byte)path[i]);
#ifdef TERMINAL_DIRECTORY_PREVIEW
 if(phase>=PREPARING){proposal_draw();return;}
#endif
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
#ifdef TERMINAL_DIRECTORY_PREVIEW
  if(phase==PREPARING){preview_status=directory_preview_stage(PAGE,selected+1,path,PROPOSAL);
#ifdef TERMINAL_DIRECTORY_RESOURCE_OWNER
   resource_notice=0;
#endif
   phase=preview_status?REJECTED:PREVIEW;draw();return 1;}
#endif
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
#ifdef TERMINAL_DIRECTORY_PREVIEW
  if(phase>=PREPARING){phase=READY;draw();return 1;}
#endif
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
#ifdef TERMINAL_DIRECTORY_PREVIEW
#ifdef TERMINAL_DIRECTORY_RESOURCE_OWNER
 if(phase==PREVIEW && (c=='r' || c=='R')){
  resource_notice=terminal_directory_resources_queue(PROPOSAL);
  if(!resource_notice){active=0;return 0;}
  draw();return 1;
 }
#endif
 if(phase>=PREPARING)return 1;
 if(c==13){phase=PREPARING;draw();return 1;}
#endif
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
