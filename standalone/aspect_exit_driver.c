/* Actual CLI RUN/WAIT: a controlled timer changes foreground vector ownership.
 * It restores its own timer vector and supplies one real BIOS key. */
#include "runtime.h"
#include "external_runtime.h"
#include "../src/process/native_program.h"
#include "../src/process/break_owner.h"
#include "../src/process/exit_owner.h"
#include <dos.h>
#include <i86.h>
#include <stdio.h>
#ifdef ASPECT_EXIT_RETRY
#include <string.h>
#include <errno.h>
#include <malloc.h>
#include "../src/aspect/process_serial.h"
static unsigned retry_observation[10];
#endif
typedef void (__interrupt __far *irq)(void);
static irq old_timer;
static volatile unsigned fired;
volatile unsigned aspect_exit_hits;
unsigned aspect_exit_extra;
void __interrupt __far aspect_exit_foreign(void){++aspect_exit_hits;}
static void __interrupt __far timer(void)
{
 if(native_program_waiting&&!fired){
  unsigned tail=*(unsigned __far *)MK_FP(0x40,0x1c);
  *(irq __far *)MK_FP(0,0x1b*4)=aspect_exit_foreign;
  *(irq __far *)MK_FP(0,0x1c*4)=old_timer;
  *(unsigned __far *)MK_FP(0x40,tail)=0x2c5a;
  tail+=2;if(tail>=0x3e)tail=0x1e;
  *(unsigned __far *)MK_FP(0x40,0x1c)=tail;
  fired=1;
 }
 _chain_intr(old_timer);
}
static unsigned psp(void);
#pragma aux psp = "mov ah,0x62" "int 0x21" "mov ax,bx" value [ax] modify [ax bx];
void runtime_external_observe(unsigned a,unsigned b,unsigned c,unsigned d)
{
#ifdef ASPECT_EXIT_RETRY
 retry_observation[0]=a;retry_observation[1]=b;retry_observation[2]=c;retry_observation[3]=d;
 retry_observation[4]=native_break_phase();retry_observation[5]=native_program_busy;
 retry_observation[6]=native_program_waiting;retry_observation[7]=aspect_process_serial_detached;
 retry_observation[8]=aspect_serial_active;retry_observation[9]=runtime_error;
#else
 (void)a;(void)b;(void)c;(void)d;
#endif
}
static unsigned exit_run(const char *path,unsigned limit)
{
 unsigned result,record[13],i;FILE *file;union REGS a,b;
#ifdef ASPECT_EXIT_RETRY
 /* A second invocation in the same terminal session exercises ordinary CLI
  * execution. Only the designated first script injects a foreground fault. */
 if(!stricmp(path,"RETRY.ASX")){
  unsigned normal=aspect_runtime_run(path,limit),error=errno,written;int handle;
  unsigned evidence[3];evidence[0]=normal;evidence[1]=error;evidence[2]=_memavl();
  if(!_dos_creat("RETRYWIT.BIN",0,&handle)){
   _dos_write(handle,evidence,sizeof(evidence),&written);_dos_close(handle);
   if(!_dos_creat("RETRYDBG.BIN",0,&handle)){
    _dos_write(handle,retry_observation,sizeof(retry_observation),&written);_dos_close(handle);
   }
  }
  return normal;
 }
#endif
 a.x.ax=0x3301;a.h.dl=0;int86(0x21,&a,&b);
 if(_dos_allocmem(0x20,&aspect_exit_extra))return 8;
 for(i=0;i<256;++i)((unsigned __far *)MK_FP(aspect_exit_extra,0))[i]=0xa55a;
 old_timer=_dos_getvect(0x1c);_dos_setvect(0x1c,timer);
 result=aspect_runtime_run(path,limit);
 _dos_setvect(0x1c,old_timer);
 record[0]=0x5845;record[1]='Q';record[2]=psp();
 record[3]=*(unsigned __far *)MK_FP(record[2]-1,3);
 record[4]=aspect_exit_extra;record[5]=0x20;record[6]=FP_OFF(aspect_exit_foreign);record[7]=FP_SEG(aspect_exit_foreign);
 record[8]=FP_OFF((void __far *)&aspect_exit_hits);record[9]=FP_SEG((void __far *)&aspect_exit_hits);
 record[10]=native_break_phase();record[11]=0;record[12]=program_exit_live();
 file=fopen("EXITWIT.BIN","wb");if(!file)return 5;
 i=fwrite(record,sizeof(record),1,file)!=1;i|=fclose(file)!=0;
 if(i||!fired||result!=10)return 5;
 return result;
}
#define aspect_runtime_run exit_run
#define main ordinary_main
#include "../src/aspect/runner.c"
#undef main
#undef aspect_runtime_run
int main(int argc,char **argv){return ordinary_main(argc,argv);}
