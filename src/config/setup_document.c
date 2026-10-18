#include "setup_document.h"
#include <string.h>
static unsigned extent(const void *p,unsigned n)
{ return p && (unsigned long)(unsigned)p+n<=65536UL; }
static unsigned separate(const void *a,unsigned as,const void *b,unsigned bs)
{ return (unsigned long)(unsigned)a+as<=(unsigned)b || (unsigned long)(unsigned)b+bs<=(unsigned)a; }
static unsigned fold(unsigned c){return c>='a' && c<='z'?c-32:c;}
static unsigned name(const char *path,char *out)
{
 unsigned i,c,base=0,ext=0,dot=0;char stem[9];
 if(!extent(path,13))return 0;
 for(i=0;i<13 && path[i];++i){
  c=fold((unsigned char)path[i]);out[i]=(char)c;
  if(c=='.'){if(dot || !base)return 0;dot=1;continue;}
  if(!((c>='A' && c<='Z') || (c>='0' && c<='9') || c=='_' || c=='-'))return 0;
  if(dot){if(++ext>3)return 0;}
  else {if(base==8)return 0;stem[base++]=(char)c;}
 }
 if(i==13 || !base || (dot && !ext))return 0;
 out[i]=0;stem[base]=0;
 if(!strcmp(stem,"CON") || !strcmp(stem,"AUX") || !strcmp(stem,"PRN") ||
  !strcmp(stem,"NUL") || !strcmp(stem,"CLOCK$"))return 0;
 if(base==4 && stem[3]>='1' && stem[3]<='9' &&
  (!memcmp(stem,"COM",3) || !memcmp(stem,"LPT",3)))return 0;
 if(!strcmp(out,"PRMEDIT.BAK"))return 0;
 /* '$' already rejected, so PRMEDIT.$$$ cannot be a target. */
 return 1;
}
static unsigned arguments(setup_document *doc,setup_document_result *r)
{
 return extent(doc,sizeof(*doc)) && extent(r,sizeof(*r)) &&
  separate(doc,sizeof(*doc),r,sizeof(*r));
}
unsigned __cdecl setup_document_open(const char *path,setup_document *doc,setup_document_result *r)
{
 prm_dos_image image;char target[13];
 if(!arguments(doc,r) || !extent(path,13) || !separate(path,13,r,sizeof(*r)))return SETUP_DOCUMENT_ARGUMENT;
 memset(r,0,sizeof(*r));r->bad_field=SETUP_NO_FIELD;
 if(!name(path,target)){r->status=SETUP_DOCUMENT_ARGUMENT;return r->status;}
 if(prm_dos_load(target,&image,&r->io)!=PRM_DOS_OK){r->status=SETUP_DOCUMENT_LOAD;return r->status;}
 memcpy(&doc->baseline,&image,sizeof(image));memcpy(&doc->staged,&image,sizeof(image));
 memset(doc->target,0,sizeof(doc->target));strcpy(doc->target,target);doc->loaded=1;doc->locked=0;
 return SETUP_DOCUMENT_OK;
}
unsigned __cdecl setup_document_save(setup_document *doc,setup_document_result *r)
{
 prm_dos_image current;char target[13];
 if(!arguments(doc,r))return SETUP_DOCUMENT_ARGUMENT;
 memset(r,0,sizeof(*r));r->bad_field=SETUP_NO_FIELD;
 if(doc->loaded!=1 || !name(doc->target,target)){
  r->status=SETUP_DOCUMENT_ARGUMENT;return r->status;
 }
 if(doc->locked){r->status=SETUP_DOCUMENT_LOCKED;return r->status;}
 if(setup_validate(&doc->staged,&r->bad_field)!=SETUP_OK){
  r->status=SETUP_DOCUMENT_INVALID;return r->status;
 }
 if(!memcmp(&doc->baseline,&doc->staged,sizeof(current)))return SETUP_DOCUMENT_OK;
 if(prm_dos_load(target,&current,&r->io)!=PRM_DOS_OK){r->status=SETUP_DOCUMENT_LOAD;return r->status;}
 if(memcmp(&current,&doc->baseline,sizeof(current))){r->status=SETUP_DOCUMENT_CHANGED;return r->status;}
 if(prm_dos_replace(target,"PRMEDIT.$$$","PRMEDIT.BAK",&doc->staged,&r->replacement)!=PRM_REPLACE_OK){
  r->status=SETUP_DOCUMENT_REPLACE;
  if(r->replacement.installed)memcpy(&doc->baseline,&doc->staged,sizeof(current));
  if(r->replacement.installed || r->replacement.original_in_backup || r->replacement.stage_exists)doc->locked=1;
  return r->status;
 }
 memcpy(&doc->baseline,&doc->staged,sizeof(current));return SETUP_DOCUMENT_OK;
}
