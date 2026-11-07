#include <dos.h>
#include <string.h>
#include "meta_key_owner.h"
#include "meta_key_resource.h"
#include "../capture/capture_file.h"
typedef char owner_layout[sizeof(meta_key_owner)==1518?1:-1];
typedef struct owner_registration {meta_key_owner __far *active;} owner_registration;
static owner_registration __based(__segname("_CODE")) registration={0};
#define TOKEN ((void *)0x4d4b)
static unsigned span(const void __far *p,unsigned n,unsigned long *a)
{*a=(unsigned long)FP_SEG(p)*16UL+FP_OFF(p);return p && (unsigned long)FP_OFF(p)+n<=65536UL && *a+n<=0x100000UL;}
static unsigned separate(const void __far *p,unsigned n,const void __far *q,unsigned m)
{unsigned long a,b;return span(p,n,&a) && span(q,m,&b) && (a+n<=b || b+m<=a);}
static unsigned valid(const meta_key_owner __far *s)
{unsigned long a;return span(s,sizeof(*s),&a) && s->cookie==0x4d4f && s->phase>=META_OWNER_ACTIVE && s->phase<=META_OWNER_CLOSED && s->claimed<=1 && s->has_current<=1 && s->pending<=1 && s->baseline_exists<=1;}
static unsigned active(const meta_key_owner __far *s)
{if(!valid(s) || registration.active!=s)return META_OWNER_STATE;if(s->phase==META_OWNER_HELD)return META_OWNER_RECOVERY;return s->phase==META_OWNER_ACTIVE && s->claimed?META_OWNER_OK:META_OWNER_STATE;}
static unsigned schema(const unsigned char __far *p)
{unsigned i,r;for(r=0;r<10;++r){if(p[r*54+1] || p[r*54]>3)return 0;for(i=0;i<52 && p[r*54+2+i];++i){}if(i==52)return 0;}return 1;}
static unsigned __far __cdecl probe(const char *identity,void *context)
{
 meta_key_owner __far *s=registration.active;unsigned i,j;
 if(context!=TOKEN || !valid(s))return 1;
 for(i=0;i<2;++i)if(i?s->pending:s->has_current)for(j=0;j<3;++j)if(!_fstrcmp(identity,s->paths[i][j]))return 1;
 return 0;
}
static unsigned status(meta_key_owner __far *s,unsigned code){s->status=code;return code;}
static unsigned held(meta_key_owner __far *s){s->phase=META_OWNER_HELD;return status(s,META_OWNER_RECOVERY);}
static unsigned recovery(const directory_replace_result *r)
{return r->close_error || r->rollback_error || r->cleanup_error || r->stage_exists || r->original_in_backup;}
unsigned __cdecl meta_key_owner_begin(meta_key_owner __far *s)
{
 unsigned e;
 if(!separate(s,sizeof(*s),&registration,sizeof(registration)))return META_OWNER_ARGUMENT;
 if(registration.active)return valid(registration.active) && registration.active->phase==META_OWNER_HELD?META_OWNER_RECOVERY:META_OWNER_BUSY;
 _fmemset(s,0,sizeof(*s));s->cookie=0x4d4f;s->phase=META_OWNER_ACTIVE;registration.active=s;
 e=capture_file_reserve(probe,TOKEN);s->claim_status=e;
 if(e){registration.active=0;s->phase=META_OWNER_CLOSED;return status(s,META_OWNER_CLAIM);}
 s->claimed=1;return META_OWNER_OK;
}
static unsigned open_selection(meta_key_owner __far *s,const char *path,const unsigned char __far *defaults,unsigned char __far *destination,unsigned bind)
{
 meta_key_resource_result resource;key_actions_dos_result read;directory_replace_result write;
 char target[64],stage[64],backup[64];unsigned e,i,r,c,exists=1;
 e=active(s);if(e)return e;
 if(!separate(s,sizeof(*s),path,64) || path[1]!=':' || path[2]!='\\' || key_editor_file_paths(path,stage,backup))return META_OWNER_ARGUMENT;
 if(!bind && (!separate(s,sizeof(*s),defaults,540) || !separate(s,sizeof(*s),destination,540) || !separate(path,64,defaults,540) || !separate(path,64,destination,540) || !schema(defaults)))return META_OWNER_ARGUMENT;
 s->created=s->io_status=s->resolve_status=s->resolve_dos_error=s->environment_error=0;_fmemset(&s->read,0,sizeof(s->read));_fmemset(&s->write,0,sizeof(s->write));
 memset(&resource,0,sizeof(resource));e=meta_key_resource_lookup(0,path,&resource);s->resolve_status=e;s->resolve_dos_error=resource.dos_error;s->environment_error=resource.environment_error;if(e!=META_RESOURCE_OK && e!=META_RESOURCE_MISSING)return status(s,META_OWNER_RESOLVE);
 for(i=0;i<64;++i){c=(unsigned char)path[i];if(c>='a' && c<='z')c-=32;target[i]=(char)c;if(!c)break;}
 if(strcmp(target,resource.path))return status(s,META_OWNER_IDENTITY);
 _fmemcpy(s->paths[1][0],resource.path,64);_fmemcpy(s->paths[1][1],stage,64);_fmemcpy(s->paths[1][2],backup,64);s->pending=1;
 e=capture_file_reserve(probe,TOKEN);s->claim_status=e;
 if(e){s->pending=0;return status(s,META_OWNER_CLAIM);}
 s->created=0;s->io_status=0;_fmemset(&s->read,0,sizeof(s->read));_fmemset(&s->write,0,sizeof(s->write));
 memset(&read,0,sizeof(read));e=key_editor_file_load(resource.path,s->staged,&read);_fmemcpy(&s->read,&read,sizeof(read));s->io_status=e;
 if(read.close_error)return held(s);
 if(e){
  if(e!=KEY_ACTIONS_DOS_OPEN || read.dos_error!=2){s->pending=0;return status(s,META_OWNER_LOAD);}
  if(bind){exists=0;s->io_status=0;}else{
  _fmemcpy(s->staged,defaults,540);for(r=0;r<10;++r){s->staged[r*54]=3;s->staged[r*54+1]=s->staged[r*54+2]=0;}
  memset(&write,0,sizeof(write));e=key_editor_file_save(resource.path,0,s->staged,&write);_fmemcpy(&s->write,&write,sizeof(write));s->io_status=e;
  if(recovery(&write))return held(s);
  if(e){s->pending=0;return status(s,META_OWNER_LOAD);}s->created=1;}
 }
 s->baseline_exists=exists;if(exists)_fmemcpy(s->baseline,s->staged,540);if(!bind)_fmemcpy(destination,s->staged,540);_fmemcpy(s->paths[0],s->paths[1],192);s->has_current=1;s->pending=0;return status(s,META_OWNER_OK);
}
unsigned __cdecl meta_key_owner_bind(meta_key_owner __far *s,const char *path)
{return open_selection(s,path,0,0,1);}
unsigned __cdecl meta_key_owner_load(meta_key_owner __far *s,const char *path,const unsigned char __far *defaults,unsigned char __far *destination)
{return open_selection(s,path,defaults,destination,0);}
unsigned __cdecl meta_key_owner_save(meta_key_owner __far *s,const unsigned char __far *records)
{
 char path[64];directory_replace_result write;unsigned e=active(s);if(e)return e;
 if(!s->has_current || s->pending)return META_OWNER_STATE;
 if(!separate(s,sizeof(*s),records,540) || !schema(records))return META_OWNER_ARGUMENT;
 _fmemset(&s->read,0,sizeof(s->read));s->resolve_status=s->resolve_dos_error=s->environment_error=0;memset(&write,0,sizeof(write));
 _fmemcpy(path,s->paths[0][0],64);e=key_editor_file_save(path,s->baseline_exists?s->baseline:0,records,&write);_fmemcpy(&s->write,&write,sizeof(write));s->io_status=e;s->created=0;
 if(write.installed){_fmemcpy(s->baseline,records,540);s->baseline_exists=1;}
 if(recovery(&write))return held(s);return status(s,e?META_OWNER_SAVE:META_OWNER_OK);
}
unsigned __cdecl meta_key_owner_end(meta_key_owner __far *s)
{
 unsigned e=active(s);if(e)return e;
 e=capture_file_release(probe,TOKEN);s->claim_status=e;if(e)return held(s);
 s->claimed=0;s->phase=META_OWNER_CLOSED;registration.active=0;return status(s,META_OWNER_OK);
}
unsigned __far __cdecl meta_key_owner_exec_allowed(void)
{return registration.active?0:1;}
