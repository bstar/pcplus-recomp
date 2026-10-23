#include "hook_transaction.h"
#include "register_owner.h"
#include "session_projection.h"
#include <string.h>
extern unsigned terminal_option_mask,terminal_directory_mode;
#pragma aux terminal_option_mask "terminal_option_mask";
#pragma aux terminal_directory_mode "terminal_directory_mode";
extern unsigned __far __cdecl terminal_register_context(void);
extern prm_dos_image __far terminal_hook_before;
typedef char stage_abi[sizeof(terminal_hook_stage)==2584?1:-1];
typedef char result_abi[sizeof(terminal_hook_result)==20?1:-1];
static unsigned extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned apart(const void *a,unsigned n,const void *b,unsigned m)
{return (unsigned long)(unsigned)a+n<=(unsigned)b || (unsigned long)(unsigned)b+m<=(unsigned)a;}
/* Keep projection's nested PRM frames disjoint in time from EXEC staging.
 * Combining these frames overflows the terminal's fixed8KiB stack. */
static unsigned project(void)
{
 prm_dos_image image;unsigned i,status;
 status=terminal_session_project_bound(&image);
 if(status)return status;
 for(i=0;i<1264;++i)terminal_hook_before.bytes[i]=image.bytes[i];
 return 0;
}
static unsigned execute(const char *path,long context,unsigned active,terminal_hook_result *result)
{
 terminal_hook_stage stage;prm_dos_image before;
 unsigned i,status,code;
 for(i=0;i<1264;++i)before.bytes[i]=terminal_hook_before.bytes[i];
 if(terminal_register_snapshot(stage.integers,stage.strings)){result->status=TERMINAL_HOOK_REGISTERS;return result->status;}
 code=hook_owner_initialize(&terminal_hook_owner);
 if(code){result->owner_status=code;result->status=TERMINAL_HOOK_OWNER;return result->status;}
 terminal_hook_phase=1;
 code=hook_owner_open(&terminal_hook_owner,stage.integers,stage.strings,before.bytes,context);
 status=TERMINAL_HOOK_OWNER;
 if(code)goto retire;
 code=hook_owner_execute(&terminal_hook_owner,path);
 result->child.status=terminal_hook_owner.result.status;
 result->child.dos_error=terminal_hook_owner.result.dos_error;
 result->child.child_status=terminal_hook_owner.result.child_status;
 result->child.retained_paragraphs=terminal_hook_owner.result.retained_paragraphs;
 if(code)goto retire;
 if(result->child.child_status){status=TERMINAL_HOOK_CHILD;goto retire;}
 code=hook_owner_collect(&terminal_hook_owner,stage.integers,stage.strings,stage.image.bytes);
 if(code)goto retire;
 status=TERMINAL_HOOK_VALIDATION;
 if(hook_return_validate(&before,&stage.image,active,&stage.settings,&result->validation))goto retire;
 status=TERMINAL_HOOK_OK;
retire:
 result->owner_status=code;
 if(terminal_hook_owner.phase || terminal_hook_owner.segment){
  code=hook_owner_close(&terminal_hook_owner);
  if(code){result->owner_status=code;status=TERMINAL_HOOK_RELEASE;}
 }
 if(!status){
  const unsigned char *from=(const unsigned char *)&stage;
  unsigned char __far *to=(unsigned char __far *)&terminal_hook_proposal;
  for(i=0;i<sizeof(stage);++i)to[i]=from[i];
  terminal_hook_phase=2;
 }else terminal_hook_phase=0;
 result->status=status;return status;
}
unsigned __far __cdecl terminal_hook_execute(const char *path,long context,
 terminal_hook_result *result)
{
 unsigned i,mode,status;unsigned char *zero;
 if(!terminal_register_context() || !extent(path,64) ||
  !extent(result,sizeof(*result)) || !apart(path,64,result,sizeof(*result)))return TERMINAL_HOOK_ARGUMENT;
 zero=(unsigned char *)result;for(i=0;i<sizeof(*result);++i)zero[i]=0;
 result->validation.offset=65535U;
 if(context< -32768L || context>32767L){result->status=TERMINAL_HOOK_ARGUMENT;return result->status;}
 for(i=0;i<64;++i){if(!path[i])break;if(path[i]=='\r'||path[i]=='\n')break;}
 if(!i || i==64 || path[i]){result->status=TERMINAL_HOOK_ARGUMENT;return result->status;}
 if(terminal_hook_phase || terminal_register_owner.phase || terminal_hook_owner.phase || terminal_hook_owner.segment){
  result->status=TERMINAL_HOOK_BUSY;return result->status;
 }
 terminal_hook_phase=1;
 if(project()){terminal_hook_phase=0;result->status=TERMINAL_HOOK_PROJECTION;return result->status;}
 mode=terminal_option_mask&96;
 status=execute(path,context,mode==32 || (mode==64 && !terminal_directory_mode),result);
 if(status && !terminal_hook_owner.phase && !terminal_hook_owner.segment)terminal_hook_phase=0;
 return status;
}
unsigned __far __cdecl terminal_hook_discard(void)
{
 if(!terminal_register_context())return TERMINAL_HOOK_ARGUMENT;
 if(terminal_hook_owner.phase || terminal_hook_owner.segment || terminal_hook_phase==1)return TERMINAL_HOOK_BUSY;
 terminal_hook_phase=0;return 0;
}
