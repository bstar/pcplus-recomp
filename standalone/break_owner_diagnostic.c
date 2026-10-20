#include "break_owner.h"
#include "native_process.h"
#include <dos.h>
#include <i86.h>
#include <malloc.h>
#include <stdio.h>
#include <string.h>
typedef void (__interrupt __far *irq)(void);
extern unsigned char native_break_original_1b[9];
extern irq NATIVE_BREAK_CODE __cdecl native_break_handler(void);
static unsigned checks,failures,children;
static void check(unsigned yes,unsigned line){++checks;if(!yes){++failures;printf("FAIL %u\n",line);}}
#define CHECK(x) check((x)!=0,__LINE__)
static unsigned char flag(void){union REGS a,b;a.x.ax=0x3300;int86(0x21,&a,&b);return b.h.dl;}
static void setflag(unsigned char value){union REGS a,b;a.x.ax=0x3301;a.h.dl=value;int86(0x21,&a,&b);}
static unsigned psp(void);
#pragma aux psp = "mov ah,0x62" "int 0x21" "mov ax,bx" value [ax] modify [ax bx];
static void setpsp(unsigned);
#pragma aux setpsp = "mov ah,0x50" "int 0x21" parm [bx] modify [ax];
static void cli(void);
#pragma aux cli = "cli" modify [];
static void sti(void);
#pragma aux sti = "sti" modify [];
static void __interrupt __far foreign(void) {}
int main(void)
{
 irq one=_dos_getvect(0x1b),twenty_three=_dos_getvect(0x23),owned;
 unsigned char original=flag(),seed[9],witness[9];unsigned policy,initial,i,block,parent;
 native_process_result result;FILE *file;
 setvbuf(stdout,0,_IONBF,0);
 for(i=0;i<9;++i)seed[i]=(unsigned char)(0xa0+i);
 memcpy(native_break_original_1b,seed,9);
 CHECK(native_break_close()==BREAK_OK);CHECK(native_break_recover()==BREAK_OK);
 CHECK(native_break_open(2)==BREAK_ARGUMENT);
 cli();i=native_break_open(1);sti();CHECK(i==BREAK_ARGUMENT);
 CHECK(native_break_phase()==BREAK_CLOSED);
 for(initial=0;initial<2;++initial)for(policy=0;policy<2;++policy){
  setflag((unsigned char)initial);
  CHECK(native_break_open(policy)==BREAK_OK);CHECK(native_break_phase()==BREAK_READY);
  CHECK(_dos_getvect(0x1b)==native_break_handler()&&_dos_getvect(0x23)==native_break_handler());
  CHECK(flag()==(policy?0:initial));CHECK(native_break_open(policy)==BREAK_STATE);
  CHECK(native_break_resume()==BREAK_STATE);
  CHECK(native_break_suspend()==BREAK_OK);CHECK(native_break_phase()==BREAK_SUSPENDED);
  CHECK(_dos_getvect(0x1b)==one&&_dos_getvect(0x23)==twenty_three&&flag()==initial);
  CHECK(native_break_suspend()==BREAK_STATE);
  remove("BRKWIT.BIN");
  CHECK(native_process_run("BRKCHLD.COM",0,0,1,&result)==NATIVE_PROCESS_OK);
  CHECK(result.child_status==42&&native_process_busy==0);++children;
  file=fopen("BRKWIT.BIN","rb");CHECK(file!=0);
  if(file){CHECK(fread(witness,1,9,file)==9);fclose(file);
   CHECK(*(unsigned *)witness==FP_OFF(one)&&*(unsigned *)(witness+2)==FP_SEG(one));
   CHECK(*(unsigned *)(witness+4)==FP_OFF(twenty_three)&&*(unsigned *)(witness+6)==FP_SEG(twenty_three));
   CHECK(witness[8]==initial);}
  CHECK(_dos_getvect(0x1b)!=one);CHECK(flag()==1);
  CHECK(native_break_resume()==BREAK_OK);CHECK(native_break_phase()==BREAK_READY);
  CHECK(_dos_getvect(0x1b)==native_break_handler()&&_dos_getvect(0x23)==native_break_handler());
  CHECK(flag()==(policy?0:initial));CHECK(native_break_close()==BREAK_OK);
  CHECK(_dos_getvect(0x1b)==one&&_dos_getvect(0x23)==twenty_three&&flag()==initial);
  CHECK(!memcmp(native_break_original_1b,seed,9));
 }
 CHECK(children==4);
 CHECK(native_break_open(1)==BREAK_OK);owned=_dos_getvect(0x1b);
 _dos_setvect(0x1b,foreign);CHECK(native_break_close()==BREAK_QUARANTINE);
 CHECK(native_break_phase()==BREAK_HELD&&_dos_getvect(0x1b)==foreign);
 CHECK(native_break_recover()==BREAK_QUARANTINE);
 _dos_setvect(0x1b,owned);CHECK(native_break_recover()==BREAK_OK);
 CHECK(_dos_getvect(0x1b)==one&&_dos_getvect(0x23)==twenty_three);
 CHECK(native_break_open(1)==BREAK_OK);native_break_original_1b[0]^=1;
 CHECK(native_break_close()==BREAK_QUARANTINE);CHECK(native_break_recover()==BREAK_OK);
 CHECK(!memcmp(native_break_original_1b,seed,9));
 CHECK(native_break_open(1)==BREAK_OK);CHECK(native_break_suspend()==BREAK_OK);
 parent=psp();i=_dos_allocmem(0x10,&block);CHECK(i==0);
 if(!i){setpsp(block);i=native_break_resume();setpsp(parent);CHECK(i==BREAK_QUARANTINE);
  CHECK(native_break_recover()==BREAK_OK);CHECK(_dos_freemem(block)==0);}
 CHECK(native_break_open(1)==BREAK_OK);CHECK(native_break_suspend()==BREAK_OK);
 _dos_setvect(0x1b,foreign);setflag(0);CHECK(native_break_close()==BREAK_OK);
 CHECK(_dos_getvect(0x1b)==one&&_dos_getvect(0x23)==twenty_three);
 CHECK(native_break_phase()==BREAK_CLOSED);
 CHECK(_nheapchk()==_HEAPOK||_nheapchk()==_HEAPEMPTY);
 _dos_setvect(0x1b,one);_dos_setvect(0x23,twenty_three);setflag(original);
 printf("BREAK OWNER checks=%u failures=%u children=%u\n",checks,failures,children);
 return failures?1:0;
}
