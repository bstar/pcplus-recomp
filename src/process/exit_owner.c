#include "exit_owner.h"
#include "break_owner.h"
#include <dos.h>
extern unsigned _STACKTOP,_psp;
extern void __cdecl program_exit_retain(unsigned,unsigned,unsigned);
extern void __cdecl program_exit_stop(void);
static unsigned owner,minimum,valid;
static unsigned data_segment(void);
#pragma aux data_segment = "mov ax,ds" value [ax] modify [];
static unsigned stack_segment(void);
#pragma aux stack_segment = "mov ax,ss" value [ax] modify [];
static unsigned flags(void);
#pragma aux flags = "pushf" "pop ax" value [ax] modify [];
static unsigned current_psp(void);
#pragma aux current_psp = "mov ah,0x62" "int 0x21" "mov ax,bx" value [ax] modify [ax bx];
static void restore_psp(unsigned);
#pragma aux restore_psp = "mov ah,0x50" "int 0x21" parm [bx] modify [ax];
static unsigned paragraphs(unsigned psp,unsigned floor)
{
 unsigned count;unsigned char __far *mcb;
 if(!psp||*(unsigned __far *)MK_FP(psp,0)!=0x20cd)return 0;
 mcb=MK_FP(psp-1,0);
 if((*mcb!='M'&&*mcb!='Z')||*(unsigned __far *)(mcb+1)!=psp)return 0;
 count=*(unsigned __far *)(mcb+3);
 if(count<floor||psp+count<psp)return 0;
 return count;
}
unsigned __cdecl program_exit_begin(void)
{
 unsigned psp,ds,top,extra;
 if(data_segment()!=stack_segment()||!(flags()&0x200)||native_break_phase()!=BREAK_CLOSED)return 10;
 if(valid)return 10;
 psp=current_psp();ds=data_segment();top=_STACKTOP;
 if(psp!=_psp||ds<psp||!top)return 10;
 /* DOSSEG puts code banks before DGROUP and the CRT stack at its static end.
  * Capture the floor before child execution; retain the entire current block. */
 extra=((top-1)>>4)+1;
 if(ds-psp>65535U-extra)return 10;
 top=ds-psp+extra;
 if(top<0x10||!paragraphs(psp,top))return 10;
 owner=psp;minimum=top;valid=1;return 0;
}
unsigned __cdecl program_exit_finish(unsigned result)
{
 unsigned count;
 if(!valid){program_exit_stop();return 10;}
 if(current_psp()!=owner)restore_psp(owner);
 if(native_break_phase()!=BREAK_CLOSED)native_break_recover();
 if(native_break_phase()==BREAK_CLOSED&&!program_exit_live())return result;
 count=paragraphs(owner,minimum);
 if(!count){program_exit_stop();return 10;}
 /* DOS31 keeps this complete PSP block and its other DOS-owned allocations.
  * No guessed PSP shrink, callback invocation or unknown-vector overwrite. */
 program_exit_retain(owner,count,10);
 program_exit_stop();return 10;
}
