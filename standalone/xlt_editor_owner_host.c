/* Production document and DOS filesystem adapters on synthetic local media. */
#include "editor_document.h"
#include <dos.h>
#include <stdio.h>
#include <string.h>
static xlt_document doc,before;
static xlt_document_result result;
static unsigned char bytes[257],readback[257];
static unsigned checks;
#define CHECK(x) do { ++checks; if(!(x)){printf("FAIL owner line %u\n",(unsigned)__LINE__);return 1;} } while(0)
static unsigned write_file(const char *name,unsigned n)
{FILE *f=fopen(name,"wb");unsigned ok;if(!f)return 0;ok=fwrite(bytes,1,n,f)==n;return fclose(f)==0 && ok;}
static unsigned exact(const char *name,unsigned n)
{FILE *f=fopen(name,"rb");unsigned got;if(!f)return 0;got=(unsigned)fread(readback,1,257,f);if(fclose(f))return 0;return got==n && !memcmp(bytes,readback,n);}
int main(void)
{
 unsigned i;for(i=0;i<256;++i)bytes[i]=(unsigned char)i;
 CHECK(write_file("TABLE.XLT",256));CHECK(!xlt_document_open("TABLE.XLT",0,&doc,&result));
 for(i=0;i<256;++i)CHECK(!xlt_document_set(&doc,i,255-i));
 CHECK(!xlt_document_save(&doc,&result) && result.installed);
 for(i=0;i<256;++i)bytes[i]=(unsigned char)(255-i);
 CHECK(exact("TABLE.XLT",256));CHECK(!xlt_document_dirty(&doc));
 CHECK(!xlt_document_set(&doc,26,255));bytes[70]=8;CHECK(write_file("TABLE.XLT",256));
 CHECK(xlt_document_save(&doc,&result)==XE_CHANGED && xlt_document_dirty(&doc));CHECK(exact("TABLE.XLT",256));
 CHECK(!xlt_document_open("TABLE.XLT",0,&doc,&result));CHECK(!xlt_document_identity(&doc));
 CHECK(!_dos_setfileattr("TABLE.XLT",_A_RDONLY));CHECK(xlt_document_save(&doc,&result)==XE_IO && xlt_document_dirty(&doc));
 CHECK(!_dos_setfileattr("TABLE.XLT",_A_NORMAL));CHECK(exact("TABLE.XLT",256));
 CHECK(write_file("XLTEDIT.BAK",256));CHECK(xlt_document_save(&doc,&result)==XE_CONFLICT);CHECK(exact("XLTEDIT.BAK",256));CHECK(!remove("XLTEDIT.BAK"));
 CHECK(write_file("XLTEDIT.$$$",256));CHECK(xlt_document_save(&doc,&result)==XE_IO);CHECK(exact("XLTEDIT.$$$",256));CHECK(!remove("XLTEDIT.$$$"));
 CHECK(!xlt_document_save(&doc,&result));for(i=0;i<256;++i)bytes[i]=(unsigned char)i;CHECK(exact("TABLE.XLT",256));
 before=doc;CHECK(write_file("SHORT.XLT",255));CHECK(xlt_document_open("SHORT.XLT",0,&doc,&result)==XE_LOAD);CHECK(!memcmp(&doc,&before,sizeof(doc)));
 CHECK(write_file("LONG.XLT",257));CHECK(xlt_document_open("LONG.XLT",0,&doc,&result)==XE_LOAD);CHECK(!memcmp(&doc,&before,sizeof(doc)));
 CHECK(!xlt_document_open("NEW.XLT",1,&doc,&result));CHECK(xlt_document_dirty(&doc));CHECK(fopen("NEW.XLT","rb")==0);
 CHECK(!xlt_document_save(&doc,&result) && result.installed);CHECK(exact("NEW.XLT",256));
 CHECK(xlt_document_open("NEW.XLT",1,&doc,&result)==XE_CONFLICT);
 puts("XLT OWNER PASS");printf("%u checks\n",checks);return 0;
}
