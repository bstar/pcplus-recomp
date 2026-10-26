/* Source-owned command menu and contextual help for the maintained terminal.
 * Code-segment constants keep UI prose outside the small-model DGROUP and
 * ahead of uninitialized far buffers. See Watcom's segment-constant objects. */
#include "command_menu.h"
#ifdef TERMINAL_REFERENCE
#include "command_reference.h"
static unsigned reference_origin;
#endif
#include "../recording/foreground.h"
extern unsigned __far __cdecl recording_ui_ready(void);
typedef unsigned short word;
typedef unsigned char byte;
typedef struct item { const char __far *name;const char __far *help;word category,key,letter; } item;
unsigned command_menu_active=0,command_menu_action=0;
static word category,selected,phase,query_size,notice;
char command_menu_script[64];
#define query command_menu_script
static word __far *view;
#define MENU_TEXT __based(__segname("_CODE"))
#define TEXT(n,s) static const char MENU_TEXT n[]=s
#define ENTRY(n,t,h) TEXT(n##_name,t);TEXT(n##_help,h)
#ifdef TERMINAL_REFERENCE
#define TABLE_KEY 0xf700
#define REDIAL_KEY 0xf600
#define TABLE_LABEL "Edit input table               Alt-W"
#define USING_FIRST "Alt-Z opens the command reference; ` opens this browser.\n"
#else
#define TABLE_KEY 0x6f00
#define REDIAL_KEY 0x2000
#define TABLE_LABEL "Edit input table               Alt-F8"
#define USING_FIRST "Alt-Z opens this menu. Left/Right or Tab changes the menu group.\n"
#endif
#ifdef TERMINAL_ORIGINAL_KEYS
#define RECEIVE_KEY 0xfa00
#define SEND_KEY 0xf900
#define RECEIVE_LABEL "Receive files                  PgDn*"
#define SEND_LABEL "Send files                     PgUp*"
#define RECORD_SUFFIX "  Alt-R"
#define SETTINGS_LABEL "Edit saved settings            Alt-S/P"
#define HISTORY_LABEL "Redisplay history              Alt-F6"
#define PAGE_HELP "\n* An assigned page key sends its keyboard-profile binding.\nUnassigned enhanced PgUp/PgDn opens local send/receive."
#else
#define RECEIVE_KEY 0x1300
#define SEND_KEY 0x1f00
#define RECEIVE_LABEL "Receive files                  Alt-R"
#define SEND_LABEL "Send files                     Alt-S"
#define RECORD_SUFFIX ""
#define SETTINGS_LABEL "Edit saved settings            Alt-F10"
#define HISTORY_LABEL "Redisplay history              Ctrl-PgUp"
#define PAGE_HELP ""
#endif
ENTRY(record,"Record / save ASPECT script" RECORD_SUFFIX,
 "Start a checked .ASP recording of prompts and bytes accepted by the UART.\n"
 "Existing files require Y before replacement; the original stays intact\n"
 "until save succeeds. Choose this command again to save. Output must\n"
 "finish first. Transfers, scripts, editors and modem changes require\n"
 "saving or canceling the recording. Exit cancels unpublished recording.");
ENTRY(cancel_record,"Cancel ASPECT recording",
 "Discard the current unpublished recording after confirmation. Already\n"
 "sent serial bytes cannot be recalled. An original target is preserved.\n"
 "Uncertain closes and failed restoration retain files for recovery.");
ENTRY(record_files,"Recording status / recovery",
 "Show the fixed target and any retained temporary or original backup.\n"
 "U offers explicit cleanup of safely owned temporary files. An original\n"
 "backup from failed restoration is never discarded here. End the session\n"
 "and recover it from DOS if necessary. Do not overwrite retained originals.");
ENTRY(receive,RECEIVE_LABEL,
 "Receive into a local DOS file with XMODEM. F2 in the filename prompt\n"
 "selects YMODEM; enter a destination directory for a batch. Request the\n"
 "download at the BBS first. HARD or NONE flow is required. XMODEM may\n"
 "retain SUB padding; YMODEM preserves each declared file length." PAGE_HELP);
