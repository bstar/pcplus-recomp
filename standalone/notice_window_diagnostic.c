#include "notice_window.h"
#include <dos.h>
#include <malloc.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned char before[4000];
static unsigned checks;
static void ck(unsigned yes){++checks;if(!yes){printf("FAIL %u\n",checks);exit(1);}}
static unsigned cursor(void){return *(unsigned __far *)MK_FP(0x40,0x50);}
static void sample(void){_fmemcpy(before,MK_FP(0xb800,0),4000);}
static void equal(void){ck(_fmemcmp(before,MK_FP(0xb800,0),4000)==0);ck(cursor()==0x0405);}
static unsigned long heap_used(void)
{
 struct _heapinfo item;int status;unsigned long bytes=0;
 item._pentry=0;
 while((status=_fheapwalk(&item))==_HEAPOK)if(item._useflag==_USEDENTRY)bytes+=item._size;
 ck(status==_HEAPEND||status==_HEAPEMPTY);return bytes;
}
int main(void)
{
 union REGS in,out;unsigned i,j,old_cursor;unsigned long baseline;
 notice_window_rect rectangles[]={{9,34,11,45,0x70},{2,2,8,30,0x1f},{0,0,24,79,0x2e},{1,1,22,76,0x4f},{10,0,12,4,0x5b},{20,60,24,79,0x6c}},bad;
 in.x.ax=3;int86(0x10,&in,&out);
 in.h.ah=2;in.h.bh=0;in.x.dx=0x0405;int86(0x10,&in,&out);
 for(i=0;i<2000;++i)((unsigned __far *)MK_FP(0xb800,0))[i]=(i%26+65)|0x1700;
 sample();old_cursor=cursor();baseline=heap_used();
 ck(notice_window_close()==0);ck(notice_window_open(0,0)==NOTICE_WINDOW_ARGUMENT);equal();
 ck(notice_window_open((const notice_window_rect *)0xfffc,0)==NOTICE_WINDOW_ARGUMENT);equal();
 *(unsigned char __far *)MK_FP(0x40,0x84)=42;
 ck(notice_window_open(&rectangles[0],0)==NOTICE_WINDOW_STATE);ck(notice_window_phase()==0);
 *(unsigned char __far *)MK_FP(0x40,0x84)=24;equal();
 bad=rectangles[0];bad.right=80;ck(notice_window_open(&bad,0)==NOTICE_WINDOW_ARGUMENT);equal();
 bad=rectangles[0];bad.bottom=8;ck(notice_window_open(&bad,0)==NOTICE_WINDOW_ARGUMENT);equal();
 bad=rectangles[0];bad.attribute=256;ck(notice_window_open(&bad,0)==NOTICE_WINDOW_ARGUMENT);equal();
 ck(notice_window_open(&rectangles[0],2)==NOTICE_WINDOW_ARGUMENT);equal();
 notice_window_fail_alloc=1;ck(notice_window_open(&rectangles[0],1)==NOTICE_WINDOW_MEMORY);equal();ck(notice_window_phase()==0);ck(notice_window_allocations==0);notice_window_fail_alloc=0;
 for(i=0;i<6;++i)for(j=0;j<2;++j){
  ck(notice_window_open(&rectangles[i],j)==0);ck(notice_window_phase()==1);
  ck(_fmemcmp(before,MK_FP(0xb800,0),4000)!=0);
  ck(notice_window_open(&rectangles[0],0)==NOTICE_WINDOW_BUSY);
  ck(notice_window_close()==0);equal();ck(notice_window_phase()==0);ck(heap_used()==baseline);
 }
 ck(notice_window_open(&rectangles[0],1)==0);notice_window_damage_guard();
 ck(notice_window_close()==NOTICE_WINDOW_GUARD);ck(notice_window_phase()==2);ck(notice_window_allocations==notice_window_frees+1);
 ck(notice_window_open(&rectangles[0],0)==NOTICE_WINDOW_BUSY);
 notice_window_damage_guard();ck(notice_window_close()==0);equal();ck(heap_used()==baseline);
 ck(notice_window_open(&rectangles[0],0)==0);
 *(unsigned char __far *)MK_FP(0x40,0x84)=42;
 ck(notice_window_close()==NOTICE_WINDOW_STATE);ck(notice_window_phase()==1);
 *(unsigned char __far *)MK_FP(0x40,0x84)=24;
 ck(notice_window_close()==0);equal();ck(heap_used()==baseline);
 for(i=0;i<100;++i){ck(notice_window_open(&rectangles[0],i&1)==0);ck(notice_window_close()==0);equal();ck(heap_used()==baseline);}
 ck(cursor()==old_cursor);ck(notice_window_allocations==114);ck(notice_window_allocations==notice_window_frees);ck(notice_window_phase()==0);
 printf("WINDOW PASS %u checks %u allocations %u frees\n",checks,notice_window_allocations,notice_window_frees);return 0;
}
