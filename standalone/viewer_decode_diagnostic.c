#include <stdio.h>
#include <string.h>
#include <dos.h>
#include "../src/filesystem/viewer_decode.h"
#ifdef VIEWER_DECODE_BOUNDARY
static struct {unsigned before;viewer_decode_state state;unsigned after;}
 __based(__segname("_CODE")) fixture;
viewer_decode_state __far * __far __cdecl viewer_fixture_state(void)
{fixture.before=0x1357;fixture.after=0x2468;return (viewer_decode_state __far *)&fixture.state;}
unsigned __far __cdecl viewer_fixture_guards(void)
{return fixture.before==0x1357&&fixture.after==0x2468;}
#else
viewer_decode_state __far * __far __cdecl viewer_fixture_state(void);
unsigned __far __cdecl viewer_fixture_guards(void);
static struct {unsigned before;viewer_decode_state state;unsigned after;} local;
static struct {unsigned before;unsigned char bytes[6468];unsigned after;} page;
static unsigned char input[4096],expected[6468],snapshot[26];
static unsigned checks,failures;
#define CHECK(x) do{checks++;if(!(x)){failures++;printf("FAIL check=%u line=%u\n",checks,__LINE__);}}while(0)
typedef struct vector {unsigned width,rows,block,length,used,status;unsigned long start,next;} vector;
typedef char vector_layout[sizeof(vector)==20?1:-1];
static void save(viewer_decode_state __far *s)
{unsigned i;for(i=0;i<sizeof(*s);i++)snapshot[i]=((unsigned char __far *)s)[i];}
static unsigned same(viewer_decode_state __far *s)
{unsigned i;for(i=0;i<sizeof(*s);i++)if(snapshot[i]!=((unsigned char __far *)s)[i])return 0;return 1;}
static void arguments(viewer_decode_state __far *s)
{
 unsigned used=0xaaaa;unsigned char saved=page.bytes[0];
 save(s);
 CHECK(viewer_decode_init(s,page.bytes,1,80,24,0)==VIEWER_ARGUMENT);
 CHECK(viewer_decode_init(s,page.bytes,6468,0,24,0)==VIEWER_ARGUMENT);
 CHECK(viewer_decode_init(s,page.bytes,6468,133,24,0)==VIEWER_ARGUMENT);
 CHECK(viewer_decode_init(s,page.bytes,6468,80,50,0)==VIEWER_ARGUMENT);
 CHECK(viewer_decode_init(s,(unsigned char __far *)s,6468,80,24,0)==VIEWER_ARGUMENT);
 CHECK(viewer_decode_init(s,MK_FP(0x5000,0xffff),6468,80,24,0)==VIEWER_ARGUMENT);
 CHECK(viewer_decode_init(s,MK_FP(0xffff,0x10),6468,80,24,0)==VIEWER_ARGUMENT);
 CHECK(viewer_decode_init(MK_FP(0x5000,0xffff),page.bytes,6468,80,24,0)==VIEWER_ARGUMENT);
 CHECK(viewer_decode_feed(s,input,257,&used)==VIEWER_ARGUMENT);
 CHECK(viewer_decode_feed(s,0,1,&used)==VIEWER_ARGUMENT);
 CHECK(viewer_decode_feed(s,input,1,0)==VIEWER_ARGUMENT);
 CHECK(viewer_decode_feed(s,input,1,(unsigned __far *)page.bytes)==VIEWER_ARGUMENT);
 CHECK(viewer_decode_feed(s,(unsigned char __far *)s,1,&used)==VIEWER_ARGUMENT);
 CHECK(viewer_decode_feed(s,page.bytes,1,&used)==VIEWER_ARGUMENT);
 CHECK(viewer_decode_feed(s,MK_FP(0x5000,0xffff),2,&used)==VIEWER_ARGUMENT);
 CHECK(viewer_decode_feed(s,input,2,(unsigned __far *)input)==VIEWER_ARGUMENT);
 CHECK(viewer_decode_feed(s,input,1,(unsigned __far *)s)==VIEWER_ARGUMENT);
 CHECK(viewer_decode_finish(0)==VIEWER_ARGUMENT);
 CHECK(viewer_decode_feed(0,input,1,&used)==VIEWER_ARGUMENT);
 CHECK(used==0xaaaa&&same(s)&&page.bytes[0]==saved);
}
int main(void)
{
 FILE *f;unsigned count,index,bank,i,size,at,used,n,status;vector v;
 viewer_decode_state __far *s;char magic[4];
 f=fopen("VECTORS.BIN","rb");if(!f)return 20;
 if(fread(magic,1,4,f)!=4||memcmp(magic,"VD01",4)||fread(&count,2,1,f)!=1)return 21;
 for(index=0;index<count;index++){
  if(fread(&v,sizeof(v),1,f)!=1||!v.width||v.width>132||!v.rows||v.rows>49||
     !v.block||v.block>256||v.length>sizeof(input))return 22;
  size=v.width*v.rows;
  if(fread(input,1,v.length,f)!=v.length||fread(expected,1,size,f)!=size)return 23;
  for(bank=0;bank<2;bank++){
   local.before=0x1357;local.after=0x2468;page.before=0x1357;page.after=0x2468;
   memset(page.bytes,0xa5,sizeof(page.bytes));
   s=viewer_fixture_state();if(!bank)s=(viewer_decode_state __far *)&local.state;
   CHECK(viewer_decode_init(s,page.bytes,sizeof(page.bytes),v.width,v.rows,v.start)==VIEWER_MORE);
   if(!index)arguments(s);
   at=0;status=VIEWER_MORE;
   while(at<v.length&&status==VIEWER_MORE){
    n=v.length-at;if(n>v.block)n=v.block;used=0xaaaa;
    status=viewer_decode_feed(s,input+at,n,&used);
    CHECK(used<=n&&(used||status!=VIEWER_MORE));at+=used;
   }
   if(status==VIEWER_MORE)status=viewer_decode_finish(s);
   CHECK(at==v.used&&status==v.status&&s->position==v.next&&s->phase==v.status);
   CHECK(!memcmp(page.bytes,expected,size));
   for(i=size;i<sizeof(page.bytes);i++)if(page.bytes[i]!=0xa5)break;
   CHECK(i==sizeof(page.bytes)&&page.before==0x1357&&page.after==0x2468);
   CHECK(local.before==0x1357&&local.after==0x2468&&viewer_fixture_guards());
   save(s);used=0xaaaa;
   CHECK(viewer_decode_feed(s,input,1,&used)==status&&used==0&&same(s));
   CHECK(viewer_decode_finish(s)==status&&same(s));
  }
 }
 CHECK(fgetc(f)==EOF);fclose(f);
 printf("VIEWDECODE vectors=%u checks=%u failures=%u\n",count,checks,failures);
 return failures?1:0;
}
#endif
