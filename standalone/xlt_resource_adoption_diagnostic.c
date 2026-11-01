/* Production XLT owner in real DOS; wrappers count actual filesystem calls. */
#include "../src/translation/xlt_live.h"
#include <dos.h>
#include <direct.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned checks,opens,reads,closes,canonicals,bad,fault;
static unsigned char selected[256],active[256],saved[256],offer[256];
static char path[64],exe[64],tail[68],previous[68];
static xlt_dos_result result;
#define CHECK(x) do { ++checks; if(!(x)){printf("FAIL %u\r\n",__LINE__);return 1;} } while(0)
unsigned resource_real_canonical(const char *,char *);
unsigned capture_fs_canonical(const char *p,char *out)
{++canonicals;return resource_real_canonical(p,out);}
unsigned __cdecl xlt_fs_open(const char *p,unsigned flags,int *h)
{++opens;if(flags!=(O_RDONLY|O_NOINHERIT))bad=1;return _dos_open(p,flags,h);}
unsigned __cdecl xlt_fs_read(int h,void *b,unsigned n,unsigned *got)
{++reads;return _dos_read(h,b,n,got);}
unsigned __cdecl xlt_fs_close(int h)
{++closes;if(fault){if(fault==1)_dos_close(h);return 6;}return _dos_close(h);}
static unsigned io_count(void){return opens+reads+closes+canonicals;}
static void setup(void)
{unsigned i;for(i=0;i<256;++i){selected[i]=(unsigned char)(i^0x55);active[i]=0xa5;}memset(path,0,64);strcpy(path,"C:\\NEW.XLT");}
static unsigned expected_reload(void)
{unsigned i;for(i=0;i<256;++i)if(active[i]!=(unsigned char)(255-i))return 0;return 1;}
static unsigned unchanged(void){return !memcmp(active,saved,256);}
int main(int argc,char **argv)
{
 unsigned mode,i,j,before;FILE *f;unsigned report[7];
 const char *invalid[]={"","NEW.XLT","C:NEW.XLT","\\NEW.XLT","c:\\NEW.XLT","C:\\new.XLT","C:/NEW.XLT","C:\\..\\NEW.XLT","C:\\NUL.XLT","C:\\COM1.XLT","C:\\TOOLONGGG.XLT","C:\\NEW.LONG","C:\\A B.XLT","C:\\NEW.XLT\\","C:\\\\NEW.XLT","C:\\A;B.XLT"};
 if(argc!=2)return 2;mode=(unsigned)atoi(argv[1]);if(mode>12)return 2;
 setup();before=io_count();
 if(mode==1 || mode==2){
  path[0]=0;memcpy(saved,active,256);
  CHECK(!xlt_live_resource_adopt(mode==1?0:2,path,selected,active));CHECK(unchanged());CHECK(io_count()==before);
  CHECK(xlt_live_reload(0,0,&result)==XLT_LIVE_STATE);CHECK(xlt_live_editor(_psp,exe,tail)==XLT_LIVE_STATE);
 }else{
  if(mode==8)strcpy(path,"C:\\ABCDEFGH\\IJKLMNOP\\QRSTUVWX\\YZABCDEF\\GHIJKLMN\\ABCDEFG\\NEW.XLT");
  CHECK(!xlt_live_resource_adopt(1,path,selected,active));CHECK(!memcmp(active,selected,256));CHECK(io_count()==before);
  CHECK(!xlt_live_editor(_psp,exe,tail));CHECK(!strcmp(exe,"C:\\XLTEDIT.EXE"));
  CHECK(tail[0]==' ' && tail[1]=='"');CHECK(!memcmp(tail+2,path,strlen(path)));CHECK(tail[strlen(path)+2]=='"' && !tail[strlen(path)+3]);strcpy(previous,tail);
  memcpy(saved,active,256);
  if(mode==3){
   for(i=0;i<sizeof(invalid)/sizeof(*invalid);++i){
    memset(path,0xcc,64);strcpy(path,invalid[i]);before=io_count();
    CHECK(xlt_live_resource_adopt(1,path,selected,active)==XLT_DOS_RESOURCE);CHECK(unchanged());CHECK(io_count()==before);
    CHECK(!xlt_live_editor(_psp,exe,tail));CHECK(!strcmp(tail,previous));
   }
   memset(path,'A',64);CHECK(xlt_live_resource_adopt(1,path,selected,active)==XLT_DOS_RESOURCE);CHECK(unchanged());
   strcpy(path,"C:\\NEW.XLT");CHECK(xlt_live_resource_adopt(0,path,selected,active)==XLT_DOS_RESOURCE);CHECK(unchanged());
   CHECK(xlt_live_resource_adopt(2,path,selected,active)==XLT_DOS_RESOURCE);CHECK(unchanged());
  }else if(mode==4){
   before=io_count();
   CHECK(xlt_live_resource_adopt(3,path,selected,active)==XLT_DOS_ARGUMENT);
   CHECK(xlt_live_resource_adopt(1,0,selected,active)==XLT_DOS_ARGUMENT);
   CHECK(xlt_live_resource_adopt(1,path,0,active)==XLT_DOS_ARGUMENT);
   CHECK(xlt_live_resource_adopt(1,path,selected,0)==XLT_DOS_ARGUMENT);
   CHECK(xlt_live_resource_adopt(1,path,active,active)==XLT_DOS_ARGUMENT);
   CHECK(xlt_live_resource_adopt(1,(char *)selected,selected,active)==XLT_DOS_ARGUMENT);
   CHECK(xlt_live_resource_adopt(1,(char *)active,selected,active)==XLT_DOS_ARGUMENT);
   CHECK(xlt_live_resource_adopt(1,(char *)0xffe0,selected,active)==XLT_DOS_ARGUMENT);
   CHECK(xlt_live_resource_adopt(1,path,(unsigned char *)0xff80,active)==XLT_DOS_ARGUMENT);
   CHECK(xlt_live_resource_adopt(1,path,selected,(unsigned char *)0xff80)==XLT_DOS_ARGUMENT);
   CHECK(unchanged());CHECK(io_count()==before);CHECK(!xlt_live_editor(_psp,exe,tail));CHECK(!strcmp(tail,previous));
  }else if(mode==5 || mode==9){
   CHECK(!xlt_live_reload(0,0,&result));before=io_count();
   CHECK(xlt_live_resource_adopt(1,path,selected,active)==XLT_LIVE_STATE);CHECK(unchanged());CHECK(io_count()==before);
   CHECK(!xlt_live_editor(_psp,exe,tail));CHECK(!strcmp(tail,previous));
   if(mode==9){CHECK(!xlt_live_offer(1,offer));for(i=0;i<256;++i)CHECK(offer[i]==(unsigned char)(255-i));}
   CHECK(!xlt_live_reload(1,active,&result));CHECK(expected_reload());
  }else if(mode==6){
   CHECK(!chdir("\\OTHER"));CHECK(!xlt_live_bind(_psp));CHECK(!xlt_live_stage(1,&result));before=io_count();
   CHECK(xlt_live_resource_adopt(1,path,selected,active)==XLT_LIVE_STATE);CHECK(unchanged());CHECK(io_count()==before);
   CHECK(!xlt_live_commit(1,active));for(i=0;i<256;++i)CHECK(active[i]==(unsigned char)(i^0xaa));
   CHECK(!xlt_live_editor(_psp,exe,tail));CHECK(!strcmp(tail," \"C:\\OTHER\\PCPLUS.XLT\""));
  }else if(mode==11 || mode==12){
   fault=mode==11?1:2;CHECK(xlt_live_reload(0,0,&result)==XLT_DOS_CLOSE);CHECK(result.close_error==6);CHECK(unchanged());before=io_count();
   CHECK(xlt_live_resource_adopt(1,path,selected,active)==XLT_LIVE_STATE);CHECK(unchanged());CHECK(io_count()==before);
   CHECK(!xlt_live_reload(2,0,&result));CHECK(!xlt_live_bind(_psp));before=io_count();
   CHECK(xlt_live_resource_adopt(1,path,selected,active)==XLT_LIVE_STATE);CHECK(unchanged());CHECK(io_count()==before);
   path[0]=0;CHECK(xlt_live_resource_adopt(0,path,selected,active)==XLT_LIVE_STATE);CHECK(unchanged());
   CHECK(!xlt_live_editor(_psp,exe,tail));CHECK(!strcmp(tail,previous));CHECK(closes==1);
  }else if(mode==7){
   for(j=0;j<3;j+=2){
    path[0]=0;before=io_count();CHECK(!xlt_live_resource_adopt(j,path,selected,active));CHECK(unchanged());CHECK(io_count()==before);
    CHECK(xlt_live_reload(0,0,&result)==XLT_LIVE_STATE);CHECK(xlt_live_editor(_psp,exe,tail)==XLT_LIVE_STATE);
    strcpy(path,"C:\\NEW.XLT");CHECK(!xlt_live_resource_adopt(1,path,selected,active));CHECK(!memcmp(active,selected,256));
   }
  }else{
   if(mode==10){memset(path,'Z',64);memset(selected,0x11,256);CHECK(unchanged());CHECK(!xlt_live_editor(_psp,exe,tail));CHECK(!strcmp(tail,previous));}
   CHECK(!chdir("\\OTHER"));CHECK(!xlt_live_reload(0,0,&result));CHECK(!xlt_live_reload(1,active,&result));CHECK(expected_reload());
  }
 }
 CHECK(!bad);CHECK(opens==closes);
 report[0]=mode;report[1]=checks;report[2]=opens;report[3]=reads;report[4]=closes;report[5]=canonicals;report[6]=bad;
 f=fopen("C:\\REPORT.BIN","wb");CHECK(f!=0);CHECK(fwrite(report,2,7,f)==7);CHECK(!fclose(f));
 puts("PASS");return 0;
}
