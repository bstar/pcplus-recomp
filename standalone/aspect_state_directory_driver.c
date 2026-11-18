/* Supplemental real DOS8086 checks. Product view/reader are separate objects;
 * only the filesystem and adopted-name/loader boundaries are controlled. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../src/redisplay/directory_view.h"
#include "../src/directory/directory_reader.h"

typedef unsigned char byte;
typedef unsigned short word;
extern word aspect_fromddir,state_directory_before,state_directory_after;
extern byte __far redisplay_snapshot[63000];
byte directory_view_scratch[512];
char terminal_directory_path[64]="PUBLIC.DIR";
word terminal_directory_entry=1;
byte terminal_browser_screen_owned,terminal_editor_screen_owned;
#pragma aux terminal_directory_path "terminal_directory_path";
#pragma aux terminal_directory_entry "terminal_directory_entry";
#pragma aux terminal_browser_screen_owned "terminal_browser_screen_owned";
#pragma aux terminal_editor_screen_owned "terminal_editor_screen_owned";
word terminal_directory_context_valid;
byte terminal_directory_context[496];
word terminal_program_active,terminal_program_pending,command_menu_active,redisplay_active;
char command_menu_script[64];
#pragma aux terminal_directory_context_valid "terminal_directory_context_valid";
#pragma aux terminal_directory_context "terminal_directory_context";
#pragma aux terminal_program_active "terminal_program_active";
#pragma aux terminal_program_pending "terminal_program_pending";
extern void __cdecl terminal_directory_script_connected(void);
#pragma aux terminal_directory_script_connected "terminal_directory_script_connected";
static struct {word before,frame[2000],after;} screen;
static unsigned checks,cases,opens,reads,closes,position,staged_status,staged_calls,loads;
static word observed_origin;
static const char *context;
static unsigned segment_difference(void);
#pragma aux segment_difference = "mov ax,ds" "mov dx,ss" "sub ax,dx" value [ax] modify [dx];
static void ck(unsigned yes)
{++checks;if(!yes){printf("FAIL %s case%u check%u\r\n",context,cases,checks);exit(1);}}
static void canaries(void)
{ck(state_directory_before==0x1357&&state_directory_after==0x2468);ck(screen.before==0x3579&&screen.after==0x468a);}
static unsigned event(word e,word k)
{unsigned result=directory_view_event(e,k,screen.frame);canaries();return result;}
unsigned __cdecl directory_reader_fs_open(const char *path,int *handle)
{ck(!strcmp(path,"PUBLIC.DIR"));++opens;position=0;*handle=17;return 0;}
unsigned __cdecl directory_reader_fs_read(int handle,void *out,unsigned n,unsigned *count)
{
 unsigned i;byte *p=out;ck(handle==17);++reads;
 if(n>DIRECTORY_DOS_FILE_SIZE-position)n=DIRECTORY_DOS_FILE_SIZE-position;
 for(i=0;i<n;++i)p[i]=0;position+=n;*count=n;return 0;
}
unsigned __cdecl directory_reader_fs_close(int handle)
{ck(handle==17);++closes;return 0;}
unsigned __far __cdecl directory_adopt_script_name(void)
{++staged_calls;if(staged_status==2)strcpy(command_menu_script,"STAGED.ASX");return staged_status;}
void __cdecl state_directory_loader(void)
{++loads;observed_origin=aspect_fromddir;}
static void drain(word value)
{
 unsigned i;
 for(i=0;i<60;++i){ck(event(3,0)==1);ck(aspect_fromddir==value);}
}
static void script_setup(word entry,word origin)
{
 ++cases;terminal_directory_context_valid=1;
 terminal_program_active=terminal_program_pending=command_menu_active=redisplay_active=0;
 memset(terminal_directory_context,0,sizeof(terminal_directory_context));
 memcpy(terminal_directory_context,&entry,2);aspect_fromddir=origin;
 staged_status=staged_calls=loads=0;observed_origin=0x5a5a;
 memset(command_menu_script,0xa5,sizeof(command_menu_script));
}
static void script_call(void)
{terminal_directory_script_connected();canaries();}
int main(void)
{
 static const word values[]={0,1,200,255,256,0x1234,0x7fff,0x8000,0xff00,0xffff};
 word *busy[4];unsigned i,j,before;
 screen.before=0x3579;screen.after=0x468a;
 context="real-mode-ds-equals-ss";ck(!segment_difference());
 context="event0-clear-before-draw-and-immediate-cancel";
 for(i=0;i<sizeof(values)/sizeof(values[0]);++i){
  ++cases;aspect_fromddir=values[i];memset(screen.frame,0xa5,sizeof(screen.frame));
  before=opens+reads+closes;ck(event(0,0)==1&&aspect_fromddir==0);
  ck(screen.frame[2]==0x1f50&&screen.frame[1919]==0x0720&&screen.frame[1999]==0x1f20);
  for(j=0;j<2000;++j)ck(screen.frame[j]!=0xa5a5);
  ck(event(1,27)==0&&aspect_fromddir==0);ck(opens+reads+closes==before);
 }
 context="inactive-events-preserve";++cases;aspect_fromddir=0xbeef;
 ck(event(2,0)==0&&event(3,0)==0&&event(1,13)==0&&aspect_fromddir==0xbeef);
 context="redraw-idle-loading-read-only-paging-reload-preserve";++cases;
 ck(event(0,0)==1&&aspect_fromddir==0);aspect_fromddir=0xbeef;
 ck(event(2,0)==1&&event(3,0)==1&&aspect_fromddir==0xbeef&&!opens);
 ck(event(1,13)==1&&opens==1&&aspect_fromddir==0xbeef);drain(0xbeef);
 ck(closes==1&&screen.frame[1762]==0x0752); /* actual read-only footer */
 ck(event(1,0x5100)==1&&opens==2&&aspect_fromddir==0xbeef);drain(0xbeef);
 ck(event(1,0x3f00)==1&&opens==3&&aspect_fromddir==0xbeef);drain(0xbeef);
 ck(event(2,0)==1&&event(1,27)==0&&aspect_fromddir==0xbeef);
 context="loading-cancel-preserves";++cases;ck(event(0,0)==1);aspect_fromddir=0xcafe;
 ck(event(1,13)==1&&event(1,27)==1&&aspect_fromddir==0xcafe);
 ck(event(3,0)==0&&aspect_fromddir==0xcafe&&closes==4);
 context="busy-reader-open-preserves-after-event0";
 for(i=0;i<2;++i){++cases;terminal_browser_screen_owned=i==0;terminal_editor_screen_owned=i==1;
  ck(event(0,0)==1&&aspect_fromddir==0);aspect_fromddir=0xabcd;before=opens;
  ck(event(1,13)==1&&opens==before&&aspect_fromddir==0xabcd);ck(event(4,0)==0&&aspect_fromddir==0xabcd);
 }
 terminal_browser_screen_owned=terminal_editor_screen_owned=0;
 context="read-only-open-through-escape-leaves-origin-cleared";++cases;
 aspect_fromddir=0xffff;ck(event(0,0)==1&&aspect_fromddir==0);
 ck(event(1,13)==1);drain(0);
 ck(screen.frame[1762]==0x0752&&aspect_fromddir==0);
 ck(event(1,27)==0&&aspect_fromddir==0);
 context="forced-stop-closes-loading-without-origin-write";++cases;
 ck(event(0,0)==1);aspect_fromddir=0x8001;ck(event(1,13)==1);
 before=reads;ck(event(2,0)==1&&reads==before&&aspect_fromddir==0x8001);
 before=closes;ck(event(4,0)==0&&closes==before+1&&aspect_fromddir==0x8001);
 context="adopted-name-writes-full-entry-before-loader";
 for(i=0;i<sizeof(values)/sizeof(values[0]);++i){script_setup(values[i],0xa5a5);staged_status=2;
  script_call();ck(staged_calls==1&&loads==1&&aspect_fromddir==values[i]&&observed_origin==values[i]);
  ck(!strcmp(command_menu_script,"STAGED.ASX"));}
 context="adoption-decline-legacy-blank-preserves";
 for(i=0;i<2;++i){script_setup(0x8123,0xcafe);terminal_directory_context[252+0x34]=i?' ':0;
  script_call();ck(staged_calls==1&&!loads&&aspect_fromddir==0xcafe);}
 context="adoption-decline-legacy-name-sets-before-loader";
 for(i=0;i<sizeof(values)/sizeof(values[0]);++i){script_setup(values[i],0xcafe);
  strcpy((char *)terminal_directory_context+252+0x34,"login");script_call();
  ck(staged_calls==1&&loads==1&&aspect_fromddir==values[i]&&observed_origin==values[i]);
  ck(!strcmp(command_menu_script,"LOGIN.ASX"));}
 context="adoption-refusal-preserves";
 for(i=0;i<3;++i){script_setup(0xffff,0xcafe);staged_status=i==0?1:i==1?3:0xffff;
  script_call();ck(staged_calls==1&&!loads&&aspect_fromddir==0xcafe);}
 context="inactive-context-and-individual-busy-gates";
 busy[0]=&terminal_program_active;busy[1]=&terminal_program_pending;busy[2]=&command_menu_active;busy[3]=&redisplay_active;
 for(i=0;i<5;++i){script_setup(0xffff,0xcafe);staged_status=2;
  if(i==4)terminal_directory_context_valid=0;else *busy[i]=0x8000;
  script_call();ck(!staged_calls&&!loads&&aspect_fromddir==0xcafe);}
 printf("ASPECT_STATE_DIRECTORY %u cases %u checks 0 failures\r\n",cases,checks);return 0;
}
