#include <dos.h>
#include "meta_loader.h"
#define CODE __based(__segname("_CODE"))
typedef struct meta_load_expected {
 unsigned magic,version,bytes,relocations;
 unsigned long crc;
 unsigned code_segment,data_segment,arena_segment,arena_bytes;
} meta_load_expected;
/* Patched only by the source-linked MZ extractor. Never inferred addresses. */
meta_load_expected CODE meta_loader_expected={0x4d4c,1,0,0,0,0,0,0,0};
typedef char expected_size[sizeof(meta_load_expected)==20?1:-1];
typedef struct meta_load_state {
 unsigned phase,reason,dos_error,opened,at,fix,base,segment,previous;
 int handle;
 unsigned long crc;
} meta_load_state;
static meta_load_state CODE state={0};
static const char CODE leaf[]="PCMETA.OVL";
unsigned __far __cdecl meta_loader_path(unsigned,const char *,char *);
unsigned __far __cdecl meta_key_owner_exec_allowed(void);
unsigned __cdecl meta_load_fs_open(const char *,int *);
unsigned __cdecl meta_load_fs_read(int,void __far *,unsigned,unsigned *);
unsigned __cdecl meta_load_fs_close(int);
static unsigned current_ss(void);
#pragma aux current_ss="mov ax,ss" value [ax];
static unsigned current_ds(void);
#pragma aux current_ds="mov ax,ds" value [ax];
static unsigned close_owned(void)
{
 unsigned e;if(!state.opened)return META_LOAD_OK;
 state.opened=0;e=meta_load_fs_close(state.handle);
 if(e){if(!state.dos_error)state.dos_error=e;state.phase=META_LOAD_HELD;state.reason=META_LOAD_RECOVERY;return META_LOAD_RECOVERY;}
 return META_LOAD_OK;
}
static unsigned fail(unsigned reason,unsigned dos)
{
 if(!state.reason)state.reason=reason;if(dos && !state.dos_error)state.dos_error=dos;
 if(close_owned())return META_LOAD_RECOVERY;
 state.phase=META_LOAD_FAILED;return state.reason;
}
unsigned __far __cdecl meta_loader_begin(unsigned psp,unsigned granted)
{
 char name[11],path[64];unsigned i,e,base,segment;unsigned long end;int handle;
 if(state.phase==META_LOAD_HELD)return META_LOAD_RECOVERY;
 if(state.phase!=META_LOAD_EMPTY)return META_LOAD_STATE;
 if(!granted)return META_LOAD_BUSY;
 if(current_ds()!=current_ss() || meta_loader_expected.magic!=0x4d4c || meta_loader_expected.version!=1 || meta_loader_expected.bytes<256 || meta_loader_expected.bytes>24000 || meta_loader_expected.relocations>512 || meta_loader_expected.arena_bytes!=63000 || meta_loader_expected.code_segment<meta_loader_expected.arena_segment || meta_loader_expected.code_segment-meta_loader_expected.arena_segment!=1024)return META_LOAD_ARGUMENT;
 if(current_ss()<meta_loader_expected.data_segment)return META_LOAD_ARGUMENT;
 base=current_ss()-meta_loader_expected.data_segment;
 if(psp>0xffef || psp+16!=base)return META_LOAD_ARGUMENT;
 end=(unsigned long)base+meta_loader_expected.arena_segment;
 if(end>=0xa000UL || end*16UL+63000UL>0xa0000UL)return META_LOAD_ARGUMENT;
 end=(unsigned long)base+meta_loader_expected.code_segment;segment=(unsigned)end;
 if(end>=0xa000UL || (unsigned long)meta_loader_expected.bytes+2UL*meta_loader_expected.relocations+16385UL>61000UL)return META_LOAD_ARGUMENT;
 state.phase=META_LOAD_READING;state.reason=state.dos_error=state.opened=state.at=state.fix=state.previous=0;
 state.handle=-1;state.base=base;state.segment=segment;state.crc=0xffffffffUL;
 for(i=0;i<11;++i)name[i]=leaf[i];
 e=meta_loader_path(psp,name,path);if(e)return fail(META_LOAD_ARGUMENT,0);
 e=meta_load_fs_open(path,&handle);if(e)return fail(META_LOAD_IO,e);
 state.handle=handle;state.opened=1;return META_LOAD_OK;
}
unsigned __far __cdecl meta_loader_step(unsigned admitted)
{
 unsigned total,n,actual=0,e,i,off,value;unsigned char __far *bytes;
 unsigned __far *words;unsigned long crc;
 if(state.phase==META_LOAD_HELD)return META_LOAD_RECOVERY;
 if(state.phase!=META_LOAD_READING && state.phase!=META_LOAD_FIXING)return META_LOAD_STATE;
 if(!admitted)return META_LOAD_BUSY;
 total=meta_loader_expected.bytes+2*meta_loader_expected.relocations;
 bytes=MK_FP(state.segment,state.at);
 if(state.phase==META_LOAD_READING){
  n=total-state.at;if(n>512)n=512;
  if(n){
   e=meta_load_fs_read(state.handle,bytes,n,&actual);
   if(e || actual!=n)return fail(META_LOAD_IO,e);
   crc=state.crc;
   for(i=0;i<n;++i){unsigned bit;crc^=bytes[i];for(bit=0;bit<8;++bit)crc=(crc>>1)^((crc&1)?0xedb88320UL:0);}
   state.crc=crc;state.at+=n;return META_LOAD_OK;
  }
  e=meta_load_fs_read(state.handle,bytes,1,&actual);
  if(e || actual)return fail(META_LOAD_IO,e);
  if(close_owned())return META_LOAD_RECOVERY;
  if((~state.crc)!=meta_loader_expected.crc)return fail(META_LOAD_IDENTITY,0);
  state.phase=META_LOAD_FIXING;return META_LOAD_OK;
 }
 words=MK_FP(state.segment,meta_loader_expected.bytes);
 for(i=0;i<32 && state.fix<meta_loader_expected.relocations;++i){
  off=words[state.fix];
  if(off>meta_loader_expected.bytes-2 || (state.fix && (state.previous>65533U || off<state.previous+2)))return fail(META_LOAD_FIXUP,0);
  value=*(unsigned __far *)MK_FP(state.segment,off);
  if((unsigned long)value+state.base>=0xa000UL)return fail(META_LOAD_FIXUP,0);
  *(unsigned __far *)MK_FP(state.segment,off)=value+state.base;
  state.previous=off;++state.fix;
 }
 if(state.fix==meta_loader_expected.relocations)state.phase=META_LOAD_READY;
 return META_LOAD_OK;
}
unsigned __far __cdecl meta_loader_enter(void)
{
 if(state.phase==META_LOAD_HELD)return META_LOAD_RECOVERY;
 if(state.phase!=META_LOAD_READY)return META_LOAD_STATE;
 state.phase=META_LOAD_ACTIVE;return META_LOAD_OK;
}
unsigned __far __cdecl meta_loader_release(void)
{
 if(state.phase==META_LOAD_HELD)return META_LOAD_RECOVERY;
 if(state.phase!=META_LOAD_READY && state.phase!=META_LOAD_ACTIVE)return META_LOAD_STATE;
 if(!meta_key_owner_exec_allowed())return META_LOAD_BUSY;
 state.phase=META_LOAD_EMPTY;return META_LOAD_OK;
}
unsigned __far __cdecl meta_loader_cancel(void)
{
 if(state.phase==META_LOAD_HELD)return META_LOAD_RECOVERY;
 if(state.phase==META_LOAD_READY || state.phase==META_LOAD_ACTIVE)return META_LOAD_STATE;
 if(close_owned())return META_LOAD_RECOVERY;
 state.phase=META_LOAD_EMPTY;return META_LOAD_OK;
}
unsigned __far __cdecl meta_loader_hold(void)
{
 if(state.phase==META_LOAD_HELD)return META_LOAD_RECOVERY;
 if(state.phase!=META_LOAD_ACTIVE)return META_LOAD_STATE;
 state.phase=META_LOAD_HELD;state.reason=META_LOAD_RECOVERY;return META_LOAD_RECOVERY;
}
unsigned __far __cdecl meta_loader_inspect(unsigned selector)
{
 switch(selector){case META_LOAD_PHASE:return state.phase;case META_LOAD_REASON:return state.reason;case META_LOAD_DOS_ERROR:return state.dos_error;case META_LOAD_READ_AT:return state.at;case META_LOAD_FIX_AT:return state.fix;case META_LOAD_HANDLE_OPEN:return state.opened;case META_LOAD_BYTES:return meta_loader_expected.bytes;case META_LOAD_RELOCATIONS:return meta_loader_expected.relocations;case META_LOAD_BASE:return state.base;case META_LOAD_SEGMENT:return state.segment;default:return 0xffff;}
}
