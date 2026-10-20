#include "owner.h"
#include <dos.h>
#include <malloc.h>
#include <string.h>
#if defined(MOUSE_DOS_PLATFORM)
typedef void (__interrupt __far *mouse_vector)(void);
extern void __far * __cdecl mouse_platform_allocate(unsigned);
extern unsigned __cdecl mouse_platform_release(void __far *);
extern mouse_vector __cdecl mouse_platform_vector(void);
static void copy_bytes(void *destination,const void *source,unsigned bytes)
{unsigned i;for(i=0;i<bytes;++i)((unsigned char *)destination)[i]=((const unsigned char *)source)[i];}
static void fill_bytes(void __far *destination,unsigned value,unsigned bytes)
{unsigned i;for(i=0;i<bytes;++i)((unsigned char __far *)destination)[i]=(unsigned char)value;}
#define OWNER_ALLOC(n) mouse_platform_allocate(n)
#define OWNER_RELEASE(p) mouse_platform_release(p)
#define OWNER_VECTOR() mouse_platform_vector()
#define OWNER_COPY(d,s,n) copy_bytes(d,s,n)
#define OWNER_FILL(p,v,n) fill_bytes(p,v,n)
#else
static unsigned release_storage(void __far *pointer){_ffree(pointer);return 0;}
#define OWNER_ALLOC(n) _fmalloc(n)
#define OWNER_RELEASE(p) release_storage(p)
#define OWNER_VECTOR() _dos_getvect(0x33)
#define OWNER_COPY(d,s,n) memcpy(d,s,n)
#define OWNER_FILL(p,v,n) _fmemset(p,v,n)
#endif
extern unsigned mouse_scale_x,mouse_scale_y,mouse_present,mouse_count,mouse_code;
extern unsigned char mouse_enabled[6];
extern unsigned __cdecl mouse_platform_size(void),mouse_platform_reset(void),mouse_platform_depth(void);
extern void __cdecl mouse_platform_save(void __far *),mouse_platform_restore(void __far *);
extern void __cdecl mouse_platform_init(unsigned,unsigned);
extern unsigned __cdecl mouse_platform_poll(void),mouse_platform_read(void);
static unsigned same_segments(void);
#pragma aux same_segments = "mov ax,ds" "mov dx,ss" "sub ax,dx" "neg ax" "sbb ax,ax" "inc ax" value [ax] modify [dx];
static unsigned interrupts_on(void);
#pragma aux interrupts_on = "pushf" "pop ax" "and ax,0x200" value [ax] modify [];
static struct {
 unsigned phase,bytes,mutated;
 unsigned char __far *storage;
 void (__interrupt __far *vector)(void);
 mouse_settings settings;
 unsigned char native[28];
} held;
static unsigned extent(const void *p,unsigned bytes)
{return p&&(unsigned long)(unsigned)p+bytes<=65536UL;}
static unsigned valid(const mouse_settings *s)
{
 unsigned i;
 if(!extent(s,sizeof(*s))||s->scale_x<1||s->scale_x>999||s->scale_y<1||s->scale_y>999)return 0;
 for(i=0;i<6;++i)if(s->enabled[i]>1)return 0;
 return 1;
}
unsigned __cdecl mouse_settings_decode(const unsigned char *image,unsigned bytes,mouse_settings *out)
{
 mouse_settings candidate;unsigned i;
 if(!same_segments()||bytes!=0x4f0||!extent(image,bytes)||!extent(out,sizeof(*out))||
    ((unsigned long)(unsigned)image<(unsigned long)(unsigned)out+sizeof(*out)&&
     (unsigned long)(unsigned)out<(unsigned long)(unsigned)image+bytes))return MOUSE_ARGUMENT;
 candidate.scale_x=image[0x4e4]|((unsigned)image[0x4e5]<<8);
 candidate.scale_y=image[0x4e6]|((unsigned)image[0x4e7]<<8);
 for(i=0;i<6;++i)candidate.enabled[i]=1;
 if(!valid(&candidate))return MOUSE_ARGUMENT;
 OWNER_COPY(out,&candidate,sizeof(candidate));return MOUSE_OK;
}
unsigned __cdecl mouse_owner_phase(void){return held.phase;}
unsigned __cdecl mouse_owner_bytes(void){return held.bytes;}
static unsigned guards(void)
{
 unsigned i;
 if(!held.storage||!held.bytes)return 0;
 for(i=0;i<16;++i)if(held.storage[i]!=0xa5||held.storage[16+held.bytes+i]!=0x5a)return 0;
 return 1;
}
static unsigned intact(void)
{return guards()&&OWNER_VECTOR()==held.vector&&mouse_platform_size()==held.bytes;}
static unsigned quarantine(void){held.phase=MOUSE_QUARANTINED;return MOUSE_STATE;}
unsigned __cdecl mouse_owner_open(const mouse_settings *settings)
{
 unsigned bytes;
 void (__interrupt __far *vector)(void);
 unsigned char __far *storage;
 if(!same_segments()||!interrupts_on()||!valid(settings))return MOUSE_ARGUMENT;
 if(held.phase!=MOUSE_CLOSED||mouse_platform_depth()!=65535U)return MOUSE_STATE;
 vector=OWNER_VECTOR();if(!vector)return MOUSE_DRIVER;
 bytes=mouse_platform_size();if(!bytes||bytes>65503U)return MOUSE_DRIVER;
 storage=OWNER_ALLOC(bytes+32);if(!storage)return MOUSE_MEMORY;
 if((unsigned long)FP_OFF(storage)+bytes+32>65536UL){OWNER_RELEASE(storage);return MOUSE_MEMORY;}
 OWNER_FILL(storage,0xa5,16);OWNER_FILL(storage+16+bytes,0x5a,16);
 mouse_platform_save(storage+16);
 /* Publish storage before the first driver mutation, so close can recover. */
 held.storage=storage;held.bytes=bytes;held.vector=vector;held.mutated=0;
 OWNER_COPY(&held.settings,settings,sizeof(held.settings));
 OWNER_COPY(held.native,&mouse_scale_x,22);OWNER_COPY(held.native+22,mouse_enabled,6);
 held.phase=MOUSE_QUARANTINED;
 if(!intact()){
  /* No driver mutation yet: a rejected snapshot owns only this allocation. */
  if(OWNER_RELEASE(storage))return MOUSE_STATE;
  held.storage=0;held.bytes=0;held.phase=MOUSE_CLOSED;return MOUSE_STATE;
 }
 held.mutated=1;
 OWNER_COPY(mouse_enabled,held.settings.enabled,6);
 mouse_platform_init(held.settings.scale_x,held.settings.scale_y);
 if(!mouse_present||!intact())return MOUSE_DRIVER;
 held.phase=MOUSE_READY;return MOUSE_OK;
}
unsigned __cdecl mouse_owner_suspend(void)
{
 if(!same_segments()||!interrupts_on())return MOUSE_ARGUMENT;
 if(held.phase!=MOUSE_READY)return MOUSE_STATE;
 if(!intact()||mouse_platform_depth()!=65535U)return quarantine();
 held.phase=MOUSE_QUARANTINED;
 if(!mouse_platform_reset())return MOUSE_DRIVER;
 if(!intact())return MOUSE_STATE;
 held.phase=MOUSE_SUSPENDED;return MOUSE_OK;
}
unsigned __cdecl mouse_owner_resume(void)
{
 if(!same_segments()||!interrupts_on())return MOUSE_ARGUMENT;
 if(held.phase!=MOUSE_SUSPENDED)return MOUSE_STATE;
 if(!intact()||mouse_platform_depth()!=65535U)return quarantine();
 held.phase=MOUSE_QUARANTINED;
 OWNER_COPY(mouse_enabled,held.settings.enabled,6);
 mouse_platform_init(held.settings.scale_x,held.settings.scale_y);
 if(!mouse_present||!intact())return MOUSE_DRIVER;
 held.phase=MOUSE_READY;return MOUSE_OK;
}
unsigned __cdecl mouse_owner_close(void)
{
 if(!same_segments()||!interrupts_on())return MOUSE_ARGUMENT;
 if(held.phase==MOUSE_CLOSED)return MOUSE_OK;
 if(held.mutated){
  if(!intact()||mouse_platform_depth()!=65535U)return quarantine();
  held.phase=MOUSE_QUARANTINED;
  mouse_platform_restore(held.storage+16);
  if(!intact())return MOUSE_STATE;
  OWNER_COPY(&mouse_scale_x,held.native,22);OWNER_COPY(mouse_enabled,held.native+22,6);
  held.mutated=0;
 }
 if(OWNER_RELEASE(held.storage))return quarantine();
 held.storage=0;held.bytes=0;held.phase=MOUSE_CLOSED;
 return MOUSE_OK;
}
unsigned __cdecl mouse_owner_key(unsigned *key)
{
 if(!same_segments()||!interrupts_on()||!extent(key,sizeof(*key)))return MOUSE_ARGUMENT;
 if(held.phase!=MOUSE_READY)return MOUSE_STATE;
 if(mouse_platform_depth()!=65535U||mouse_scale_x!=held.settings.scale_x||
    mouse_scale_y!=held.settings.scale_y||(mouse_count&&mouse_code>=6)||!intact())return quarantine();
 if(!mouse_platform_poll())return MOUSE_PENDING;
 *key=mouse_platform_read();return MOUSE_OK;
}
