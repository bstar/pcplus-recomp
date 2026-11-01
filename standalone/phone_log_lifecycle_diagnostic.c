/* Actual DOS lifecycle + real queue/backend. Explicit end-refusal and physical
 * close ambiguity are diagnostic boundary models, not product binary patches. */
#include "../src/directory/phone_log_lifecycle.h"
#include "../src/directory/phone_log_file.h"
#include "../src/capture/capture_fs.h"
#include <dos.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef PHONE_LOG_QUEUE_FAR
extern unsigned char __far phone_log_queue_store[666];
#define QFAR __far
#else
extern unsigned char phone_log_queue_store[666];
#define QFAR
#endif
extern unsigned char phone_log_lifecycle_store[38];
unsigned __cdecl lifecycle_real_queue_end(unsigned long,const phone_log_stamp *);
unsigned phone_real_write(int,const void *,unsigned,unsigned *);
unsigned phone_real_close(int);
static unsigned checks,mode,refuse_end,short_write,ambiguous_close,io_calls;
static phone_log_stamp start={1999,12,31,23,59,58},finish={2000,1,1,0,0,3};
static unsigned stack_segment(void);
#pragma aux stack_segment = "mov ax,ss" value [ax] modify exact [];
#define CHECK(c) do{++checks;if(!(c)){printf("FAIL case%u line%u\n",mode,__LINE__);return 1;}}while(0)
#ifdef PHONE_LOG_LIFECYCLE_BANK
unsigned __cdecl lifecycle_queue_end_fault(unsigned long generation,const phone_log_stamp *stamp)
#else
unsigned phone_log_queue_end(unsigned long generation,const phone_log_stamp *stamp)
#endif
{if(refuse_end)return PLQ_FULL;return lifecycle_real_queue_end(generation,stamp);}
unsigned capture_fs_write(int h,const void *p,unsigned n,unsigned *written)
{++io_calls;if(short_write){short_write=0;return phone_real_write(h,p,3,written);}return phone_real_write(h,p,n,written);}
unsigned capture_fs_close(int h)
{unsigned status;++io_calls;status=phone_real_close(h);if(ambiguous_close){ambiguous_close=0;return status?status:6;}return status;}
static unsigned drain(void)
{
 phone_log_queue_snapshot q;unsigned status,i;
 for(i=0;i<8;++i){status=phone_log_queue_inspect(&q);if(status)return status;
  if(!q.queued)return PLQ_OK;status=phone_log_queue_poll();if(status)return status;}
 return PLQ_FULL;
}
int main(int argc,char **argv)
{
 phone_log_lifecycle_snapshot v,before;phone_log_queue_snapshot q;
 phone_log_stamp changed=finish,invalid=finish;
 unsigned i,n,ds,context[6];char path[128];
 unsigned char jft_before[20],__far *jft;union REGS regs;FILE *file;
 if(argc!=2)return 1;mode=atoi(argv[1]);if(mode>6)return 1;
 regs.h.ah=0x62;intdos(&regs,&regs);jft=MK_FP(regs.x.bx,0x18);
 for(i=0;i<20;++i)jft_before[i]=jft[i];
 ds=FP_SEG(&v);CHECK(ds==stack_segment());
 CHECK(capture_fs_canonical("CALLS.FON",path)==0);
 CHECK(phone_log_queue_configure(mode!=5,path)==PLQ_OK);
 CHECK(phone_log_lifecycle_inspect(&v)==PLQ_OK&&v.generation==0&&!v.active&&!v.pending);
 CHECK(phone_log_lifecycle_end(&finish)==PLQ_STATE);
 if(mode==6){
  /* Explicit idle-generation fixture, not an application binary patch.
   * Native owner generation at +2, queue last_started/last_ended at +18/+22. */
  phone_log_lifecycle_store[2]=254;
  for(i=3;i<6;++i)phone_log_lifecycle_store[i]=255;
  for(i=18;i<26;++i)phone_log_queue_store[i]=(i==18||i==22)?254:255;
  CHECK(phone_log_lifecycle_inspect(&v)==PLQ_OK&&v.generation==0xfffffffeUL&&!v.active);
  CHECK(phone_log_queue_inspect(&q)==PLQ_OK&&q.last_started==v.generation&&q.last_ended==v.generation&&!q.active);
 }
 if(mode==5){
  CHECK(phone_log_lifecycle_ready()==PLQ_DISABLED);
  CHECK(phone_log_lifecycle_begin("LoC LAB","5550100",&start)==PLQ_DISABLED);
  CHECK(phone_log_lifecycle_service()==PLQ_OK&&io_calls==0);
 }else{
  CHECK(phone_log_lifecycle_ready()==PLQ_OK);
  invalid.month=13;
  CHECK(phone_log_lifecycle_begin("LoC LAB","5550100",&invalid)==PLQ_CLOCK);
  CHECK(phone_log_lifecycle_inspect(&v)==PLQ_OK&&v.generation==(mode==6?0xfffffffeUL:0UL));
  CHECK(phone_log_lifecycle_begin("LoC LAB","5550100",&start)==PLQ_OK);
  CHECK(phone_log_lifecycle_begin(0,0,0)==PLQ_DUPLICATE);
  CHECK(phone_log_lifecycle_inspect(&v)==PLQ_OK&&v.generation==(mode==6?0xffffffffUL:1UL)&&v.active&&!v.pending);
  CHECK(phone_log_lifecycle_ready()==PLQ_STATE&&io_calls==0);
  if(mode==2){
   refuse_end=1;CHECK(phone_log_lifecycle_end(&finish)==PLL_PENDING);
   CHECK(phone_log_lifecycle_inspect(&before)==PLQ_OK&&before.active&&before.pending&&before.pending_status==PLQ_FULL);
   changed.hour=1;CHECK(phone_log_lifecycle_end(&changed)==PLQ_DUPLICATE);
   CHECK(phone_log_lifecycle_inspect(&v)==PLQ_OK&&!memcmp(&v,&before,sizeof(v)));
   CHECK(phone_log_lifecycle_ready()==PLQ_BUSY);
   CHECK(phone_log_lifecycle_begin("WRONG","000",&changed)==PLQ_BUSY);
   CHECK(phone_log_lifecycle_service()==PLQ_FULL&&io_calls==0);
   refuse_end=0;CHECK(phone_log_lifecycle_service()==PLQ_OK);
  }else if(mode==4){
   ambiguous_close=1;CHECK(phone_log_queue_poll()==PLQ_RECOVERY);
   n=io_calls;CHECK(phone_log_lifecycle_end(&finish)==PLL_PENDING);
   CHECK(phone_log_lifecycle_inspect(&v)==PLQ_OK&&v.pending&&v.pending_status==PLQ_RECOVERY);
   CHECK(phone_log_lifecycle_service()==PLQ_RECOVERY&&io_calls==n);
   CHECK(phone_log_lifecycle_begin("WRONG","000",&changed)==PLQ_BUSY);
   CHECK(phone_log_queue_retry()==PLQ_RECOVERY&&io_calls==n);
  }else{
   CHECK(phone_log_lifecycle_end(0)==PLQ_ARGUMENT);
   CHECK(phone_log_lifecycle_end(&invalid)==PLQ_CLOCK);
   invalid=start;invalid.second=57;
   CHECK(phone_log_lifecycle_end(&invalid)==PLQ_CLOCK);
   CHECK(phone_log_lifecycle_inspect(&v)==PLQ_OK&&v.active&&!v.pending);
   CHECK(phone_log_lifecycle_end(&finish)==PLQ_OK);
  }
  if(mode==6){
   CHECK(phone_log_lifecycle_begin("WRAP","5550100",&start)==PLQ_OK);
   CHECK(phone_log_lifecycle_inspect(&v)==PLQ_OK&&v.generation==1&&v.active);
   CHECK(phone_log_lifecycle_end(&finish)==PLQ_OK);
  }
  if(mode==1){
   CHECK(phone_log_lifecycle_begin("TWO","5550100",&start)==PLQ_OK);
   CHECK(phone_log_lifecycle_end(&finish)==PLQ_OK);
   CHECK(phone_log_queue_inspect(&q)==PLQ_OK&&q.queued==4);
   CHECK(phone_log_lifecycle_inspect(&before)==PLQ_OK&&before.generation==2);
   CHECK(phone_log_lifecycle_begin("WRONG","000",&start)==PLQ_FULL);
   CHECK(phone_log_lifecycle_inspect(&v)==PLQ_OK&&!memcmp(&v,&before,sizeof(v)));
   CHECK(phone_log_queue_poll()==PLQ_OK);
   CHECK(phone_log_lifecycle_ready()==PLQ_FULL);
   CHECK(phone_log_queue_poll()==PLQ_OK);
   CHECK(phone_log_lifecycle_ready()==PLQ_OK);
   CHECK(phone_log_lifecycle_begin("THREE","5550100",&start)==PLQ_OK);
   CHECK(phone_log_lifecycle_end(&finish)==PLQ_OK);
  }
  if(mode==3){
   short_write=1;CHECK(phone_log_queue_poll()==PLQ_FILE);n=io_calls;
   CHECK(phone_log_lifecycle_ready()==PLQ_RETRY);
   CHECK(phone_log_lifecycle_begin("WRONG","000",&start)==PLQ_RETRY&&io_calls==n);
   CHECK(phone_log_queue_retry()==PLQ_OK&&io_calls==n);
  }
  if(mode!=4){
   CHECK(drain()==PLQ_OK);n=io_calls;
   CHECK(phone_log_lifecycle_end(&changed)==PLQ_DUPLICATE);
   CHECK(phone_log_lifecycle_service()==PLQ_OK&&io_calls==n);
   CHECK(phone_log_lifecycle_inspect(&v)==PLQ_OK&&!v.active&&!v.pending&&!v.pending_status);
   CHECK(v.generation==(mode==1?3UL:1UL));
   CHECK(phone_log_queue_inspect(&q)==PLQ_OK&&!q.active&&!q.queued&&q.committed_events==(mode==1?6UL:mode==6?4UL:2UL));
  }
 }
 CHECK(phone_log_lifecycle_inspect(0)==PLQ_ARGUMENT);
 CHECK(phone_log_lifecycle_inspect((phone_log_lifecycle_snapshot *)phone_log_lifecycle_store)==PLQ_ARGUMENT);
 for(i=0;i<20;++i)CHECK(jft_before[i]==jft[i]);
 context[0]=ds;context[1]=stack_segment();
 context[2]=FP_SEG((void __far *)phone_log_queue_store);context[3]=FP_SEG(phone_log_lifecycle_store);
 context[4]=sizeof(phone_log_lifecycle_store);context[5]=sizeof(v);
 CHECK(context[0]==context[3]);
#ifdef PHONE_LOG_QUEUE_FAR
 CHECK(context[0]!=context[2]);
#else
 CHECK(context[0]==context[2]);
#endif
 file=fopen("CONTEXT.BIN","wb");CHECK(file!=0);
 n=fwrite(context,1,sizeof(context),file);CHECK(fclose(file)==0&&n==sizeof(context));
 printf("LIFECYCLE %u checks 0 failures\n",checks);return 0;
}
