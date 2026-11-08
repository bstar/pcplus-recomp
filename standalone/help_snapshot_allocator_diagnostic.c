#include "../src/aspect/runtime.h"
#include <stdio.h>
extern void __far * __far __cdecl help_parent_frame_allocate(unsigned);
extern unsigned __far __cdecl help_parent_frame_release(void __far *);
static unsigned ready,begin_fail,end_fail,private_fail,private_end_fail;
static unsigned begins,ends,allocations,releases,checks,failures;
static unsigned char parent_frame[4032],private_frame[4032];
unsigned __cdecl aspect_render_help_snapshot_ready(void){return ready;}
void __far * __cdecl aspect_render_snapshot_begin(unsigned bytes)
{++begins;if(bytes!=4032||begin_fail)return 0;return parent_frame;}
unsigned __cdecl aspect_render_snapshot_end(void){++ends;return end_fail;}
void __far * __far __cdecl help_fallback_frame_allocate(unsigned bytes)
{++allocations;if(bytes!=4032||private_fail)return 0;return private_frame;}
unsigned __far __cdecl help_fallback_frame_release(void __far *p)
{++releases;return p!=private_frame?ASPECT_RUN_STATE:private_end_fail;}
static void check(unsigned yes,unsigned line)
{++checks;if(!yes){++failures;printf("FAIL %u\n",line);}}
#define CHECK(x) check((x)!=0,__LINE__)
int main(void)
{
 void __far *p;
 ready=1;
 CHECK(!help_parent_frame_allocate(4000)&&begins==0&&allocations==0);
 CHECK(help_parent_frame_release(parent_frame)==ASPECT_RUN_STATE&&ends==0);
 p=help_parent_frame_allocate(4032);
 CHECK(p==parent_frame&&begins==1&&allocations==0);
 CHECK(!help_parent_frame_allocate(4032)&&begins==1);
 CHECK(help_parent_frame_release(private_frame)==ASPECT_RUN_STATE&&ends==0);
 end_fail=ASPECT_RUN_SERIAL;
 CHECK(help_parent_frame_release(p)==ASPECT_RUN_SERIAL&&ends==1);
 CHECK(!help_parent_frame_allocate(4032)&&begins==1);
 end_fail=0;
 CHECK(help_parent_frame_release(p)==0&&ends==2);
 CHECK(help_parent_frame_release(p)==ASPECT_RUN_STATE&&ends==2);
 /* An authenticated parent refusal must not silently choose a DOS buffer. */
 begin_fail=1;
 CHECK(!help_parent_frame_allocate(4032)&&begins==2&&allocations==0);
 begin_fail=0;
 p=help_parent_frame_allocate(4032);
 CHECK(p==parent_frame&&begins==3);
 CHECK(help_parent_frame_release(p)==0&&ends==3);
 ready=2;
 CHECK(!help_parent_frame_allocate(4032)&&begins==3&&allocations==0);
 ready=0;private_fail=1;
 CHECK(!help_parent_frame_allocate(4032)&&allocations==1);
 private_fail=0;p=help_parent_frame_allocate(4032);
 CHECK(p==private_frame&&allocations==2&&begins==3);
 CHECK(help_parent_frame_release(parent_frame)==ASPECT_RUN_STATE&&releases==0);
 /* Changing context does not change the allocator that owns an existing frame. */
 ready=1;private_end_fail=ASPECT_RUN_IO;
 CHECK(help_parent_frame_release(p)==ASPECT_RUN_IO&&releases==1&&ends==3);
 CHECK(!help_parent_frame_allocate(4032)&&begins==3&&allocations==2);
 private_end_fail=0;
 CHECK(help_parent_frame_release(p)==0&&releases==2&&ends==3);
 CHECK(help_parent_frame_release(p)==ASPECT_RUN_STATE&&releases==2);
 p=help_parent_frame_allocate(4032);
 CHECK(p==parent_frame&&begins==4);
 ready=0;
 CHECK(help_parent_frame_release(p)==0&&ends==4&&releases==2);
 printf("HELPALLOC checks=%u failures=%u\n",checks,failures);
 return failures?1:0;
}
