#include "compiler_lease.h"
#include <i86.h>
#include "compiler_lease_private.h"
#ifdef COMPILER_LEASE_BANKED
#pragma code_seg("LEASE_BANK", "LEASE_BANK")
#else
#pragma code_seg("LEASE_CODE", "FARCODE")
#endif
static unsigned word_at(unsigned seg,unsigned offset)
{return *(unsigned __far *)MK_FP(seg,offset);}
static unsigned block(unsigned psp,unsigned size)
{
 unsigned char type;
 if(!psp || psp>=0xa000 || size<16 || size>0xa000-psp)return 0;
 type=*(unsigned char __far *)MK_FP(psp-1,0);
 return (type=='M'||type=='Z') && word_at(psp-1,1)==psp && word_at(psp-1,3)==size && word_at(psp,0)==0x20cd;
}
static unsigned identity(unsigned token,unsigned owner)
{
 return lease_dos_context() && held.cookie==COOKIE && token==held.token && owner && owner!=held.parent &&
  lease_dos_psp()==owner && word_at(owner,0)==0x20cd && word_at(owner,0x16)==held.parent &&
  word_at(owner-1,1)==owner;
}
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
static unsigned cleanup(void)
{
 unsigned status=0;
 if(held.handle!=65535U){status=lease_dos_close(held.handle);held.handle=65535U;if(status)return failure(CL_IO);}
 if(held.created){if(lease_dos_unlink(held.name))return failure(CL_IO);held.created=0;}
 held.phase=CL_IDLE;held.owner=0;return 0;
}
static unsigned reserve(void)
{
 unsigned drive,i,n=3,j,value,attempt,exists;
 drive=lease_dos_drive();if(drive>25)return CL_ARGUMENT;
 if(lease_dos_cwd(held.cwd))return failure(CL_IO);
 held.name[0]=(unsigned char)('A'+drive);held.name[1]=':';held.name[2]='\\';
 for(i=0;i<64 && held.cwd[i];++i){if(i==63)return CL_ARGUMENT;held.name[n++]=held.cwd[i];}
 if(n>3)held.name[n++]='\\';
 for(attempt=0;attempt<64;++attempt){
  value=held.sequence++;
  held.name[n]='L';held.name[n+1]='P';held.name[n+2]='M';held.name[n+3]='0';
  for(j=0;j<4;++j){i=(value>>(j*4))&15;held.name[n+7-j]=(unsigned char)(i<10?'0'+i:'A'+i-10);}
  held.name[n+8]='.';held.name[n+9]='T';held.name[n+10]='M';held.name[n+11]='P';held.name[n+12]=0;
  /* Keep exclusive creation authoritative. Avoid opening existing names:
   * DOSBox-X2026.07.02's6C failure path leaks its preliminary open handle. */
  exists=lease_dos_exists(held.name);
  if(exists==1)continue;
  if(exists==65535U)return failure(CL_IO);
  held.handle=lease_dos_create(held.name);
  if(held.handle!=65535U){held.created=1;return 0;}
  if(lease_dos_error()!=80)return failure(CL_IO);
 }
 held.dos_error=80;return CL_IO; /* All reserved names already exist. */
}
unsigned __far __cdecl compiler_lease_init(unsigned parent,unsigned keep,unsigned token)
{
 unsigned full,i;
 if(!lease_dos_context() || lease_dos_psp()!=parent)return CL_IDENTITY;
 if(held.cookie==COOKIE && (held.phase!=CL_IDLE || held.busy))return CL_STATE;
 full=word_at(parent-1,3);
 if(!token || !block(parent,full) || keep<16 || keep>=full)return CL_ARGUMENT;
 /* Caller is the parent. Link audit, not a child-supplied scalar, proves the
  * resident extent. Never expose init on the future child bridge. */
 for(i=0;i<STATE_BYTES;++i)((unsigned char __far *)&held)[i]=0;
 held.cookie=COOKIE;held.parent=parent;held.keep=keep;held.full=full;held.token=token;
 held.handle=65535U;held.valid=1;return 0;
}
#ifdef COMPILER_LEASE_BANKED
unsigned __far __cdecl compiler_lease_prepare(unsigned token,unsigned owner)
#else
unsigned __far __cdecl compiler_lease_begin(unsigned token,unsigned owner)
#endif
{
 unsigned status,seg,remaining,paras,n,i;unsigned char __far *p;
 if(held.cookie==COOKIE && held.busy)return CL_STATE;
 if(!identity(token,owner))return CL_IDENTITY;
 if(held.phase!=CL_IDLE)return CL_STATE;
 held.full=word_at(held.parent-1,3);
 if(!block(held.parent,held.full) || held.keep>=held.full ||
    (owner>=held.parent && owner<held.parent+held.full))return CL_IDENTITY;
 if(lease_dos_version()<4)return CL_UNSUPPORTED;
 held.busy=1;held.owner=owner;held.phase=CL_BACKING;held.dos_error=0;
 status=reserve();if(status)goto unchanged;
 seg=held.parent+held.keep;remaining=held.full-held.keep;held.crc=0xffff;
 while(remaining){
  paras=remaining>CHUNK_PARAS?CHUNK_PARAS:remaining;n=paras<<4;p=MK_FP(seg,0);
  held.crc=checksum(held.crc,p,n);
  if(lease_dos_write(held.handle,p,n)!=n){status=failure(CL_IO);goto unchanged;}
  seg+=paras;remaining-=paras;
 }
 /* Close flushes, then reopen no-inherit. Never retain an ambiguous handle
  * after DOS close errors: DOS may have closed it even on an error return. */
 status=lease_dos_close(held.handle);held.handle=65535U;
 if(status){status=failure(CL_IO);goto unchanged;}
 held.handle=lease_dos_open(held.name);if(held.handle==65535U){status=failure(CL_IO);goto unchanged;}
 seg=held.parent+held.keep;remaining=held.full-held.keep;
 while(remaining){
  paras=remaining>VERIFY_PARAS?VERIFY_PARAS:remaining;n=paras<<4;p=MK_FP(seg,0);
  if(lease_dos_read(held.handle,held.buffer,n)!=n){status=failure(CL_IO);goto unchanged;}
  for(i=0;i<n;++i)if(p[i]!=held.buffer[i]){status=CL_CORRUPT;goto unchanged;}
  seg+=paras;remaining-=paras;
 }
 if(lease_dos_read(held.handle,held.buffer,1)!=0){status=CL_CORRUPT;goto unchanged;}
 if(lease_dos_rewind(held.handle)){status=failure(CL_IO);goto unchanged;}
#ifdef COMPILER_LEASE_BANKED
 held.phase=CL_PREPARED;return done(0);
#else
 status=lease_dos_resize(held.parent,held.keep);
 if(status){status=failure(CL_RESIZE);goto unchanged;}
 held.valid=0;held.phase=CL_LENT;return done(0);
#endif
unchanged:
 held.valid=1;held.phase=CL_CLEANUP;
 /* Preserve the original failure; cleanup failure leaves owned state for
  * retry, and blocks beginning a different lease. */
 cleanup();return done(status);
}
#ifdef COMPILER_LEASE_BANKED
unsigned __far __cdecl compiler_lease_finalize(unsigned token,unsigned owner)
{
 if(held.cookie==COOKIE && held.busy)return CL_STATE;
 if(!identity(token,owner))return CL_IDENTITY;
 if(owner!=held.owner || held.phase!=CL_CLEANUP || !held.valid ||
    !block(held.parent,held.full))return CL_STATE;
 held.busy=1;return done(cleanup());
}
#else
unsigned __far __cdecl compiler_lease_end(unsigned token,unsigned owner)
{
 unsigned seg,remaining,paras,n,crc=0xffff,actual;
 if(held.cookie==COOKIE && held.busy)return CL_STATE;
 if(!identity(token,owner))return CL_IDENTITY;
 if(owner!=held.owner || held.phase==CL_IDLE || held.phase==CL_BACKING)return CL_STATE;
 held.busy=1;
 if(held.phase==CL_CLEANUP)return done(cleanup());
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
 if(lease_dos_read(held.handle,held.buffer,1)!=0 || crc!=held.crc)return done(CL_CORRUPT);
 held.valid=1;held.phase=CL_CLEANUP;return done(cleanup());
}
unsigned __far __cdecl compiler_lease_info(unsigned selector)
{
 if(held.cookie!=COOKIE)return 65535U;
 if(selector==0)return held.phase;if(selector==1)return held.full;if(selector==2)return held.keep;
 if(selector==3)return held.valid;if(selector==4)return held.dos_error;if(selector==5)return held.crc;
 if(selector==6)return held.parent;if(selector==7)return held.owner;if(selector==8)return held.handle;
 if(selector==9)return held.sequence;
 return 65535U;
}

#endif