ENTRY(send,SEND_LABEL,
 "Choose a local DOS file to send with XMODEM/1K. F2 selects YMODEM;\n"
 "enter a DOS file pattern for a batch. Start the BBS upload first.\n"
 "Sources are opened read-only. A transfer owns the local keyboard\n"
 "until it completes or is canceled; menu keys are not protocol data." PAGE_HELP);
ENTRY(snapshot,"Write screen                   Alt-G",
 "Append the current 80 by 25 text screen to PCPLUS.SCR. This is a\n"
 "character snapshot, not a graphics image. File errors are reported;\n"
 "a partial append can remain. Active file owners must use distinct paths.");
ENTRY(capture,"Open / close capture           Alt-F1",
 "Choose a text-capture path; Enter accepts the default PCPLUS.LOG.\n"
 "This appends incoming text, or closes an already open capture.\n"
 "Alt-F2 holds or resumes capture. Incoming data and terminal replies\n"
 "continue while the menu is open. PROGRAM closes capture before DOS\n"
 "child execution. Check the file after a write or close error.");
ENTRY(hold,"Hold / resume capture          Alt-F2",
 "Hold or resume an already open processed-text capture. A held log\n"
 "does not receive new text. This command does not open a log; use\n"
 "Open / close capture first.");
ENTRY(crlf,"Toggle CR adds LF              Alt-F3",
 "Toggle CR-adds-LF for the terminal display and processed text capture.\n"
 "Binary transfer and clipboard packet bytes remain controlled by\n"
 "their own protocols and separator settings.");
ENTRY(exit,"Exit to DOS                    Alt-X",
 "End the session and return to DOS. The terminal closes its file\n"
 "owners and restores the UART, interrupt vectors and display state.\n"
 "You can also press Alt-X directly from this menu or its help pages.");
ENTRY(redial,"Dial selected target           Alt-D",
 "Start the explicitly selected modem or directory target when the\n"
 "line is idle. The current target comes from startup /D or /N, or\n"
 "the startup dialing directory browser. This does not open a new\n"
 "directory browser and does not interrupt an active connection.");
ENTRY(hangup,"Hang up                        Alt-H",
 "Cancel dialing or hang up the current modem connection using the\n"
 "configured method. DTR and modem commands follow the selected\n"
 "connection plan. This does not choose a different directory entry.");
ENTRY(linebreak,"Send BREAK                     Alt-B",
 "Drain outgoing bytes, hold UART BREAK for the configured interval,\n"
 "then release it while continuing to service received data.\n"
 "The pulse is a serial-line condition, not a transmitted character.\n"
 "Its physical timing requires verification on the target UART.");
ENTRY(history,HISTORY_LABEL,
 "Browse a frozen snapshot of up to 63,000 history characters.\n"
 "Use arrows, PgUp/PgDn and Home/End; / searches and F3 repeats.\n"
 "W appends history to a DOS file; C opens the filename clipboard.\n"
 "Incoming data continues. Escape restores the updated live screen.");
ENTRY(clipboard,"Filename clipboard             Alt-=",
 "Keep up to 15 filenames. A adds, E edits, D deletes, U purges;\n"
 "Space tags and C extracts names from the screen. P pastes all,\n"
 "S sends one and T sends tagged names. R changes the separator.\n"
 "Single removes a name after UART delivery, not remote confirmation.");
ENTRY(monitor,"Raw monitor                    Ctrl-\\",
 "View incoming raw byte values without normal terminal parsing.\n"
 "The monitor asks before replacing PCPLUS.DMP; decline for view only.\n"
 "Its keyboard and file ownership exclude nested local windows.\n"
 "Use Escape to return to ordinary terminal processing.");
ENTRY(printer,"Open / close printer copy      Alt-L",
 "Toggle a checked processed-text copy to DOS PRN. The bounded queue\n"
 "reports printer stalls and write failures. Device readiness in an\n"
 "emulator does not establish physical printer compatibility.");
