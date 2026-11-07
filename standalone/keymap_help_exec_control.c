/* Test-only external-process placement control. Never an application payload. */
#include <dos.h>
#include <malloc.h>
#include <process.h>
#include <stdio.h>
#include "../src/key_mapping/keymap_help.h"
#include "../src/config/resource_path.h"
unsigned keymap_help_open(const unsigned short *frame)
{
 union REGS r;char path[64],program[64],title[]="PROCOMM PLUS",decimal[11];
 unsigned descriptor[9];int result;
 (void)frame;r.h.ah=0x51;int86(0x21,&r,&r);
 if(resource_program_path(r.x.bx,"PCPLUS.HLP",path)||resource_program_path(r.x.bx,"PCHELP.RTE",program))return 1;
 descriptor[0]=(unsigned)path;descriptor[1]=(unsigned)title;descriptor[2]=17;
 descriptor[3]=0;descriptor[4]=23;descriptor[5]=31;descriptor[6]=113;descriptor[7]=8;descriptor[8]=4;
 sprintf(decimal,"%lu",((unsigned long)FP_SEG((void __far *)descriptor)<<16)|FP_OFF((void __far *)descriptor));
 _fheapshrink();result=spawnl(P_WAIT,program,"PCHELP.RTE","PCHELP",decimal,(char *)0);
 return result<0?2:result?3:0;
}
