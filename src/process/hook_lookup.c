/* Source-owned bounded composition of native353d and CRT spawn-search policy. */
#include "hook_lookup.h"
#include <dos.h>
#define CAP 260U
typedef struct entry {unsigned found,at,bytes;} entry;
typedef struct inherited {const unsigned char __far *data;entry pcplus,path,comspec;} inherited;
extern unsigned process_psp,process_keep_paragraphs;
#pragma aux process_psp "process_psp";
#pragma aux process_keep_paragraphs "process_keep_paragraphs";
extern unsigned __cdecl hook_lookup_context(void);
extern unsigned __cdecl hook_lookup_cancelled(void);
extern unsigned __cdecl hook_platform_psp(void);
extern unsigned __cdecl hook_lookup_readable(const char *);
extern unsigned __cdecl hook_lookup_access(const char *);
extern unsigned __cdecl hook_lookup_raw(const char *,const char *,process_result *);
static unsigned extent(const void *p,unsigned n)
{return p&&(unsigned long)(unsigned)p+n<=65536UL;}
static unsigned apart(const void *a,unsigned an,const void *b,unsigned bn)
{return(unsigned long)(unsigned)a+an<=(unsigned)b||(unsigned long)(unsigned)b+bn<=(unsigned)a;}
static unsigned length(const char *s,unsigned maximum)
{unsigned i;for(i=0;i<=maximum;++i){if(!extent(s,i+1))return maximum+1;if(!s[i])return i;if(s[i]=='\r'||s[i]=='\n')return maximum+1;}return maximum+1;}
static unsigned equal(const unsigned char __far *s,unsigned n,const char *key)
{unsigned i;for(i=0;key[i];++i)if(i>=n||s[i]!=(unsigned char)key[i])return 0;return i<n&&s[i]=='=';}
static void select(entry *e,unsigned at,unsigned bytes)
{if(!e->found){e->found=1;e->at=at;e->bytes=bytes;}}
static unsigned environment(inherited *e)
{
 const unsigned char __far *mcb;unsigned segment,paragraphs,start,n;unsigned long at,end,limit;
 e->pcplus.found=e->path.found=e->comspec.found=0;e->data=0;
 segment=*(const unsigned __far *)MK_FP(process_psp,0x2c);if(!segment)return 1;
 mcb=MK_FP(segment-1,0);paragraphs=mcb[3]|((unsigned)mcb[4]<<8);
 if((mcb[0]!='M'&&mcb[0]!='Z')||!paragraphs||(unsigned long)segment+paragraphs>65536UL)return 0;
 limit=(unsigned long)paragraphs*16UL;if(limit>65536UL)limit=65536UL;
 e->data=MK_FP(segment,0);at=0;
 while(at<limit){
  if(!e->data[(unsigned)at])return at!=0||(limit>1&&!e->data[1]);
  start=(unsigned)at;end=at;while(end<limit&&e->data[(unsigned)end])++end;
  if(end==limit)return 0;n=(unsigned)(end-at);
  if(equal(e->data+start,n,"PCPLUS"))select(&e->pcplus,start+7,n-7);
  if(equal(e->data+start,n,"PATH"))select(&e->path,start+5,n-5);
  if(equal(e->data+start,n,"COMSPEC"))select(&e->comspec,start+8,n-8);
  at=end+1;
 }return 0;
}
static void copy(char *to,const char *from,unsigned n)
{unsigned i;for(i=0;i<n;++i)to[i]=from[i];}
static unsigned failure(process_result *r,unsigned status,unsigned dos)
{r->status=status;r->dos_error=dos;r->child_status=0;r->retained_paragraphs=process_keep_paragraphs;return status;}
static unsigned batch(const char *s,unsigned dot)
{unsigned i;static const char ext[]=".bat";for(i=0;i<5;++i){unsigned c=(unsigned char)s[dot+i];if(c>='A'&&c<='Z')c+=32;if(c!=(unsigned char)ext[i])return 0;if(!c)break;}return 1;}
static unsigned launch(const char *name,const char *tail,unsigned is_batch,const inherited *e,process_result *r)
{
 char command[127],shell[CAP];unsigned i,n,t,prefix;
 if(hook_lookup_cancelled())return failure(r,PROCESS_TRAP,0);
 if(!is_batch){r->status=hook_lookup_raw(name,tail,r);return r->status;}
 if(!e->comspec.found||!e->comspec.bytes)return failure(r,PROCESS_ENVIRONMENT,0);
 if(e->comspec.bytes>=CAP)return failure(r,PROCESS_COMMAND,0);
 for(i=0;i<e->comspec.bytes;++i){shell[i]=e->data[e->comspec.at+i];if(shell[i]=='\r'||shell[i]=='\n')return failure(r,PROCESS_ENVIRONMENT,0);}shell[i]=0;
 n=length(name,CAP-1);t=length(tail,47);
 /* A bare CALL.BAT can be parsed as the shell's CALL command. Keep the
  * selected suffix and qualify a relative file so built-ins cannot win. */
 prefix=name[0]!='\\'&&name[0]!='/'&&!(n>1&&name[1]==':')&&
  !(n>1&&name[0]=='.'&&(name[1]=='\\'||name[1]=='/'))?2:0;
 if(n+t+3+prefix>126)return failure(r,PROCESS_COMMAND,0);
 command[0]='/';command[1]='c';command[2]=' ';
 if(prefix){command[3]='.';command[4]='\\';}
 copy(command+3+prefix,name,n);copy(command+3+prefix+n,tail,t+1);
 r->status=hook_lookup_raw(shell,command,r);return r->status;
}
static unsigned spawn(char *name,const char *tail,const inherited *e,process_result *r)
{
 static const char extensions[3][5]={".com",".exe",".bat"};unsigned i,j,n,base=0,dot=CAP;
 n=length(name,CAP-1);if(n>=CAP)return failure(r,PROCESS_COMMAND,0);
 if(hook_lookup_cancelled())return failure(r,PROCESS_TRAP,0);
 for(i=0;i<n;++i)if(name[i]=='/'||name[i]=='\\')base=i;
 for(i=base;i<n;++i)if(name[i]=='.'){dot=i;break;}
 if(dot!=CAP)return launch(name,tail,batch(name,dot),e,r);
 if(n+4>=CAP)return failure(r,PROCESS_COMMAND,0);
 for(i=0;i<3;++i){
  for(j=0;j<5;++j)name[n+j]=extensions[i][j];
  if(hook_lookup_cancelled())return failure(r,PROCESS_TRAP,0);
  if(!hook_lookup_access(name))return launch(name,tail,i==2,e,r);
 }
 name[n]=0;return failure(r,PROCESS_EXEC,2);
}
unsigned __far __cdecl hook_lookup_run(const char *name,const char *tail,process_result *r)
{
 inherited e;char resolved[CAP],candidate[CAP];unsigned n,t,i,used,start,at,count,status;
 if(!hook_lookup_context()||hook_platform_psp()!=process_psp)return PROCESS_ARGUMENT;
 n=length(name,63);t=length(tail,47);
 if(!n||n>63||t>47||name[0]=='['||!extent(r,sizeof(*r))||!apart(name,n+1,r,sizeof(*r))||!apart(tail,t+1,r,sizeof(*r)))return PROCESS_ARGUMENT;
 if(!environment(&e))return failure(r,PROCESS_ENVIRONMENT,0);
 if(hook_lookup_cancelled())return failure(r,PROCESS_TRAP,0);
 used=0;
 if(hook_lookup_readable(name)&&e.pcplus.found&&e.pcplus.bytes){
  if(e.pcplus.bytes>=CAP)return failure(r,PROCESS_COMMAND,0);
  for(i=0;i<e.pcplus.bytes;++i){resolved[used++]=e.data[e.pcplus.at+i];if(resolved[i]=='\r'||resolved[i]=='\n')return failure(r,PROCESS_ENVIRONMENT,0);}
  if(resolved[used-1]!='\\'){if(used+1>=CAP)return failure(r,PROCESS_COMMAND,0);resolved[used++]='\\';}
 }
 if(used+n>=CAP)return failure(r,PROCESS_COMMAND,0);copy(resolved+used,name,n+1);n+=used;
 copy(candidate,resolved,n+1);status=spawn(candidate,tail,&e,r);
 if(status!=PROCESS_EXEC||(r->dos_error!=2&&r->dos_error!=3)||!e.path.found)return status;
 for(i=0;i<n;++i)if(resolved[i]=='/'||resolved[i]=='\\'||(i==1&&resolved[i]==':'))return status;
 at=0;
 while(at<e.path.bytes){
  if(hook_lookup_cancelled())return failure(r,PROCESS_TRAP,0);
  start=at;while(at<e.path.bytes&&e.data[e.path.at+at]!=';')++at;
  count=at-start;while(at<e.path.bytes&&e.data[e.path.at+at]==';')++at;
  /* Native path_component stops on an initial empty or oversized component. */
  if(!count||count>=259)break;used=count;
  for(i=0;i<count;++i){candidate[i]=e.data[e.path.at+start+i];if(candidate[i]=='\r'||candidate[i]=='\n')return failure(r,PROCESS_ENVIRONMENT,0);}
  if(candidate[used-1]!='\\'&&candidate[used-1]!='/')candidate[used++]='\\';
  if(used+n>=CAP)break;copy(candidate+used,resolved,n+1);
  status=spawn(candidate,tail,&e,r);if(status!=PROCESS_EXEC)break;
  if(r->dos_error!=2&&r->dos_error!=3&&!(candidate[0]=='/'||candidate[0]=='\\'))break;
  if(r->dos_error!=2&&r->dos_error!=3&&candidate[1]!='/'&&candidate[1]!='\\')break;
 }
 return status;
}
