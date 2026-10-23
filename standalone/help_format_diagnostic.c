#include "../src/help/format.h"
#include <stdio.h>
#include <string.h>
static unsigned checks,failures;
static void check(unsigned yes,unsigned line){++checks;if(!yes){++failures;printf("FAIL %u\n",line);}}
#define CHECK(x) check((x)!=0,__LINE__)
static void putword(unsigned char *p,unsigned x){p[0]=(unsigned char)x;p[1]=(unsigned char)(x>>8);}
static unsigned char index_bytes[79];
int main(void)
{
 unsigned char context[18],backup[79],text[8];unsigned i,status;
 unsigned long pointer=123;help_context c;help_header h;help_record r;FILE *file;
 CHECK(help_pointer_parse("305419896",&pointer)==0&&pointer==0x12345678UL);
 CHECK(help_pointer_parse("4294967278",&pointer)==0&&pointer==0xffffffeeUL);
 CHECK(help_pointer_parse("4294967295",&pointer)==HELP_RANGE&&pointer==0xffffffeeUL);
 CHECK(help_pointer_parse("4294967296",&pointer)==HELP_RANGE);
 CHECK(help_pointer_parse("00000000000",&pointer)==HELP_FORMAT);
 CHECK(help_pointer_parse("65536",&pointer)==0&&pointer==65536UL);
 CHECK(help_pointer_parse("65535",&pointer)==HELP_RANGE);
 CHECK(help_pointer_parse("",&pointer)==HELP_RANGE);
 CHECK(help_pointer_parse("-1",&pointer)==HELP_FORMAT);
 CHECK(help_pointer_parse(" 65536",&pointer)==HELP_FORMAT);
 CHECK(help_pointer_parse("65536x",&pointer)==HELP_FORMAT);
 CHECK(help_pointer_parse(0,&pointer)==HELP_ARGUMENT);
 CHECK(help_pointer_parse("65536",0)==HELP_ARGUMENT);
 for(i=0;i<9;++i)putword(context+i*2,i+1);
 CHECK(help_context_decode(context,18,&c)==0&&c.path_offset==1&&c.title_offset==2&&c.topic==3);
 for(i=0;i<6;++i)CHECK(c.ui_words[i]==i+4);
 CHECK(help_context_decode(context,17,&c)==HELP_FORMAT);
 putword(context+4,65535U);CHECK(help_context_decode(context,18,&c)==0&&help_topic_select(c.topic,47)==0);
 putword(context,0);CHECK(help_context_decode(context,18,&c)==HELP_FORMAT);
 CHECK(help_topic_select(41,47)==41);CHECK(help_topic_select(47,47)==0);CHECK(help_topic_select(32768U,65535U)==0);
 memset(index_bytes,0,sizeof(index_bytes));index_bytes[0]=2;putword(index_bytes+1,3);
 memcpy(index_bytes+3,"Terminal",8);putword(index_bytes+35,2);putword(index_bytes+37,79);
 memcpy(index_bytes+41,"Files",5);putword(index_bytes+73,1);putword(index_bytes+75,1);putword(index_bytes+77,1);
 CHECK(help_header_decode(index_bytes,3,65545UL,&h)==0&&h.topics==2&&h.lines==3&&h.text_start==79);
 CHECK(help_index_validate(index_bytes,79,65545UL)==0);
 CHECK(help_record_decode(index_bytes+41,38,&h,65545UL,&r)==0&&r.offset==65537UL&&r.lines==1&&!strcmp(r.title,"Files"));
 CHECK(help_header_decode(index_bytes,2,65545UL,&h)==HELP_FORMAT);
 CHECK(help_header_decode(index_bytes,3,78,&h)==HELP_FORMAT);
 CHECK(help_index_validate(index_bytes,78,65545UL)==HELP_FORMAT);
 memcpy(backup,index_bytes,79);putword(index_bytes+1,4);CHECK(help_index_validate(index_bytes,79,65545UL)==HELP_FORMAT);memcpy(index_bytes,backup,79);
 putword(index_bytes+37,78);CHECK(help_index_validate(index_bytes,79,65545UL)==HELP_RANGE);memcpy(index_bytes,backup,79);
 putword(index_bytes+75,80);putword(index_bytes+77,0);CHECK(help_index_validate(index_bytes,79,65545UL)==HELP_FORMAT);memcpy(index_bytes,backup,79);
 putword(index_bytes+75,65535U);putword(index_bytes+77,65535U);CHECK(help_index_validate(index_bytes,79,65545UL)==HELP_RANGE);memcpy(index_bytes,backup,79);
 memset(index_bytes+41,'X',32);CHECK(help_record_decode(index_bytes+41,38,&h,65545UL,&r)==0&&r.title[31]=='X'&&!r.title[32]);memcpy(index_bytes,backup,79);
 file=fopen("HELPTEST.HLP","wb");CHECK(file!=0);if(!file)return 2;
 CHECK(fwrite(index_bytes,79,1,file)==1);CHECK(fputs("ONE\nTWO\n",file)>=0);
 CHECK(fseek(file,65537L,SEEK_SET)==0);CHECK(fputs("THREE\n",file)>=0);CHECK(fclose(file)==0);
 file=fopen("HELPTEST.HLP","rb");CHECK(file!=0);if(!file)return 3;
 CHECK(fread(index_bytes,79,1,file)==1);CHECK(fseek(file,0,SEEK_END)==0);
 CHECK(ftell(file)==65543L);CHECK(help_index_validate(index_bytes,79,(unsigned long)ftell(file))==0);
 status=help_record_decode(index_bytes+41,38,&h,65543UL,&r);CHECK(status==0);
 CHECK(fseek(file,(long)r.offset,SEEK_SET)==0);memset(text,0,8);CHECK(fread(text,1,6,file)==6&&!memcmp(text,"THREE\n",6));CHECK(fclose(file)==0);
 printf("HELPFMT checks=%u failures=%u\n",checks,failures);return failures?1:0;
}
