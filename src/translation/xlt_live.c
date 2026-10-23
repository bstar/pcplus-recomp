/* Maintained staged input-mode handoff. Native editor shared memory is separate. */
#include "xlt_live.h"
#include "../config/resource_path.h"
#include <string.h>
extern unsigned capture_fs_canonical(const char *,char *);
static struct {
 unsigned ready,mode,current_error,fallback_error,fallback_kind,selected,reload;
 char current[64],fallback[64];
 unsigned char table[256];
} owner;
/* Nonzero serialized guard: the custom DOS host does not promise zeroed BSS. */
static unsigned bound=2;
static unsigned active_bound=2;
static char active_path[64];
static unsigned extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned separate(const void *a,unsigned an,const void *b,unsigned bn)
{return (unsigned long)(unsigned)a+an<=(unsigned)b || (unsigned long)(unsigned)b+bn<=(unsigned)a;}
static unsigned external(const void *p,unsigned n)
{return extent(p,n) && separate(p,n,&owner,sizeof(owner)) && separate(p,n,&bound,sizeof(bound)) &&
 separate(p,n,&active_bound,sizeof(active_bound)) && separate(p,n,active_path,sizeof(active_path));}
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
 memset(result,0,sizeof(*result));owner.ready=owner.reload=0;
 if(bound!=1){result->status=XLT_LIVE_STATE;return result->status;}
 if(mode==1){
  if(!owner.current[0]){result->status=XLT_DOS_RESOURCE;result->dos_error=owner.current_error;return result->status;}
  owner.selected=1;status=xlt_dos_read(owner.current,owner.table,result);
  if(status==XLT_DOS_OPEN && (result->dos_error==2 || result->dos_error==3)){
   if(owner.fallback_kind==2){memset(result,0,sizeof(*result));result->status=XLT_DOS_RESOURCE;result->dos_error=owner.fallback_error;return result->status;}
   if(!owner.fallback_kind){owner.selected=2;status=xlt_dos_read(owner.fallback,owner.table,result);}
  }
  if(status)return status;
 }
 owner.mode=mode;owner.ready=1;return XLT_DOS_OK;
}
unsigned __cdecl xlt_live_commit(unsigned mode,unsigned char *table)
{
 if(mode>2 || !external(table,256))return XLT_DOS_ARGUMENT;
 if(bound!=1 || !owner.ready || mode!=owner.mode)return XLT_LIVE_STATE;
 if(mode==1){
  memcpy(table,owner.table,256);
  memcpy(active_path,owner.selected==2?owner.fallback:owner.current,64);
 }else active_path[0]=0;
 active_bound=1;owner.ready=owner.reload=0;return XLT_DOS_OK;
}

#ifdef TERMINAL_HOOK_INPUT
unsigned __cdecl xlt_live_offer(unsigned mode,unsigned char *table)
{
 if(mode>2 || !external(table,256))return XLT_DOS_ARGUMENT;
 if(bound!=1 || !owner.ready || mode!=owner.mode)return XLT_LIVE_STATE;
 if(mode==1)memcpy(table,owner.table,256);
 return XLT_DOS_OK;
}
#endif
#ifdef TERMINAL_HOOK_APPLY
unsigned __cdecl xlt_live_commit_check(unsigned mode,unsigned char *table)
{
 if(mode>2 || !external(table,256))return XLT_DOS_ARGUMENT;
 return bound==1 && owner.ready && mode==owner.mode?XLT_DOS_OK:XLT_LIVE_STATE;
}
void __cdecl xlt_live_publish(unsigned mode,unsigned char *table)
{
 if(mode==1){memcpy(table,owner.table,256);memcpy(active_path,owner.selected==2?owner.fallback:owner.current,64);}
 else active_path[0]=0;
 active_bound=1;owner.ready=owner.reload=0;
}
#endif

/* Startup uses the same staged reader as live changes. Remember the actual
 * chosen canonical source only after the checked read and commit succeed. */
