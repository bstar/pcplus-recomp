/* DOS16 fault model: production document/loader with deterministic DOS adapters. */
#include "editor_document.h"
#include "editor_fs.h"
#include "xlt_dos_fs.h"
#include <stdio.h>
#include <string.h>
static xlt_document doc,before;
static xlt_document_result result;
static unsigned char files[3][257];
static unsigned present[3],lengths[3],position,attributes;
static unsigned fault,io,closes,checks;
enum { CREATE=1,WRITE,SHORT0,SHORT255,CLOSE_WRITE,MOVE_OLD,INSTALL,
 ROLLBACK,DELETE_BACKUP,DELETE_STAGE,READ,PROBE,CLOSE_READ,OPEN };
#define CHECK(x) do { ++checks; if(!(x)){printf("FAIL line %u fault %u\n",(unsigned)__LINE__,fault);return 1;} } while(0)
static int slot(const char *s)
{return !strcmp(s,"TABLE.XLT")?0:!strcmp(s,"XLTEDIT.$$$")?1:!strcmp(s,"XLTEDIT.BAK")?2:-1;}
unsigned __cdecl xlt_edit_inspect(const char *s,unsigned *a)
{int n=slot(s);++io;if(n<0 || !present[n])return 2;*a=n==0?attributes:0;return 0;}
unsigned __cdecl xlt_edit_create(const char *s,int *h)
{int n=slot(s);++io;if(fault==CREATE)return 5;if(n<0)return 3;if(present[n])return 80;present[n]=1;lengths[n]=0;*h=n;return 0;}
unsigned __cdecl xlt_edit_write(int h,const void *b,unsigned n,unsigned *count)
{++io;if(fault==WRITE || fault==DELETE_STAGE){*count=0;return 29;}if(fault==SHORT0)n=0;if(fault==SHORT255)n=255;memcpy(files[h],b,n);lengths[h]=n;*count=n;return 0;}
unsigned __cdecl xlt_edit_rename(const char *a,const char *b)
{int from=slot(a),to=slot(b);++io;
 if((from==0 && fault==MOVE_OLD) || (from==1 && (fault==INSTALL || fault==ROLLBACK)) || (from==2 && fault==ROLLBACK))return 5;
 if(from<0 || to<0 || !present[from])return 2;if(present[to])return 5;
 memcpy(files[to],files[from],257);lengths[to]=lengths[from];present[from]=0;present[to]=1;return 0;}
unsigned __cdecl xlt_edit_delete(const char *s)
{int n=slot(s);++io;if((n==1 && fault==DELETE_STAGE) || (n==2 && fault==DELETE_BACKUP))return 5;if(n<0 || !present[n])return 2;present[n]=0;return 0;}
unsigned __cdecl xlt_fs_open(const char *s,unsigned flags,int *h)
{int n=slot(s);(void)flags;++io;if(fault==OPEN)return 5;if(n<0 || !present[n])return 2;*h=n;position=0;return 0;}
unsigned __cdecl xlt_fs_read(int h,void *b,unsigned n,unsigned *count)
{++io;if(fault==READ || (fault==PROBE && position==256))return 30;
 if(n>lengths[h]-position)n=lengths[h]-position;memcpy(b,files[h]+position,n);position+=n;*count=n;return 0;}
unsigned __cdecl xlt_fs_close(int h)
{++io;++closes;return (h==1 && fault==CLOSE_WRITE) || (h==0 && fault==CLOSE_READ)?6:0;}
static unsigned reset(unsigned new_file)
{unsigned i;fault=io=closes=attributes=0;memset(present,0,sizeof(present));memset(lengths,0,sizeof(lengths));
 for(i=0;i<256;++i)files[0][i]=(unsigned char)i;present[0]=!new_file;lengths[0]=256;
 return xlt_document_open("TABLE.XLT",new_file,&doc,&result);}
