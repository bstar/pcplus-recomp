/* Source-owned DOS allocation and synchronous native-reset transaction.
 * The original CRT heap is not copied or emulated here. */
#include "shadow_owner.h"
#include <dos.h>
#include <setjmp.h>
#include <stdlib.h>
#include <string.h>

#define IMAGE_BYTES 0xd600U
#define VIDEO_BYTES 4000U
#define SHADOW_MAX 6336U
#define GUARD_BYTES 16U
typedef struct { unsigned segment,bytes; } block;
extern unsigned char shadow_image[];
extern unsigned shadow_offset,shadow_segment,shadow_bytes,shadow_rows,shadow_columns;
extern unsigned shadow_cga_port,shadow_bios_cursor,shadow_configured_wide;
extern unsigned shadow_status_hidden,shadow_dec_keys,shadow_flags_pointer,shadow_values_pointer;
extern unsigned shadow_viewport_enabled,shadow_logical_columns;
extern unsigned char shadow_flag_plane[],shadow_value_plane[];
extern void __cdecl shadow_native_invoke(unsigned);
extern unsigned __cdecl shadow_entry_flags(void);
static block committed,pending,snapshot;
static unsigned active,release_seen,error_code,saved_cursor,saved_shape;
static jmp_buf unwind;
#ifdef SHADOW_DIAGNOSTIC
unsigned shadow_fail_allocation,shadow_abort_after_allocation,shadow_fail_release;
unsigned shadow_abort_after_reset,shadow_reenter,shadow_reenter_result,shadow_foreign_release;
unsigned shadow_allocations,shadow_releases,shadow_native_errors;
#endif

