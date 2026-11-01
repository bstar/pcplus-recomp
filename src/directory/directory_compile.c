#include "directory_compile.h"
#include "../capture/capture_file.h"
#include "../capture/capture_fs.h"
#include "../config/resource_path.h"
#include <dos.h>
#include <string.h>
#pragma aux directory_compile_storage "directory_compile_storage";
typedef char compile_owner_abi[sizeof(directory_compile_owner)==256?1:-1];
static unsigned cookie=0xdb10;
#define OWNER (&directory_compile_storage)
static unsigned equal(const char *near_path,const char __far *far_path)
{unsigned i;for(i=0;i<64;++i){if(near_path[i]!=far_path[i])return 0;if(!near_path[i])return 1;}return 0;}
static void copy_to(char __far *to,const char *from)
{unsigned i;for(i=0;i<64;++i)to[i]=from[i];}
static unsigned canonical(const char *path)
{return path[0]>='A' && path[0]<='Z' && path[1]==':' && path[2]=='\\' && capture_file_validate_path(path,0);}
static unsigned __far __cdecl probe(const char *path,void *context)
{
 unsigned n=0,i,j;
 if(context!=&cookie || cookie!=0xdb11)return 1;
 if(equal(path,OWNER->source) || equal(path,OWNER->target) || equal(path,OWNER->compiler))return 1;
 for(i=0;i<64 && OWNER->target[i];++i)if(OWNER->target[i]=='\\')n=i+1;
 for(i=0;i<n;++i)if(path[i]!=OWNER->target[i])return 0;
 if(path[n]!='L' || path[n+1]!='P' || path[n+2]!='C')return 0;
 for(j=3;j<8;++j)if(!((path[n+j]>='0' && path[n+j]<='9') || (path[n+j]>='A' && path[n+j]<='F')))return 0;
 return !strcmp(path+n+8,".TMP") || !strcmp(path+n+8,".BAK");
}
unsigned __cdecl directory_compile_initialize(void)
{
 unsigned i;
 if(cookie==0xdb10){for(i=0;i<256;++i)((unsigned char __far *)OWNER)[i]=0;cookie=0xdb11;return 0;}
 return cookie==0xdb11 && OWNER->state<=DC_FAILED && OWNER->state!=DC_ACTIVE && OWNER->state!=DC_HELD?0:DC_STATE;
}
unsigned __cdecl directory_compile_exec_allowed(void)
{return cookie==0xdb10 || (cookie==0xdb11 && OWNER->state<=DC_FAILED && OWNER->state!=DC_HELD && (OWNER->state!=DC_ACTIVE || OWNER->reserved[0]==1));}
static unsigned present(const char *path,unsigned *error)
{unsigned attributes=0;*error=capture_fs_attributes(path,&attributes);return *error!=2 && *error!=3;}
static unsigned valid_bundle(const directory_resource_bundle __far *b)
{
 unsigned long p=(unsigned long)FP_SEG(b)*16UL+FP_OFF(b);
 unsigned long owner=(unsigned long)FP_SEG(OWNER)*16UL+FP_OFF(OWNER);
 unsigned long guard=(unsigned long)FP_SEG((void __far *)&cookie)*16UL+FP_OFF((void __far *)&cookie);
 return b && (unsigned long)FP_OFF(b)+sizeof(*b)<=65536UL && p+sizeof(*b)<=1048576UL &&
  (p+sizeof(*b)<=owner || owner+256UL<=p) && (p+sizeof(*b)<=guard || guard+2UL<=p);
}
unsigned __cdecl directory_compile_run(unsigned psp,directory_resource_bundle __far *b)
{
 directory_compile_owner __far *r=OWNER;
 char source[64],target[64],compiler[64],tail[68];
 directory_script_fingerprint expected,now,compiled;
 directory_script_result io;process_result child;
 unsigned status,i,n,error,claim=0,attempt;
 if(!psp || !valid_bundle(b))return DC_ARGUMENT;
 for(i=0;i<64;++i)source[i]=b->script_path[i];
 for(n=0;n<64 && source[n];++n){}
 if(b->script.kind!=DSCRIPT_SOURCE || n<5 || n==64 || strcmp(source+n-4,".ASP") || !canonical(source))return DC_ARGUMENT;
 for(i=0;i<12;++i)((unsigned char *)&expected)[i]=((const unsigned char __far *)&b->script)[i];
 status=directory_compile_initialize();if(status)return status;
 attempt=r->attempts+1;for(i=0;i<256;++i)((unsigned char __far *)r)[i]=0;
 r->attempts=attempt;r->state=DC_ACTIVE;
 memset(target,0,sizeof(target));memcpy(target,source,n+1);target[n-1]='X';
 memset(compiler,0,sizeof(compiler));status=resource_program_path(psp,"ASPCOMP.EXE",compiler);
 if(status || !canonical(compiler)){r->status=DC_PATH;r->source_status=status;goto done;}
 copy_to(r->source,source);copy_to(r->target,target);copy_to(r->compiler,compiler);
 for(i=0;i<12;++i)((unsigned char __far *)&r->before)[i]=((unsigned char *)&expected)[i];
 status=capture_file_reserve(probe,&cookie);
 if(status){r->status=DC_CLAIM;r->source_status=status;goto done;}claim=1;
 if(present(target,&error)){r->status=DC_TARGET;r->dos_error=error;goto finished;}
 memset(&io,0,sizeof(io));status=directory_script_read(source,DSCRIPT_SOURCE,&now,&io);
 if(status){r->status=DC_SOURCE;r->source_status=status;r->dos_error=io.dos_error;r->close_error=io.close_error;goto finished;}
 if(memcmp(&now,&expected,12)){r->status=DC_CHANGED;goto finished;}
 memset(tail,0,sizeof(tail));tail[0]=' ';memcpy(tail+1,source,n);
 memset(&child,0,sizeof(child));r->reserved[0]=1;
 status=process_run(compiler,tail,&child);r->reserved[0]=0;
 for(i=0;i<8;++i)((unsigned char __far *)&r->child)[i]=((unsigned char *)&child)[i];
 if(status || child.child_status){r->status=DC_PROCESS;r->source_status=status;r->dos_error=child.dos_error;goto failed_child;}
 memset(&io,0,sizeof(io));status=directory_script_read(source,DSCRIPT_SOURCE,&now,&io);
 if(status || memcmp(&now,&expected,12)){
  r->status=status?DC_SOURCE:DC_CHANGED;r->source_status=status;r->dos_error=io.dos_error;r->close_error=io.close_error;r->state=DC_HELD;goto finished;
 }
 memset(&io,0,sizeof(io));status=directory_script_read(target,DSCRIPT_COMPILED,&compiled,&io);
 if(status){r->status=DC_OUTPUT;r->source_status=status;r->dos_error=io.dos_error;r->close_error=io.close_error;goto failed_child;}
 r->installed=1;
 for(i=0;i<12;++i)((unsigned char __far *)&r->compiled)[i]=((unsigned char *)&compiled)[i];
 goto finished;
failed_child:
 if(present(target,&error))r->state=DC_HELD;
finished:
 if(r->close_error || r->state==DC_HELD){r->state=DC_HELD;return r->status;}
 if(claim){r->release_status=capture_file_release(probe,&cookie);if(r->release_status){r->state=DC_HELD;if(!r->status)r->status=DC_RELEASE;return r->status;}}
done:
 r->state=r->status?DC_FAILED:DC_DONE;
 if(!r->status){copy_to(b->script_path,target);for(i=0;i<12;++i)((unsigned char __far *)&b->script)[i]=((unsigned char *)&compiled)[i];}
 return r->status;
}
