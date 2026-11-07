#include <string.h>
#include "meta_picker_scan.h"
#include "meta_scan_fs.h"
#include "../directory/directory_replace.h"
typedef char scan_layout[sizeof(meta_picker_scan)<=160?1:-1];
static unsigned span(const void __far *p,unsigned n,unsigned long *a)
{*a=(unsigned long)FP_SEG(p)*16UL+FP_OFF(p);return p && (unsigned long)FP_OFF(p)+n<=65536UL && *a+n<=0x100000UL;}
static unsigned separate(const void __far *p,unsigned n,const void __far *q,unsigned m)
{unsigned long a,b;return span(p,n,&a) && span(q,m,&b) && (a+n<=b || b+m<=a);}
static unsigned pair(const meta_picker_scan __far *s,const meta_picker_state __far *p)
{return separate(s,sizeof(*s),p,sizeof(*p)) && p->cookie==0x4d50 && p->count<=1001 && separate(s,sizeof(*s),p->names,META_PICKER_BYTES) && separate(p,sizeof(*p),p->names,META_PICKER_BYTES);}
static unsigned valid(const meta_picker_scan __far *s)
{
 unsigned long a;
 return span(s,sizeof(*s),&a) && s->cookie==0x4d53 && s->phase<=META_SCAN_CANCELED && s->started<=1 && s->limit_reached<=1 && pair(s,s->picker) && s->table==s->picker->names && s->collected==s->picker->count;
}
/* Keep scanner-owned constants out of the parent's nearly-full DGROUP. */
static unsigned allowed(unsigned c)
{return c>=128 || (c>='A' && c<='Z') || (c>='a' && c<='z') || (c>='0' && c<='9') || c=='!' || c=='#' || c=='$' || c=='%' || c=='&' || c=='\'' || c=='(' || c==')' || c=='-' || c=='@' || c=='^' || c=='_' || c=='`' || c=='{' || c=='}' || c=='~';}
static unsigned pattern(const char *source,char *out)
{
 char request[64],stage[64],backup[64];unsigned i,n;unsigned long a;
 if(!span(source,64,&a))return 0;
 for(n=0;n<64 && source[n];++n){}if(n<8 || n==64)return 0;
 for(i=0;i<=n;++i){unsigned c=(unsigned char)source[i];if(c>='a' && c<='z')c-=32;request[i]=(char)(c=='/'?'\\':c);}
 if(request[1]!=':' || request[2]!='\\' || request[n-6]!='\\' || (request[n-5]!='*' || request[n-4]!='.' || request[n-3]!='K' || request[n-2]!='E' || request[n-1]!='Y'))return 0;
 request[n-5]='A';
 if(directory_replace_paths(request,stage,backup))return 0;
 n=strlen(stage)-10;memcpy(out,stage,n);out[n]='*';out[n+1]='.';out[n+2]='K';out[n+3]='E';out[n+4]='Y';out[n+5]=0;for(i=n+6;i<64;++i)out[i]=0;return 1;
}
unsigned __cdecl meta_picker_scan_begin(meta_picker_scan __far *s,meta_picker_state __far *p,const char *source)
{
 char normalized[64];
 if(!pair(s,p) || !separate(s,sizeof(*s),source,64) || !separate(p,sizeof(*p),source,64) || !separate(p->names,META_PICKER_BYTES,source,64) || !pattern(source,normalized))return META_SCAN_ARGUMENT;
 if(p->phase!=META_PICKER_COLLECT || p->count)return META_SCAN_STATE;
 s->cookie=0x4d53;s->phase=META_SCAN_READ;s->status=s->dos_error=s->started=s->limit_reached=s->collected=0;s->picker=p;s->table=p->names;
 _fmemset(&s->continuation,0,sizeof(s->continuation));_fmemcpy(s->pattern,normalized,64);return META_SCAN_OK;
}
static unsigned fail(meta_picker_scan __far *s,unsigned status,unsigned error)
{s->phase=META_SCAN_FAILED;s->status=status;s->dos_error=error;return status;}
static unsigned seal(meta_picker_scan __far *s)
{
 unsigned status=meta_picker_seal(s->picker);if(status)return fail(s,META_SCAN_CORE,status);
 s->phase=s->picker->phase==META_PICKER_SORT?META_SCAN_SORT:META_SCAN_DONE;return META_SCAN_OK;
}
unsigned __cdecl meta_picker_scan_step(meta_picker_scan __far *s)
{
 struct find_t find;char search[64],stem[9];unsigned error,i,n;
 if(!valid(s))return META_SCAN_ARGUMENT;
 if(s->phase==META_SCAN_SORT){
  if(s->picker->phase!=META_PICKER_SORT)return META_SCAN_STATE;
  error=meta_picker_sort_step(s->picker,64);if(error)return fail(s,META_SCAN_CORE,error);
  if(s->picker->phase==META_PICKER_ACTIVE)s->phase=META_SCAN_DONE;return META_SCAN_OK;
 }
 if(s->phase!=META_SCAN_READ || s->picker->phase!=META_PICKER_COLLECT)return META_SCAN_STATE;
 if(s->started){_fmemcpy(&find,&s->continuation,sizeof(find));error=meta_scan_fs_next(&find);}
 else{_fmemcpy(search,s->pattern,64);memset(&find,0,sizeof(find));error=meta_scan_fs_first(search,&find);}
 if(error==18)return seal(s);
 if(error)return fail(s,META_SCAN_DOS,error);
 s->started=1;_fmemcpy(&s->continuation,&find,sizeof(find));
 if(find.attrib&(_A_HIDDEN|_A_SYSTEM|_A_SUBDIR|_A_VOLID))return META_SCAN_OK;
 for(n=0;n<sizeof(find.name) && find.name[n] && find.name[n]!='.';++n){}
 if(!n || n>8 || n+4>=sizeof(find.name) || find.name[n]!='.' || find.name[n+4])return fail(s,META_SCAN_NAME,0);
 for(i=0;i<3;++i){unsigned c=(unsigned char)find.name[n+1+i];if(c>='a' && c<='z')c-=32;if(c!=(i==0?'K':i==1?'E':'Y'))return fail(s,META_SCAN_NAME,0);}
 for(i=0;i<n;++i){unsigned c=(unsigned char)find.name[i];
  if(!allowed(c))return fail(s,META_SCAN_NAME,0);
  stem[i]=find.name[i];}stem[n]=0;for(i=n+1;i<9;++i)stem[i]=0;
 error=meta_picker_add(s->picker,stem);if(error)return fail(s,META_SCAN_CORE,error);++s->collected;
 if(s->collected==META_PICKER_CAPACITY){s->limit_reached=1;return seal(s);}return META_SCAN_OK;
}
unsigned __cdecl meta_picker_scan_cancel(meta_picker_scan __far *s)
{
 if(!valid(s))return META_SCAN_ARGUMENT;
 if(s->phase!=META_SCAN_READ && s->phase!=META_SCAN_SORT)return META_SCAN_STATE;
 s->phase=META_SCAN_CANCELED;return META_SCAN_OK;
}
