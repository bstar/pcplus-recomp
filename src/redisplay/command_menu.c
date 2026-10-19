/* Source-owned command menu and contextual help for the maintained terminal.
 * Code-segment constants keep UI prose outside the small-model DGROUP and
 * ahead of uninitialized far buffers. See Watcom's segment-constant objects. */
#include "command_menu.h"
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
ENTRY(receive,"Receive files                  Alt-R",
 "Receive into a local DOS file with XMODEM. F2 in the filename prompt\n"
 "selects YMODEM; enter a destination directory for a batch. Request the\n"
 "download at the BBS first. HARD or NONE flow is required. XMODEM may\n"
 "retain SUB padding; YMODEM preserves each declared file length.");
ENTRY(send,"Send files                     Alt-S",
 "Choose a local DOS file to send with XMODEM/1K. F2 selects YMODEM;\n"
 "enter a DOS file pattern for a batch. Start the BBS upload first.\n"
 "Sources are opened read-only. A transfer owns the local keyboard\n"
 "until it completes or is canceled; menu keys are not protocol data.");
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
ENTRY(history,"Redisplay history              Ctrl-PgUp",
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
ENTRY(settings,"Edit saved settings            Alt-F10",
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
ENTRY(table,"Edit input table               Alt-F8",
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
 "Alt-Z opens this menu. Left/Right or Tab changes the menu group.\n"
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
 ROW(receive,0,0x1300,'R'),ROW(send,0,0x1f00,'S'),ROW(snapshot,0,0x2200,'W'),
 ROW(script,0,0xfe00,'A'),ROW(capture,0,0x6800,'O'),ROW(hold,0,0x6900,'H'),ROW(crlf,0,0x6a00,'T'),ROW(exit,0,0x2d00,'X'),
 ROW(redial,1,0x2000,'D'),ROW(hangup,1,0x2300,'H'),ROW(linebreak,1,0x3000,'B'),
 ROW(history,2,0x8400,'R'),ROW(clipboard,2,0x8300,'F'),ROW(monitor,2,0x2b1c,'M'),ROW(printer,2,0x2600,'P'),
 ROW(settings,3,0x7100,'E'),ROW(reload,3,0x7000,'R'),ROW(table,3,0x6f00,'T'),ROW(using,4,0,'U'),ROW(keys,4,0,'K'),ROW(scope,4,0,'A')};
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
static byte fold(byte c){return c>='a' && c<='z'?c-32:c;}
static void text(word at,const char __far *s,word attr)
{while(*s && at<2000)view[at++]=attr|(byte)*s++;}
static void prose(word at,const char __far *s)
{word col=0;byte c;while((c=*s++)!=0 && at<1840){if(c==10){at+=80-col;col=0;}else{view[at++]=0x0700|c;if(++col==76){at+=4;col=0;}}}}
static void draw(void)
{
 word i,n=0,at;for(i=0;i<2000;++i)view[i]=0x0720;
 for(i=0;i<80;++i)view[i]=view[1920+i]=0x1f20;
 text(1,title,0x1f00);
 for(i=0;i<5;++i)text(162+i*15,categories[i],i==category?0x7000:0x1f00);
 if(phase==1){text(402,items[selected].name,0x1f00);prose(562,items[selected].help);text(1921,help_footer,0x1f00);}
 else{
  for(i=0;i<COUNT;++i)if(items[i].category==category){
   at=402+n++*80;view[at]=0x1f00|items[i].letter;view[at+1]=0x1f00|')';
   text(at+3,items[i].name,i==selected?0x7000:0x0700);
  }
  if(notice)text(1921,no_match,0x1f00);else text(1921,footer,0x1f00);
 }
 if(phase==2 || phase==3){for(i=1760;i<1840;++i)view[i]=0x1f20;text(1762,phase==3?script_label:find_label,0x1f00);
  for(i=0;i<query_size;++i)view[(phase==3?1782:1768)+i]=0x1f00|(byte)query[i];
  for(i=1920;i<2000;++i)view[i]=0x1f20;text(1921,phase==3?script_footer:find_footer,0x1f00);}
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
unsigned __cdecl command_menu_event(word event,word key,word __far *frame)
{
 word i,n;byte c=(byte)key;
 if(event==0){command_menu_action=0;command_menu_active=1;category=selected=phase=notice=0;view=frame;draw();return 1;}
 if(event==4){command_menu_action=command_menu_active=0;return 0;}
 if(!command_menu_active)return 0;
 if(event!=1)return 1;
 if(key==0x2d00){command_menu_action=key;command_menu_active=0;return 0;}
 if(c==27){if(phase){phase=notice=0;draw();return 1;}command_menu_active=0;return 0;}
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
  if(items[selected].key==0xfe00){phase=3;query_size=0;query[0]=0;}
  else if(!items[selected].key)phase=1;
  else{command_menu_action=items[selected].key;command_menu_active=0;return 0;}
 }
 draw();return 1;
}
