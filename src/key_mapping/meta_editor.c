#include <dos.h>
#include <string.h>
#include "meta_editor.h"
#include "meta_key_resource.h"
#define TEXT __based(__segname("_CODE"))
static const char TEXT prompt_label[]="LOAD FILE:";
static const char TEXT working[]="File operation pending...";
static const char TEXT nofiles[]="No KEY files found.";
static const char TEXT failed[]="File operation failed. Definitions retained.";
static const char TEXT fatal[]="KEY recovery required. Return to DOS.";
static unsigned span(const void __far *p,unsigned n,unsigned long *a)
{*a=(unsigned long)FP_SEG(p)*16UL+FP_OFF(p);return p && (unsigned long)FP_OFF(p)+n<=65536UL && *a+n<=0x100000UL;}
static unsigned separate(const void __far *p,unsigned n,const void __far *q,unsigned m)
{unsigned long a,b;return span(p,n,&a) && span(q,m,&b) && (a+n<=b || b+m<=a);}
static unsigned valid(const meta_editor __far *s)
{unsigned long a;return span(s,sizeof(*s),&a) && s->cookie==0x4d45 && s->phase<=META_EDITOR_FATAL && s->owner_started<=1 && s->fallback<=1;}
static unsigned string(const char __far *s)
{unsigned i;unsigned long a;if(!span(s,64,&a))return 0;for(i=0;i<64 && s[i];++i)if((unsigned char)s[i]<32 || (unsigned char)s[i]>126)return 0;return i && i<64;}
static unsigned schema(const unsigned char __far *p)
{unsigned r,i;for(r=0;r<10;++r){if(p[r*54+1] || p[r*54]>3)return 0;for(i=0;i<52 && p[r*54+2+i];++i){}if(i==52)return 0;}return 1;}
static unsigned failure(meta_editor __far *s,unsigned code,unsigned error)
{
 s->backend_status=code;s->dos_error=error;s->notice=1;
 if(code==META_OWNER_RECOVERY || (s->owner_started && s->owner.phase==META_OWNER_HELD)){s->phase=META_EDITOR_FATAL;return META_EDITOR_RECOVERY;}
 if(s->dialog.phase==META_DIALOG_WAIT)meta_dialog_complete(&s->dialog,1,0,0);
 s->phase=META_EDITOR_DIALOG;return META_EDITOR_IO;
}
static unsigned owner_error(const meta_editor __far *s)
{
 if(s->owner.write.dos_error)return s->owner.write.dos_error;
 if(s->owner.write.close_error)return s->owner.write.close_error;
 if(s->owner.write.rollback_error)return s->owner.write.rollback_error;
 if(s->owner.write.cleanup_error)return s->owner.write.cleanup_error;
 if(s->owner.read.dos_error)return s->owner.read.dos_error;
 if(s->owner.read.close_error)return s->owner.read.close_error;
 return s->owner.resolve_dos_error;
}
static unsigned cancel(meta_editor __far *s)
{if(s->dialog.phase==META_DIALOG_WAIT)meta_dialog_cancel(&s->dialog);s->phase=META_EDITOR_DIALOG;s->notice=0;return META_EDITOR_OK;}
static unsigned ensure(meta_editor __far *s)
{unsigned e;if(s->owner_started)return META_OWNER_OK;e=meta_key_owner_begin(&s->owner);if(!e)s->owner_started=1;return e;}
unsigned __cdecl meta_editor_open(meta_editor __far *s,unsigned psp,const unsigned char __far *records,const char __far *name,const char __far *path,unsigned shape)
{
 char request[64],a[64],b[64];unsigned long at;
 if(!span(s,sizeof(*s),&at) || !separate(s,sizeof(*s),records,540) || !separate(s,sizeof(*s),name,64) || !separate(s,sizeof(*s),path,64) || !string(name) || !string(path) || !schema(records))return META_EDITOR_ARGUMENT;
 if(!meta_key_owner_exec_allowed() || (s->cookie==0x4d45 && s->phase!=META_EDITOR_CLOSED))return META_EDITOR_BUSY;
 _fmemcpy(request,path,64);if(request[1]!=':' || request[2]!='\\' || key_editor_file_paths(request,a,b))return META_EDITOR_ARGUMENT;
 _fmemset(s,0,sizeof(*s));meta_dialog_open(&s->dialog,records,name,shape);_fmemcpy(s->expected,records,540);_fmemcpy(s->current_path,path,64);_fmemcpy(s->initial_path,path,64);
 s->cookie=0x4d45;s->phase=META_EDITOR_INIT;s->psp=psp;return META_EDITOR_OK;
}
unsigned __cdecl meta_editor_key(meta_editor __far *s,unsigned key)
{
 unsigned e;char pattern[64],stem[9],path[64];unsigned i;
 if(!valid(s))return META_EDITOR_ARGUMENT;if(s->phase==META_EDITOR_FATAL)return META_EDITOR_RECOVERY;
 if(s->phase==META_EDITOR_INIT && key==27)return meta_editor_stop(s);
 if((s->phase==META_EDITOR_RESOLVE || s->phase==META_EDITOR_LOAD || s->phase==META_EDITOR_SAVE) && key==27)return cancel(s);
 if(s->phase==META_EDITOR_NAME){
  e=meta_file_prompt_key(&s->prompt,key);
  if(e==META_FILE_CANCEL)return cancel(s);
  if(e==META_FILE_PICK){s->fallback=0;s->phase=META_EDITOR_PLAN;}
  else if(e==META_FILE_LOAD){_fmemcpy(s->pending_name,s->prompt.candidate,64);s->phase=META_EDITOR_RESOLVE;}
  return e==META_FILE_ARGUMENT?META_EDITOR_ARGUMENT:META_EDITOR_OK;
 }
 if(s->phase==META_EDITOR_PICK){
  e=meta_picker_key(&s->picker,key);if(e==META_PICKER_BELL){++s->dialog.bells;return META_EDITOR_OK;}if(e)return META_EDITOR_ARGUMENT;
  if(s->picker.phase==META_PICKER_CANCEL)return cancel(s);
  if(s->picker.phase==META_PICKER_ACCEPT){
   meta_picker_selected(&s->picker,stem);_fmemcpy(pattern,s->pattern,64);e=meta_key_resource_selected(pattern,stem,path);if(e)return failure(s,e,0);
   _fmemcpy(s->pending_path,path,64);for(i=0;stem[i];++i)s->pending_name[i]=stem[i];s->pending_name[i]='.';s->pending_name[i+1]='K';s->pending_name[i+2]='E';s->pending_name[i+3]='Y';s->pending_name[i+4]=0;s->phase=META_EDITOR_LOAD;
  }return META_EDITOR_OK;
 }
 if((s->phase==META_EDITOR_PLAN || s->phase==META_EDITOR_SCAN) && key==27){if(s->phase==META_EDITOR_SCAN)meta_picker_scan_cancel(&s->scan);return cancel(s);}
 if(s->phase!=META_EDITOR_DIALOG)return META_EDITOR_BUSY;
 e=meta_dialog_key(&s->dialog,key);s->notice=0;
 if(e==META_DIALOG_LOAD){meta_file_prompt_begin(&s->prompt,1,s->dialog.saved_shape);s->phase=META_EDITOR_NAME;}
 else if(e==META_DIALOG_SAVE)s->phase=META_EDITOR_SAVE;
 else if(s->dialog.phase==META_DIALOG_CLOSED)s->phase=META_EDITOR_CLOSING;
 return e==META_DIALOG_ARGUMENT?META_EDITOR_ARGUMENT:META_EDITOR_OK;
}
unsigned __cdecl meta_editor_step(meta_editor __far *s,unsigned admitted)
{
 char path[64],name[64];meta_key_resource_result r;unsigned e;
 if(!valid(s) || admitted>1)return META_EDITOR_ARGUMENT;if(s->phase==META_EDITOR_FATAL)return META_EDITOR_RECOVERY;
 if(s->phase==META_EDITOR_CLOSING){
  if(s->owner_started){if(!admitted)return META_EDITOR_BUSY;e=meta_key_owner_end(&s->owner);if(e){s->backend_status=e;s->notice=1;s->phase=META_EDITOR_FATAL;return META_EDITOR_RECOVERY;}s->owner_started=0;}
  s->phase=META_EDITOR_CLOSED;return META_EDITOR_OK;
 }
 if(s->phase==META_EDITOR_DIALOG || s->phase==META_EDITOR_NAME || s->phase==META_EDITOR_PICK || s->phase==META_EDITOR_CLOSED)return META_EDITOR_OK;
 if(!admitted)return META_EDITOR_BUSY;
 if(s->phase==META_EDITOR_INIT){
  e=ensure(s);if(e)return failure(s,e,0);_fmemcpy(path,s->current_path,64);e=meta_key_owner_bind(&s->owner,path);if(e)return failure(s,e,owner_error(s));s->phase=META_EDITOR_DIALOG;return META_EDITOR_OK;
 }
 if(s->phase==META_EDITOR_PLAN){
  e=meta_key_resource_pattern(s->psp,s->fallback,&r);
  if(e==META_RESOURCE_MISSING){cancel(s);s->notice=2;return META_EDITOR_OK;}if(e)return failure(s,e,r.dos_error);
  _fmemcpy(s->pattern,r.path,64);meta_picker_begin(&s->picker,s->names);e=meta_picker_scan_begin(&s->scan,&s->picker,r.path);if(e)return failure(s,e,0);s->phase=META_EDITOR_SCAN;return META_EDITOR_OK;
 }
 if(s->phase==META_EDITOR_SCAN){
  e=meta_picker_scan_step(&s->scan);if(e)return failure(s,e,s->scan.dos_error);
  if(s->scan.phase==META_SCAN_DONE){if(s->picker.phase==META_PICKER_EMPTY){if(!s->fallback){s->fallback=1;s->phase=META_EDITOR_PLAN;}else{cancel(s);s->notice=2;}}else s->phase=META_EDITOR_PICK;}
  return META_EDITOR_OK;
 }
 if(s->phase==META_EDITOR_RESOLVE){
  _fmemcpy(name,s->pending_name,64);e=meta_key_resource_lookup(s->psp,name,&r);if(e!=META_RESOURCE_OK && e!=META_RESOURCE_MISSING)return failure(s,e,r.dos_error);_fmemcpy(s->pending_path,r.path,64);s->phase=META_EDITOR_LOAD;return META_EDITOR_OK;
 }
 if(s->phase==META_EDITOR_LOAD){
  e=ensure(s);if(e)return failure(s,e,0);_fmemcpy(path,s->pending_path,64);e=meta_key_owner_load(&s->owner,path,s->dialog.records,s->loaded);if(e)return failure(s,e,owner_error(s));
  e=meta_dialog_complete(&s->dialog,0,s->loaded,s->pending_name);if(e){s->backend_status=e;s->notice=1;s->phase=META_EDITOR_FATAL;return META_EDITOR_RECOVERY;}_fmemcpy(s->current_path,s->owner.paths[0][0],64);s->phase=META_EDITOR_DIALOG;s->notice=0;return META_EDITOR_OK;
 }
 if(s->phase==META_EDITOR_SAVE){
  e=ensure(s);if(e)return failure(s,e,0);
  if(!s->owner.has_current){_fmemcpy(path,s->current_path,64);e=meta_key_owner_bind(&s->owner,path);if(e)return failure(s,e,0);}
  e=meta_key_owner_save(&s->owner,s->dialog.records);if(e)return failure(s,e,owner_error(s));e=meta_dialog_complete(&s->dialog,0,0,0);if(e){s->backend_status=e;s->notice=1;s->phase=META_EDITOR_FATAL;return META_EDITOR_RECOVERY;}s->phase=META_EDITOR_DIALOG;s->notice=0;return META_EDITOR_OK;
 }return META_EDITOR_ARGUMENT;
}
unsigned __cdecl meta_editor_stop(meta_editor __far *s)
{if(!valid(s))return META_EDITOR_ARGUMENT;if(s->phase==META_EDITOR_FATAL)return META_EDITOR_RECOVERY;if(s->phase==META_EDITOR_CLOSED)return META_EDITOR_OK;if(s->phase==META_EDITOR_SCAN)meta_picker_scan_cancel(&s->scan);if(s->dialog.phase==META_DIALOG_WAIT)meta_dialog_cancel(&s->dialog);s->dialog.phase=META_DIALOG_CLOSED;s->phase=META_EDITOR_CLOSING;return META_EDITOR_OK;}
static void label(unsigned __far *f,unsigned at,const char __far *p,unsigned attr)
{while(*p && at<2000)f[at++]=(attr<<8)|(unsigned char)*p++;}
unsigned __cdecl meta_editor_draw(const meta_editor __far *s,unsigned __far *frame,unsigned attr)
{
 unsigned r,c;const char __far *message=0;
 if(!valid(s) || attr>255 || !separate(s,sizeof(*s),frame,4000))return META_EDITOR_ARGUMENT;
 if(s->phase==META_EDITOR_CLOSED)return META_EDITOR_OK;
 if(meta_dialog_draw(&s->dialog,frame,attr))return META_EDITOR_ARGUMENT;
 if(s->phase==META_EDITOR_NAME){
  for(r=7;r<=11;++r)for(c=2;c<=39;++c)frame[r*80+c]=(attr<<8)|' ';
  for(c=3;c<39;++c)frame[7*80+c]=frame[11*80+c]=(attr<<8)|205;
  for(r=8;r<11;++r)frame[r*80+2]=frame[r*80+39]=(attr<<8)|186;
  frame[7*80+2]=(attr<<8)|201;frame[7*80+39]=(attr<<8)|187;frame[11*80+2]=(attr<<8)|200;frame[11*80+39]=(attr<<8)|188;
  label(frame,9*80+3,prompt_label,attr);for(c=0;c<8;++c)frame[9*80+17+c]=(attr<<8)|s->prompt.editor.field[c];
 }else if(s->phase==META_EDITOR_PICK){if(meta_picker_draw(&s->picker,frame,attr))return META_EDITOR_ARGUMENT;}
 if(s->phase==META_EDITOR_FATAL)message=fatal;else if(s->notice==1)message=failed;else if(s->notice==2)message=nofiles;
 else if(s->phase!=META_EDITOR_DIALOG && s->phase!=META_EDITOR_NAME && s->phase!=META_EDITOR_PICK)message=working;
 if(message){for(c=0;c<80;++c)frame[20*80+c]=0x0720;label(frame,20*80+1,message,7);}return META_EDITOR_OK;
}
unsigned __cdecl meta_editor_cursor(const meta_editor __far *s)
{if(!valid(s))return 0xffff;if(s->phase==META_EDITOR_NAME)return 0x0911+s->prompt.editor.cursor;return s->phase==META_EDITOR_DIALOG?meta_dialog_cursor(&s->dialog):0xffff;}
unsigned __cdecl meta_editor_shape(const meta_editor __far *s)
{if(!valid(s))return 0xffff;if(s->phase==META_EDITOR_NAME)return meta_filename_shape(&s->prompt.editor);return s->phase==META_EDITOR_DIALOG?meta_dialog_shape(&s->dialog):s->dialog.saved_shape|0x2000;}
unsigned __cdecl meta_editor_matches(const meta_editor __far *s,const unsigned char __far *records,const char __far *path)
{return valid(s) && s->phase==META_EDITOR_CLOSED && separate(s,sizeof(*s),records,540) && separate(s,sizeof(*s),path,64) && string(path) && !_fmemcmp(s->expected,records,540) && !_fstrcmp(s->initial_path,path);}
unsigned __cdecl meta_editor_proposal(const meta_editor __far *s,unsigned char __far *records,char __far *name,char __far *path)
{
 if(!valid(s) || s->phase!=META_EDITOR_CLOSED || !separate(s,sizeof(*s),records,540) || !separate(s,sizeof(*s),name,64) || !separate(s,sizeof(*s),path,64) || !separate(records,540,name,64) || !separate(records,540,path,64) || !separate(name,64,path,64))return META_EDITOR_ARGUMENT;
 _fmemcpy(records,s->dialog.records,540);_fmemcpy(name,s->dialog.name,64);_fmemcpy(path,s->current_path,64);return META_EDITOR_OK;
}
