#include "native_display.h"
#include "native_process.h"
#include <dos.h>
#include <malloc.h>
#include <stdio.h>
static unsigned checks,failures;
static void check(unsigned value,unsigned line){++checks;if(!value){++failures;printf("FAIL %u\n",line);}}
#define CHECK(x) check((x)!=0,__LINE__)
static void mode(unsigned value){union REGS in,out;in.x.ax=value;int86(0x10,&in,&out);}
static unsigned cell(unsigned i){return (i*37+0x1741)&65535U;}
static void fill(unsigned pattern)
{unsigned i;unsigned __far *video=MK_FP(native_display_segment,0);for(i=0;i<native_display_bytes/2;++i)video[i]=pattern?0xa55a:cell(i);}
static void compare(void)
{unsigned i;unsigned __far *video=MK_FP(native_display_segment,0);for(i=0;i<native_display_bytes/2;++i)CHECK(video[i]==cell(i));}
static void text_case(unsigned value,unsigned columns,unsigned rows)
{
 unsigned before=native_display_frees;
 mode(value);CHECK(native_display_probe()==0);CHECK(native_display_columns==columns&&native_display_rows==rows);
 fill(0);CHECK(native_display_capture()==0);CHECK(native_display_capture()==NATIVE_DISPLAY_BUSY);
 fill(1);CHECK(native_display_restore()==0);CHECK(!native_display_owned&&native_display_frees==before+1);compare();
 CHECK(native_display_restore()==NATIVE_DISPLAY_STATE);native_display_discard();CHECK(native_display_frees==before+1);
 printf("TEXT mode=%u columns=%u rows=%u bytes=%u\n",value,columns,rows,native_display_bytes);
}
int main(void)
{
 union REGS in,out;native_process_result result;unsigned before;
 setvbuf(stdout,0,_IONBF,0);
 text_case(1,40,25);text_case(3,80,25);text_case(7,80,25);
 mode(3);in.x.ax=0x1112;in.x.bx=0;int86(0x10,&in,&out);
 CHECK(native_display_probe()==0);CHECK(native_display_rows==50);fill(0);
 CHECK(native_display_capture()==0);fill(1);CHECK(native_display_restore()==0);compare();
 mode(3);CHECK(native_display_probe()==0);fill(0);native_display_fail_alloc=1;
 CHECK(native_display_capture()==NATIVE_DISPLAY_MEMORY);CHECK(!native_display_owned);compare();native_display_fail_alloc=0;
 CHECK(native_display_capture()==0);before=native_display_frees;
 CHECK(native_process_run("VIDEO.COM",0,0,1,&result)==0);CHECK(result.child_status==37);
 CHECK(native_display_restore()==NATIVE_DISPLAY_STATE);CHECK(native_display_owned&&native_display_frees==before);
 mode(3);CHECK(native_display_restore()==0);compare();
 CHECK(native_display_capture()==0);mode(0x13);before=native_display_frees;
 native_display_discard();CHECK(!native_display_owned&&native_display_frees==before+1);
 CHECK(native_display_probe()==NATIVE_DISPLAY_STATE);CHECK(native_display_capture()==NATIVE_DISPLAY_STATE);
 mode(3);in.x.ax=0x0501;int86(0x10,&in,&out);
 CHECK(native_display_capture()==NATIVE_DISPLAY_STATE);mode(3);
 {unsigned char __far *rows=MK_FP(0x40,0x84);unsigned char old=*rows;
  before=native_display_allocs;*rows=255;
  CHECK(native_display_capture()==NATIVE_DISPLAY_STATE);CHECK(native_display_allocs==before);*rows=old;}
 CHECK(native_display_allocs==native_display_frees+1); /* One deliberately failed allocation. */
 printf("DISPLAY %u checks %u failures\n",checks,failures);
 return failures?1:0;
}
