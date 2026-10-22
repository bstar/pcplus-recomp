#include "runtime.h"
#include "file_io.h"
#include "serial.h"
#include "script_file_runtime.h"
#include "environment_runtime.h"
#include "external_runtime.h"
#include "source_compile.h"
#include "native_process.h"
#include "native_program.h"
#include "native_display.h"
#include "process_handles.h"
#include <conio.h>
#include <dos.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
extern aspect_file runtime_file;
extern unsigned runtime_find_live,runtime_file_info_live,runtime_file_times_live;
extern unsigned char native_dos_major;
extern unsigned __cdecl aspect_serial_psp(void);
extern unsigned native_backup_extent,runtime_frame;
extern unsigned char runtime_arena[0x3aca];
static unsigned checks,failures;
static unsigned trace_count,full_trace,expected_trace_raw=37;
static unsigned large_environment;
static char padding[32][256];
static char *seed_environment[128],**original_environment;
#define CHECK(x) check((x)!=0,__LINE__)
/* Far entry points remain in the near CRT segment. */
static void __far diagnostic_printf(const char *format,...)
{
 va_list args;va_start(args,format);vprintf(format,args);va_end(args);
}
#pragma code_seg("PROCESSDIAG")
/* No near CRT calls from this bank. Keep exactly the original fourteen-byte
 * prefix and241 padding bytes without another near-segment adapter. */
