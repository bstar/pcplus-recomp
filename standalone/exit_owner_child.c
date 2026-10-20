#include "exit_owner.h"
#include "break_owner.h"
#include <dos.h>
#include <i86.h>
#include <stdio.h>
#include <string.h>
static volatile unsigned hits;
static unsigned live;
unsigned __cdecl program_exit_live(void){return live;}
static void __interrupt __far foreign(void){++hits;}
static unsigned psp(void);
#pragma aux psp = "mov ah,0x62" "int 0x21" "mov ax,bx" value [ax] modify [ax bx];
static void setpsp(unsigned);
#pragma aux setpsp = "mov ah,0x50" "int 0x21" parm [bx] modify [ax];
static void cli(void);
#pragma aux cli = "cli" modify [];
static void sti(void);
#pragma aux sti = "sti" modify [];
extern unsigned char native_break_original_1b[9];
int main(int argc,char **argv)
{
 unsigned record[13],extra,token=0,status,i;char mode;FILE *file;
 union REGS a,b;
 if(argc!=2)return 90;mode=argv[1][0];
 a.x.ax=0x3301;a.h.dl=argv[1][1]-'0';int86(0x21,&a,&b);
 cli();status=program_exit_begin();sti();if(status!=10)return 91;
 if(program_exit_begin()||program_exit_begin()!=10)return 92;
 if(_dos_allocmem(0x20,&extra))return 93;
 for(i=0;i<256;++i)((unsigned __far *)MK_FP(extra,0))[i]=0xa55a;
 if(mode!='N'&&mode!='L'){
  if(native_break_open(1))return 94;
  if(mode=='Q')_dos_setvect(0x1b,foreign);
  if(mode=='D')native_break_original_1b[0]^=1;
  if((mode=='Q'||mode=='D')&&native_break_close()!=BREAK_QUARANTINE)return 95;
 }
 live=mode=='L';
 if(mode=='P'&&_dos_allocmem(0x10,&token))return 96;
 record[0]=0x5845;record[1]=mode;record[2]=psp();
 record[3]=*(unsigned __far *)MK_FP(record[2]-1,3);
 record[4]=extra;record[5]=0x20;record[6]=FP_OFF(foreign);record[7]=FP_SEG(foreign);
 record[8]=FP_OFF((void __far *)&hits);record[9]=FP_SEG((void __far *)&hits);
 record[10]=native_break_phase();record[11]=argv[1][1]-'0';record[12]=live;
 file=fopen("EXITWIT.BIN","wb");if(!file)return 97;
 status=fwrite(record,sizeof(record),1,file)!=1;status|=fclose(file)!=0;if(status)return 98;
 if(token)setpsp(token);
 return program_exit_finish(37);
}
