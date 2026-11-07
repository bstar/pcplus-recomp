#include <dos.h>
#include <string.h>
#include "meta_key_resource.h"
#include "../config/resource_path.h"
#include "../capture/capture_fs.h"
#include "../directory/directory_replace.h"
typedef char resource_layout[sizeof(meta_key_resource_result)==74?1:-1];
static unsigned span(const void *p,unsigned n){return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned separate(const void *p,unsigned n,const void *q,unsigned m)
{return span(p,n) && span(q,m) && ((unsigned long)(unsigned)p+n<=(unsigned)q || (unsigned long)(unsigned)q+m<=(unsigned)p);}
static unsigned fold(unsigned c){return c>='a' && c<='z'?c-32:c;}
static void dummy(char *p){p[0]='A';p[1]='.';p[2]='K';p[3]='E';p[4]='Y';p[5]=0;}
static unsigned lexical(const char *name)
{char a[64],b[64];return span(name,64) && !directory_replace_paths(name,a,b);}
static unsigned finish(meta_key_resource_result *r,unsigned status)
{r->status=status;return status;}
static unsigned canonical(const char *name,char *out,meta_key_resource_result *r)
{
 char path[128];unsigned i,c,error;
 memset(path,0,sizeof(path));error=capture_fs_canonical(name,path);
 if(error){r->dos_error=error;return META_RESOURCE_CANONICAL;}
 for(i=0;i<128 && path[i];++i){c=fold((unsigned char)path[i]);path[i]=(char)(c=='/'?'\\':c);}
 if(!i || i>63 || path[0]<'A' || path[0]>'Z' || path[1]!=':' || path[2]!='\\' || !lexical(path))return META_RESOURCE_PATH;
 memset(out,0,64);memcpy(out,path,i+1);return META_RESOURCE_OK;
}
static unsigned inspect(const char *name,meta_key_resource_result *r)
{
 unsigned error,attr,status=canonical(name,r->path,r);if(status)return status;
 error=capture_fs_attributes(r->path,&attr);r->dos_error=error;
 if(error==2 || error==3)return META_RESOURCE_MISSING;
 if(error || (attr&(_A_SUBDIR|_A_VOLID)))return META_RESOURCE_INSPECT;
 r->exists=1;return META_RESOURCE_OK;
}
static unsigned fallback(unsigned psp,const char *leaf,char *out,meta_key_resource_result *r)
{
 char stub[64],name[13];unsigned status,n,i,prefix;
 dummy(name);status=resource_pcplus_path(psp,name,stub);r->environment_error=status;
 if(status==RESOURCE_PATH_ABSENT)return META_RESOURCE_MISSING;
 if(status)return META_RESOURCE_ENVIRONMENT;
 prefix=strlen(stub)-5;n=strlen(leaf);if(prefix+n>=64){r->environment_error=RESOURCE_PATH_SIZE;return META_RESOURCE_ENVIRONMENT;}
 for(i=0;i<prefix;++i)out[i]=stub[i];for(i=0;i<=n;++i)out[prefix+i]=leaf[i];return META_RESOURCE_OK;
}
unsigned __cdecl meta_key_resource_lookup(unsigned psp,const char *name,meta_key_resource_result *r)
{
 char alternate[64];unsigned status,qualified;
 if(!separate(name,64,r,sizeof(*r)) || !lexical(name))return META_RESOURCE_ARGUMENT;
 memset(r,0,sizeof(*r));qualified=strchr(name,':')!=0 || strchr(name,'\\')!=0 || strchr(name,'/')!=0;r->source=qualified?META_RESOURCE_EXPLICIT:META_RESOURCE_CURRENT;
 status=inspect(name,r);if(status!=META_RESOURCE_MISSING || qualified)return finish(r,status);
 status=fallback(psp,name,alternate,r);if(status)return finish(r,status);
 r->source=META_RESOURCE_PCPLUS;r->dos_error=0;return finish(r,inspect(alternate,r));
}
unsigned __cdecl meta_key_resource_pattern(unsigned psp,unsigned use_fallback,meta_key_resource_result *r)
{
 char name[64],alternate[64];unsigned n,status;
 if(!span(r,sizeof(*r)) || use_fallback>1)return META_RESOURCE_ARGUMENT;
 memset(r,0,sizeof(*r));r->source=use_fallback?META_RESOURCE_PCPLUS:META_RESOURCE_CURRENT;dummy(name);
 if(use_fallback){status=fallback(psp,name,alternate,r);if(status)return finish(r,status);}
 status=canonical(use_fallback?alternate:name,r->path,r);if(status)return finish(r,status);
 n=strlen(r->path);if(n<8 || r->path[n-5]!='A' || r->path[n-4]!='.' || r->path[n-3]!='K' || r->path[n-2]!='E' || r->path[n-1]!='Y')return finish(r,META_RESOURCE_PATH);r->path[n-5]='*';return finish(r,META_RESOURCE_OK);
}
unsigned __cdecl meta_key_resource_selected(const char *pattern,const char *stem,char *out)
{
 char stage[64];unsigned i,n,k;
 if(!separate(pattern,64,out,64) || !separate(stem,9,out,64) || !span(pattern,64) || !span(stem,9))return META_RESOURCE_ARGUMENT;
 for(n=0;n<64 && pattern[n];++n){}if(n<8 || n==64 || pattern[1]!=':' || pattern[2]!='\\' || pattern[n-6]!='\\' || pattern[n-5]!='*' || pattern[n-4]!='.' || fold(pattern[n-3])!='K' || fold(pattern[n-2])!='E' || fold(pattern[n-1])!='Y')return META_RESOURCE_ARGUMENT;
 for(k=0;k<9 && stem[k];++k){}if(!k || k>8 || n-5+k+4>=64)return META_RESOURCE_ARGUMENT;
 memset(stage,0,64);for(i=0;i<n-5;++i)stage[i]=(char)fold((unsigned char)pattern[i]);
 for(i=0;i<k;++i){unsigned c=fold((unsigned char)stem[i]);if(c=='.' || c==':' || c=='\\' || c=='/')return META_RESOURCE_ARGUMENT;stage[n-5+i]=(char)c;}
 i=n-5+k;stage[i]='.';stage[i+1]='K';stage[i+2]='E';stage[i+3]='Y';if(!lexical(stage))return META_RESOURCE_ARGUMENT;
 memcpy(out,stage,64);return META_RESOURCE_OK;
}
