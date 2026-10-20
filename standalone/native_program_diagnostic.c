#include "native_program.h"
#include "native_display.h"
#include "process_serial.h"
#include <conio.h>
#include <dos.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
unsigned char aspect_serial_test_buffer[128];
extern unsigned char runtime_arena[0x3aca];
extern void __cdecl program_ui_cursor(unsigned);
extern void __cdecl program_ui_scanlines(unsigned);
static unsigned checks,failures,base,vector,mask,wait_ticks,wait_seen,wait_good,wait_prompt,reentry_good;
static void (__interrupt __far *our_uart)(void),(__interrupt __far *old_timer)(void);
static const char prompt[]="Press any key to continue ...";
static native_program_result nested;
static void check(unsigned value,unsigned line){++checks;if(!value){++failures;printf("FAIL %u\n",line);}}
#define CHECK(x) check((x)!=0,__LINE__)
#if defined(NATIVE_PROGRAM_BREAK_OWNER)
#include "break_owner.h"
typedef void (__interrupt __far *break_irq)(void);
static unsigned char break_flag(void)
{union REGS a,b;a.x.ax=0x3300;int86(0x21,&a,&b);return b.h.dl;}
static void set_break_flag(unsigned char flag)
{union REGS a,b;a.x.ax=0x3301;a.h.dl=flag;int86(0x21,&a,&b);}
static unsigned __cdecl checked_program_execute(const char *program,const char *tail,
 unsigned processor,unsigned wait,unsigned save,native_program_result *result)
{
 break_irq one,twenty_three;unsigned char flag,witness[9];unsigned status;FILE *f;
 /* The timer's intentional reentry must perform no DOS operation. */
 if(native_program_busy)return native_program_execute(program,tail,processor,wait,save,result);
 one=_dos_getvect(0x1b);twenty_three=_dos_getvect(0x23);flag=break_flag();
 if(!processor)remove("BRKWIT.BIN");
 status=native_program_execute(program,tail,processor,wait,save,result);
 CHECK(native_break_phase()==BREAK_CLOSED);
 CHECK(_dos_getvect(0x1b)==one&&_dos_getvect(0x23)==twenty_three&&break_flag()==flag);
 if(status==0&&!processor&&(result->process.child_status==37||result->process.child_status==247)){
  f=fopen("BRKWIT.BIN","rb");CHECK(f!=0);
  if(f){CHECK(fread(witness,1,9,f)==9);fclose(f);
   CHECK(*(unsigned *)witness==FP_OFF(one)&&*(unsigned *)(witness+2)==FP_SEG(one));
   CHECK(*(unsigned *)(witness+4)==FP_OFF(twenty_three)&&*(unsigned *)(witness+6)==FP_SEG(twenty_three));
   CHECK(witness[8]==flag);}
 }
 return status;
}
#define native_program_execute checked_program_execute
#endif
static void __interrupt __far timer(void)
{
 if(native_program_waiting&&!wait_seen&&++wait_ticks>=3){
  unsigned i,tail;unsigned __far *video=MK_FP(0xb800,24*160);
  unsigned long irq=*(unsigned long __far *)MK_FP(0,vector*4);
  wait_seen=1;
  wait_good=aspect_serial_active==1&&!aspect_process_serial_detached&&
   inp(base+3)==3&&inp(base+1)==1&&!(inp(0x21)&mask)&&
   irq==((unsigned long)FP_SEG(our_uart)<<16|FP_OFF(our_uart));
  wait_prompt=1;for(i=0;i<sizeof(prompt)-1;++i)if(video[i]!=(0x0e00|prompt[i]))wait_prompt=0;
  /* First line is still child output while WAIT is visible; resetting the
   * parent mode before WAIT would erase it. Native scroll moves X up once. */
  if(*(unsigned __far *)MK_FP(0xb800,0)!=0x1f58)wait_prompt=0;
  nested.status=0xa55a;
  reentry_good=native_program_execute("BAD",0,0,0,1,&nested)==NATIVE_PROGRAM_BUSY&&nested.status==0xa55a;
  tail=*(unsigned __far *)MK_FP(0x40,0x1c);
  *(unsigned __far *)MK_FP(0x40,tail)=0x1177;tail+=2;if(tail>=0x3e)tail=0x1e;
  *(unsigned __far *)MK_FP(0x40,tail)=0x2c7a;tail+=2;if(tail>=0x3e)tail=0x1e;
  *(unsigned __far *)MK_FP(0x40,0x1c)=tail;
 }
 _chain_intr(old_timer);
}
static void mode(unsigned value){union REGS in,out;in.x.ax=value;int86(0x10,&in,&out);}
static unsigned pattern(unsigned i){return (i*37+0x1741)&65535U;}
static void prepare(void)
{
 unsigned i;unsigned __far *video;union REGS in,out;
 mode(3);CHECK(native_display_probe()==0);video=MK_FP(native_display_segment,0);
 for(i=0;i<2000;++i)video[i]=pattern(i);
 in.h.ah=1;in.x.cx=0x0607;int86(0x10,&in,&out);program_ui_cursor(0x070b);
}
static void restored(void)
{
 unsigned i;union REGS in,out;unsigned __far *video=MK_FP(0xb800,0);
 CHECK(native_display_probe()==0&&native_display_columns==80&&native_display_rows==25);
 for(i=0;i<2000;++i)CHECK(video[i]==pattern(i));
 in.h.ah=3;in.h.bh=0;int86(0x10,&in,&out);CHECK(out.x.dx==0x070b&&out.x.cx==0x0607);
 CHECK(!native_display_owned&&!native_program_busy&&!native_process_busy&&!aspect_process_serial_detached);
}
static unsigned send(unsigned byte)
{unsigned long start=aspect_serial_ticks();while(aspect_serial_try_write(byte)){if(aspect_serial_poll()||aspect_serial_ticks()-start>72)return 1;}return 0;}
static unsigned receive(unsigned count)
{unsigned long start=aspect_serial_ticks();while(aspect_serial_available()<count){if(aspect_serial_poll()||aspect_serial_ticks()-start>72)return 1;}return 0;}
static void text_case(const char *child,unsigned value,unsigned rows)
{
 unsigned i,count,height,segment;unsigned __far *video;
 union REGS in,out;native_program_result result;
#if defined(NATIVE_PROGRAM_BREAK_OWNER)
 set_break_flag(value&1);
#endif
 if(rows==43)program_ui_scanlines(1);
 else program_ui_scanlines(2);
 mode(value);
 if(rows!=25){in.x.ax=0x1112;in.x.bx=0;int86(0x10,&in,&out);}
 CHECK(native_display_probe()==0&&native_display_rows==rows);
 count=native_display_bytes/2;segment=native_display_segment;
 height=*(unsigned __far *)MK_FP(0x40,0x85);video=MK_FP(segment,0);
 for(i=0;i<count;++i)video[i]=pattern(i);
 program_ui_cursor(0x070b);in.h.ah=1;in.x.cx=0x0304;int86(0x10,&in,&out);
 CHECK(native_program_execute(child,"S",0,0,1,&result)==0);CHECK(result.process.child_status==37);
 CHECK(native_display_probe()==0&&native_display_rows==rows&&native_display_bytes==count*2&&native_display_segment==segment);
 CHECK(*(unsigned __far *)MK_FP(0x40,0x85)==height);
 for(i=0;i<count;++i)CHECK(video[i]==pattern(i));
 in.h.ah=3;in.h.bh=0;int86(0x10,&in,&out);CHECK(out.x.dx==0x070b&&out.x.cx==0x0304);
 printf("VIEW mode=%u rows=%u bytes=%u\n",value,rows,count*2);
}
int main(int argc,char **argv)
{
 unsigned port,i,j,pic,mcr,lcr,ier,dll,dlm,before,far_before;char child[13],name[13];
 native_program_result result;FILE *held[6],*f;
 void (__interrupt __far *old_uart)(void);
 static char environment[]="CTRLVAR=OWNED";
 static const unsigned char initial[]={0,0x1a,0x80,0xff},after[]={'N','E','X','T'};
 union REGS in,out;
#if defined(NATIVE_PROGRAM_BREAK_OWNER)
 unsigned char caller_break=break_flag();
#endif
 setvbuf(stdout,0,_IONBF,0);if(argc!=2)return 99;
 port=argv[1][2]-'0';base=port==1?0x3f8:0x2f8;vector=port==1?12:11;mask=port==1?16:8;
 old_uart=_dos_getvect(vector);pic=inp(0x21);mcr=inp(base+4);lcr=inp(base+3);
 outp(base+3,lcr&127);ier=inp(base+1);outp(base+3,lcr|128);dll=inp(base);dlm=inp(base+1);outp(base+3,lcr);
 outp(base+4,mcr|1);CHECK(aspect_serial_open(argv[1])==0);our_uart=_dos_getvect(vector);
#if defined(NATIVE_PROGRAM_BREAK_OWNER)
 set_break_flag(0);
#endif
 CHECK(putenv(environment)==0);
 for(i=0;i<6;++i){sprintf(name,"HOLD%u.DAT",i);held[i]=fopen(name,"wb+");CHECK(held[i]!=0);
  if(!held[i])return 99;for(j=0;j<256;++j)fputc(j,held[i]);fflush(held[i]);CHECK(fseek(held[i],i+9,SEEK_SET)==0);}
 for(i=0;i<sizeof(runtime_arena);++i)runtime_arena[i]=(i*17+31)&255;
 sprintf(child,"OWN%u",port);
 CHECK(send('D')==0);CHECK(receive(4)==0);CHECK(aspect_serial_read()==0);CHECK(aspect_serial_rx_count==3);
 prepare();CHECK(native_program_execute(child,"S",0,0,1,&result)==0);CHECK(result.process.child_status==37);restored();
 CHECK(_dos_getvect(vector)==our_uart&&aspect_serial_active==1);CHECK(aspect_serial_rx_count==3);
 CHECK(aspect_serial_unread()==0);for(i=0;i<4;++i)CHECK(aspect_serial_read()==initial[i]);
 CHECK(send('R')==0);CHECK(receive(4)==0);for(i=0;i<4;++i)CHECK(aspect_serial_read()==after[i]);
 prepare();CHECK(native_program_execute(child,"N",0,0,0,&result)==0);CHECK(result.process.child_status==37&&!result.view_reset);
 CHECK(*(unsigned __far *)MK_FP(0xb800,0)==0x2e4e);
 in.h.ah=3;in.h.bh=0;int86(0x10,&in,&out);CHECK(out.x.dx==0x070b&&out.x.cx==0x0607);
 prepare();CHECK(native_program_execute(child,"T",0,0,0,&result)==0);
 CHECK(result.process.child_status==247&&result.view_reset==1);CHECK(*(unsigned __far *)MK_FP(0xb800,0)==0x2e4e);
 prepare();old_timer=_dos_getvect(0x1c);_dos_setvect(0x1c,timer);
 CHECK(native_program_execute(child,"W",0,1,1,&result)==0);_dos_setvect(0x1c,old_timer);
 CHECK(result.process.child_status==37&&result.wait_key==0x1177);CHECK(wait_seen&&wait_good&&wait_prompt&&reentry_good);restored();
 in.h.ah=0;int86(0x16,&in,&out);CHECK(out.x.ax==0x2c7a);
 prepare();CHECK(native_program_execute(child,"G",0,0,0,&result)==0);CHECK(result.process.child_status==37&&result.view_reset==1);
 CHECK(native_display_probe()==0&&native_display_rows==25);
 text_case(child,1,25);text_case(child,2,25);text_case(child,7,25);text_case(child,3,43);text_case(child,3,50);
 prepare();CHECK(native_program_execute("NO-SUCH.COM",0,0,0,1,&result)==NATIVE_PROGRAM_PROCESS);
 CHECK(result.process.status==NATIVE_PROCESS_EXEC);restored();
 prepare();native_display_fail_alloc=1;
 CHECK(native_program_execute(child,"S",0,0,1,&result)==NATIVE_PROGRAM_DISPLAY);native_display_fail_alloc=0;
 CHECK(result.display_status==NATIVE_DISPLAY_MEMORY);restored();
 prepare();native_fail_near=1;
 CHECK(native_program_execute(child,"S",0,0,1,&result)==NATIVE_PROGRAM_PROCESS);native_fail_near=0;
 CHECK(result.process.status==NATIVE_PROCESS_MEMORY||result.process.status==NATIVE_PROCESS_EXEC);restored();
 prepare();before=native_near_calls;far_before=native_far_calls;native_fail_at=before+2;
 CHECK(native_program_execute(child,"S",0,0,1,&result)==0);native_fail_at=0;
 CHECK(result.process.child_status==37&&native_far_calls==far_before+1&&native_near_calls==before+2);restored();
 CHECK(native_program_execute(0,0,0,0,1,&result)==NATIVE_PROGRAM_ARGUMENT);
 CHECK(native_program_execute(child,0,2,0,1,&result)==NATIVE_PROGRAM_ARGUMENT);
 CHECK(native_program_execute(child,0,0,2,1,&result)==NATIVE_PROGRAM_ARGUMENT);
 CHECK(native_program_execute(child,0,0,0,2,&result)==NATIVE_PROGRAM_ARGUMENT);
 prepare();CHECK(native_display_capture()==0);before=native_display_frees;
 CHECK(native_program_execute(child,"S",0,0,1,&result)==NATIVE_PROGRAM_BUSY);
 CHECK(native_display_owned&&native_display_frees==before);native_display_discard();restored();
 prepare();CHECK(aspect_serial_compile_pause()==0);
 CHECK(native_program_execute(child,"S",0,0,1,&result)==NATIVE_PROGRAM_SERIAL);
 CHECK(result.serial_status==ASPECT_SERIAL_BUSY&&aspect_serial_active==1&&!aspect_process_serial_detached);
 CHECK(aspect_serial_compile_resume()==0);restored();
 before=native_display_allocs;mode(0x13);
 CHECK(native_program_execute(child,"S",0,0,1,&result)==NATIVE_PROGRAM_DISPLAY);CHECK(native_display_allocs==before);
 mode(3);in.x.ax=0x0501;int86(0x10,&in,&out);
 CHECK(native_program_execute(child,"S",0,0,1,&result)==NATIVE_PROGRAM_DISPLAY);CHECK(native_display_allocs==before);
 prepare();CHECK(native_program_execute("ver > SYS.OUT",0,1,0,1,&result)==0);
 CHECK(result.process.child_status==0&&result.process.crt_error==0&&result.process.dos_error==0);restored();
 f=fopen("SYS.OUT","rb");CHECK(f!=0);if(f){CHECK(fgetc(f)!=EOF);fclose(f);}
 for(i=0;i<sizeof(runtime_arena);++i)CHECK(runtime_arena[i]==((i*17+31)&255));
 for(i=0;i<6;++i){CHECK(ftell(held[i])==(long)i+9);CHECK(fgetc(held[i])==(int)i+9);fclose(held[i]);}
 CHECK(strcmp(getenv("CTRLVAR"),"OWNED")==0);
 CHECK(send('F')==0);CHECK(receive(4)==0);
 CHECK(aspect_serial_read()=='E');CHECK(aspect_serial_read()=='N');CHECK(aspect_serial_read()=='D');CHECK(aspect_serial_read()=='!');
 CHECK(aspect_serial_close()==0);CHECK(_dos_getvect(vector)==old_uart);CHECK(inp(0x21)==pic);
 CHECK(inp(base+4)==(mcr|1));CHECK(inp(base+3)==(lcr&127)&&inp(base+1)==ier);
 outp(base+3,lcr|128);CHECK(inp(base)==dll&&inp(base+1)==dlm);outp(base+3,lcr);outp(base+4,mcr);
 prepare();CHECK(native_program_execute("ver > CLOSED.OUT",0,1,0,1,&result)==0);restored();
 CHECK(!aspect_serial_active&&_dos_getvect(vector)==old_uart&&inp(0x21)==pic);
 f=fopen("CHILD.OUT","rb");CHECK(f!=0);if(f){char b[5];CHECK(fread(b,1,5,f)==5);CHECK(b[0]=='C'&&b[1]=='O'&&b[2]=='M'&&b[3]=='0'+port&&b[4]=='S');fclose(f);}
 /* Give DOSBox's separate nullmodem packet-flush timer one BIOS tick after
  * the hardware TEMT drain, so emulator exit cannot erase its final XOFF. */
 {unsigned long tick=aspect_serial_ticks();while(aspect_serial_ticks()==tick);}
#if defined(NATIVE_PROGRAM_BREAK_OWNER)
 CHECK(native_break_phase()==BREAK_CLOSED);set_break_flag(caller_break);
#endif
 printf("PROGRAM COM%u %c %u checks %u failures\n",port,argv[1][12],checks,failures);
 return failures?1:0;
}
