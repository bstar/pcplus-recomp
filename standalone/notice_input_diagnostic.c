#include "notice.h"
#include "notice_input.h"
#include "notice_unwind.h"
#include <dos.h>
#include <malloc.h>
#include <setjmp.h>
#include <stdio.h>
#include <string.h>
extern unsigned mouse_scale_x,mouse_count,mouse_code,mouse_button_pending;
extern unsigned char mouse_enabled[6];
extern unsigned __cdecl mouse_test_emit(unsigned,unsigned,unsigned);
extern unsigned __cdecl mouse_platform_size(void);
extern void __cdecl mouse_platform_save(void __far *);
extern void __far mouse_test_prior_callback(void);
static unsigned checks,failures,polls,jump;
static jmp_buf outer;
static void check(unsigned pass,unsigned line)
{++checks;if(!pass){++failures;printf("FAIL %u\n",line);}}
#define CHECK(x) check((x)!=0,__LINE__)
static unsigned __cdecl service(void)
{
 ++polls;CHECK(notice_input_close()==MOUSE_STATE);
 if(jump)longjmp(outer,1);
 return 0;
}
static void exchange(void (__far *callback)(void),unsigned mask)
{
 union REGS in,out;struct SREGS s;
 segread(&s);s.es=FP_SEG(callback);in.x.ax=0x14;in.x.cx=mask;in.x.dx=FP_OFF(callback);int86x(0x33,&in,&out,&s);
}
static void seed(unsigned key)
{union REGS in,out;in.x.ax=0x0500;in.x.cx=key;int86(0x16,&in,&out);CHECK(out.h.al==0);}
static void __interrupt __far replaced(void){}
int main(void)
{
 mouse_settings settings={8,4,{1,1,1,1,1,1}};
 notice_options options={0x70,0,74,1000000UL,service,0};notice_result result;
 unsigned i,key,bytes,status;unsigned char native[28];
 unsigned char __far *before;
 unsigned char __far *after;
 void (__interrupt __far *vector)(void);
 bytes=mouse_platform_size();CHECK(bytes>0&&bytes<65504U);
 before=_fmalloc(bytes);after=_fmalloc(bytes);if(!before||!after)return 90;
 exchange(mouse_test_prior_callback,11);mouse_platform_save(before);
 memcpy(native,&mouse_scale_x,22);memcpy(native+22,mouse_enabled,6);
 vector=_dos_getvect(0x33);
 CHECK(notice_input_close()==MOUSE_OK);
 settings.scale_x=0;CHECK(notice_input_open(&settings)==MOUSE_ARGUMENT);
 CHECK(mouse_owner_phase()==MOUSE_CLOSED&&notice_input_close()==MOUSE_OK);settings.scale_x=8;
 CHECK(mouse_owner_open(&settings)==MOUSE_OK);
 CHECK(notice_input_open(&settings)==MOUSE_STATE);
 CHECK(notice_input_close()==MOUSE_STATE&&mouse_owner_phase()==MOUSE_READY);
 key=0xa55a;CHECK(notice_input_peek(&key)==MOUSE_STATE&&key==0xa55a);
 CHECK(notice_input_read(&key)==MOUSE_STATE&&key==0xa55a);
 CHECK(mouse_owner_close()==MOUSE_OK);
 CHECK(notice_input_open(&settings)==MOUSE_OK);
 CHECK(notice_input_open(&settings)==MOUSE_STATE);
 key=0xa55a;CHECK(notice_input_peek(&key)==MOUSE_PENDING&&key==0xa55a);
 CHECK(notice_input_peek(0)==MOUSE_ARGUMENT);
 seed(0x1e61);seed(0x3062);
 CHECK(mouse_test_emit(1,0,(unsigned)-8)==1);CHECK(mouse_count==2);
 for(i=0;i<4;++i){key=0xa55a;CHECK(notice_input_peek(&key)==MOUSE_OK&&key==0x4800&&mouse_count==2);}
 for(i=0;i<2;++i){
  status=notice_show("Native mouse repetition",0,&options,&result);
  CHECK(status==NOTICE_KEY&&result.key==0x4800&&mouse_count==1-i&&!notice_active());
 }
 status=notice_show("BIOS normalized a",0,&options,&result);CHECK(status==NOTICE_KEY&&result.key=='a');
 status=notice_show("BIOS normalized b",0,&options,&result);CHECK(status==NOTICE_KEY&&result.key=='b');
 CHECK(mouse_test_emit(2,0,(unsigned)-8)==1);
 key=0xa55a;CHECK(notice_input_peek(&key)==MOUSE_OK&&key==0x1c0d&&mouse_count==1);
 status=notice_show("Mouse Enter",0,&options,&result);CHECK(status==NOTICE_KEY&&result.key==13&&mouse_count==0&&mouse_button_pending==0);
 CHECK(mouse_test_emit(8,0,(unsigned)-8)==1);
 CHECK(notice_input_peek(&key)==MOUSE_OK&&key==0x011b&&mouse_count==1);
 status=notice_show("Mouse Escape",0,&options,&result);CHECK(status==NOTICE_CANCELLED&&result.key==27&&mouse_count==0);
 seed(0x011b);seed(0x2c7a);
 status=notice_show("BIOS Escape preserves typeahead",0,&options,&result);CHECK(status==NOTICE_CANCELLED&&result.key==27);
 CHECK(notice_input_read(&key)==MOUSE_OK&&key=='z');
 options.timeout_ticks=2;options.service=0;
 status=notice_show("Bounded idle",0,&options,&result);CHECK(status==NOTICE_TIMEOUT&&!notice_active());
 options.timeout_ticks=74;options.service=service;jump=1;
 if(!setjmp(outer)){
  notice_show("Outer jump",0,&options,&result);CHECK(0);
 }else{
  CHECK(notice_active()&&mouse_owner_phase()==MOUSE_READY);
  CHECK(notice_input_close()==MOUSE_STATE);
  CHECK(notice_unwind(&result)==NOTICE_OK&&!notice_active());
 }
 jump=0;CHECK(notice_input_close()==MOUSE_OK);
 mouse_platform_save(after);CHECK(!_fmemcmp(before,after,bytes));
 CHECK(!memcmp(native,&mouse_scale_x,22)&&!memcmp(native+22,mouse_enabled,6));
 CHECK(notice_input_open(&settings)==MOUSE_OK);
 _dos_setvect(0x33,replaced);
 options.service=0;status=notice_show("Changed driver vector",0,&options,&result);
 CHECK(status==NOTICE_INPUT&&result.service_status==MOUSE_STATE&&!notice_active());
 CHECK(mouse_owner_phase()==MOUSE_QUARANTINED&&mouse_owner_bytes()==bytes);
 CHECK(notice_input_close()==MOUSE_STATE&&mouse_owner_bytes()==bytes);
 _dos_setvect(0x33,vector);CHECK(notice_input_close()==MOUSE_OK);
 mouse_platform_save(after);CHECK(!_fmemcmp(before,after,bytes));
 CHECK(!memcmp(native,&mouse_scale_x,22)&&!memcmp(native+22,mouse_enabled,6));
 CHECK(notice_input_close()==MOUSE_OK&&polls>0);
#ifdef NOTICE_INPUT_BIOS_FALLBACK
 _dos_setvect(0x33,0);
 CHECK(notice_input_open(&settings)==MOUSE_OK&&notice_input_active()==2);
 CHECK(mouse_owner_phase()==MOUSE_CLOSED&&mouse_owner_bytes()==0);
 seed(0x1c0d);seed(0x011b);seed(0x2c7a);
 CHECK(notice_input_peek(&key)==MOUSE_OK&&key==0x1c0d);
 status=notice_show("No mouse: BIOS Enter",0,&options,&result);CHECK(status==NOTICE_KEY&&result.key==13);
 status=notice_show("No mouse: BIOS Escape",0,&options,&result);CHECK(status==NOTICE_CANCELLED&&result.key==27);
 CHECK(notice_input_read(&key)==MOUSE_OK&&key=='z');
 CHECK(notice_input_close()==MOUSE_OK&&!notice_input_active());
 _dos_setvect(0x33,vector);mouse_platform_save(after);CHECK(!_fmemcmp(before,after,bytes));
 CHECK(!memcmp(native,&mouse_scale_x,22)&&!memcmp(native+22,mouse_enabled,6));
#endif
 exchange(0,0);_ffree(before);_ffree(after);
 printf("NINPUT checks=%u failures=%u driver_bytes=%u\n",checks,failures,bytes);
 return failures?1:0;
}
