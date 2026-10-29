#include "directory_resources.h"
#include "directory_live.h"
#include "../config/resource_path.h"
#include "../capture/capture_file.h"
#include "../capture/capture_fs.h"
#ifdef DIRECTORY_TRANSLATION_RESOURCES
#include "../translation/xlt_dos.h"
#endif
#include <dos.h>
#include <string.h>
#ifndef KEY_RESOURCE_PRIVATE_READS
#error Directory resources require non-inheritable KEY/KBD readers
#endif
typedef char dr_word_abi[sizeof(unsigned)==2?1:-1];
#ifdef DIRECTORY_TRANSLATION_RESOURCES
typedef char dr_request_abi[sizeof(directory_resource_request)==314?1:-1];
typedef char dr_bundle_abi[sizeof(directory_resource_bundle)==1948?1:-1];
typedef char dr_snapshot_abi[sizeof(directory_resource_snapshot)==206?1:-1];
const unsigned directory_translation_layout[5]={314,1948,206,202,6624};
#else
typedef char dr_request_abi[sizeof(directory_resource_request)==248?1:-1];
typedef char dr_bundle_abi[sizeof(directory_resource_bundle)==1624?1:-1];
typedef char dr_snapshot_abi[sizeof(directory_resource_snapshot)==142?1:-1];
#endif
directory_resource_snapshot directory_resource_result;
static unsigned cookie=0xd620;
static unsigned long linear(const void __far *p)
{return (unsigned long)FP_SEG(p)*16UL+FP_OFF(p);}
static unsigned span(const void __far *p,unsigned n)
{return p && (unsigned long)FP_OFF(p)+n<=65536UL && linear(p)+n<=1048576UL;}
static unsigned separate(const void __far *p,unsigned n,const void __far *q,unsigned m)
{return linear(p)+n<=linear(q) || linear(q)+m<=linear(p);}
static unsigned external(const void __far *p,unsigned n)
{return span(p,n) && separate(p,n,&cookie,2) && separate(p,n,&directory_resource_result,sizeof(directory_resource_result));}
static unsigned available(void)
{
 if(cookie!=0xd621)return DR_STATE;
 if(directory_resource_result.state==DR_ACTIVE)return DR_BUSY;
 if(directory_resource_result.state==DR_HELD)return DR_RECOVERY;
 if(directory_resource_result.state!=DR_IDLE && directory_resource_result.state!=DR_RESOLVED)return DR_STATE;
 return 0;
}
unsigned __cdecl directory_resources_initialize(void)
{
 if(cookie==0xd620){memset(&directory_resource_result,0,sizeof(directory_resource_result));cookie=0xd621;return 0;}
 return available();
}
unsigned __far __cdecl directory_resources_exec_allowed(void)
{return cookie==0xd620 || (cookie==0xd621 && (directory_resource_result.state==DR_IDLE || directory_resource_result.state==DR_RESOLVED));}
static unsigned absolute(const char *p)
{return capture_file_validate_path(p,0) && p[0]>='A' && p[0]<='Z' && p[1]==':' && p[2]=='\\';}
static unsigned canonical(const char *path,char *out)
{
 char stage[128];unsigned n,c,status;
 memset(stage,0,sizeof(stage));status=capture_fs_canonical(path,stage);
 if(status){directory_resource_result.dos_error=status;return DR_CANONICAL;}
 for(n=0;n<128 && stage[n];++n){
  c=(unsigned char)stage[n];if(c>='a' && c<='z')c-=32;if(c=='/')c='\\';stage[n]=(char)c;
 }
 if(n>63 || !absolute(stage))return DR_PATH;
 memcpy(out,stage,n+1);return 0;
}
/* Return0 found,1 missing,2 operational error; error status is retained. */
static unsigned inspect(const char *path,char *out)
{
 unsigned status,attributes=0;
 status=canonical(path,out);
 if(status){directory_resource_result.status=status;return 2;}
 status=capture_fs_attributes(out,&attributes);
 if(status==2 || status==3){memset(out,0,64);return 1;}
 if(status || (attributes&0x18)){
  directory_resource_result.status=DR_LOOKUP;directory_resource_result.dos_error=status;return 2;
 }
 return 0;
}
static unsigned lookup(unsigned psp,const char *leaf,char *out)
{
 char path[64];unsigned status;
 status=inspect(leaf,out);if(status!=1)return status;
 status=resource_pcplus_path(psp,leaf,path);
 if(status==RESOURCE_PATH_ABSENT)return 1;
 if(status){directory_resource_result.status=DR_LOOKUP;directory_resource_result.source_status=status;return 2;}
 return inspect(path,out);
}
static unsigned __far __cdecl reserved(const char *identity,void *context)
{
 if(context!=&directory_resource_result)return 1;
 return !strcmp(identity,directory_resource_result.keyboard_path) || !strcmp(identity,directory_resource_result.actions_path)
#ifdef DIRECTORY_TRANSLATION_RESOURCES
  || !strcmp(identity,directory_resource_result.translation_path)
#endif
 ;
}
unsigned __cdecl directory_resources_stage(const directory_resource_request *request,
 const unsigned char *defaults,directory_resource_bundle __far *output)
{
 directory_resource_bundle stage;
 directory_resource_snapshot *r=&directory_resource_result;
 keymap_dos_result kbd;key_actions_dos_result key;
#ifdef DIRECTORY_TRANSLATION_RESOURCES
 xlt_dos_result xlt;
 const unsigned allowed_mask=512U|4096U|16384U;
#endif
 char keyboard[13],actions[13];unsigned status,i,j,claim=0;
 status=available();if(status)return status;
 if(!external(request,sizeof(*request)) || !external(defaults,948) || !external(output,sizeof(*output)) ||
  !separate(request,sizeof(*request),defaults,948) || !separate(request,sizeof(*request),output,sizeof(*output)) ||
  !separate(defaults,948,output,sizeof(*output)))return DR_ARGUMENT;
 if((request->profile!=4 && request->profile!=6) || (request->cli_mask&~(
#ifdef DIRECTORY_TRANSLATION_RESOURCES
  allowed_mask
#else
  512U|4096U
#endif
 )))return DR_ARGUMENT;
#ifdef DIRECTORY_TRANSLATION_RESOURCES
 if(request->translation_mode>2)return DR_ARGUMENT;
 if(request->cli_mask&16384){
  for(j=0;j<64 && request->cli_translation[j];++j){}
  if(j==64 || !absolute(request->cli_translation))return DR_ARGUMENT;
 }
#endif
 /* Fixed-size request fields must be terminated before the path validator. */
 for(i=0;i<2;++i){
  const char *path=i?request->cli_actions:request->cli_keyboard;
  if(!(request->cli_mask&(i?4096U:512U)))continue;
  for(j=0;j<64 && path[j];++j){}
  if(j==64 || !absolute(path))return DR_ARGUMENT;
 }
 if(directory_binding_name(request->record+0x56,0,actions) ||
  directory_binding_name(request->record+0x5f,1,keyboard))return DR_ARGUMENT;
 for(i=0;i<79;++i){for(j=0;j<12 && defaults[i*12+j];++j){}if(j==12)return DR_ARGUMENT;}
 memset(r,0,sizeof(*r));r->state=DR_ACTIVE;
 memset(&stage,0,sizeof(stage));stage.profile=request->profile;
 memcpy(stage.keyboard,defaults,948);
 for(i=0;i<10;++i)stage.actions[i*54]=3;
 if(request->cli_mask&512){
  status=inspect(request->cli_keyboard,stage.keyboard_path);stage.keyboard_source=DR_CLI;
  if(status==1){r->status=DR_LOOKUP;r->dos_error=2;}
  if(status)goto resolved;
 }else if(keyboard[0]){
  status=lookup(request->psp,keyboard,stage.keyboard_path);stage.keyboard_source=DR_DIRECTORY;
  if(status==1){status=lookup(request->psp,"PCPLUS.KBD",stage.keyboard_path);stage.keyboard_source=DR_FALLBACK;}
  if(status==2)goto resolved;
  if(status==1)stage.keyboard_source=DR_DEFAULT;
 }
 if(request->cli_mask&4096){
  status=inspect(request->cli_actions,stage.actions_path);stage.actions_source=DR_CLI;
  if(status==1){r->status=DR_LOOKUP;r->dos_error=2;}
  if(status)goto resolved;
 }else if(actions[0]){
  status=lookup(request->psp,actions,stage.actions_path);stage.actions_source=DR_DIRECTORY;
  if(status==2)goto resolved;
  if(status==1)stage.actions_source=DR_DEFAULT;
 }
#ifdef DIRECTORY_TRANSLATION_RESOURCES
 stage.translation_mode=request->cli_mask&16384?1:request->translation_mode;
 if(stage.translation_mode==1){
  if(request->cli_mask&16384){
   status=inspect(request->cli_translation,stage.translation_path);stage.translation_source=DR_CLI;
  }else status=lookup(request->psp,"PCPLUS.XLT",stage.translation_path);
  if(status==1){r->status=DR_LOOKUP;r->dos_error=2;}
  if(status)goto resolved;
 }
 memcpy(r->translation_path,stage.translation_path,64);
#endif
 memcpy(r->keyboard_path,stage.keyboard_path,64);memcpy(r->actions_path,stage.actions_path,64);
 if(stage.keyboard_path[0] || stage.actions_path[0]
#ifdef DIRECTORY_TRANSLATION_RESOURCES
  || stage.translation_path[0]
#endif
 ){
  r->claim_status=capture_file_reserve(reserved,r);
  if(r->claim_status){r->status=DR_CLAIM;goto resolved;}
  claim=1;
 }
 if(stage.keyboard_path[0]){
  status=keymap_dos_read(stage.keyboard_path,request->profile,stage.keyboard,&kbd);
  if(status){r->status=DR_KEYMAP;r->source_status=status;r->dos_error=kbd.dos_error;r->close_error=kbd.close_error;goto finished;}
  stage.mask|=512;
 }
 if(stage.actions_path[0]){
  status=key_actions_dos_read(stage.actions_path,stage.actions,&key);
  if(status){r->status=DR_ACTIONS;r->source_status=status;r->dos_error=key.dos_error;r->close_error=key.close_error;goto finished;}
  stage.mask|=4096;
 }
#ifdef DIRECTORY_TRANSLATION_RESOURCES
 if(stage.translation_path[0]){
  status=xlt_dos_read(stage.translation_path,stage.translation,&xlt);
  if(status){r->status=DR_TRANSLATION;r->source_status=status;r->dos_error=xlt.dos_error;r->close_error=xlt.close_error;goto finished;}
  stage.mask|=16384;
 }
#endif
finished:
 if(r->close_error){r->state=DR_HELD;return r->status;}
 if(claim){r->release_status=capture_file_release(reserved,r);if(r->release_status){r->state=DR_HELD;if(!r->status)r->status=DR_RELEASE;return r->status;}}
resolved:
 r->state=DR_RESOLVED;
 if(!r->status){
#ifdef TERMINAL_DIRECTORY_RESOURCE_OWNER
  for(i=0;i<sizeof(stage);++i)((unsigned char __far *)output)[i]=((unsigned char *)&stage)[i];
#else
  _fmemcpy(output,&stage,sizeof(stage));
#endif
 }
 return r->status;
}
