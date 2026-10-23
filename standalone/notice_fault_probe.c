/* Pure observation and controlled synchronous faults in NOTICECODE. */
#include "runtime.h"
#include "external_runtime.h"
#include "external_unwind.h"
#include "serial.h"
#include "file_io.h"
#include "script_file_runtime.h"
#include "../src/process/native_program.h"
#include "../src/process/native_display.h"
#include "../src/process/process_handles.h"
#include "../src/process/program_notice.h"
#include "../src/ui/notice_window.h"
#include "notice_fault.h"
#include <dos.h>
extern aspect_file runtime_file;
unsigned notice_fault_report[62];
unsigned notice_fault_memory_request,notice_fault_memory_segment,notice_fault_exec_count,notice_fault_exec_mode;
extern unsigned native_crt_error,native_dos_error;
static unsigned armed,kind,psp,cursor,first_return;
static unsigned quarantine,quarantine_cursor;
static unsigned short quarantine_screen[2000];
static notice_window_rect replacement={2,2,6,25,0x1f};
extern void __far __cdecl notice_window_damage_guard(void);
extern unsigned notice_window_allocations,notice_window_frees;
static unsigned short screen[2000],vectors[6];
static unsigned char jft[20];
static unsigned current_psp(void);
#pragma aux current_psp = "mov ah,0x62" "int 0x21" "mov ax,bx" value [ax] modify [ax bx];
static void video(void);
#pragma aux video = "mov ax,3" "int 0x10" "mov ah,2" "xor bx,bx" "mov dx,0x0405" "int 0x10" modify [ax bx cx dx];
static void line_ready(unsigned);
#pragma aux line_ready = "add dx,4" "in al,dx" "or al,1" "out dx,al" parm [dx] modify [ax dx];
static unsigned video_equal(void)
{unsigned i;for(i=0;i<2000;++i)if(screen[i]!=((unsigned __far *)MK_FP(0xb800,0))[i])return 0;return *(unsigned __far *)MK_FP(0x40,0x50)==cursor;}
static unsigned quarantine_equal(void)
{unsigned i;for(i=0;i<2000;++i)if(quarantine_screen[i]!=((unsigned __far *)MK_FP(0xb800,0))[i])return 0;return *(unsigned __far *)MK_FP(0x40,0x50)==quarantine_cursor;}
static unsigned resources_equal(void)
{
 unsigned i;unsigned char __far *table=MK_FP(psp,0x18);
 for(i=0;i<20;++i)if(jft[i]!=table[i])return 0;
 for(i=0;i<6;++i)if(vectors[i]!=((unsigned __far *)MK_FP(0,i<2?0:i<4?0x8c:0x90))[i&1])return 0;
 return current_psp()==psp;
}
static unsigned clean(void)
{
 return !(runtime_live|runtime_abi_bad|(unsigned)runtime_file.handle|runtime_script_file_live|
  runtime_script_file_cleanup_errors|native_process_busy|native_program_busy|native_program_waiting|
  native_display_owned|process_handles_active|runtime_external_cleanup_error|notice_active()|notice_window_phase());
}
void __far __cdecl notice_fault_prepare(void)
{
 unsigned i;const char *request=notice_fault_request();
 video();psp=current_psp();cursor=0x0405;
 line_ready(request&&request[2]=='2'?0x2f8:0x3f8);
 for(i=0;i<2000;++i)screen[i]=((unsigned __far *)MK_FP(0xb800,0))[i]=(i%26+65)|0x1700;
 for(i=0;i<20;++i)jft[i]=((unsigned char __far *)MK_FP(psp,0x18))[i];
 for(i=0;i<6;++i)vectors[i]=((unsigned __far *)MK_FP(0,i<2?0:i<4?0x8c:0x90))[i&1];
 armed=request&&request[0]>='0'&&request[0]<='3'?request[0]-'0':0;
 kind=request&&request[1]=='A'?1:request&&request[1]=='F'?2:0;
 notice_fault_report[0]=0x4e46;notice_fault_report[1]=armed;notice_fault_report[2]=kind;
 notice_fault_memory_request=request&&request[0]&&request[1]&&request[2]&&request[3]=='M';
 notice_fault_exec_mode=request&&request[0]&&request[1]&&request[2]&&request[3]=='F'?4:0;
 if(request&&request[0]&&request[1]&&request[2]&&request[3])quarantine=request[4]=='G'?1:request[4]=='W'?2:0;
 notice_fault_report[37]=quarantine;
}
void __cdecl notice_fault_phase(unsigned phase)
{
 if(phase==2&&program_notice_calls==1){
  const char *text;unsigned i,length=0,match=1;
  switch(program_notice_errno){
  case 2:text="Program not found.";break;
  case 7:text="Command line is too long.";break;
  case 8:text="Invalid executable format.";break;
  case 12:text="Insufficient memory to run program.";break;
  default:text="Unable to execute program.";break;
  }
  while(text[length])++length;
  for(i=0;i<length;++i)if(((unsigned __far *)MK_FP(0xb800,0))[10*80+40-length/2+i]!=(0x7000|(unsigned char)text[i]))match=0;
  notice_fault_report[11]=match;
 }
 if(armed!=phase)return;
 if(phase==2&&quarantine){
  unsigned i;
  notice_fault_report[48]=program_notice_retry(); /* A live callback must reject. */
  if(quarantine==1)notice_window_damage_guard();
  else{
   notice_fault_report[50]=notice_window_close();
   if(notice_window_open(&replacement,0))notice_fault_report[50]=99;
  }
  for(i=0;i<2000;++i)quarantine_screen[i]=((unsigned __far *)MK_FP(0xb800,0))[i];
  quarantine_cursor=*(unsigned __far *)MK_FP(0x40,0x50);
 }
 armed=0;++notice_fault_report[3];notice_fault_raise(kind);
}
void __far __cdecl notice_fault_poll(unsigned count)
{
 unsigned at=program_notice_calls==1?12:13;
 if(count>notice_fault_report[at])notice_fault_report[at]=count;
 if(armed==2&&count<508)return;
 notice_fault_phase(2);
}
unsigned __far __cdecl notice_fault_run(const char *path,unsigned limit)
{
 unsigned first,second;
 first=notice_fault_runtime_run(path,limit);first_return=first;
 notice_fault_report[4]=first;notice_fault_report[5]=program_notice_calls;
 notice_fault_report[6]=program_notice_errno;notice_fault_report[7]=program_notice_result.status;
 notice_fault_report[8]=program_notice_result.window_status;
 notice_fault_report[9]=clean();notice_fault_report[10]=video_equal();
 notice_fault_report[14]=resources_equal();notice_fault_report[15]=runtime_external_raw_status;
 notice_fault_report[16]=runtime_external_recoveries;notice_fault_report[17]=aspect_serial_active;
 notice_fault_report[31]=native_dos_error;notice_fault_report[35]=notice_fault_exec_count;
 notice_fault_memory_request=notice_fault_exec_mode=0;
 if(quarantine){
  notice_fault_report[38]=native_program_busy;notice_fault_report[39]=process_handles_active;
  notice_fault_report[40]=runtime_script_file_live;notice_fault_report[41]=runtime_file.handle!=0;
  notice_fault_report[42]=notice_active();notice_fault_report[43]=notice_window_phase();
  notice_fault_report[44]=program_notice_result.cause;
  notice_fault_report[45]=program_notice_retry();
  notice_fault_report[46]=program_notice_active()&&native_program_busy&&process_handles_active&&runtime_script_file_live==6;
  notice_fault_report[47]=quarantine_equal();
  notice_fault_report[49]=notice_fault_runtime_run("RECOVER.ASX",limit);
  if(quarantine==1)notice_window_damage_guard();
  else notice_fault_report[50]=notice_window_close();
  notice_fault_report[51]=program_notice_retry();
  notice_fault_report[52]=clean();notice_fault_report[53]=resources_equal();notice_fault_report[54]=video_equal();
  notice_fault_report[55]=runtime_external_cleanup_error;
  notice_fault_report[56]=notice_window_allocations;notice_fault_report[57]=notice_window_frees;
  notice_fault_report[58]=program_notice_result.cause;
 }
 second=notice_fault_runtime_run("RECOVER.ASX",limit);
 notice_fault_report[18]=second;notice_fault_report[19]=program_notice_calls;
 notice_fault_report[20]=program_notice_result.status;notice_fault_report[21]=program_notice_result.window_status;
 notice_fault_report[22]=clean();notice_fault_report[23]=video_equal();notice_fault_report[24]=resources_equal();
 notice_fault_report[25]=runtime_external_raw_status;notice_fault_report[26]=runtime_external_recoveries;
 notice_fault_report[27]=aspect_serial_active;
 notice_fault_report[29]=native_crt_error;notice_fault_report[30]=native_dos_error;
 notice_fault_report[36]=notice_fault_exec_count;
 notice_fault_report[59]=notice_window_allocations;notice_fault_report[60]=notice_window_frees;
 notice_fault_report[61]=program_notice_active();
 return first_return;
}
