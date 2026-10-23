#include "../src/help/document.h"
#include <stdio.h>
#include <string.h>
static unsigned checks,failures,calls,largest,fail_read,short_read;
static unsigned char prefix[117];
static help_document document;static help_cursor cursor;static help_find search;
static void check(unsigned yes,unsigned line){++checks;if(!yes){++failures;printf("FAIL %u\n",line);}}
#define CHECK(x) check((x)!=0,__LINE__)
static void putword(unsigned char *p,unsigned x){p[0]=(unsigned char)x;p[1]=(unsigned char)(x>>8);}
static void putlong(unsigned char *p,unsigned long x){putword(p,(unsigned)x);putword(p+2,(unsigned)(x>>16));}
static unsigned HELP_DOC_CODE HELP_DOC_CALL read_at(void *cookie,unsigned long offset,unsigned char *out,unsigned bytes,unsigned *got)
{
 FILE *file=(FILE *)cookie;++calls;if(bytes>largest)largest=bytes;
 if(fail_read)return 1;
 if(fseek(file,(long)offset,SEEK_SET))return 1;
 *got=(unsigned)fread(out,1,short_read&&bytes?bytes-1:bytes,file);return ferror(file)!=0;
}
static unsigned admit(FILE *file,unsigned long bytes)
{
 unsigned status=help_document_begin(&document,read_at,file,bytes),before;
 while(status==HELP_DOC_PENDING){before=calls;status=help_document_step(&document);CHECK(calls-before<=1);}
 return status;
}
static unsigned line(void)
{
 unsigned status,before;
 do{before=calls;status=help_cursor_step(&cursor);CHECK(calls-before<=1);}while(status==HELP_DOC_PENDING);
 return status;
}
static unsigned find(const char *query,unsigned topic,unsigned long from)
{
 unsigned status,before,budget=200;
 status=help_find_begin(&search,&document,query,topic,from);
 while(status==HELP_DOC_PENDING&&budget--){before=calls;status=help_find_step(&search);CHECK(calls-before<=2);}
 CHECK(budget!=0);return status;
}
int main(void)
{
 FILE *file;unsigned i,status,before;unsigned long bytes;
 memset(prefix,0,sizeof(prefix));prefix[0]=3;putword(prefix+1,8);
 memcpy(prefix+3,"FIRST",5);putword(prefix+35,5);putlong(prefix+37,117);
 memcpy(prefix+41,"Sparse navigation",17);putword(prefix+73,2);putlong(prefix+75,65537UL);
 memset(prefix+79,'Z',32);putword(prefix+111,1);putlong(prefix+113,65650UL);
 file=fopen("DOCUMENT.HLP","wb");CHECK(file!=0);if(!file)return 2;
 CHECK(fwrite(prefix,117,1,file)==1);fputs("First needle\n\n",file);
 for(i=0;i<70;++i)fputc('X',file);
 fputs("NEEDLE\r\n",file);fputs("\260\261\262 CP437\ntail needle\n",file);
 CHECK(fseek(file,65537L,SEEK_SET)==0);fputs("next needle\nmore\n",file);
 CHECK(fseek(file,65650L,SEEK_SET)==0);fputs("last\n",file);CHECK(fclose(file)==0);
 file=fopen("DOCUMENT.HLP","rb");CHECK(file!=0);if(!file)return 3;
 CHECK(fseek(file,0,SEEK_END)==0);bytes=(unsigned long)ftell(file);CHECK(bytes==65655UL);
 CHECK(admit(file,bytes)==HELP_DOC_OK&&document.header.topics==3&&document.header.lines==8);
 before=calls;CHECK(help_cursor_begin(&cursor,&document,0)==0&&calls-before<=2);
 CHECK(line()==HELP_DOC_LINE&&!strcmp(cursor.line,"First needle"));
 CHECK(line()==HELP_DOC_LINE&&!cursor.line[0]);
 CHECK(line()==HELP_DOC_LINE&&strlen(cursor.line)==76&&!strcmp(cursor.line+70,"NEEDLE"));
 CHECK(line()==HELP_DOC_LINE&&(unsigned char)cursor.line[0]==0xb0&&(unsigned char)cursor.line[2]==0xb2);
 CHECK(line()==HELP_DOC_LINE&&!strcmp(cursor.line,"tail needle"));CHECK(line()==HELP_DOC_END);
 CHECK(help_cursor_begin(&cursor,&document,1)==0&&cursor.record.offset==65537UL);
 CHECK(line()==HELP_DOC_LINE&&!strcmp(cursor.line,"next needle"));CHECK(line()==HELP_DOC_LINE&&!strcmp(cursor.line,"more"));CHECK(line()==HELP_DOC_END);
 CHECK(find("needle",0,0)==HELP_DOC_FOUND&&search.match_topic==0&&search.match_line==1);
 CHECK(find("NeEdLe",0,2)==HELP_DOC_FOUND&&search.match_topic==0&&search.match_line==3);
 CHECK(find("needle",0,4)==HELP_DOC_FOUND&&search.match_topic==0&&search.match_line==5);
 CHECK(find("needle",0,6)==HELP_DOC_FOUND&&search.match_topic==1&&search.match_line==1);
 CHECK(find("needle",1,2)==HELP_DOC_FOUND&&search.match_topic==0&&search.match_line==1);
 CHECK(find("sparse",0,0)==HELP_DOC_FOUND&&search.match_topic==1&&search.match_line==0);
 CHECK(find("more",1,2)==HELP_DOC_FOUND&&search.match_topic==1&&search.match_line==2);
 CHECK(find("missing text",2,0)==HELP_DOC_END&&!search.active);
 CHECK(find("more",1,65536UL)==HELP_DOC_FOUND&&search.match_topic==1&&search.match_line==2);
 CHECK(help_find_begin(&search,&document,"needle",0,0)==HELP_DOC_PENDING);help_find_cancel(&search);
 CHECK(!search.active&&help_find_step(&search)==HELP_DOC_ARGUMENT);
 CHECK(help_find_begin(&search,&document,"",0,0)==HELP_DOC_ARGUMENT);
 CHECK(help_find_begin(&search,&document,"needle",0,65537UL)==HELP_DOC_ARGUMENT);
 CHECK(help_cursor_begin(&cursor,&document,3)==HELP_DOC_ARGUMENT);
 fail_read=1;CHECK(help_cursor_begin(&cursor,&document,0)==HELP_DOC_IO);fail_read=0;
 short_read=1;CHECK(help_cursor_begin(&cursor,&document,0)==HELP_DOC_IO);short_read=0;
 CHECK(admit(file,116)==HELP_DOC_FORMAT);
 CHECK(help_document_begin(&document,read_at,file,0x80000000UL)==HELP_DOC_RANGE);
 CHECK(admit(file,bytes)==HELP_DOC_OK);CHECK(largest<=80);CHECK(fclose(file)==0);
 /* Authored malformed body: missing LF, NUL and overlong line reject while
  * the decoder stays bounded; no original help text enters the test. */
 for(i=0;i<3;++i){
  unsigned j;file=fopen("BAD.HLP","wb");CHECK(file!=0);if(!file)return 4;
  prefix[0]=1;putword(prefix+1,1);putword(prefix+35,1);putlong(prefix+37,41);
  fwrite(prefix,41,1,file);
  if(i==0)fputs("unterminated",file);
  else if(i==1){fputc(0,file);fputc(10,file);}
  else{for(j=0;j<82;++j)fputc('x',file);fputc(10,file);}
  fclose(file);file=fopen("BAD.HLP","rb");CHECK(file!=0);if(!file)return 5;
  fseek(file,0,SEEK_END);bytes=(unsigned long)ftell(file);
  CHECK(admit(file,bytes)==0);CHECK(help_cursor_begin(&cursor,&document,0)==0);
  status=line();CHECK(status==(i==2?HELP_DOC_RANGE:HELP_DOC_FORMAT));fclose(file);
 }
 printf("HELPDOC checks=%u failures=%u max_read=%u\n",checks,failures,largest);return failures?1:0;
}
