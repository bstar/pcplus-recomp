#include "owner.h"
#include <dos.h>
#include <malloc.h>
#include <process.h>
#include <stdio.h>
#include <string.h>
extern unsigned mouse_scale_x,mouse_scale_y,mouse_present,mouse_count,mouse_code,mouse_button_pending;
extern unsigned char mouse_enabled[6];
extern unsigned __cdecl mouse_test_emit(unsigned,unsigned,unsigned);
extern unsigned __cdecl mouse_platform_size(void);
extern void __cdecl mouse_platform_save(void __far *);
extern void __far mouse_test_prior_callback(void);
static unsigned checks,failures;
static unsigned char image[0x4f0],native[28];
static void check(unsigned pass,unsigned line)
{++checks;if(!pass){++failures;printf("FAIL %u\n",line);}}
#define CHECK(x) check((x)!=0,__LINE__)
static void exchange(void (__far *callback)(void),unsigned mask)
{
 union REGS in,out;struct SREGS segments;
 segread(&segments);segments.es=FP_SEG(callback);in.x.ax=0x14;in.x.cx=mask;in.x.dx=FP_OFF(callback);
 int86x(0x33,&in,&out,&segments);
}
static void seed_key(void)
{union REGS in,out;in.x.ax=0x0500;in.x.cx=0x256b;int86(0x16,&in,&out);CHECK(out.h.al==0);}
static unsigned bios_peek(void)
{union REGS in,out;in.x.ax=0x0100;int86(0x16,&in,&out);return out.x.ax;}
int main(void)
{
 mouse_settings settings,untouched;unsigned key,i,bytes;
 unsigned char __far *before;
 unsigned char __far *after;
 void (__interrupt __far *vector)(void);
 memset(image,0xa5,sizeof(image));image[0x4e4]=8;image[0x4e5]=0;image[0x4e6]=4;image[0x4e7]=0;
 CHECK(mouse_settings_decode(image,sizeof(image),&settings)==MOUSE_OK);
 CHECK(settings.scale_x==8&&settings.scale_y==4);
 for(i=0;i<6;++i)CHECK(settings.enabled[i]==1);
 untouched=settings;image[0x4e4]=0;
 CHECK(mouse_settings_decode(image,sizeof(image),&settings)==MOUSE_ARGUMENT);
 CHECK(!memcmp(&settings,&untouched,sizeof(settings)));image[0x4e4]=8;
 settings.scale_y=0;CHECK(mouse_owner_open(&settings)==MOUSE_ARGUMENT);
 CHECK(mouse_owner_phase()==MOUSE_CLOSED&&mouse_owner_bytes()==0);settings=untouched;
 bytes=mouse_platform_size();CHECK(bytes>0&&bytes<65504U);
 before=_fmalloc(bytes);after=_fmalloc(bytes);if(!before||!after)return 90;
 vector=_dos_getvect(0x33);
 exchange(mouse_test_prior_callback,0x0b);
 mouse_platform_save(before);
 mouse_scale_x=6;mouse_scale_y=7;mouse_present=0;mouse_count=2;mouse_code=3;mouse_button_pending=1;
 memcpy(native,&mouse_scale_x,22);memcpy(native+22,mouse_enabled,6);
 CHECK(mouse_owner_open(&settings)==MOUSE_OK);
 CHECK(mouse_owner_phase()==MOUSE_READY&&mouse_owner_bytes()==bytes);
 CHECK(mouse_owner_open(&settings)==MOUSE_STATE);
 seed_key();CHECK(mouse_test_emit(1,16,8)==1);
 key=0xaaaa;CHECK(mouse_owner_key(&key)==MOUSE_OK&&key==0x4d00&&mouse_count==1);
 CHECK(bios_peek()==0x256b);
 CHECK(mouse_owner_key(&key)==MOUSE_OK&&key==0x4d00&&mouse_count==0);
 CHECK(mouse_owner_key(&key)==MOUSE_OK&&key=='k');
 key=0xaaaa;CHECK(mouse_owner_key(&key)==MOUSE_PENDING&&key==0xaaaa);
 CHECK(mouse_test_emit(0x0a,16,8)==1);
 CHECK(mouse_owner_key(&key)==MOUSE_OK&&key==13&&mouse_button_pending==0);
 CHECK(mouse_test_emit(8,16,8)==1);
 CHECK(mouse_owner_key(&key)==MOUSE_OK&&key==27);
 CHECK(mouse_owner_suspend()==MOUSE_OK&&mouse_owner_phase()==MOUSE_SUSPENDED);
 CHECK(mouse_owner_key(&key)==MOUSE_STATE);
 CHECK(spawnl(P_WAIT,"MUTATE.COM","MUTATE.COM",(char *)0)==37);
 CHECK(mouse_owner_resume()==MOUSE_OK&&mouse_owner_phase()==MOUSE_READY);
 CHECK(mouse_scale_x==8&&mouse_scale_y==4&&mouse_count==0);
 CHECK(mouse_test_emit(1,16,8)==1);
 CHECK(mouse_owner_key(&key)==MOUSE_OK&&key==0x4d00);
 CHECK(mouse_owner_suspend()==MOUSE_OK);
 CHECK(spawnl(P_WAIT,"VECTOR.COM","VECTOR.COM",(char *)0)==37);
 CHECK(mouse_owner_resume()==MOUSE_STATE&&mouse_owner_phase()==MOUSE_QUARANTINED);
 CHECK(mouse_owner_close()==MOUSE_STATE&&mouse_owner_bytes()==bytes);
 _dos_setvect(0x33,vector);
 CHECK(mouse_owner_close()==MOUSE_OK&&mouse_owner_phase()==MOUSE_CLOSED&&mouse_owner_bytes()==0);
 CHECK(!memcmp(native,&mouse_scale_x,22)&&!memcmp(native+22,mouse_enabled,6));
 mouse_platform_save(after);CHECK(!_fmemcmp(before,after,bytes));
 CHECK(mouse_owner_close()==MOUSE_OK);
 exchange(0,0);_ffree(before);_ffree(after);
 printf("MOUSEKEY checks=%u failures=%u driver_bytes=%u\n",checks,failures,bytes);
 return failures?1:0;
}