int main(void)
{
 unsigned f,n,old_io;char bad[13];
 CHECK(!reset(0));CHECK(!xlt_document_dirty(&doc));old_io=io;CHECK(!xlt_document_save(&doc,&result));CHECK(io==old_io);
 for(n=0;n<256;++n)CHECK(!xlt_document_set(&doc,n,255-n));
 CHECK(!xlt_document_save(&doc,&result));CHECK(result.installed && !doc.locked && !xlt_document_dirty(&doc));
 for(n=0;n<256;++n)CHECK(files[0][n]==255-n);
 CHECK(!present[1] && !present[2]);CHECK(!xlt_document_identity(&doc));CHECK(xlt_document_dirty(&doc));
 CHECK(!xlt_document_save(&doc,&result));for(n=0;n<256;++n)CHECK(files[0][n]==n);
 for(f=CREATE;f<=OPEN;++f){
  CHECK(!reset(0));CHECK(!xlt_document_set(&doc,26,255));fault=f;
  CHECK(xlt_document_save(&doc,&result)!=XE_OK);
  if(f==DELETE_BACKUP){CHECK(result.installed && present[0] && present[2] && doc.locked);CHECK(files[0][26]==255 && !xlt_document_dirty(&doc));}
  else {CHECK(!result.installed && xlt_document_dirty(&doc));CHECK(doc.baseline[26]==26 && doc.staged[26]==255);
   if(f==ROLLBACK){CHECK(!present[0] && present[2] && doc.locked);CHECK(files[2][26]==26 && result.rollback_error==5);}
   else {CHECK(present[0] && files[0][26]==26);}
  }
  if(f==CLOSE_WRITE || f==DELETE_STAGE){CHECK(present[1] && doc.locked && result.stage_exists);}
  if(f==CLOSE_WRITE)CHECK(result.close_error==6 && closes==3);
  if(f==SHORT0 || f==SHORT255)CHECK(result.bytes_written==(f==SHORT0?0:255) && !present[1]);
  if(f==INSTALL)CHECK(!result.rollback_error && !present[1] && !present[2] && !doc.locked);
  if(doc.locked){old_io=io;CHECK(xlt_document_save(&doc,&result)==XE_LOCKED);CHECK(io==old_io);CHECK(xlt_document_set(&doc,0,1)==XE_LOCKED);}
 }
 CHECK(!reset(0));CHECK(!xlt_document_set(&doc,0,255));files[0][70]=8;
 CHECK(xlt_document_save(&doc,&result)==XE_CHANGED);CHECK(xlt_document_dirty(&doc) && !present[1]);
 CHECK(!reset(0));CHECK(!xlt_document_set(&doc,0,255));attributes=1;
 CHECK(xlt_document_save(&doc,&result)==XE_IO);CHECK(result.dos_error==5 && files[0][0]==0 && !present[1]);
 for(n=1;n<=2;++n){CHECK(!reset(0));CHECK(!xlt_document_set(&doc,0,255));present[n]=1;files[n][0]=77;
  CHECK(xlt_document_save(&doc,&result)!=XE_OK);CHECK(files[n][0]==77 && files[0][0]==0 && xlt_document_dirty(&doc));}
 CHECK(!reset(1));CHECK(xlt_document_dirty(&doc) && !present[0]);CHECK(!xlt_document_save(&doc,&result));
 CHECK(result.installed && present[0] && !present[1] && !present[2]);
 CHECK(!reset(1));present[0]=1;files[0][0]=77;CHECK(xlt_document_save(&doc,&result)==XE_CHANGED);CHECK(files[0][0]==77 && xlt_document_dirty(&doc));
 CHECK(!reset(0));before=doc;lengths[0]=255;CHECK(xlt_document_open("TABLE.XLT",0,&doc,&result)==XE_LOAD);CHECK(!memcmp(&before,&doc,sizeof(doc)));
 lengths[0]=257;CHECK(xlt_document_open("TABLE.XLT",0,&doc,&result)==XE_LOAD);CHECK(!memcmp(&before,&doc,sizeof(doc)));
 CHECK(!reset(0));before=doc;old_io=io;
 CHECK(xlt_document_open(doc.target,0,&doc,&result)==XE_ARGUMENT);
 CHECK(xlt_document_open("TABLE.XLT",0,&doc,(xlt_document_result *)&doc)==XE_ARGUMENT);
 CHECK(xlt_document_open("TABLE.XLT",0,(xlt_document *)65530U,&result)==XE_ARGUMENT);
 CHECK(xlt_document_save(0,&result)==XE_ARGUMENT);
 CHECK(xlt_document_set(&doc,256,0)==XE_ARGUMENT && xlt_document_set(&doc,0,256)==XE_ARGUMENT);
 CHECK(io==old_io && !memcmp(&before,&doc,sizeof(doc)));
 for(n=0;n<8;++n){static const char *names[]={"CON.XLT","COM1.XLT","LPT9","XLTEDIT.BAK","XLTEDIT.$$$","A/B.XLT","A..XLT","TOOLONG99.XLT"};
  memset(bad,0,13);strncpy(bad,names[n],12);CHECK(xlt_document_open(bad,0,&doc,&result)==XE_ARGUMENT);CHECK(io==old_io);}
 printf("XLT FAULT PASS %u checks\n",checks);return 0;
}
