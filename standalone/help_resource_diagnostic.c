#include "../src/help/resource.h"
#include <dos.h>
#include <stdio.h>
#include <string.h>
extern unsigned _psp;
static unsigned checks,failures;
#ifdef ASPECT_DEFER_HELP_RESOURCE
extern unsigned help_resource_heap_fail,help_resource_heap_live,help_resource_heap_bytes;
extern unsigned help_view_fail_allocate,help_view_fail_release;
#endif
static unsigned char original[4000],jft[20];
static void check(unsigned yes,unsigned line){++checks;if(!yes){++failures;printf("FAIL %u\n",line);}}
#define CHECK(x) check((x)!=0,__LINE__)
static unsigned contains(unsigned row,const char *text)
{
 unsigned i,j,n=(unsigned)strlen(text);unsigned char __far *screen=MK_FP(0xb800,row*160);
 for(i=0;i+n<=80;++i){for(j=0;j<n&&screen[(i+j)*2]==(unsigned char)text[j];++j){}if(j==n)return 1;}
 return 0;
}
static unsigned pump(unsigned row,const char *text)
{
 unsigned budget=10000;
 while(budget--){if(contains(row,text))return 1;if(help_resource_step())return 0;}
 return 0;
}
static unsigned restored(void)
{unsigned i;for(i=0;i<4000;++i)if(original[i]!=((unsigned char __far *)MK_FP(0xb800,0))[i])return 0;return 1;}
static unsigned handles(void)
{unsigned i;for(i=0;i<20;++i)if(jft[i]!=((unsigned char __far *)MK_FP(_psp,0x18))[i])return 0;return 1;}
static unsigned close_all(void)
{
 if(help_resource_close()||help_view_close())return 1;
#ifdef ASPECT_DEFER_HELP_RESOURCE
 if(help_resource_release()||help_resource_heap_live)return 1;
#endif
 return 0;
}
int main(void)
{
 unsigned i;FILE *f;unsigned char header[41];
 for(i=0;i<4000;++i)original[i]=((unsigned char __far *)MK_FP(0xb800,0))[i]=(unsigned char)(i*13U+7U);
 for(i=0;i<20;++i)jft[i]=((unsigned char __far *)MK_FP(_psp,0x18))[i];
#ifdef ASPECT_EARLY_HELP_MODEL
 help_resource_heap_fail=1;
 CHECK(help_resource_prepare()==HELP_VIEW_MEMORY&&help_resource_heap_live==0);
 help_resource_heap_fail=0;
 CHECK(help_resource_prepare()==0&&help_resource_heap_live==1&&!help_resource_active()&&!help_view_active());
 CHECK(help_resource_prepare()==0&&help_resource_heap_live==1&&handles()&&restored());
 CHECK(help_resource_release()==0&&help_resource_heap_live==0);
 CHECK(help_resource_prepare()==0&&help_resource_open("LOCHELP.HLP")==0&&help_resource_heap_live==1);
 CHECK(help_resource_prepare()==HELP_VIEW_STATE&&help_resource_heap_live==1);
 CHECK(close_all()==0&&restored()&&handles());
#endif
#ifdef ASPECT_DEFER_HELP_RESOURCE
 CHECK(help_resource_heap_live==0&&help_resource_step()==HELP_VIEW_STATE&&help_resource_key(27)==HELP_VIEW_STATE);
 help_resource_heap_fail=1;
 CHECK(help_resource_open("LOCHELP.HLP")==HELP_VIEW_MEMORY&&!help_resource_active()&&!help_view_active()&&handles()&&restored());
 CHECK(help_resource_heap_live==0);help_resource_heap_fail=0;
 help_view_fail_allocate=1;
 CHECK(help_resource_open("LOCHELP.HLP")==HELP_VIEW_MEMORY&&!help_resource_active()&&!help_view_active()&&handles()&&restored());
 CHECK(help_resource_heap_live==0);help_view_fail_allocate=0;
 CHECK(help_resource_open("LOCHELP.HLP")==0&&pump(3,"EXTERNAL PROGRAM / ERROR NOTICE"));
 CHECK(help_resource_heap_live==1&&help_resource_heap_bytes>=3000);
 CHECK(help_resource_close()==0&&!help_resource_active()&&help_resource_heap_live==1);
 CHECK(help_resource_release()==HELP_VIEW_STATE&&help_resource_heap_live==1);
 help_view_fail_release=1;CHECK(close_all()!=0&&help_view_active()&&help_resource_heap_live==1);
 help_view_fail_release=0;CHECK(close_all()==0&&restored()&&handles());
 for(i=0;i<8;++i){
  CHECK(help_resource_open("LOCHELP.HLP")==0&&help_resource_heap_live==1);
  CHECK(pump(3,"EXTERNAL PROGRAM / ERROR NOTICE"));CHECK(close_all()==0&&restored()&&handles());
 }
#endif
 CHECK(help_resource_open("ABSENT.HLP")==HELP_RESOURCE_MISSING&&!help_resource_active()&&!help_view_active()&&handles()&&restored());
 CHECK(help_resource_open("LOCHELP.HLP")==0&&help_resource_active()&&help_view_active());
 CHECK(pump(3,"EXTERNAL PROGRAM / ERROR NOTICE"));CHECK(contains(5,"command could not run"));
 CHECK(help_resource_key(0x5100)==0);CHECK(pump(5,"batch command"));
 CHECK(help_resource_key(0x4700)==0);CHECK(pump(5,"command could not run"));
 CHECK(help_resource_key(0x4d00)==0);CHECK(pump(3,"SERIAL SESSION / LOCAL INPUT"));
 CHECK(help_resource_key('/')==0&&contains(23,"Find:"));
 CHECK(help_resource_key('x')==0&&help_resource_key(8)==0&&help_resource_key(27)==0);
 CHECK(help_resource_key('/')==0);
 for(i=0;i<6;++i)CHECK(help_resource_key("xmodem"[i])==0);
 CHECK(help_resource_key(13)==0);CHECK(pump(3,"Receive files"));CHECK(pump(5,"XMODEM"));
 CHECK(help_resource_key(0x3d00)==0);CHECK(pump(5,"download at the BBS"));
 CHECK(help_resource_key(0x3d00)==0);CHECK(pump(3,"Send files"));
 CHECK(help_resource_key('/')==0);
 for(i=0;i<7;++i)help_resource_key("zzzzzzz"[i]);
 CHECK(help_resource_key(13)==0);CHECK(pump(23,"No matching text"));
 CHECK(help_resource_key('/')==0&&help_resource_key('m')==0&&help_resource_key(13)==0);
 CHECK(help_resource_key(27)==0);CHECK(!contains(23,"Searching"));
 CHECK(help_resource_key(27)==HELP_RESOURCE_CLOSE);CHECK(close_all()==0&&!help_resource_active()&&!help_view_active()&&handles()&&restored());
 CHECK(help_resource_open("LOCHELP.HLP")==0&&help_resource_key(27)==HELP_RESOURCE_CLOSE);
 CHECK(close_all()==0&&handles()&&restored());
 f=fopen("BADHELP.HLP","wb");CHECK(f!=0);if(!f)return 2;fputs("bad",f);CHECK(fclose(f)==0);
 CHECK(help_resource_open("BADHELP.HLP")==0&&help_resource_active());CHECK(pump(3,"HELP RESOURCE ERROR"));
 CHECK(help_resource_key(13)==HELP_RESOURCE_CLOSE);CHECK(close_all()==0&&handles()&&restored());
 memset(header,0,sizeof(header));header[0]=header[1]=header[35]=1;header[37]=41;
 memcpy(header+3,"CP437 LONG LINE",15);
 f=fopen("LONG.HLP","wb");CHECK(f!=0);if(!f)return 3;
 CHECK(fwrite(header,41,1,f)==1);
 for(i=0;i<74;++i)fputc('X',f);
 fputs("\260\261TAIL\n",f);CHECK(fclose(f)==0);
 CHECK(help_resource_open("LONG.HLP")==0);CHECK(pump(3,"CP437 LONG LINE"));
 CHECK(contains(6,"\260\261TAIL"));CHECK(close_all()==0&&handles()&&restored());
 printf("HELPRESOURCE checks=%u failures=%u\n",checks,failures);return failures?1:0;
}
