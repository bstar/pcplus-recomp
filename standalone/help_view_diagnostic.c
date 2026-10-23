#include "../src/help/view.h"
#include "../src/help/notice_content.h"
#include <dos.h>
#include <stdio.h>
#include <string.h>
static unsigned checks,failures;
static unsigned char saved[4000],current[4000];
static help_page invalid;
static char long_title[76];
extern unsigned __cdecl help_view_bad_context(unsigned);
static void check(unsigned yes,unsigned line){++checks;if(!yes){++failures;printf("FAIL %u\n",line);}}
#define CHECK(x) check((x)!=0,__LINE__)
static void capture(unsigned char *p)
{unsigned i;for(i=0;i<4000;++i)p[i]=((unsigned char __far *)MK_FP(0xb800,0))[i];}
static void pattern(void)
{unsigned i;for(i=0;i<4000;++i)((unsigned char __far *)MK_FP(0xb800,0))[i]=(unsigned char)(i*17U+3U);capture(saved);}
static unsigned same(void){capture(current);return !memcmp(current,saved,4000);}
static void cursor(unsigned position,unsigned shape)
{union REGS a,b;a.h.ah=1;a.x.cx=shape;int86(0x10,&a,&b);a.h.ah=2;a.x.dx=position;a.x.bx=0;int86(0x10,&a,&b);}
int main(void)
{
 unsigned i;FILE *f;
 pattern();cursor(0x070b,0x0607);
 CHECK(help_view_close()==0&&!help_view_active());
 CHECK(help_view_bad_context(0)==HELP_VIEW_STATE&&same());
 CHECK(help_view_bad_context(1)==HELP_VIEW_STATE&&same());
 CHECK(help_view_open(0,2,0)==HELP_VIEW_ARGUMENT&&same());
 CHECK(help_view_open(notice_help_pages,0,0)==HELP_VIEW_ARGUMENT&&same());
 CHECK(help_view_open(notice_help_pages,2,2)==HELP_VIEW_ARGUMENT&&same());
 memset(long_title,'A',75);long_title[75]=0;invalid.title=long_title;
 CHECK(help_view_open(&invalid,1,0)==HELP_VIEW_ARGUMENT&&same());
 help_view_fail_allocate=1;CHECK(help_view_open(notice_help_pages,2,0)==HELP_VIEW_MEMORY&&!help_view_active()&&same());help_view_fail_allocate=0;
 CHECK(help_view_open(notice_help_pages,2,0)==0&&help_view_active()==2);
 CHECK(help_view_bad_context(0)==HELP_VIEW_STATE&&help_view_active()==2);
 CHECK(help_view_bad_context(1)==HELP_VIEW_STATE&&help_view_active()==2);
 CHECK(((unsigned char __far *)MK_FP(0xb800,166))[0]=='P');
 CHECK(help_view_open(notice_help_pages,2,0)==HELP_VIEW_STATE);
 CHECK(help_view_topic()==0&&help_view_key(0x4d00)==0&&help_view_topic()==1);
 CHECK(help_view_key(0x4700)==0&&help_view_topic()==0);
 CHECK(help_view_key(0x4f00)==0&&help_view_topic()==1);
 CHECK(help_view_key(0x4900)==0&&help_view_topic()==0);
 CHECK(help_view_key(0x5100)==0&&help_view_topic()==1);
 CHECK(help_view_key('t')==0&&help_view_topic()==0);
 CHECK(help_view_key('x')==0&&help_view_active()==2);
 f=fopen("HELP.BIN","wb");CHECK(f!=0);if(!f)return 2;capture(current);CHECK(fwrite(current,4000,1,f)==1&&fclose(f)==0);
 CHECK(help_view_key(27)==0&&!help_view_active()&&same());
 CHECK(*(unsigned __far *)MK_FP(0x40,0x50)==0x070b&&*(unsigned __far *)MK_FP(0x40,0x60)==0x0607);
 CHECK(help_view_open(notice_help_pages,2,1)==0);help_view_damage_guard();capture(current);
 CHECK(help_view_close()==HELP_VIEW_GUARD&&help_view_active()==3);
 for(i=0;i<4000;++i)if(((unsigned char __far *)MK_FP(0xb800,0))[i]!=current[i])break;
 CHECK(i==4000);help_view_damage_guard();CHECK(help_view_close()==0&&same());
 CHECK(help_view_open(notice_help_pages,2,0)==0);
 *(unsigned __far *)MK_FP(0x40,0x4a)=79;
 CHECK(help_view_close()==HELP_VIEW_STATE&&help_view_active()==3);
 *(unsigned __far *)MK_FP(0x40,0x4a)=80;CHECK(help_view_close()==0&&same());
 CHECK(help_view_open(notice_help_pages,2,0)==0);help_view_fail_release=1;
 CHECK(help_view_close()==HELP_VIEW_STATE&&help_view_active()==3&&same());
 ((unsigned char __far *)MK_FP(0xb800,0))[0]=0x5a;help_view_fail_release=0;
 CHECK(help_view_close()==0&&!help_view_active()&&((unsigned char __far *)MK_FP(0xb800,0))[0]==0x5a);
 CHECK(help_view_open(notice_help_pages,2,0)==0&&help_view_key(13)==0&&!help_view_active());
 CHECK(help_view_key(0)==HELP_VIEW_STATE);
 CHECK(help_view_open(notice_help_pages,2,0)==0);
 ((unsigned char __far *)MK_FP(0xb800,0))[0]=0x6b;
 CHECK(help_view_discard()==0&&!help_view_active()&&((unsigned char __far *)MK_FP(0xb800,0))[0]==0x6b);
 CHECK(help_view_open(notice_help_pages,2,0)==0);help_view_fail_release=1;
 CHECK(help_view_discard()==HELP_VIEW_STATE&&help_view_active()==3);
 ((unsigned char __far *)MK_FP(0xb800,0))[0]=0x6c;help_view_fail_release=0;
 CHECK(help_view_close()==0&&!help_view_active()&&((unsigned char __far *)MK_FP(0xb800,0))[0]==0x6c);
 printf("HELPVIEW checks=%u failures=%u\n",checks,failures);return failures?1:0;
}