unsigned __cdecl xlt_live_initialize(unsigned psp,unsigned mode,const char *path,
 unsigned char *table,xlt_dos_result *result)
{
 char fallback[64];unsigned status,n,lookup;
 if(mode>2 || !external(table,256) || !external(result,sizeof(*result)) ||
    !separate(table,256,result,sizeof(*result)) || (path && mode!=1))return XLT_DOS_ARGUMENT;
 if(path){
  for(n=0;n<64;++n){if(!external(path,n+1))return XLT_DOS_ARGUMENT;if(!path[n])break;}
  if(!n || n==64 || !separate(path,n+1,table,256) ||
     !separate(path,n+1,result,sizeof(*result)))return XLT_DOS_ARGUMENT;
 }
 active_bound=bound=2;active_path[0]=0;memset(&owner,0,sizeof(owner));
 memset(result,0,sizeof(*result));
 if(mode!=1){active_bound=1;return XLT_DOS_OK;}
 owner.fallback_kind=1;bound=1;
 {
  if(!canonical(path?path:"PCPLUS.XLT",owner.current,&owner.current_error)){
   result->status=XLT_DOS_RESOURCE;result->dos_error=owner.current_error;return result->status;
  }
 }
 status=xlt_live_stage(1,result);
 /* Preserve startup's lazy lookup: a valid or damaged current file must not
  * inspect PCPLUS at all. Only missing default files enable environment IO. */
 if(!path && status==XLT_DOS_OPEN && (result->dos_error==2 || result->dos_error==3)){
  lookup=resource_pcplus_path(psp,"PCPLUS.XLT",fallback);
  if(lookup==RESOURCE_PATH_OK){
   if(!canonical(fallback,owner.fallback,&owner.fallback_error)){
    memset(result,0,sizeof(*result));result->status=XLT_DOS_RESOURCE;
    result->dos_error=owner.fallback_error;return result->status;
   }
   owner.selected=2;status=xlt_dos_read(owner.fallback,owner.table,result);
   if(!status){owner.mode=owner.ready=1;}
  }else if(lookup!=RESOURCE_PATH_ABSENT){memset(result,0,sizeof(*result));result->status=status=XLT_DOS_RESOURCE;}
 }
 if(status)return status;
 status=xlt_live_commit(1,table);result->status=status;return status;
}

/* Only this API's successful stage can be accepted/canceled by this API.
 * Ordinary settings staging remains a separate transaction. */
unsigned __cdecl xlt_live_reload(unsigned action,unsigned char *table,xlt_dos_result *result)
{
 unsigned status;
 if(action>2 || !external(result,sizeof(*result)) ||
    (action==1?(!external(table,256) || !separate(table,256,result,sizeof(*result))):table!=0))return XLT_DOS_ARGUMENT;
 memset(result,0,sizeof(*result));
 if(action==2){if(owner.reload)owner.ready=owner.reload=0;return XLT_DOS_OK;}
 if(action==1){
  if(!owner.reload){result->status=XLT_LIVE_STATE;return result->status;}
  status=xlt_live_commit(1,table);result->status=status;return status;
 }
 owner.ready=owner.reload=0;
 if(active_bound!=1 || !active_path[0]){result->status=XLT_LIVE_STATE;return result->status;}
 memset(&owner,0,sizeof(owner));bound=1;owner.fallback_kind=1;
 memcpy(owner.current,active_path,64);
 status=xlt_live_stage(1,result);if(!status)owner.reload=1;return status;
}

unsigned __cdecl xlt_live_editor(unsigned psp,char *executable,char *tail)
{
 char program[64],command[68];unsigned n,c;
 if(!external(executable,64) || !external(tail,68) || !separate(executable,64,tail,68))return XLT_DOS_ARGUMENT;
 if(active_bound!=1 || !active_path[0])return XLT_LIVE_STATE;
 for(n=0;n<64 && active_path[n];++n){c=(unsigned char)active_path[n];if(c<32 || c==127 || c=='"')return XLT_DOS_RESOURCE;}
 if(!n || n==64)return XLT_DOS_RESOURCE;
 memset(program,0,sizeof(program));
 if(resource_program_path(psp,"XLTEDIT.EXE",program))return XLT_DOS_RESOURCE;
 memset(command,0,sizeof(command));command[0]=' ';command[1]='"';
 memcpy(command+2,active_path,n);command[n+2]='"';
 memcpy(executable,program,sizeof(program));memcpy(tail,command,sizeof(command));return XLT_DOS_OK;
}
