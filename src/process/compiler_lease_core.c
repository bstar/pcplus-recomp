/* Maintained source component. Runs on the authenticated child DS=SS stack.
 * Every instruction/callee/state byte here must remain below the lease cut.
 * PREPARE returns out of the bank before shrink. END restores and verifies
 * the entire bank before invoking FINALIZE. No bank call in quarantine. */
#include "compiler_lease_private.h"
#pragma code_seg("LEASE_CORE", "FARCODE")
extern unsigned __far __cdecl compiler_lease_prepare(unsigned,unsigned);
extern unsigned __far __cdecl compiler_lease_finalize(unsigned,unsigned);
extern unsigned char __far compiler_lease_bank_start;
extern unsigned char __far compiler_lease_bank_end;
static unsigned word_at(unsigned seg,unsigned offset)
{return *(unsigned __far *)MK_FP(seg,offset);}
#ifdef COMPILER_LEASE_COMPACT
extern unsigned __far __cdecl lease_core_block(unsigned,unsigned);
extern unsigned __far __cdecl lease_core_checksum(unsigned,unsigned,unsigned);
#define block lease_core_block
#define checksum(c,p,n) lease_core_checksum(c,FP_SEG(p),n)
#else
static unsigned block(unsigned psp,unsigned size)
{
 unsigned char type;
 if(!psp || psp>=0xa000 || size<16 || size>0xa000-psp)return 0;
 type=*(unsigned char __far *)MK_FP(psp-1,0);
 return (type=='M'||type=='Z') && word_at(psp-1,1)==psp && word_at(psp-1,3)==size && word_at(psp,0)==0x20cd;
}
#endif
#ifndef COMPILER_LEASE_COMPACT
static unsigned identity(unsigned token,unsigned owner)
{
 return lease_dos_context() && held.cookie==COOKIE && token==held.token && owner && owner!=held.parent &&
  lease_dos_psp()==owner && word_at(owner,0)==0x20cd && word_at(owner,0x16)==held.parent &&
  word_at(owner-1,1)==owner;
}
#endif
#ifndef COMPILER_LEASE_COMPACT
static unsigned checksum(unsigned crc,const unsigned char __far *p,unsigned n)
{
 unsigned i,b;
 for(i=0;i<n;++i){crc^=p[i];for(b=0;b<8;++b)crc=(crc>>1)^((crc&1)?0xa001:0);}
 return crc;
}
static unsigned failure(unsigned code)
{held.dos_error=lease_dos_error();return code;}
static unsigned done(unsigned code)
{held.busy=0;return code;}

unsigned __far __cdecl compiler_lease_begin(unsigned token,unsigned owner)
{
 unsigned status;
 if(held.cookie==COOKIE && held.busy)return CL_STATE;
 if(!identity(token,owner))return CL_IDENTITY;
 if(held.phase!=CL_IDLE)return CL_STATE;
 status=compiler_lease_prepare(token,owner);if(status)return status;
 /* No frame/return address in the bank survives this call. */
 held.busy=1;
 if(lease_dos_resize(held.parent,held.keep)){
  status=failure(CL_RESIZE);held.phase=CL_CLEANUP;held.busy=0;
  compiler_lease_finalize(token,owner);return status;
 }
 held.valid=0;held.phase=CL_LENT;return done(0);
}
unsigned __far __cdecl compiler_lease_end(unsigned token,unsigned owner)
{
 unsigned seg,remaining,paras,n,crc=0xffff,actual;
 if(held.cookie==COOKIE && held.busy)return CL_STATE;
 if(!identity(token,owner))return CL_IDENTITY;
 if(owner!=held.owner || (held.phase!=CL_LENT && held.phase!=CL_RESTORING && held.phase!=CL_CLEANUP))return CL_STATE;
 if(held.phase==CL_CLEANUP){
  if(!held.valid || !block(held.parent,held.full))return CL_STATE;
  return compiler_lease_finalize(token,owner);
 }
 held.busy=1;
 actual=word_at(held.parent-1,3);
 if(!block(held.parent,actual) || actual<held.keep || actual>held.full)return done(CL_IDENTITY);
 if(actual!=held.full && lease_dos_resize(held.parent,held.full))return done(failure(CL_RESTORE));
 held.phase=CL_RESTORING;
 if(lease_dos_rewind(held.handle))return done(failure(CL_IO));
 seg=held.parent+held.keep;remaining=held.full-held.keep;
 while(remaining){
  paras=remaining>CHUNK_PARAS?CHUNK_PARAS:remaining;n=paras<<4;
  if(lease_dos_read(held.handle,MK_FP(seg,0),n)!=n)return done(failure(CL_IO));
  crc=checksum(crc,MK_FP(seg,0),n);seg+=paras;remaining-=paras;
 }
 if(lease_dos_read(held.handle,held_buffer,1)!=0 || crc!=held.crc)return done(CL_CORRUPT);
 held.valid=1;held.phase=CL_CLEANUP;held.busy=0;
 return compiler_lease_finalize(token,owner);
}
unsigned __far __cdecl compiler_lease_info(unsigned selector)
{
 if(held.cookie!=COOKIE)return 65535U;
 if(selector==0)return held.phase;if(selector==1)return held.full;if(selector==2)return held.keep;
 if(selector==3)return held.valid;if(selector==4)return held.dos_error;if(selector==5)return held.crc;
 if(selector==6)return held.parent;if(selector==7)return held.owner;if(selector==8)return held.handle;
 if(selector==9)return held.sequence;
 if(selector==10)return FP_SEG(&compiler_lease_bank_start);
 if(selector==11)return FP_OFF(&compiler_lease_bank_start);
 if(selector==12)return FP_OFF(&compiler_lease_bank_end)-FP_OFF(&compiler_lease_bank_start);
 return 65535U;
}

