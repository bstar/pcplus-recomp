#include <stdio.h>
#include <string.h>
#include <malloc.h>
#include "../src/filesystem/viewer_session.h"
#include "../src/filesystem/viewer_file.h"
static unsigned token;
static unsigned long checks,failures,max_steps;
static unsigned char expected[6468];
#define CHECK(x) do{checks++;if(!(x)){failures++;printf("FAIL check=%lu line=%u\n",checks,__LINE__);}}while(0)
typedef struct header {char path[64];unsigned width,rows,actions,start_status;} header;
typedef struct action {unsigned op,status,phase,rescan;unsigned long page,next;} action;
typedef char header_layout[sizeof(header)==72?1:-1];
typedef char action_layout[sizeof(action)==16?1:-1];
static unsigned pump(unsigned *rescan)
{
 viewer_session_snapshot s;unsigned result=VS_OK;unsigned long steps=0;
 for(;;){
  CHECK(viewer_session_inspect(&s)==VS_OK);
  if(s.phase!=VS_LOADING)break;
  if(s.page<s.target)*rescan=1;
  CHECK(s.cache_first<=s.cache_last&&s.cache_last-s.cache_first<64);
  if(!s.pending_seek)CHECK(s.read_position>=s.next&&s.read_position-s.next==s.buffered-s.consumed);
  if(++steps>200000UL){CHECK(0);return VS_INVARIANT;}
  result=viewer_session_step();
 }
 if(steps>max_steps)max_steps=steps;
 return result;
}
int main(void)
{
 FILE *f;char magic[4];unsigned scenarios,k,j,i,size,r,start,rescan;
 unsigned char __far *allocation;unsigned char __far *page;
 viewer_session_snapshot s,before;viewer_file_snapshot file;header h;action a;
 allocation=_fmalloc(6500);if(!allocation)return 20;page=allocation+16;
 for(i=0;i<6500;i++)allocation[i]=0xa5;
 CHECK(viewer_session_inspect(&before)==VS_OK);
 CHECK(viewer_session_begin("D:\\LONG.DAT",&token,page,6468,0,24)==VS_ARGUMENT);
 CHECK(viewer_session_begin("D:\\LONG.DAT",&token,page,6468,80,50)==VS_ARGUMENT);
 CHECK(viewer_session_begin("D:\\LONG.DAT",&token,page,1,80,24)==VS_ARGUMENT);
 CHECK(viewer_session_begin("CON",&token,page,6468,80,24)==VS_ARGUMENT);
 CHECK(viewer_session_begin("D:\\LONG.DAT",0,page,6468,80,24)==VS_ARGUMENT);
 CHECK(viewer_session_inspect(&s)==VS_OK&&!memcmp(&s,&before,sizeof(s)));
 for(i=0;i<6500;i++)if(allocation[i]!=0xa5)break;CHECK(i==6500);
 f=fopen("SCENARIO.BIN","rb");if(!f)return 21;
 if(fread(magic,1,4,f)!=4||memcmp(magic,"VS01",4)||fread(&scenarios,2,1,f)!=1)return 22;
 for(k=0;k<scenarios;k++){
  if(fread(&h,sizeof(h),1,f)!=1)return 23;size=h.width*h.rows;
  if(!h.width||h.width>132||!h.rows||h.rows>49||size>6468)return 24;
  for(i=0;i<6500;i++)allocation[i]=0xa5;
  start=viewer_session_begin(h.path,&token,page,6468,h.width,h.rows);CHECK(start==h.start_status);
  for(j=0;j<h.actions;j++){
   if(fread(&a,sizeof(a),1,f)!=1)return 25;rescan=0;
   if(!a.op){r=start;if(r==VS_OK)r=pump(&rescan);}
   else if(a.op<=3){r=viewer_session_move(a.op-1);if(r==VS_OK)r=pump(&rescan);}
   else if(a.op==4)r=viewer_session_stop();
   else if(a.op==5)r=viewer_session_step();
   else return 26;
   CHECK(viewer_session_inspect(&s)==VS_OK);
   if((r!=a.status||s.phase!=a.phase||s.page!=a.page||s.next!=a.next)&&failures<10)
    printf("DETAIL case=%u action=%u op=%u r=%u want=%u phase=%u error=%u file=%u decode=%u page=%lu target=%lu next=%lu wantnext=%lu buf=%u/%u read=%lu\n",k,j,a.op,r,a.status,s.phase,s.error,s.file_status,s.decode_status,s.page,s.target,s.next,a.next,s.consumed,s.buffered,s.read_position);
   CHECK(r==a.status);
   CHECK(s.phase==a.phase&&s.page==a.page&&s.next==a.next);
   CHECK(!a.rescan||rescan);
   if(a.phase==VS_READY){
    if(fread(expected,1,size,f)!=size)return 27;
    for(i=0;i<size;i++)if(page[i]!=expected[i])break;CHECK(i==size);
    before=s;CHECK(viewer_session_step()==VS_STATE);
    CHECK(viewer_session_inspect(&s)==VS_OK&&!memcmp(&s,&before,sizeof(s)));
   }
   for(i=0;i<16;i++)CHECK(allocation[i]==0xa5&&allocation[6484+i]==0xa5);
  }
  r=viewer_session_stop();CHECK(r==(h.start_status==VS_OK?VS_OK:VS_IO));
  CHECK(viewer_session_inspect(&s)==VS_OK&&s.phase==VS_CLOSED&&!s.owned);
  CHECK(viewer_file_inspect(&file)==VF_OK&&file.handle==0xffff&&!file.claimed);
 }
 CHECK(fgetc(f)==EOF);fclose(f);_ffree(allocation);
 printf("VIEWPAGE scenarios=%u checks=%lu failures=%lu maxsteps=%lu\n",scenarios,checks,failures,max_steps);
 return failures?1:0;
}
