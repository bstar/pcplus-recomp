#include "batch_upload.h"
#include "batch_upload_fs.h"
#include "upload_file.h"
#include <string.h>
#include <stddef.h>
typedef char word_16[sizeof(unsigned)==2?1:-1];
typedef char long_32[sizeof(unsigned long)==4?1:-1];
typedef char result_size_offset[offsetof(batch_upload_result,size)==86?1:-1];
typedef char result_bytes[sizeof(batch_upload_result)==90?1:-1];
batch_upload_result batch_upload_current;
static unsigned cookie=0xbaa0,started,active;
static char search[64],prefix[64];
static unsigned extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned separate(const void *a,unsigned an,const void *b,unsigned bn)
{return (unsigned long)(unsigned)a+an<=(unsigned)b || (unsigned long)(unsigned)b+bn<=(unsigned)a;}
static unsigned safe(const void *p,unsigned n)
{
 return extent(p,n) && separate(p,n,&batch_upload_current,sizeof(batch_upload_current)) &&
 separate(p,n,&batch_upload_find,sizeof(batch_upload_find)) &&
 separate(p,n,&upload_source_result,sizeof(upload_source_result)) &&
 separate(p,n,search,sizeof(search)) && separate(p,n,prefix,sizeof(prefix)) &&
 separate(p,n,&cookie,sizeof(cookie)) && separate(p,n,&started,sizeof(started)) && separate(p,n,&active,sizeof(active));
}
static unsigned fold(unsigned c){return c>='a' && c<='z'?c-32:c;}
static unsigned leaf(const char *s,unsigned n,unsigned wild)
{
 unsigned i,base=0,ext=0,dot=0,c,haswild=0;char stem[9];
 for(i=0;i<n;++i){c=(unsigned char)s[i];
  if(c=='.'){if(dot || !base)return 0;dot=1;continue;}
  if(c=='*' || c=='?'){if(!wild)return 0;haswild=1;}
  else if(!((c>='A' && c<='Z') || (c>='0' && c<='9') || strchr("!#$%&'()-@^_`{}~",c)))return 0;
  if(dot){if(++ext>3)return 0;}else{if(base==8)return 0;stem[base++]=(char)c;}
 }
 if(!base || (dot && !ext))return 0;stem[base]=0;
 if(haswild)return 1;
 if(!strcmp(stem,"CON") || !strcmp(stem,"PRN") || !strcmp(stem,"AUX") || !strcmp(stem,"NUL") || !strcmp(stem,"CLOCK$"))return 0;
 return !(base==4 && stem[3]>='1' && stem[3]<='9' && (!memcmp(stem,"COM",3) || !memcmp(stem,"LPT",3)));
}
static unsigned normalize(const char *s,char *out,unsigned *parent)
{
 unsigned n,start=0,i;
 for(n=0;n<64;++n){if(!safe(s,n+1))return 0;out[n]=(char)fold((unsigned char)s[n]);if(out[n]=='/')out[n]='\\';if(!out[n])break;}
 if(!n || n==64)return 0;
 if(n>=2 && out[1]==':'){if(out[0]<'A' || out[0]>'Z')return 0;start=2;}
 if(out[start]=='\\')++start;
 for(i=start;;++i)if(out[i]=='\\' || !out[i]){
  if(!leaf(out+start,i-start,!out[i]))return 0;
  if(!out[i])break;start=i+1;
 }
 *parent=start;return 1;
}
static unsigned fail(unsigned status,unsigned error,unsigned source)
{
 if(!batch_upload_current.status){batch_upload_current.status=status;batch_upload_current.dos_error=error;batch_upload_current.source_status=source;}
 batch_upload_current.state=BU_BROKEN;return status;
}
unsigned __cdecl batch_upload_initialize(void)
{
 unsigned s;
 if(cookie==0xbaa1 && upload_source_result.handle_uncertain)return BU_RECOVERY;
 if(cookie==0xbaa1 && (active || batch_upload_current.state==BU_ENUMERATING))return BU_BUSY;
 s=upload_source_initialize();if(s)return s==UF_RECOVERY?BU_RECOVERY:BU_BUSY;
 memset(&batch_upload_current,0,sizeof(batch_upload_current));memset(&batch_upload_find,0,sizeof(batch_upload_find));
 started=active=0;search[0]=prefix[0]=0;cookie=0xbaa1;return BU_OK;
}
unsigned __cdecl batch_upload_begin(const char *pattern)
{
 char candidate[64];unsigned n;
 if(cookie!=0xbaa1)return BU_STATE;
 if(upload_source_result.handle_uncertain)return BU_RECOVERY;
 if(active || upload_source_result.handle_open || batch_upload_current.state==BU_ENUMERATING)return BU_BUSY;
 if(!normalize(pattern,candidate,&n))return BU_ARGUMENT;
 memset(&batch_upload_current,0,sizeof(batch_upload_current));strcpy(search,candidate);
 memcpy(prefix,candidate,n);prefix[n]=0;started=0;batch_upload_current.state=BU_ENUMERATING;return BU_OK;
}
unsigned __cdecl batch_upload_next(void)
{
 unsigned e,n,i,s;char path[64],name[13];
 if(cookie!=0xbaa1)return BU_STATE;
 if(upload_source_result.handle_uncertain)return BU_RECOVERY;
 if(active)return BU_BUSY;
 if(batch_upload_current.state==BU_FINISHED)return BU_DONE;
 if(batch_upload_current.state!=BU_ENUMERATING)return BU_STATE;
 for(;;){
  e=started?batch_upload_fs_next():batch_upload_fs_first(search);started=1;
  if(e==18){batch_upload_current.state=BU_FINISHED;return BU_DONE;}
  if(e)return fail(BU_ENUMERATE,e,0);
  if(batch_upload_find.attrib&0x1e)continue; /* hidden/system/volume/directory */
  for(n=0;n<13 && batch_upload_find.name[n];++n)name[n]=(char)fold((unsigned char)batch_upload_find.name[n]);
  if(n==13 || !leaf(name,n,0))return fail(BU_ARGUMENT,0,0);name[n]=0;
  i=strlen(prefix);if(i+n>=64)return fail(BU_ARGUMENT,0,0);
  memcpy(path,prefix,i);strcpy(path+i,name);
  s=upload_source_begin(path);if(s)return fail(s==UF_RECOVERY?BU_RECOVERY:BU_SOURCE,upload_source_result.dos_error,s);
  active=1;
  if(upload_source_result.size>0x7ffffbffUL){upload_source_abort();active=upload_source_result.handle_open || upload_source_result.handle_uncertain;return fail(active?BU_RECOVERY:BU_SOURCE,0,UF_ARGUMENT);}
  if(upload_source_open(path,"rb")!=2){s=upload_source_result.first_status;upload_source_abort();active=upload_source_result.handle_open || upload_source_result.handle_uncertain;return fail(active?BU_RECOVERY:BU_SOURCE,upload_source_result.dos_error,s);}
  strcpy(batch_upload_current.name,name);strcpy(batch_upload_current.path,path);batch_upload_current.size=upload_source_result.size;
  batch_upload_current.state=BU_READING;return BU_FILE;
 }
}
unsigned __cdecl batch_upload_read(void *data,unsigned capacity,unsigned *count)
{
 unsigned n;
 if(capacity>1024 || !safe(count,sizeof(*count)) || (capacity && (!safe(data,capacity) || !separate(data,capacity,count,sizeof(*count)))))return BU_ARGUMENT;
 if(cookie!=0xbaa1 || !active || batch_upload_current.state!=BU_READING)return BU_STATE;
 *count=0;n=upload_source_read(data,1,capacity,2);
 if(n==0xffff)return fail(BU_SOURCE,upload_source_result.dos_error,upload_source_result.first_status);
 *count=n;return BU_OK;
}
unsigned __cdecl batch_upload_close(void)
{
 unsigned s;
 if(cookie!=0xbaa1)return BU_STATE;
 if(upload_source_result.handle_uncertain)return BU_RECOVERY;
 if(!active || batch_upload_current.state!=BU_READING)return BU_STATE;
 if(upload_source_result.consumed!=upload_source_result.size)return BU_BUSY;
 s=upload_source_close(2);
 if(s){active=upload_source_result.handle_open || upload_source_result.handle_uncertain;return fail(active?BU_RECOVERY:BU_SOURCE,upload_source_result.close_error,upload_source_result.first_status);}
 s=upload_source_finish();active=0;if(s)return fail(BU_SOURCE,upload_source_result.dos_error,s);
 batch_upload_current.state=BU_ENUMERATING;return BU_OK;
}
unsigned __cdecl batch_upload_abort(void)
{
 unsigned s;
 if(cookie!=0xbaa1)return BU_STATE;
 s=upload_source_abort();active=upload_source_result.handle_open || upload_source_result.handle_uncertain;
 if(s)return fail(active?BU_RECOVERY:BU_SOURCE,upload_source_result.close_error,s);
 batch_upload_current.state=BU_ABORTED;return BU_OK;
}