#endif
#ifdef COMPILER_LEASE_MODULE
/* Trusted parent-only cold entry. Caller must hold the inactive overlay arena;
 * this does not grant permission to overwrite a live menu or snapshot. No DOS
 * child bridge may expose it. Load/check/fix first, enter bank only when valid. */
typedef struct {unsigned magic,version,bytes,fixups,crc,target,keep;} lease_module;
extern const lease_module __far compiler_lease_expected;
extern unsigned __far __cdecl compiler_lease_init(unsigned,unsigned,unsigned);
unsigned __far __cdecl compiler_lease_load(const char *path,unsigned parent,unsigned token)
{
 unsigned fd,n,status,seg,crc,at,previous=0,value,i,actual,base=parent+16;
 unsigned char __far *body;
 const lease_module __far *m=&compiler_lease_expected;
 if(!lease_dos_context() || lease_dos_psp()!=parent)return CL_IDENTITY;
 if(held.cookie==COOKIE && (held.phase!=CL_IDLE || held.busy))return CL_STATE;
 if(!token || m->magic!=0x4342 || m->version!=1 || m->bytes<2 || m->bytes>4096 ||
    m->fixups>256 || m->target>0x9fff-base || m->keep<16)return CL_ARGUMENT;
 n=m->bytes+m->fixups*2;seg=base+m->target;actual=word_at(parent-1,3);
 if(!block(parent,actual) || m->keep>=actual ||
    seg<parent+m->keep || seg+(n+15)/16>parent+actual ||
    FP_SEG(&compiler_lease_bank_start)!=seg || FP_OFF(&compiler_lease_bank_start)!=0 ||
    FP_OFF(&compiler_lease_bank_end)!=m->bytes)return CL_ARGUMENT;
 fd=lease_dos_open((const unsigned char __far *)path);if(fd==65535U)return CL_IO;
 body=MK_FP(seg,0);status=0;
 if(lease_dos_read(fd,body,n)!=n || lease_dos_read(fd,held_buffer,1)!=0)status=CL_IO;
 if(lease_dos_close(fd))status=CL_IO;
 if(status)return status;
 crc=checksum(0xffff,body,n);if(crc!=m->crc)return CL_CORRUPT;
 /* Validate the complete fixup table before changing any loaded word. */
 for(i=0;i<m->fixups;++i){
  at=*(unsigned __far *)(body+m->bytes+i*2);
  if(at>m->bytes-2 || (i && at<previous+2))return CL_CORRUPT;
  value=*(unsigned __far *)(body+at);
  if(value>0x9fff-base)return CL_CORRUPT;
  previous=at;
 }
 for(i=0;i<m->fixups;++i){
  at=*(unsigned __far *)(body+m->bytes+i*2);
  *(unsigned __far *)(body+at)+=base;
 }
 return compiler_lease_init(parent,m->keep,token);
}
#endif
