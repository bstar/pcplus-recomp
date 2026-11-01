/* Actual DOS queue/file/sink composition. Mode2 deliberately reports an
 * ambiguous close after closing the DOS handle; mode4 deliberately removes
 * the private claim to check that polling refuses a conflicting replacement. */
#include "../src/directory/phone_log_queue.h"
#include "../src/directory/phone_log_file.h"
#include "../src/capture/capture_file.h"
#include "../src/capture/capture_fs.h"
#include <dos.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef PHONE_LOG_QUEUE_FAR
extern unsigned char __far phone_log_queue_store[666];
#else
extern unsigned char phone_log_queue_store[666];
#endif
unsigned phone_real_write(int,const void *,unsigned,unsigned *);
unsigned phone_real_close(int);
static unsigned checks,mode,writes,closes,short_next,close_next,logging;
static unsigned probe_reentry,reentry_failed,reentry_count,foreign;
static char path[128],other[128];
static phone_log_stamp start={1999,12,31,23,59,58},finish={2000,1,1,0,0,3};
static unsigned stack_segment(void);
#pragma aux stack_segment = "mov ax,ss" value [ax] modify exact [];
#define CHECK(c) do{++checks;if(!(c)){printf("FAIL reservation%u line%u\n",mode,__LINE__);return 1;}}while(0)
static void reentry(void)
{
 phone_log_queue_snapshot view;
 if(phone_log_queue_initialize()!=PLQ_BUSY||phone_log_queue_configure(0,0)!=PLQ_BUSY||
    phone_log_queue_start(42,0,0,0)!=PLQ_BUSY||phone_log_queue_end(42,0)!=PLQ_BUSY||
    phone_log_queue_poll()!=PLQ_BUSY||phone_log_queue_retry()!=PLQ_BUSY||
    phone_log_queue_inspect(&view)!=PLQ_BUSY)reentry_failed=1;
 ++reentry_count;
}
static unsigned __far __cdecl recorder(const char *identity,void *context)
{
 if(probe_reentry){
  reentry();
  if(capture_file_unclaim(&phone_log_file_result)!=CF_BUSY||
     capture_file_claim(path,&foreign)!=CF_BUSY||
     capture_file_release(recorder,context)!=CF_BUSY)reentry_failed=1;
 }
 return !strcmp(identity,(const char *)context);
}
unsigned capture_fs_write(int handle,const void *data,unsigned count,unsigned *written)
{
 ++writes;if(logging)reentry();
 if(short_next){short_next=0;return phone_real_write(handle,data,3,written);}
 return phone_real_write(handle,data,count,written);
}
unsigned capture_fs_close(int handle)
{
 unsigned status;++closes;if(logging)reentry();status=phone_real_close(handle);
 if(close_next){close_next=0;return status?status:6;}return status;
}
static unsigned poll_queue(void)
{unsigned status;logging=1;status=phone_log_queue_poll();logging=0;return status;}
static unsigned drain(void)
{
 phone_log_queue_snapshot view;unsigned i,status;
 for(i=0;i<8;++i){
  status=phone_log_queue_inspect(&view);if(status)return status;
  if(!view.queued)return PLQ_OK;status=poll_queue();if(status)return status;
 }
 return PLQ_FULL;
}
static unsigned excluded(void)
{
 return capture_file_begin(path,CF_NEW)==CF_BUSY&&snapshot_file_begin(path,CF_NEW)==CF_BUSY&&
        monitor_file_begin(path,CF_REPLACE)==CF_BUSY&&history_file_event(HISTORY_BEGIN,path,0)==CF_BUSY;
}
int main(int argc,char **argv)
{
 phone_log_queue_snapshot before,after;unsigned i,w,c;
 unsigned char saved_jft[20],__far *jft;union REGS regs;
 if(argc!=2)return 1;mode=(unsigned)atoi(argv[1]);if(mode>4)return 1;
 regs.h.ah=0x62;intdos(&regs,&regs);jft=(unsigned char __far *)MK_FP(regs.x.bx,0x18);
 for(i=0;i<20;++i)saved_jft[i]=jft[i];
 CHECK(FP_SEG(&before)==stack_segment());
#ifdef PHONE_LOG_QUEUE_FAR
 CHECK(FP_SEG((void __far *)phone_log_queue_store)!=FP_SEG(&before));
#else
 CHECK(FP_SEG((void __far *)phone_log_queue_store)==FP_SEG(&before));
#endif
 CHECK(capture_fs_canonical("CALLS.FON",path)==0&&capture_fs_canonical("OTHER.FON",other)==0);
 CHECK(capture_file_initialize()==CF_OK&&snapshot_file_initialize()==CF_OK&&monitor_file_initialize()==CF_OK);
 CHECK(phone_log_queue_initialize()==PLQ_OK);
 if(mode==3){
  CHECK(capture_file_begin(path,CF_NEW)==CF_OK);
  CHECK(phone_log_queue_inspect(&before)==PLQ_OK&&!before.enabled);
  CHECK(phone_log_queue_configure(1,path)==PLQ_BUSY);
  CHECK(phone_log_queue_inspect(&after)==PLQ_OK&&!memcmp(&before,&after,sizeof(before)));
  CHECK(capture_file_close()==CF_OK);
 }
 if(mode==0||mode==3)CHECK(capture_file_reserve(recorder,other)==CF_OK);
 if(mode==3)probe_reentry=1;
 CHECK(phone_log_queue_configure(1,path)==PLQ_OK&&excluded());
 CHECK(phone_log_queue_configure(1,path)==PLQ_OK);
 if(mode==0){
  CHECK(phone_log_queue_configure(1,other)==PLQ_BUSY&&excluded());
  CHECK(capture_file_release(recorder,other)==CF_OK);
  CHECK(phone_log_queue_configure(1,other)==PLQ_OK);
  CHECK(capture_file_begin(other,CF_NEW)==CF_BUSY);
  CHECK(phone_log_queue_configure(1,path)==PLQ_OK&&excluded());
 }
 CHECK(phone_log_queue_start(1,"LoC LAB","5550100",&start)==PLQ_OK);
 CHECK(phone_log_queue_configure(0,0)==PLQ_BUSY&&phone_log_queue_configure(1,other)==PLQ_BUSY);
 CHECK(phone_log_queue_configure(1,path)==PLQ_OK&&excluded());
 if(mode==1){
  short_next=1;CHECK(poll_queue()==PLQ_FILE);
  CHECK(phone_log_queue_inspect(&after)==PLQ_OK&&after.queued==1&&after.retry_required);
  CHECK(excluded()&&phone_log_queue_configure(0,0)==PLQ_BUSY);
  w=writes;CHECK(poll_queue()==PLQ_RETRY&&writes==w);
  CHECK(phone_log_queue_retry()==PLQ_OK);
 }else if(mode==2){
  close_next=1;CHECK(poll_queue()==PLQ_RECOVERY);
  CHECK(phone_log_queue_inspect(&before)==PLQ_OK&&before.queued==1&&before.recovery_required);
  w=writes;c=closes;
  CHECK(phone_log_queue_configure(0,0)==PLQ_RECOVERY&&phone_log_queue_configure(1,other)==PLQ_RECOVERY);
  CHECK(phone_log_queue_retry()==PLQ_RECOVERY&&poll_queue()==PLQ_RECOVERY&&excluded());
  CHECK(writes==w&&closes==c);
  CHECK(phone_log_queue_inspect(&after)==PLQ_OK&&!memcmp(&before,&after,sizeof(before)));
 }else if(mode==4){
  CHECK(capture_file_unclaim(&phone_log_file_result)==CF_OK);
  CHECK(capture_file_claim(other,&foreign)==CF_OK);
  CHECK(phone_log_queue_inspect(&before)==PLQ_OK);w=writes;c=closes;
  CHECK(poll_queue()==PLQ_BUSY&&writes==w&&closes==c);
  CHECK(phone_log_queue_inspect(&after)==PLQ_OK&&!memcmp(&before,&after,sizeof(before)));
  CHECK(capture_file_unclaim(&foreign)==CF_OK);
  CHECK(poll_queue()==PLQ_OK&&excluded());
 }
 if(mode!=2){
  CHECK(phone_log_queue_end(1,&finish)==PLQ_OK&&drain()==PLQ_OK&&excluded());
  CHECK(phone_log_queue_inspect(&after)==PLQ_OK&&!after.active&&!after.queued&&after.committed_events==2);
  CHECK(phone_log_queue_configure(0,0)==PLQ_OK);
  /* Subsequent capture calls run outside the queue: its busy guard must not
   * be asserted by a probe originating from an unrelated sink operation. */
  probe_reentry=0;
  CHECK(capture_file_begin(path,CF_APPEND)==CF_OK&&capture_file_close()==CF_OK);
 }
 if(mode==3){
  probe_reentry=0;CHECK(capture_file_release(recorder,other)==CF_OK&&reentry_count>0);
 }
 CHECK(!reentry_failed);
 for(i=0;i<20;++i)CHECK(saved_jft[i]==jft[i]);
 printf("LOGCLAIM %u checks 0 failures\n",checks);return 0;
}