ENTRY(settings,SETTINGS_LABEL,
 "Open source-built PRMEDIT for the explicitly selected current-folder\n"
 "8.3 PRM leaf. An eligible idle session can adopt validated changes\n"
 "after returning; serial/profile changes require confirmation.\n"
 "The menu does not create a complete factory configuration.");
ENTRY(reload,"Reload input table             Alt-F9",
 "Reload the selected input translation table from its absolute path.\n"
 "The file must contain exactly 256 bytes. Y accepts a checked stage;\n"
 "other answers keep the active table. Queued input uses the new table.\n"
 "Only table mode is eligible. Capture closes during the UART handoff.\n"
 "Editing a file does not silently replace its active in-memory table.");
ENTRY(table,TABLE_LABEL,
 "Open XLTEDIT beside this terminal's executable for the selected table.\n"
 "The absolute table source stays fixed across directory changes.\n"
 "F1 saves changes; Escape returns. Y then applies a checked snapshot;\n"
 "other answers retain the active table. Only table mode is eligible.\n"
 "Capture closes while the UART and interrupt belong to the editor.");
ENTRY(script,"Run script",
 "Run a compiled ASPECT script from a local DOS file.\n"
 "Enter a DOS 8.3 path; Escape cancels. The script temporarily owns\n"
 "the current port. Capture closes; the terminal restores its screen\n"
 "and received data after the script returns. Connected scripts resume\n"
 "automatically on success. Offline scripts/errors wait for a key.");
ENTRY(using,"Using the command menu",
 USING_FIRST
 "Up/Down or Home/End selects a command; a listed letter runs it.\n"
 "Enter also runs the selected command. F1 shows contextual help.\n"
 "/ finds text in command names and help. Escape returns one level.\n"
 "Incoming BBS data continues while these windows are open.");
ENTRY(keys,"Keyboard and session commands",
 "Local Alt commands control this terminal; they are not BBS input.\n"
 "Ordinary function and cursor keys use the selected keyboard profile.\n"
 "Alt-1 through Alt-0 run configured TEXT or PROGRAM meta actions.\n"
 "A running macro, child program, monitor or transfer owns its keys.\n"
 "Close this menu before typing ordinary commands to the BBS.");
ENTRY(scope,"Application status",
 "This maintained source-built terminal is still being reconstructed.\n"
 "The menu exposes implemented commands and source-owned help.\n"
 "Other emulations, Host, additional transfer protocols and\n"
 "complete original menus/settings remain under development.\n"
 "Loopback BBS tests do not replace physical UART/modem validation.");
#define ROW(n,c,k,l) {n##_name,n##_help,c,k,l}
static const item MENU_TEXT items[]={
 ROW(receive,0,RECEIVE_KEY,'R'),ROW(send,0,SEND_KEY,'S'),ROW(snapshot,0,0x2200,'W'),
 ROW(script,0,0xfe00,'A'),ROW(capture,0,0x6800,'O'),ROW(hold,0,0x6900,'H'),ROW(crlf,0,0x6a00,'T'),ROW(exit,0,0x2d00,'X'),
 ROW(redial,1,REDIAL_KEY,'D'),ROW(hangup,1,0x2300,'H'),ROW(linebreak,1,0x3000,'B'),
 ROW(history,2,0x8400,'R'),ROW(clipboard,2,0x8300,'F'),ROW(monitor,2,0x2b1c,'M'),ROW(printer,2,0x2600,'P'),
 ROW(settings,3,0x7100,'E'),ROW(reload,3,0x7000,'R'),ROW(table,3,TABLE_KEY,'T'),ROW(using,4,0,'U'),ROW(keys,4,0,'K'),ROW(scope,4,0,'A'),
 ROW(record,0,0xfd00,'C'),ROW(cancel_record,0,0xfc00,'D'),ROW(record_files,0,0xfb00,'F')};
