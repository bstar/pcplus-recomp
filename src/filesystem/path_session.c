#include "path_session.h"
#include <dos.h>
path_session_state __based(__segname("_CODE")) path_session_storage={PATH_SESSION_COLD};
typedef char state_layout[sizeof(path_session_state)==76?1:-1];
typedef char word_abi[sizeof(unsigned)==2?1:-1];
#define S path_session_storage
static unsigned external(const void *p,unsigned n)
{
 unsigned long a,b;
 if(!p || (unsigned long)(unsigned)p+n>65536UL)return 0;
 a=(unsigned long)FP_SEG((const void __far *)p)*16UL+FP_OFF((const void __far *)p);
 b=(unsigned long)FP_SEG((const void __far *)&S)*16UL+FP_OFF((const void __far *)&S);
 return a+n<=b || b+sizeof(S)<=a;
}
static unsigned snapshot(unsigned drive,char *out)
{
 unsigned i,error;
 if(drive>25)return 15;
 out[0]=(char)('A'+drive);out[1]=':';out[2]='\\';
 for(i=3;i<68;++i)out[i]=(char)0xa5;
 error=path_getcwd(drive,out+3);if(error)return error;
 if((unsigned char)out[67]!=0xa5)return 13;
 for(i=3;i<67;++i)if(!out[i])return 0;
 return 13;
}
unsigned __far __cdecl path_session_current(char *out)
{
 char stage[68];unsigned i,error;
 if(!external(out,68))return PATH_ARGUMENT;
 error=snapshot(path_current_drive(),stage);S.last_dos_error=error;
 if(error)return PATH_DRIVE;
 for(i=0;i<68;++i){out[i]=stage[i];if(!stage[i])break;}
 return PATH_OK;
}
unsigned __far __cdecl path_session_begin(void)
{
 char stage[68];unsigned drive,i,error;
 if(S.state==PATH_SESSION_ACTIVE)return S.quarantined?PATH_SESSION_QUARANTINED:PATH_OK;
 if(S.state==PATH_SESSION_RESTORED)return PATH_OK;
 if(S.state!=PATH_SESSION_COLD)return PATH_SESSION_UNBOUND;
 drive=path_current_drive();error=snapshot(drive,stage);S.last_dos_error=error;
 if(error)return PATH_DRIVE;
 for(i=0;i<68;++i){S.startup_path[i]=stage[i];if(!stage[i])break;}
 S.startup_drive=drive;S.quarantined=0;S.state=PATH_SESSION_ACTIVE;
 return PATH_OK;
}
unsigned __far __cdecl path_session_change(const char *path,path_result *result)
{
 unsigned n,status;
 if(S.quarantined)return PATH_SESSION_QUARANTINED;
 if(S.state!=PATH_SESSION_ACTIVE)return PATH_SESSION_UNBOUND;
 if(!external(result,sizeof(*result)))return PATH_ARGUMENT;
 for(n=0;n<64;++n){if(!external(path,n+1))return PATH_ARGUMENT;if(!path[n])break;}
 status=path_change(path,result);
 if(status!=PATH_ARGUMENT){
  S.last_dos_error=result->dos_error;
  if(result->rollback_failed || status==PATH_ROLLBACK)S.quarantined=1;
 }
 return status;
}
unsigned __far __cdecl path_session_restore(void)
{
 char saved[68],current[68];unsigned i,drive,error,selected;
 if(S.state==PATH_SESSION_COLD || S.state==PATH_SESSION_RESTORED)return PATH_OK;
 if(S.state!=PATH_SESSION_ACTIVE)return PATH_SESSION_UNBOUND;
 drive=S.startup_drive;
 for(i=0;i<68;++i){saved[i]=S.startup_path[i];if(!saved[i])break;}
 /* Internal trusted DOS snapshot can exceed path_change's public63-byte
  * request limit. Native restore consumes the bounded68-byte owned copy. */
 S.quarantined=1;S.last_dos_error=0;
 if(i==68 || drive>25 || saved[0]!=(char)('A'+drive) || saved[1]!=':' || saved[2]!='\\')return PATH_VERIFY;
 if(path_native_change(saved))return PATH_CHANGE;
 selected=path_select_drive(drive);
 error=snapshot(drive,current);S.last_dos_error=error;
 if(error || selected!=drive || path_current_drive()!=drive)return PATH_VERIFY;
 for(i=0;i<68;++i){if(saved[i]!=current[i])return PATH_VERIFY;if(!saved[i])break;}
 if(i==68)return PATH_VERIFY;
 S.quarantined=0;S.state=PATH_SESSION_RESTORED;return PATH_OK;
}
unsigned __far __cdecl path_session_quarantined(void)
{return S.quarantined!=0;}