static void __far diagnostic_padding(char *target,unsigned index)
{
 static const char prefix[]="LOC_PADDING00=";
 unsigned n;
 for(n=0;n<14;++n)target[n]=prefix[n];
 target[11]=(char)('0'+index/10);target[12]=(char)('0'+index%10);
 for(n=14;n<255;++n)target[n]='P';
 target[255]=0;
}
static void __far check(unsigned good,unsigned line){++checks;if(!good){++failures;diagnostic_printf("FAIL %u\n",line);}}
static unsigned __far seed_large_environment(void)
{
 unsigned i,count=0;
 while(original_environment[count]){
  if(count>=95)return 99;
  seed_environment[count]=original_environment[count];++count;
 }
 for(i=0;i<32;++i){diagnostic_padding(padding[i],i);seed_environment[count+i]=padding[i];}
 seed_environment[count+32]=0;environ=seed_environment;return 0;
}
void __far runtime_external_observe(unsigned raw,unsigned processor,unsigned wait,unsigned save)
{
 static const unsigned full_raw[]={37,37,37,65535U,0,0,37,37,0,1,37};
 if(full_trace){
  CHECK(trace_count<sizeof(full_raw)/sizeof(full_raw[0]));
  if(trace_count<sizeof(full_raw)/sizeof(full_raw[0]))CHECK(raw==full_raw[trace_count]);
  CHECK(processor==(trace_count==4));CHECK(wait==(trace_count==2));CHECK(save==(trace_count!=1));
 }else{CHECK(raw==expected_trace_raw);CHECK(!processor&&!wait&&save==1);}
 if(large_environment){
  CHECK(native_backup_extent>(unsigned)(runtime_frame-(unsigned)runtime_arena));
  diagnostic_printf("ARENA borrowed%u live-frame%u\n",native_backup_extent,(unsigned)(runtime_frame-(unsigned)runtime_arena));
 }
 diagnostic_printf("EXTERNAL %u raw%u processor%u wait%u save%u\n",trace_count,raw,processor,wait,save);++trace_count;
}
static void __far diagnostic_clean_state(void)
{
 CHECK(!runtime_live&&!runtime_script_file_live&&!runtime_file.handle&&!runtime_abi_bad);
 CHECK(!runtime_find_live&&!runtime_file_info_live&&!runtime_file_times_live);
 CHECK(!native_process_busy&&!native_program_busy&&!native_display_owned&&!process_handles_active);
 CHECK(runtime_script_file_peak==6&&runtime_script_file_open_calls==6&&runtime_script_file_close_calls==6);
 CHECK(!runtime_script_file_cleanup_errors);
}
#pragma code_seg()
int main(int argc,char **argv)
{
 unsigned port,base,vector,old_mcr,pic,status,expected=0,raw=37,recovery=0,psp,jft_count,far_before;
 unsigned char jft_before[255];unsigned char __far *jft;char child[13];
 native_process_result control;FILE *file;
 void (__interrupt __far *old_irq)(void),(__interrupt __far *old_zero)(void);
 union REGS in,out;
 setvbuf(stdout,0,_IONBF,0);if(argc<3||argc>4)return 99;
 original_environment=environ;
 large_environment=argc==4&&!strcmp(argv[3],"large");
 if(large_environment&&seed_large_environment())return 99;
 full_trace=!strcmp(argv[1],"FULL.ASX");
 port=argv[2][2]-'0';base=port==1?0x3f8:0x2f8;vector=port==1?12:11;
 old_mcr=inp(base+4);pic=inp(0x21);old_irq=_dos_getvect(vector);old_zero=_dos_getvect(0);
 outp(base+4,old_mcr|1);CHECK(aspect_serial_open(argv[2])==0);
 CHECK(runtime_environment_put("CTRLVAR=OWNED")==0);
 /* Same child, without the private-handle bracket, demonstrates a real
  * inherited descriptor through DOS AH42. Exit98 is specific to that check. */
 sprintf(child,"OWN%u.COM",port);file=fopen("CONTROL.DAT","wb+");CHECK(file!=0);
 CHECK(native_process_run(child,"S",0,1,&control)==0);CHECK(control.child_status==98);
 if(file)fclose(file);
 psp=aspect_serial_psp();jft_count=*(unsigned __far *)MK_FP(psp,0x32);
 if(jft_count>255){runtime_environment_release();environ=original_environment;return 99;}jft=*(unsigned char __far * __far *)MK_FP(psp,0x34);
 _fmemcpy(jft_before,jft,jft_count);
 far_before=native_far_calls;
 if(argc==4){
  if(!strcmp(argv[3],"fallback")||large_environment)native_fail_at=native_near_calls+2;
  else if(!strcmp(argv[3],"memory")){native_fail_near=1;raw=65535U;}
  else if(!strcmp(argv[3],"divide"))raw=12;
  else if(!strcmp(argv[3],"abort"))expected=ASPECT_RUN_DIVIDE_ZERO;
  else if(!strcmp(argv[3],"budget"))expected=ASPECT_RUN_BUDGET;
 }
 expected_trace_raw=raw;
 in.x.ax=3;int86(0x10,&in,&out);
 {unsigned i;unsigned __far *video=MK_FP(0xb800,0);for(i=0;i<2000;++i)video[i]=(i*37+0x1741)&65535U;}
 status=aspect_runtime_run(argv[1],argc==4&&!strcmp(argv[3],"budget")?100:5000);
 native_fail_at=native_fail_near=0;
 CHECK(status==expected);CHECK(_dos_getvect(0)==old_zero);
 diagnostic_clean_state();
 if(argc==4&&(!strcmp(argv[3],"fallback")||large_environment))CHECK(native_far_calls==far_before+1);
 if(!expected){CHECK(runtime_integer_b[0]==317);CHECK(runtime_external_raw_status==raw);CHECK(runtime_external_private_count==7);}
 CHECK(_fmemcmp(jft_before,jft,jft_count)==0);
 if(expected){
  recovery=aspect_runtime_run("RECOVER.ASX",3000)==0;
  CHECK(recovery&&runtime_integer_b[0]==317&&runtime_external_raw_status==37);
  CHECK(!runtime_live&&!runtime_script_file_live&&!runtime_file.handle&&!process_handles_active&&!runtime_script_file_cleanup_errors);
  CHECK(_dos_getvect(0)==old_zero&&_fmemcmp(jft_before,jft,jft_count)==0);
 }
 CHECK(trace_count==(full_trace?11:expected?2:1));
 CHECK(native_dos_major==3);CHECK(aspect_serial_close()==0);
 CHECK(_dos_getvect(vector)==old_irq&&inp(0x21)==pic);outp(base+4,old_mcr);
 {unsigned long tick=aspect_serial_ticks();while(aspect_serial_ticks()==tick);}
 printf("ASPECT PROCESS COM%u %c result%u raw%u calls%u private%u compiler%u checks%u failures%u recovery%u control98 JFT-preserved\n",port,argv[2][12],status,
  runtime_external_raw_status,runtime_external_calls,runtime_external_private_count,runtime_compiler_calls,checks,failures,recovery);
 runtime_environment_release();environ=original_environment;
 return failures?1:0;
}
