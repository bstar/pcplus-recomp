#include "viewer_file.h"
#include "viewer_file_backend.h"
#include <dos.h>
typedef unsigned word;
typedef unsigned char byte;
typedef struct viewer_file_owner {
 word cookie;void *token;word busy;viewer_file_snapshot result;
} viewer_file_owner;
viewer_file_owner __based(__segname("_CODE")) viewer_file_storage=
 {0x5646,0,0,{VF_IDLE,0,0,0,0,0,0xffff,0,0,{0}}};
typedef char owner_layout[sizeof(viewer_file_owner)==90?1:-1];
typedef char result_layout[sizeof(viewer_file_snapshot)==84?1:-1];
#define S viewer_file_storage
#define R S.result
static unsigned long address(const void __far *p)
{return ((unsigned long)FP_SEG(p)<<4)+FP_OFF(p);}
static word span(const void __far *p,word n)
{return p&&n&&n-1<=0xffffU-FP_OFF(p)&&address(p)<=0xfffffUL-(n-1);}
static word overlap(const void __far *a,word an,const void __far *b,word bn)
{return address(a)<address(b)+bn&&address(b)<address(a)+an;}
static word safe(const void __far *p,word n)
{return span(p,n)&&!overlap(p,n,(const void __far *)&S,sizeof(S));}
static word enter(void)
{
 if(S.cookie!=0x5646)return VF_STATE;
 if(S.busy)return VF_BUSY;
 if(R.phase==VF_UNCERTAIN)return VF_RECOVERY;
 return VF_OK;
}
static word fail(word status,word error)
{
 if(!R.first_status){R.first_status=status;R.dos_error=error;}
 R.phase=VF_BROKEN;return status;
}
static word close_owned(void)
{
 word error;
 if(R.handle!=0xffff){
  error=viewer_kernel_close(R.handle);
  if(error){R.close_error=error;fail(VF_CLOSE,error);R.phase=VF_UNCERTAIN;return R.first_status;}
  R.handle=0xffff;
 }
 if(R.claimed){
  error=viewer_admit_release(S.token);
  if(error){R.release_error=error;fail(VF_RELEASE,0);R.phase=VF_UNCERTAIN;return R.first_status;}
  R.claimed=0;
 }
 S.token=0;R.phase=VF_CLOSED;return R.first_status;
}
unsigned __far __cdecl viewer_file_conflict(const char *identity,void *token)
{
 word i;
 if(S.cookie!=0x5646||!token||token!=S.token||!identity)return 1;
 for(i=0;i<64;i++){
  if(identity[i]!=R.path[i])return 0;
  if(!identity[i])return 1;
 }
 return 1;
}
unsigned __far __cdecl viewer_file_open(const char *path,void *token)
{
 char absolute[128];word i,n,error,attributes,handle=0xffff,result;
 result=enter();if(result)return result;
 if(!token||!safe((const void __far *)path,64)||!viewer_admit_validate(path))return VF_ARGUMENT;
 if(R.handle!=0xffff||R.claimed)return VF_BUSY;
 S.busy=1;
 R.phase=VF_IDLE;R.first_status=R.dos_error=R.close_error=R.claim_error=R.release_error=0;
 R.position=0;S.token=token;
 for(i=0;i<64;i++)R.path[i]=0;
 for(i=0;i<128;i++)absolute[i]=0;
 error=viewer_kernel_canonical(path,absolute);
 for(n=0;n<128&&absolute[n];n++){
  if(absolute[n]>='a'&&absolute[n]<='z')absolute[n]-=32;
  if(absolute[n]=='/')absolute[n]='\\';
 }
 if(error||!n||n>63||absolute[0]<'A'||absolute[0]>'Z'||absolute[1]!=':'||absolute[2]!='\\'||
    !viewer_admit_validate(absolute)){fail(VF_CANONICAL,error);goto done;}
 for(i=0;i<=n;i++)R.path[i]=absolute[i];
 error=viewer_admit_claim(absolute,token);
 if(error){R.claim_error=error;fail(VF_CLAIM,0);goto done;}
 R.claimed=1;
 error=viewer_kernel_attributes(absolute,&attributes);
 if(error||(attributes&0x18)){fail(VF_ATTRIBUTES,error);goto done;}
 error=viewer_kernel_open(absolute,&handle);
 if(error){fail(VF_OPEN,error);goto done;}
 if(handle>=0x8000){fail(VF_PROTOCOL,0);R.phase=VF_UNCERTAIN;S.busy=0;return VF_PROTOCOL;}
 R.handle=handle;
 error=viewer_kernel_device(handle,&attributes);
 if(error||(attributes&0x80)){fail(VF_INSPECT,error);goto done;}
 R.phase=VF_OPENED;S.busy=0;return VF_OK;
done:
 result=close_owned();S.busy=0;return result;
}
unsigned __far __cdecl viewer_file_read(void __far *buffer,word count,word *actual)
{
 word error,received=0,result=enter();
 if(result)return result;
 if(!safe((void __far *)actual,sizeof(*actual))||count>256||
    (count&&(!safe(buffer,count)||overlap(buffer,count,(void __far *)actual,sizeof(*actual)))))return VF_ARGUMENT;
 if(R.phase!=VF_OPENED||R.handle==0xffff||!R.claimed)return VF_STATE;
 if(!count){*actual=0;return VF_OK;}
 if(R.position>0xffffffffUL-count)return fail(VF_OVERFLOW,0);
 S.busy=1;error=viewer_kernel_read(R.handle,buffer,count,&received);
 if(error)result=fail(VF_READ,error);
 else if(received>count)result=fail(VF_PROTOCOL,0);
 else{R.position+=received;*actual=received;result=VF_OK;}
 S.busy=0;return result;
}
unsigned __far __cdecl viewer_file_seek(unsigned long position)
{
 unsigned long actual=0;word error,result=enter();
 if(result)return result;
 if(position>0x7fffffffUL)return VF_ARGUMENT;
 if(R.phase!=VF_OPENED||R.handle==0xffff||!R.claimed)return VF_STATE;
 S.busy=1;error=viewer_kernel_seek(R.handle,position,&actual);
 if(error)result=fail(VF_SEEK,error);
 else if(actual!=position)result=fail(VF_PROTOCOL,0);
 else{R.position=actual;result=VF_OK;}
 S.busy=0;return result;
}
unsigned __far __cdecl viewer_file_close(void)
{
 word result=enter();if(result)return result;
 S.busy=1;result=close_owned();S.busy=0;return result;
}
unsigned __far __cdecl viewer_file_inspect(viewer_file_snapshot *out)
{
 word i;
 if(S.cookie!=0x5646)return VF_STATE;
 if(S.busy)return VF_BUSY;
 if(!safe((void __far *)out,sizeof(*out)))return VF_ARGUMENT;
 for(i=0;i<sizeof(*out);i++)((byte *)out)[i]=((byte __far *)&R)[i];
 return VF_OK;
}