static unsigned same(void __far *pointer,const block *b)
{return b->segment&&FP_SEG(pointer)==b->segment&&FP_OFF(pointer)==GUARD_BYTES;}
static void __far *payload(const block *b)
{return MK_FP(b->segment,GUARD_BYTES);}
static unsigned guards(const block *b)
{
 unsigned i;unsigned char __far *p;
 if(!b->segment)return 1;
 p=MK_FP(b->segment,0);
 for(i=0;i<GUARD_BYTES;++i)
  if(p[i]!=0xa5||p[GUARD_BYTES+b->bytes+i]!=0xa5)return 0;
 return 1;
}
static unsigned allocate(block *b,unsigned bytes)
{
 unsigned segment,status;unsigned long extent=(unsigned long)bytes+2U*GUARD_BYTES;
 if(b->segment||!bytes||extent>65520UL)return SHADOW_STATE;
#ifdef SHADOW_DIAGNOSTIC
 if(shadow_fail_allocation&&!--shadow_fail_allocation)return SHADOW_MEMORY;
#endif
 status=_dos_allocmem((unsigned)((extent+15UL)>>4),&segment);
 if(status)return SHADOW_MEMORY;
 b->segment=segment;b->bytes=bytes;
 _fmemset(MK_FP(segment,0),0xa5,GUARD_BYTES);
 _fmemset(MK_FP(segment,GUARD_BYTES+bytes),0xa5,GUARD_BYTES);
#ifdef SHADOW_DIAGNOSTIC
 ++shadow_allocations;
#endif
 return SHADOW_OK;
}
static unsigned release(block *b)
{
 unsigned status;
 if(!b->segment)return SHADOW_OK;
 if(!guards(b))return SHADOW_GUARD;
#ifdef SHADOW_DIAGNOSTIC
 if(shadow_fail_release){--shadow_fail_release;return SHADOW_RELEASE;}
#endif
 status=_dos_freemem(b->segment);
 if(status)return SHADOW_RELEASE;
 b->segment=b->bytes=0;
#ifdef SHADOW_DIAGNOSTIC
 ++shadow_releases;
#endif
 return SHADOW_OK;
}
static void abort_native(unsigned error)
{
 error_code=error;
 if(!active)exit(90); /* Diagnostic binding must never be called unowned. */
 longjmp(unwind,1);
}
void __far *__cdecl shadow_allocate(unsigned bytes)
{
 unsigned status;
 if(!active||pending.segment||!bytes||bytes>SHADOW_MAX)
  abort_native(SHADOW_STATE);
 if(committed.segment&&!release_seen)abort_native(SHADOW_STATE);
#ifdef SHADOW_DIAGNOSTIC
 if(shadow_reenter){--shadow_reenter;shadow_reenter_result=shadow_request(0);}
#endif
 status=allocate(&pending,bytes);
 if(status){error_code=status;return 0;}
#ifdef SHADOW_DIAGNOSTIC
 if(shadow_abort_after_allocation){--shadow_abort_after_allocation;abort_native(SHADOW_NATIVE);}
 if(shadow_foreign_release){--shadow_foreign_release;shadow_release_request(MK_FP(0x1234,16));}
#endif
 return payload(&pending);
}
void __cdecl shadow_release_request(void __far *pointer)
{
 if(!active||!same(pointer,&committed)||release_seen)abort_native(SHADOW_STATE);
 release_seen=1; /* Retain old storage until the surrounding reset commits. */
}
void __cdecl shadow_native_error(void)
{
#ifdef SHADOW_DIAGNOSTIC
 ++shadow_native_errors;
#endif
 abort_native(error_code?error_code:SHADOW_NATIVE);
}
static unsigned admitted(void)
{
 union REGS in,out;
 if((shadow_entry_flags()&0x600U)!=0x200U||active||pending.segment||snapshot.segment||shadow_columns!=80||
    shadow_rows!=24||shadow_cga_port||shadow_bios_cursor!=1||
    shadow_status_hidden!=1||shadow_dec_keys!=1||
    shadow_flags_pointer!=(unsigned)shadow_flag_plane||shadow_values_pointer!=(unsigned)shadow_value_plane)
  return 0;
 if(shadow_viewport_enabled!=!!committed.segment||
    shadow_logical_columns!=(committed.segment?132U:80U))return 0;
 if(committed.segment){
  if(!same(MK_FP(shadow_segment,shadow_offset),&committed)||shadow_bytes!=committed.bytes||!guards(&committed))return 0;
 }else if(shadow_segment||shadow_offset)return 0;
 in.h.ah=0x0f;int86(0x10,&in,&out);
 return out.h.al==3&&out.h.ah==80&&out.h.bh==0;
}
static void cursor_save(void)
{
 union REGS in,out;
 in.h.ah=3;in.h.bh=0;int86(0x10,&in,&out);
 saved_cursor=out.x.dx;saved_shape=out.x.cx;
}
static void cursor_restore(void)
{
 union REGS in,out;
 in.h.ah=1;in.x.cx=saved_shape;int86(0x10,&in,&out);
 in.h.ah=2;in.h.bh=0;in.x.dx=saved_cursor;int86(0x10,&in,&out);
}
unsigned __cdecl shadow_request(unsigned wide)
{
 unsigned status;unsigned char __far *copy;
 if(wide>1||!admitted())return SHADOW_STATE;
 error_code=0;release_seen=0;
 status=allocate(&snapshot,IMAGE_BYTES+VIDEO_BYTES+committed.bytes);
 if(status)return status;
 copy=payload(&snapshot);
 _fmemcpy(copy,(void __far *)shadow_image,IMAGE_BYTES);
 _fmemcpy(copy+IMAGE_BYTES,MK_FP(0xb800,0),VIDEO_BYTES);
 if(committed.segment)_fmemcpy(copy+IMAGE_BYTES+VIDEO_BYTES,payload(&committed),committed.bytes);
 cursor_save();active=1;
 if(!setjmp(unwind)){
  shadow_native_invoke(wide);
#ifdef SHADOW_DIAGNOSTIC
  if(shadow_abort_after_reset){--shadow_abort_after_reset;error_code=SHADOW_NATIVE;}
#endif
  if(!guards(&snapshot)||!guards(&pending)||!guards(&committed))error_code=SHADOW_GUARD;
  if(pending.segment){
   if(!same(MK_FP(shadow_segment,shadow_offset),&pending)||shadow_bytes!=pending.bytes)error_code=SHADOW_STATE;
  }else if(shadow_segment||shadow_offset){
   if(!same(MK_FP(shadow_segment,shadow_offset),&committed)||release_seen)error_code=SHADOW_STATE;
  }else if(committed.segment&&!release_seen)error_code=SHADOW_STATE;
 }
 if(error_code){
  /* Synchronous typed errors only: the guarded snapshot and old allocation
   * remain owned. An unknown canary violation is retained for diagnosis. */
  if(!guards(&snapshot)||!guards(&committed)||!guards(&pending)){
   active=0;return SHADOW_GUARD;
  }
  _fmemcpy((void __far *)shadow_image,copy,IMAGE_BYTES);
  _fmemcpy(MK_FP(0xb800,0),copy+IMAGE_BYTES,VIDEO_BYTES);
  if(committed.segment)_fmemcpy(payload(&committed),copy+IMAGE_BYTES+VIDEO_BYTES,committed.bytes);
  cursor_restore();
  status=release(&pending);if(status){active=0;return status;}
 }else if(release_seen){
  status=release(&committed);if(status){active=0;return status;}
 }
 if(!error_code&&pending.segment){committed=pending;pending.segment=pending.bytes=0;}
 active=0;status=release(&snapshot);return status?status:error_code;
}
unsigned __cdecl shadow_close(void)
{
 unsigned status;
 if(active||(shadow_entry_flags()&0x600U)!=0x200U)return SHADOW_STATE;
 status=release(&pending);if(status)return status;
 status=release(&snapshot);if(status)return status;
 status=release(&committed);
 if(!status)shadow_offset=shadow_segment=0;
 return status;
}
unsigned __cdecl shadow_owned_blocks(void)
{return !!committed.segment+!!pending.segment+!!snapshot.segment;}
unsigned __cdecl shadow_last_error(void){return error_code;}
