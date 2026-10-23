#include "notice_input.h"
#include "notice_input_exit.h"
#include <dos.h>
#include <stdio.h>
extern unsigned _psp,mouse_count;
/* Controlled unrelated-lease boundaries for the bank's ASPECT exit predicate. */
unsigned native_process_busy,native_program_busy,native_program_waiting;
unsigned process_handles_active,aspect_process_serial_detached,aspect_serial_active;
unsigned runtime_external_scope_storage,runtime_external_invocation_active;
unsigned runtime_keyboard_mode;
static unsigned data_segment(void);
#pragma aux data_segment = "mov ax,ds" value [ax] modify [];
static void registration(unsigned *v)
{
 union REGS a,b;struct SREGS s;
 segread(&s);s.es=0;a.x.ax=0x14;a.x.cx=a.x.dx=0;int86x(0x33,&a,&b,&s);
 v[0]=b.x.cx;v[1]=b.x.dx;v[2]=s.es;
 a=b;a.x.ax=0x14;int86x(0x33,&a,&b,&s);
}
int main(int argc,char **argv)
{
 mouse_settings settings={8,4,{1,1,1,1,1,1}};
 unsigned record[12],v[3],extra,i;FILE *file;
 if(argc!=2)return 90;
 if(notice_input_exit_prepare())return 91;
 if(notice_input_open(&settings))return notice_input_exit_finish(93);
 if(_dos_allocmem(0x20,&extra))return notice_input_exit_finish(94);
 for(i=0;i<256;++i)((unsigned __far *)MK_FP(extra,0))[i]=0xa55a;
 registration(v);
 record[0]=0x4e49;record[1]=_psp;record[2]=*(unsigned __far *)MK_FP(_psp-1,3);
 record[3]=v[1];record[4]=v[2];record[5]=FP_OFF((void __far *)&mouse_count);
 record[6]=data_segment();record[7]=extra;record[8]=0x20;record[9]=argv[1][0]=='C';
 record[10]=mouse_owner_phase();record[11]=mouse_owner_bytes();
 file=fopen("INPUTWIT.BIN","wb");if(!file)return notice_input_exit_finish(95);
 if(fwrite(record,sizeof(record),1,file)!=1||fclose(file))return notice_input_exit_finish(96);
 if(record[9]&&notice_input_close())return notice_input_exit_finish(97);
 return notice_input_exit_finish(77);
}
