/* Execute the actual recovered producer while a real source-built DOS child
 * consumes its still-live parent stack descriptor. No terminal/UI publication. */
#include <dos.h>
#include <process.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../src/help/format.h"
extern unsigned __cdecl help_probe_invoke(void);
extern unsigned help_probe_topic,help_probe_ui0,help_probe_ui1,help_probe_ui2,help_probe_ui3,help_probe_ui4,help_probe_ui5;
extern char help_probe_title[];
static unsigned calls,resolutions,failures,checks;
static unsigned long expected_pointer;
static char resolved[66];
int __cdecl help_probe_format(char *out,const char *format,unsigned long pointer)
{
 return sprintf(out,format,pointer);
}
#define CHECK(x) do{++checks;if(!(x)){++failures;printf("FAIL %u\n",__LINE__);}}while(0)
char *__cdecl help_probe_resolve(const char *key)
{
 if(!strcmp(key,"PCPLUS.HLP")){++resolutions;strcpy(resolved,"HELP.HLP");}
 else{CHECK(!strcmp(key,"PCHELP.RTE"));++resolutions;strcpy(resolved,"HLPPROBE.EXE");}
 return resolved;
}
unsigned __cdecl help_probe_execute(const char *exe,const char *tail,unsigned a,unsigned b,unsigned c)
{
 unsigned long pointer=0;
 CHECK(a==0&&b==0&&c==0);CHECK(!strcmp(exe,"HLPPROBE.EXE"));CHECK(!strncmp(tail," PCHELP ",8));
 CHECK(help_pointer_parse(tail+8,&pointer)==HELP_OK);expected_pointer=pointer;++calls;
 return (unsigned)spawnl(P_WAIT,exe,exe,"PCHELP",tail+8,(char *)0);
}
static void record(void)
{
 unsigned char raw[18];unsigned selected;unsigned long pointer;char path[64],title[40];FILE *f;help_context ctx;
 f=fopen("HLPREC.BIN","rb");CHECK(f!=0);if(!f)return;
 CHECK(fread(&pointer,4,1,f)==1);CHECK(fread(raw,1,18,f)==18);CHECK(fread(&selected,2,1,f)==1);
 CHECK(fread(path,1,64,f)==64);CHECK(fread(title,1,40,f)==40);CHECK(fgetc(f)==EOF);CHECK(fclose(f)==0);
 CHECK(pointer==expected_pointer);CHECK(help_context_decode(raw,18,&ctx)==0);
 CHECK(ctx.path_offset==(unsigned)(pointer&65535UL)-96);
 CHECK(ctx.title_offset==(unsigned)help_probe_title);CHECK(ctx.topic==help_probe_topic);
 CHECK(ctx.ui_words[0]==help_probe_ui0&&ctx.ui_words[1]==help_probe_ui1&&ctx.ui_words[2]==help_probe_ui2&&ctx.ui_words[3]==help_probe_ui3&&ctx.ui_words[4]==help_probe_ui4&&ctx.ui_words[5]==help_probe_ui5);
 CHECK(selected==((help_probe_topic&0x8000)||help_probe_topic>=47?0:help_probe_topic));
 CHECK(!strcmp(path,"HELP.HLP")&&!strcmp(title,"LoC // PCPlus Help"));
}
int main(void)
{
 static const unsigned topics[]={0,19,41,45,46,47,0x8000,0xffff};
 unsigned i;setvbuf(stdout,0,_IONBF,0);
 for(i=0;i<sizeof(topics)/sizeof(topics[0]);++i){
  help_probe_topic=topics[i];help_probe_ui0=i;help_probe_ui1=7+i;help_probe_ui2=15+i;
  help_probe_ui3=0x7000+i;help_probe_ui4=0xffff-i;help_probe_ui5=i*17;
  CHECK(help_probe_invoke()==0);record();
 }
 CHECK(calls==8&&resolutions==16);CHECK(remove("HLPREC.BIN")==0);
 CHECK(spawnl(P_WAIT,"HLPPROBE.EXE","HLPPROBE.EXE","WRONG","0",(char *)0)==3);
 CHECK(spawnl(P_WAIT,"HLPPROBE.EXE","HLPPROBE.EXE","PCHELP","65536",(char *)0)==5);
 CHECK(spawnl(P_WAIT,"HLPPROBE.EXE","HLPPROBE.EXE","PCHELP","4294967296",(char *)0)==4);
 {FILE *f=fopen("HLPREC.BIN","rb");CHECK(!f);if(f)fclose(f);}
 printf("CONTEXT checks=%u errors=%u children=8 invalid=3\n",checks,failures);
 return failures?1:0;
}
