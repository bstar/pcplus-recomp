/* Maintained staged input-mode handoff. Native editor shared memory is separate. */
#include "xlt_live.h"
#include "../config/resource_path.h"
#include <string.h>
extern unsigned capture_fs_canonical(const char *,char *);
static struct {
 unsigned ready,mode,current_error,fallback_error,fallback_kind;
 char current[64],fallback[64];
 unsigned char table[256];
} owner;
/* Nonzero serialized guard: the custom DOS host does not promise zeroed BSS. */
static unsigned bound=2;
static unsigned extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned separate(const void *a,unsigned an,const void *b,unsigned bn)
{return (unsigned long)(unsigned)a+an<=(unsigned)b || (unsigned long)(unsigned)b+bn<=(unsigned)a;}
static unsigned external(const void *p,unsigned n)
{return extent(p,n) && separate(p,n,&owner,sizeof(owner)) && separate(p,n,&bound,sizeof(bound));}
static unsigned canonical(const char *source,char *destination,unsigned *error)
{
 char absolute[128];unsigned n;
 memset(absolute,0,sizeof(absolute));*error=capture_fs_canonical(source,absolute);
 if(*error)return 0;
 for(n=0;n<64;++n)if(!absolute[n])break;
 if(!n || n==64)return 0;
 memcpy(destination,absolute,n+1);return 1;
}
unsigned __cdecl xlt_live_bind(unsigned psp)
{
 char path[64];unsigned lookup,current_valid;
 bound=2;memset(&owner,0,sizeof(owner));
 current_valid=canonical("PCPLUS.XLT",owner.current,&owner.current_error);
 lookup=resource_pcplus_path(psp,"PCPLUS.XLT",path);
 owner.fallback_kind=lookup==RESOURCE_PATH_ABSENT?1:2;
 if(lookup==RESOURCE_PATH_OK && canonical(path,owner.fallback,&owner.fallback_error))owner.fallback_kind=0;
 bound=1;return current_valid?XLT_DOS_OK:XLT_DOS_RESOURCE;
}
unsigned __cdecl xlt_live_stage(unsigned mode,xlt_dos_result *result)
{
 unsigned status;
 if(mode>2 || !external(result,sizeof(*result)))return XLT_DOS_ARGUMENT;
 memset(result,0,sizeof(*result));owner.ready=0;
 if(bound!=1){result->status=XLT_LIVE_STATE;return result->status;}
 if(mode==1){
  if(!owner.current[0]){result->status=XLT_DOS_RESOURCE;result->dos_error=owner.current_error;return result->status;}
  status=xlt_dos_read(owner.current,owner.table,result);
  if(status==XLT_DOS_OPEN && (result->dos_error==2 || result->dos_error==3)){
   if(owner.fallback_kind==2){memset(result,0,sizeof(*result));result->status=XLT_DOS_RESOURCE;result->dos_error=owner.fallback_error;return result->status;}
   if(!owner.fallback_kind)status=xlt_dos_read(owner.fallback,owner.table,result);
  }
  if(status)return status;
 }
 owner.mode=mode;owner.ready=1;return XLT_DOS_OK;
}
unsigned __cdecl xlt_live_commit(unsigned mode,unsigned char *table)
{
 if(mode>2 || !external(table,256))return XLT_DOS_ARGUMENT;
 if(bound!=1 || !owner.ready || mode!=owner.mode)return XLT_LIVE_STATE;
 if(mode==1)memcpy(table,owner.table,256);
 owner.ready=0;return XLT_DOS_OK;
}
