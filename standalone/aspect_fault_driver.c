/* Diagnostic CLI wrapper: real first fault, then a second actual VM invocation
 * on the same attached renderer/UART. The original first error is propagated. */
#include "runtime.h"
#include "external_unwind.h"
#include "external_runtime.h"
#include "serial.h"
#include "resident_render.h"
#include "environment_runtime.h"
#include "script_file_runtime.h"
#include "file_io.h"
#include "../src/process/native_program.h"
#include "../src/process/native_display.h"
#include "../src/process/process_handles.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <malloc.h>
#include <dos.h>
#if defined(NATIVE_PROGRAM_BREAK_OWNER)
#include "../src/process/break_owner.h"
#define VECTOR_COUNT 4
static unsigned char caller_break;
static unsigned query_break(void);
#pragma aux query_break = "mov ax,0x3300" "int 0x21" "xor ax,ax" "mov al,dl" value [ax] modify [ax dx];
static void set_break(unsigned);
#pragma aux set_break = "mov ax,0x3301" "int 0x21" parm [dx] modify [ax];
#else
#define VECTOR_COUNT 3
#endif
extern aspect_file runtime_file;
extern char **environ;
extern unsigned native_backup_extent;
static unsigned report[20];
static char padding[32][256];
static char *seed[128];
static unsigned psp;
static unsigned char jft_before[20];
static unsigned char __far *jft;
static void (__interrupt __far *vectors[VECTOR_COUNT])(void);
static const unsigned char vector_numbers[VECTOR_COUNT]={0,0x23,0x24
#if defined(NATIVE_PROGRAM_BREAK_OWNER)
 ,0x1b
#endif
};
extern unsigned __cdecl aspect_serial_psp(void);
static unsigned clean(void)
{
 unsigned i;
 for(i=0;i<VECTOR_COUNT;++i)if(vectors[i]!=_dos_getvect(vector_numbers[i]))return 0;
#if defined(NATIVE_PROGRAM_BREAK_OWNER)
 if(native_break_phase()!=BREAK_CLOSED||query_break()!=0)return 0;
#endif
 return !(runtime_live|runtime_abi_bad|(unsigned)runtime_file.handle|runtime_script_file_live|runtime_script_file_cleanup_errors|
  native_process_busy|native_program_busy|native_program_waiting|native_display_owned|
  process_handles_active|runtime_external_scope_active()|runtime_external_checkpoint_active()|
  aspect_render_program_active())&&aspect_serial_psp()==psp&&!_fmemcmp(jft_before,jft,20);
}
void runtime_external_observe(unsigned raw,unsigned processor,unsigned wait,unsigned save)
{(void)raw;(void)processor;(void)wait;(void)save;}
static unsigned fault_run(const char *path,unsigned limit)
{
 unsigned first,i;unsigned long tick=aspect_serial_ticks();
#if defined(NATIVE_PROGRAM_BREAK_OWNER)
 set_break(0);
#endif
 psp=aspect_serial_psp();jft=MK_FP(psp,0x18);_fmemcpy(jft_before,jft,20);
 for(i=0;i<VECTOR_COUNT;++i)vectors[i]=_dos_getvect(vector_numbers[i]);
 first=aspect_runtime_run(path,limit);
 report[3]=first;report[5]=runtime_external_fault_fired;report[6]=runtime_external_recoveries;
 report[7]=runtime_external_cleanup_error;report[8]=runtime_external_arena_ok;
 report[9]=clean();report[10]=native_backup_extent;report[11]=runtime_external_frame_offset;
 report[12]=native_owned_count|native_far_owned;report[13]=aspect_serial_active;report[14]=aspect_render_active();
 report[16]=runtime_external_raw_status;
 report[17]=(unsigned)(aspect_serial_ticks()-tick);report[18]=runtime_external_arena_changed;
 report[19]=native_display_allocs==native_display_frees;
 native_fail_at=runtime_external_fault_at=0;
 report[4]=aspect_runtime_run("RECOVER.ASX",limit);report[15]=clean();
 return first;
}
#define aspect_runtime_run fault_run
#define main ordinary_main
#include "../src/aspect/runner.c"
#undef main
#undef aspect_runtime_run
int main(int argc,char **argv)
{
 char **original=environ;const char *request=getenv("PCPFAULT");unsigned i,n=0;int result;FILE *file;
 if(!request)return 90;
#if defined(NATIVE_PROGRAM_BREAK_OWNER)
 caller_break=(unsigned char)query_break();
#endif
 i=request[0]-'0';
 if(request[1]>='0'&&request[1]<='9'){i=i*10+request[1]-'0';request+=2;}else ++request;
 report[0]=0x4652;report[1]=runtime_external_fault_at=i;
 report[2]=runtime_external_fault_kind=*request=='A'?1:*request=='F'?2:*request=='L'?3:0;
 while(original[n]&&n<94){seed[n]=original[n];++n;}
 if(report[1]!=8)for(i=0;i<32;++i){memset(padding[i],'P',255);padding[i][0]='Q';padding[i][1]='A'+i;padding[i][2]='=';padding[i][255]=0;seed[n++]=padding[i];}
 seed[n]=0;environ=seed;
 runtime_external_arena_copy=_fmalloc(0x3aca);if(!runtime_external_arena_copy)return 91;
 native_fail_at=report[1]==8?0:2;
 result=ordinary_main(argc,argv);
#if defined(NATIVE_PROGRAM_BREAK_OWNER)
 set_break(caller_break);
#endif
 file=fopen("FAULT.BIN","wb");if(!file)return 92;
 fwrite(report,sizeof(report),1,file);fclose(file);
 _ffree(runtime_external_arena_copy);runtime_external_arena_copy=0;
 runtime_environment_release();environ=original;
 return result;
}
