/* Actual DOS file ownership and synthetic bounded PSP trailers. */
#include "editor_document.h"
#include "resource_path.h"
#include <dos.h>
#include <direct.h>
#include <stdio.h>
#include <string.h>
static xlt_document doc,before;
static xlt_document_result result;
static unsigned checks,psp,envseg;
static unsigned char __far *env;
static char guarded[66],saved[66],path[80],stage[80],backup[80];
#define CHECK(x) do {++checks;if(!(x)){printf("FAIL paths line %u\n",(unsigned)__LINE__);return 1;}} while(0)
static unsigned put(const char *name,unsigned byte)
{FILE *f=fopen(name,"wb");unsigned i;if(!f)return 0;for(i=0;i<256;++i)if(fputc(byte,f)==EOF)return 0;return fclose(f)==0;}
static unsigned exact(const char *name,unsigned byte)
{FILE *f=fopen(name,"rb");unsigned i;if(!f)return 0;for(i=0;i<256;++i)if(fgetc(f)!=(int)byte)return 0;i=fgetc(f)==EOF;return fclose(f)==0 && i;}
static void environment(const char *program,unsigned count)
{unsigned i,at=0;const char text[]="PCPLUS=C:\\WRONG\0";
 for(i=0;i<512;++i)env[i]=0;
 for(i=0;i<sizeof(text);++i)env[at++]=(unsigned char)text[i];
 env[at++]=(unsigned char)count;env[at++]=(unsigned char)(count>>8);
 for(i=0;program[i];++i)env[at++]=(unsigned char)program[i];
 memset(guarded,0xa5,sizeof(guarded));memcpy(saved,guarded,sizeof(saved));}
int main(void)
{
 unsigned i,n;char drive;
 CHECK(!_dos_allocmem(16,&psp));CHECK(!_dos_allocmem(32,&envseg));env=(unsigned char __far *)MK_FP(envseg,0);
 *(unsigned __far *)MK_FP(psp,0x2c)=envseg;
 environment("C:\\APP\\TERMINAL.EXE",1);
 CHECK(!resource_program_path(psp,"XLTEDIT.EXE",guarded+1));
 CHECK(!strcmp(guarded+1,"C:\\APP\\XLTEDIT.EXE") && (unsigned char)guarded[0]==0xa5 && (unsigned char)guarded[65]==0xa5);
 environment("C:\\MY DIR\\TERMINAL.EXE",1);CHECK(!resource_program_path(psp,"XLTEDIT.EXE",guarded+1));CHECK(!strcmp(guarded+1,"C:\\MY DIR\\XLTEDIT.EXE"));
 for(i=0;i<7;++i){static const char *bad[]={"TERMINAL.EXE","C:TERMINAL.EXE","C:\\","1:\\APP\\T.EXE","C:/APP/T.EXE","C:\\A?\\T.EXE","C:\\A\"\\T.EXE"};
  environment(bad[i],1);CHECK(resource_program_path(psp,"XLTEDIT.EXE",guarded+1)!=0);CHECK(!memcmp(guarded,saved,sizeof(saved)));}
 for(i=0;i<3;++i){environment("C:\\APP\\TERMINAL.EXE",i==0?0:i==1?2:256);CHECK(resource_program_path(psp,"XLTEDIT.EXE",guarded+1)!=0);CHECK(!memcmp(guarded,saved,sizeof(saved)));}
 environment("C:\\APP\\TERMINAL.EXE",1);for(i=0;i<512;++i)env[i]='A';CHECK(resource_program_path(psp,"XLTEDIT.EXE",guarded+1)==RESOURCE_PATH_ENVIRONMENT);CHECK(!memcmp(guarded,saved,sizeof(saved)));
 environment("C:\\APP\\TERMINAL.EXE",1);CHECK(resource_program_path(psp,"../BAD",guarded+1)==RESOURCE_PATH_ARGUMENT);CHECK(resource_program_path(psp,"XLTEDIT.EXE",(char *)65500U)==RESOURCE_PATH_ARGUMENT);
 CHECK(!_dos_freemem(envseg));CHECK(!_dos_freemem(psp));
 CHECK(!_mkdir("CFG"));CHECK(put("TABLE.XLT",42));CHECK(put("XLTEDIT.BAK",43));CHECK(put("XLTEDIT.$$$",44));CHECK(put("CFG\\TABLE.XLT",45));
 drive=(char)('A'+_getdrive()-1);strcpy(path,"C:\\CFG\\TABLE.XLT");path[0]=drive;
 CHECK(!xlt_document_open(path,0,&doc,&result));CHECK(!xlt_document_set(&doc,70,255));CHECK(!xlt_document_save(&doc,&result) && result.installed);
 CHECK(exact("TABLE.XLT",42) && exact("XLTEDIT.BAK",43) && exact("XLTEDIT.$$$",44));
 CHECK(put("CFG\\TABLE.XLT",46)); /* independent full-file overwrite */
 CHECK(xlt_document_save(&doc,&result)==0); /* no local changes: no overwrite */
 CHECK(!xlt_document_open(path,0,&doc,&result));CHECK(!xlt_document_identity(&doc));CHECK(put("CFG\\XLTEDIT.BAK",47));
 CHECK(xlt_document_save(&doc,&result)==XE_CONFLICT && exact("CFG\\XLTEDIT.BAK",47));CHECK(!remove("CFG\\XLTEDIT.BAK"));
 CHECK(!xlt_document_save(&doc,&result));CHECK(!xlt_document_dirty(&doc));
 CHECK(put("CFG\\T\x82" "ST.XLT",48));strcpy(path,"C:\\CFG\\T\x82" "ST.XLT");path[0]=drive;
 CHECK(!xlt_document_open(path,0,&doc,&result));CHECK(!xlt_document_set(&doc,70,49));CHECK(!xlt_document_save(&doc,&result) && result.installed);
 before=doc;
 {static const char *bad[]={"C:\\CON.XLT","C:\\CFG\\NUL","C:\\CFG\\COM1.XLT","C:\\CFG\\XLTEDIT.BAK","C:\\CFG\\XLTEDIT.$$$","C:\\..\\TABLE.XLT","C:TABLE.XLT","C:\\\\TABLE.XLT","C:\\CON .XLT","C:\\CFG\\"};
 for(i=0;i<10;++i){CHECK(xlt_document_open(bad[i],0,&doc,&result)==XE_ARGUMENT);CHECK(!memcmp(&before,&doc,sizeof(doc)));}}
 /* The shortest target leaf can need a longer, still bounded recovery path. */
 path[0]=drive;strcpy(path+1,":\\");
 for(i=0;i<6;++i){strcat(path,"ABCDEFGH");CHECK(!_mkdir(path));strcat(path,"\\");}
 strcat(path,"ABCD");CHECK(!_mkdir(path));strcat(path,"\\");n=(unsigned)strlen(path);CHECK(n==62);
 strcpy(stage,path);strcpy(backup,path);strcat(stage,"XLTEDIT.$$$");strcat(backup,"XLTEDIT.BAK");strcat(path,"A");CHECK(strlen(path)==63);
 CHECK(!xlt_document_open(path,1,&doc,&result));CHECK(!xlt_document_save(&doc,&result) && result.installed);CHECK(!xlt_document_dirty(&doc));
 CHECK(fopen(stage,"rb")==0 && fopen(backup,"rb")==0);
 printf("XLT PATHS PASS %u checks\n",checks);return 0;
}
