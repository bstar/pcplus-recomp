/* Maintained bounds around recovered PROGRAM's COMSPEC /c policy. */
#include "dos_exec.h"
#include <dos.h>
#include <stddef.h>
extern unsigned process_psp;
typedef char word_abi[sizeof(unsigned)==2?1:-1];
typedef char result_abi[sizeof(process_result)==8?1:-1];
typedef char child_abi[offsetof(process_result,child_status)==4?1:-1];
typedef struct environment_span {
 const unsigned char __far *bytes;
 unsigned comspec_at,comspec_size,path_at,path_size;
 unsigned has_comspec,has_path;
} environment_span;
static unsigned extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned disjoint(const void *a,unsigned n,const void *b,unsigned m)
{return (unsigned long)(unsigned)a+n<=(unsigned)b || (unsigned long)(unsigned)b+m<=(unsigned)a;}
static unsigned name_equal(const unsigned char __far *p,unsigned at,
 unsigned length,const char *name)
{
 unsigned i=0;
 while(name[i]){if(i>=length || p[at+i]!=(unsigned char)name[i])return 0;++i;}
 return i<length && p[at+i]=='=';
}
static unsigned environment(environment_span *span)
{
 const unsigned short __far *psp;
 const unsigned char __far *mcb;
 const unsigned char __far *bytes;
 unsigned segment,paragraphs,start,length,key_length;
 unsigned long at,end,limit;
 span->has_comspec=span->has_path=0;
 if(!process_psp)return 0;
 psp=(const unsigned short __far *)MK_FP(process_psp,0);
 segment=psp[0x2c/2];
 if(!segment)return 1; /* Empty inherited environment: try COMMAND.COM. */
 mcb=(const unsigned char __far *)MK_FP(segment-1,0);
 paragraphs=mcb[3]|((unsigned)mcb[4]<<8);
 if((mcb[0]!='M' && mcb[0]!='Z') || !paragraphs ||
  (unsigned long)segment+paragraphs>65536UL)return 0;
 limit=(unsigned long)paragraphs*16UL;
 if(limit>65536UL)limit=65536UL;
 bytes=(const unsigned char __far *)MK_FP(segment,0);span->bytes=bytes;
 at=0;
 while(at<limit){
  if(!bytes[(unsigned)at]){
   if(at)return 1;
   return limit>1 && !bytes[1];
  }
  start=(unsigned)at;end=at;
  while(end<limit && bytes[(unsigned)end])++end;
  if(end>=limit)return 0;
  length=(unsigned)(end-at);
  if(!span->has_comspec && name_equal(bytes,start,length,"COMSPEC")){
   key_length=8;span->comspec_at=start+key_length;
   span->comspec_size=length-key_length;span->has_comspec=1;
  }
  if(!span->has_path && name_equal(bytes,start,length,"PATH")){
   key_length=5;span->path_at=start+key_length;
   span->path_size=length-key_length;span->has_path=1;
  }
  at=end+1;
 }
 return 0; /* No complete environment terminator in its owned DOS block. */
}
static unsigned fallback(unsigned error)
{return error==2 || error==3 || error==5;}
static void zero_result(process_result *r)
{r->status=r->dos_error=r->child_status=r->retained_paragraphs=0;}
static unsigned execute(const char *path,const char *tail,process_result *r)
{
 unsigned status;
 zero_result(r);status=process_run(path,tail,r);r->status=status;
 return status;
}
process_status_code __cdecl program_execute(const char *command,process_result *result)
{
 environment_span env;
 process_result stage;
 char program[128],tail[56];
 unsigned n,i,at,start,length,used,status;
 static const char fallback_name[]="COMMAND.COM";
 if(!extent(result,sizeof(*result)) || !command)return PROCESS_ARGUMENT;
 for(n=0;n<52;++n){
  if(!extent(command,n+1))return PROCESS_ARGUMENT;
  if(!command[n])break;
  if(command[n]=='\r' || command[n]=='\n')return PROCESS_ARGUMENT;
 }
 if(!n || n>=52 || !disjoint(command,n+1,result,sizeof(*result)))return PROCESS_ARGUMENT;
 zero_result(&stage);
 if(!environment(&env)){stage.status=PROCESS_ENVIRONMENT;*result=stage;return stage.status;}
 tail[0]=' ';tail[1]='/';tail[2]='c';tail[3]=' ';
 for(i=0;i<=n;++i)tail[4+i]=command[i];
 if(env.has_comspec && env.comspec_size){
  if(env.comspec_size>=sizeof(program)){
   stage.status=PROCESS_ENVIRONMENT;*result=stage;return stage.status;
  }
  for(i=0;i<env.comspec_size;++i)program[i]=env.bytes[env.comspec_at+i];
  program[i]=0;
  status=execute(program,tail,&stage);
  if(status!=PROCESS_EXEC || !fallback(stage.dos_error)){*result=stage;return status;}
 }
 status=execute(fallback_name,tail,&stage);
 if(status!=PROCESS_EXEC || !fallback(stage.dos_error) || !env.has_path){*result=stage;return status;}
 at=0;
 while(at<env.path_size){
  start=at;
  while(at<env.path_size && env.bytes[env.path_at+at]!=';')++at;
  length=at-start;if(at<env.path_size)++at;
  if(!length || length>=sizeof(program))continue;
  used=length;
  if(env.bytes[env.path_at+start+length-1]!='\\' &&
   env.bytes[env.path_at+start+length-1]!='/' &&
   env.bytes[env.path_at+start+length-1]!=':')++used;
  if(used+sizeof(fallback_name)>sizeof(program))continue;
  for(i=0;i<length;++i)program[i]=env.bytes[env.path_at+start+i];
  if(used>length)program[length]='\\';
  for(i=0;i<sizeof(fallback_name);++i)program[used+i]=fallback_name[i];
  status=execute(program,tail,&stage);
  if(status!=PROCESS_EXEC || !fallback(stage.dos_error))break;
 }
 *result=stage;return stage.status;
}