#define COUNT (sizeof(items)/sizeof(items[0]))
static const char MENU_TEXT categories[][12]={"File","Connection","View","Setup","Help"};
TEXT(title,"PCPLUS  Command Menu");
TEXT(footer,"Left/Right Tab: group  Up/Down: select  Enter: run  F1: help  /: find  Esc");
TEXT(help_footer,"Up/Down PgUp/PgDn: topic  /: find  Esc: command menu  Alt-X: exit");
TEXT(find_footer,"Find command/help text: Enter searches from the next topic; Esc cancels.");
TEXT(no_match,"No matching topic. / changes the search; arrows select a command.");
TEXT(find_label,"Find: ");
TEXT(script_label,"Script DOS 8.3 path: ");
TEXT(script_footer,"Enter: run script  Escape: cancel  Backspace: edit");
TEXT(record_title,"ASPECT Recorder");
TEXT(record_path_label,"Recording file: DOS 8.3 path ending in .ASP");
TEXT(record_path_footer,"Enter: start  Escape: cancel  Backspace: edit");
TEXT(replace_question,"This destination exists. Replace it when recording is saved? Y/N");
TEXT(cancel_question,"Discard the unpublished recording? Y/N");
TEXT(clean_question,"Discard owned scratch / remove a saved backup? Y/N");
TEXT(record_footer,"Esc: command menu   U: cleanup retained temporary files");
TEXT(record_saved,"Recording saved.");
TEXT(record_cancelled,"Recording canceled; original destination preserved.");
TEXT(record_busy,"Output, held input or another operation is pending. Try again when idle.");
TEXT(record_owned,"Save or cancel recording before changing the serial byte owner.");
TEXT(record_error,"Recording operation failed. Retained files are listed below.");
TEXT(record_bad_path,"Choose a writable DOS 8.3 .ASP path; no devices or wildcards.");
TEXT(record_cleaned,"Temporary files cleaned. Original error details remain below.");
TEXT(record_active,"Recording active. Esc returns to the BBS; File/C saves, File/D cancels.");
TEXT(record_idle,"No active recording.");
TEXT(record_target,"Target:");TEXT(record_stage,"Owned scratch:");TEXT(record_backup,"Original backup:");
TEXT(record_original,"Original backup retained: recover from DOS after ending the session.");
TEXT(record_uncertain,"Close uncertain: retained files cannot be cleaned in this session.");
TEXT(record_codes,"Status:       DOS:       Close:       Restore:");
static byte fold(byte c){return c>='a' && c<='z'?c-32:c;}
static void text(word at,const char __far *s,word attr)
{while(*s && at<2000)view[at++]=attr|(byte)*s++;}
static void prose(word at,const char __far *s)
{word col=0;byte c;while((c=*s++)!=0 && at<1840){if(c==10){at+=80-col;col=0;}else{view[at++]=0x0700|c;if(++col==76){at+=4;col=0;}}}}
static void near_text(word at,const char *s,word count)
{word i;for(i=0;i<count && s[i] && at<1840;++i)view[at++]=0x0700|(byte)s[i];}
static void owned_path(word at,const recording_file *r,const char *leaf)
{word n=r->directory_length;if(n>115)n=115;near_text(at,r->target,n);near_text(at+n,leaf,12);}
static void record_number(word at,word value)
{char digits[5];word n=0;do{digits[n++]=(char)('0'+value%10);value/=10;}while(value);while(n)view[at++]=0x0700|(byte)digits[--n];}
static word record_start(word mode)
{
 word status;
 if(!recording_ui_ready()){notice=103;phase=6;return 1;}
 status=recording_terminal_begin(mode,30);
 if(!status){command_menu_active=0;return 0;}
 phase=status==RF_CONFLICT && mode==RF_NEW?5:6;notice=status;return 1;
}
static word record_blocked(word key)
{
 const recording_file *r=recording_terminal_inspect();
 if(!r || !r->claimed)return 0;
 return key==RECEIVE_KEY || key==SEND_KEY || key==0xfe00 || key==REDIAL_KEY || key==0x2300 ||
  key==0x3000 || key==0x2b1c || key==0x7100 || key==0x7000 || key==TABLE_KEY;
}
static void record_view(void)
{
 const recording_file *r=recording_terminal_inspect();word i;
 for(i=320;i<1920;++i)view[i]=0x0720;
 text(402,record_title,0x1f00);
 if(phase==4){text(562,record_path_label,0x0700);near_text(722,recording_terminal_path,63);text(1921,record_path_footer,0x1f00);return;}
 if(phase==5)text(562,replace_question,0x0f00);
 else if(phase==7)text(562,cancel_question,0x0f00);
 else if(phase==8)text(562,clean_question,0x0f00);
 else if(notice==101)text(562,record_saved,0x0f00);
 else if(notice==102)text(562,record_cancelled,0x0f00);
 else if(notice==103)text(562,record_busy,0x0f00);
 else if(notice==104)text(562,record_owned,0x0f00);
 else if(notice==105)text(562,record_cleaned,0x0f00);
 else if(notice==RF_ARGUMENT)text(562,record_bad_path,0x0f00);
 else if(notice)text(562,record_error,0x0f00);
 else if(r && r->state==RF_RECORDING)text(562,record_active,0x0700);
 else text(562,record_idle,0x0700);
 if(r){if(r->status){text(722,record_codes,0x0700);record_number(730,r->status);record_number(742,r->dos_error);
   record_number(754,r->close_error);record_number(772,r->restore_error);}
  text(802,record_target,0x0700);near_text(882,r->target,128);
  if(r->stage_owned){text(1122,record_stage,0x0700);owned_path(1202,r,r->stage);}
  if(r->backup_owned){text(1442,record_backup,0x0700);owned_path(1522,r,r->backup);}
  if(r->backup_owned && !r->published)text(1762,record_original,0x0f00);
  else if(r->handle_state==2)text(1762,record_uncertain,0x0f00);
 }
 text(1921,record_footer,0x1f00);
}
static void draw(void)
{
 word i,n=0,at;
#ifdef TERMINAL_REFERENCE
 if(phase==9){command_reference_event(2,0,view);return;}
#endif
 for(i=0;i<2000;++i)view[i]=0x0720;
 for(i=0;i<80;++i)view[i]=view[1920+i]=0x1f20;
 text(1,title,0x1f00);
 for(i=0;i<5;++i)text(162+i*15,categories[i],i==category?0x7000:0x1f00);
 if(phase>=4){record_view();return;}
 if(phase==1){text(402,items[selected].name,0x1f00);prose(562,items[selected].help);text(1921,help_footer,0x1f00);}
 else{
  for(i=0;i<COUNT;++i)if(items[i].category==category){
   at=402+n++*80;view[at]=0x1f00|items[i].letter;view[at+1]=0x1f00|')';
   text(at+3,items[i].name,i==selected?0x7000:0x0700);
  }
  if(notice)text(1921,no_match,0x1f00);else text(1921,footer,0x1f00);
 }
 if(phase==2 || phase==3){for(i=1760;i<1840;++i)view[i]=0x1f20;
  if(phase==3)text(1762,script_label,0x1f00);else text(1762,find_label,0x1f00);
  for(i=0;i<query_size;++i)view[(phase==3?1782:1768)+i]=0x1f00|(byte)query[i];
  for(i=1920;i<2000;++i)view[i]=0x1f20;
  if(phase==3)text(1921,script_footer,0x1f00);else text(1921,find_footer,0x1f00);}
}
static word matches(const char __far *s)
{
 word i;while(*s){for(i=0;i<query_size && s[i] && fold((byte)s[i])==fold((byte)query[i]);++i){}
  if(i==query_size)return 1;++s;}return 0;
}
static void search(void)
{
 word n,i=selected;notice=0;if(!query_size)return;
 for(n=0;n<COUNT;++n){if(++i==COUNT)i=0;if(matches(items[i].name)||matches(items[i].help)){
  selected=i;category=items[i].category;phase=1;return;}}
 notice=1;phase=0;
}
#ifdef TERMINAL_ORIGINAL_KEYS
static void record_toggle(void)
{
 const recording_file *r=recording_terminal_inspect();
 if(r && r->state==RF_RECORDING){
  phase=6;if(!recording_ui_ready())notice=103;else{word status=recording_terminal_stop();notice=status?status:101;}
 }else if(r && (r->claimed || r->state==RF_RECOVERY_STATE)){phase=6;notice=r->status?r->status:RF_RECOVERY;}
 else{phase=4;notice=0;for(query_size=0;query_size<63 && recording_terminal_path[query_size];++query_size){} }
}
#endif
unsigned __cdecl command_menu_event(word event,word key,word __far *frame)
{
 word i,n;byte c=(byte)key;
 if(event==0){command_menu_action=0;command_menu_active=1;category=selected=phase=notice=0;view=frame;
  if(!recording_terminal_inspect())recording_terminal_initialize();
#ifdef TERMINAL_REFERENCE
  reference_origin=0;
  if(key==0x2c00 || command_reference_unavailable(key)){
   reference_origin=1;phase=9;command_reference_event(0,key,view);return 1;}
  if(key==0x6c00){reference_origin=1;command_reference_event(0,key,view);
   selected=3;phase=3;query_size=0;query[0]=0;
   if(record_blocked(0xfe00)){phase=6;notice=104;}}
  if(key==0x1700){reference_origin=1;command_reference_event(0,key,view);selected=20;category=4;phase=1;}
#endif
#ifdef TERMINAL_ORIGINAL_KEYS
  if(key==0x1300){for(i=0;i<COUNT;++i)if(items[i].key==0xfd00){selected=i;break;}record_toggle();}
#endif
  draw();return 1;}
 if(event==4){command_menu_action=command_menu_active=0;return 0;}
 if(!command_menu_active)return 0;
 if(event!=1)return 1;
 if(key==0x2d00){command_menu_action=key;command_menu_active=0;return 0;}
 if(c==27){
#ifdef TERMINAL_REFERENCE
  if(phase==9){command_menu_active=0;return 0;}
  if(reference_origin){phase=9;notice=0;draw();return 1;}
#endif
  if(phase){phase=notice=0;draw();return 1;}command_menu_active=0;return 0;}
#ifdef TERMINAL_REFERENCE
 if(phase==9){
  n=command_reference_event(1,key,view);
  if(n==1){command_menu_active=0;return 0;}
  if(n==0x200){reference_origin=0;category=selected=phase=notice=0;draw();return 1;}
  if(n>=0x300 && n<0x300+COUNT){selected=n-0x300;category=items[selected].category;phase=1;draw();return 1;}
  if(n>=0x100 && n<0x100+COUNT){selected=n-0x100;category=items[selected].category;phase=notice=0;goto activate;}
  return 1;
 }
 if(!phase && c=='`'){reference_origin=1;phase=9;command_reference_event(0,0x2c00,view);return 1;}
#endif
 if(phase==4){
  if(c==13){if(!record_start(RF_NEW))return 0;}
  else if(c==8){if(query_size)recording_terminal_path[--query_size]=0;}
  else if(c>=32 && c<127 && query_size<63){recording_terminal_path[query_size++]=c;recording_terminal_path[query_size]=0;}
  draw();return 1;
 }
 if(phase==5){if(fold(c)=='Y'){if(!record_start(RF_REPLACE))return 0;}else if(fold(c)=='N'){phase=0;notice=0;}draw();return 1;}
 if(phase==7 || phase==8){
  if(fold(c)=='Y'){const recording_file *r;
   i=phase;n=phase==7?recording_terminal_cancel():recording_terminal_cleanup();r=recording_terminal_inspect();
   notice=n;
   if(r && !r->claimed && !r->handle_state && !r->stage_owned && !r->backup_owned)notice=i==7 && !r->published?102:105;
   phase=6;}
  else if(fold(c)=='N'){notice=0;phase=6;}draw();return 1;
 }
 if(phase==6){const recording_file *r=recording_terminal_inspect();
  if(fold(c)=='U' && r && r->state!=RF_RECORDING && (r->claimed || r->stage_owned || r->backup_owned)){phase=8;draw();}return 1;}
 if(phase==3){if(c==13){if(query_size){command_menu_action=0xfe00;command_menu_active=0;return 0;}}
  else if(c==8){if(query_size)query[--query_size]=0;}
  else if(c>=32 && c<127 && query_size<57){query[query_size++]=c;query[query_size]=0;}draw();return 1;}
 if(phase==2){if(c==13)search();else if(c==8){if(query_size)query[--query_size]=0;}
  else if(c>=32 && c<127 && query_size<31){query[query_size++]=c;query[query_size]=0;}draw();return 1;}
 if(c=='/'){phase=2;query_size=notice=0;query[0]=0;draw();return 1;}
 if(phase==1){if(key==0x4800||key==0x48e0||key==0x4900||key==0x49e0)selected=selected?selected-1:COUNT-1;
  else if(key==0x5000||key==0x50e0||key==0x5100||key==0x51e0)selected=(selected+1)%COUNT;
  category=items[selected].category;draw();return 1;}
 notice=0;
 if(key==0x4b00||key==0x4be0||key==0x0f00||key==0x4d00||key==0x4de0||c==9){
  if(key==0x4b00||key==0x4be0||key==0x0f00)category=category?category-1:4;else category=(category+1)%5;
  for(i=0;i<COUNT;++i)if(items[i].category==category){selected=i;break;}
 }else if(key==0x4700||key==0x47e0||key==0x4f00||key==0x4fe0){
  for(i=0;i<COUNT;++i)if(items[i].category==category){selected=i;if(key==0x4700||key==0x47e0)break;}
 }else if(key==0x4800||key==0x48e0||key==0x5000||key==0x50e0){
  i=selected;for(n=0;n<COUNT;++n){i=(key==0x4800||key==0x48e0)?(i?i-1:COUNT-1):(i+1)%COUNT;
   if(items[i].category==category){selected=i;break;}}
 }else if(key==0x3b00){phase=1;}
 else{
  if(c!=13){for(i=0;i<COUNT;++i)if(items[i].category==category && items[i].letter==fold(c)){selected=i;break;}
   if(i==COUNT){draw();return 1;}}
#ifdef TERMINAL_REFERENCE
activate:
#endif
  if(record_blocked(items[selected].key)){phase=6;notice=104;}
  else if(items[selected].key==0xfd00){
#ifdef TERMINAL_ORIGINAL_KEYS
   record_toggle();
#else
   const recording_file *r=recording_terminal_inspect();
   if(r && r->state==RF_RECORDING){
    phase=6;if(!recording_ui_ready())notice=103;else{n=recording_terminal_stop();notice=n?n:101;}
   }else if(r && (r->claimed || r->state==RF_RECOVERY_STATE)){phase=6;notice=r->status?r->status:RF_RECOVERY;}
   else{phase=4;notice=0;for(query_size=0;query_size<63 && recording_terminal_path[query_size];++query_size){} }
#endif
  }
  else if(items[selected].key==0xfc00){const recording_file *r=recording_terminal_inspect();
   phase=r && (r->state==RF_RECORDING || (r->claimed && !r->published))?7:6;notice=r?r->status:RF_STATE;}
  else if(items[selected].key==0xfb00){const recording_file *r=recording_terminal_inspect();
   phase=6;notice=r?r->status:RF_STATE;if(notice==RF_CANCELLED)notice=102;}
  else if(items[selected].key==0xfe00){phase=3;query_size=0;query[0]=0;}
  else if(!items[selected].key)phase=1;
  else{command_menu_action=items[selected].key;command_menu_active=0;return 0;}
 }
 draw();return 1;
}
