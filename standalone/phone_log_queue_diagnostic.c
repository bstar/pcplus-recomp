/* Real DOS queue -> checked file backend. Prefix/close faults and private
 * owner corruption are explicit test probes, never application patches. */
#include "../src/directory/phone_log_queue.h"
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
unsigned phone_real_write(int,const void *,unsigned,unsigned *);
unsigned phone_real_close(int);
static unsigned mode,checks,writes,closes,short_next,close_next,reentry_checks,reentry_failed;
static phone_log_stamp start={1999,12,31,23,59,58},finish={2000,1,1,0,0,3};
static char path[128];
static unsigned stack_segment(void);
#pragma aux stack_segment = "mov ax,ss" value [ax] modify exact [];
#define CHECK(c) do{++checks;if(!(c)){printf("FAIL case%u line%u file%u\n",mode,__LINE__,phone_log_file_result.status);return 1;}}while(0)
static void reentry(void)
{
 unsigned char before[666];unsigned i;phone_log_queue_snapshot view;
 for(i=0;i<666;++i)before[i]=phone_log_queue_store[i];
 if(phone_log_queue_initialize()!=PLQ_BUSY||phone_log_queue_poll()!=PLQ_BUSY||
    phone_log_queue_start(42,0,0,0)!=PLQ_BUSY||phone_log_queue_end(42,0)!=PLQ_BUSY||
    phone_log_queue_configure(0,0)!=PLQ_BUSY||phone_log_queue_retry()!=PLQ_BUSY||
    phone_log_queue_inspect(&view)!=PLQ_BUSY)reentry_failed=1;
 for(i=0;i<666;++i)if(before[i]!=phone_log_queue_store[i])reentry_failed=1;
 ++reentry_checks;
}
unsigned capture_fs_write(int handle,const void *data,unsigned count,unsigned *written)
{
 ++writes;reentry();
 if(short_next){short_next=0;return phone_real_write(handle,data,3,written);}
 return phone_real_write(handle,data,count,written);
}
unsigned capture_fs_close(int handle)
{
 unsigned status;++closes;reentry();status=phone_real_close(handle);
 if(close_next){close_next=0;return status?status:6;}return status;
}
static unsigned drain(void)
{
 phone_log_queue_snapshot view;unsigned status,n;
 for(n=0;n<8;++n){
  status=phone_log_queue_inspect(&view);if(status)return status;
  if(!view.queued)return PLQ_OK;status=phone_log_queue_poll();if(status)return status;
 }
 return PLQ_FULL;
}
static int save(const char *name,const void *data,unsigned count)
{FILE *stream=fopen(name,"wb");unsigned n;if(!stream)return 0;n=fwrite(data,1,count,stream);return fclose(stream)==0&&n==count;}
int main(int argc,char **argv)
{
 phone_log_queue_snapshot view,saved;
 phone_log_stamp invalid,long_start={1980,1,1,0,0,0},long_end={2099,12,31,23,59,59},now;
 unsigned i,before,j,flag,context[8],alias=0;
 unsigned char jft_before[20],__far *jft,prm[1264],prm_copy[1264],raw[666];
 char name[64],number[64];unsigned long seconds,location,base;
 unsigned QFAR *words=(unsigned QFAR *)phone_log_queue_store;
 union REGS regs;
 if(argc!=2)return 1;mode=(unsigned)atoi(argv[1]);if(mode>8)return 1;
 regs.h.ah=0x62;intdos(&regs,&regs);jft=(unsigned char __far *)MK_FP(regs.x.bx,0x18);
 for(i=0;i<20;++i)jft_before[i]=jft[i];
 context[0]=FP_SEG(&view);
 context[1]=stack_segment();
 context[2]=FP_SEG((void __far *)phone_log_queue_store);context[3]=FP_OFF((void __far *)phone_log_queue_store);
 context[4]=sizeof(phone_log_queue_store);context[5]=sizeof(view);
 CHECK(context[0]==context[1]);
#ifdef PHONE_LOG_QUEUE_FAR
 CHECK(context[2]!=context[0]);
#else
 CHECK(context[2]==context[0]);
#endif
 CHECK(phone_log_queue_initialize()==PLQ_OK);
 CHECK(capture_fs_canonical("CALLS.FON",path)==0);
 CHECK(phone_log_queue_configure(1,path)==PLQ_OK);
 if(mode==0){
  CHECK(phone_log_queue_start(1,"LoC LAB","5550100",&start)==PLQ_OK);
  CHECK(phone_log_queue_start(1,0,0,0)==PLQ_DUPLICATE);
  CHECK(phone_log_queue_poll()==PLQ_OK);
  CHECK(phone_log_queue_end(1,&finish)==PLQ_OK&&phone_log_queue_end(1,0)==PLQ_DUPLICATE);
  CHECK(drain()==PLQ_OK);
  before=writes;CHECK(phone_log_queue_poll()==PLQ_OK&&writes==before);
 }else if(mode==1){
  CHECK(phone_log_queue_start(10,"LoC LAB","5550100",&start)==PLQ_OK);
  short_next=1;CHECK(phone_log_queue_poll()==PLQ_FILE);
  CHECK(phone_log_queue_inspect(&view)==PLQ_OK&&view.queued==1&&view.active&&view.retry_required);
  CHECK(phone_log_queue_end(10,&finish)==PLQ_OK);before=writes;
  CHECK(phone_log_queue_poll()==PLQ_RETRY&&writes==before);
  CHECK(phone_log_queue_configure(0,0)==PLQ_BUSY);
  CHECK(phone_log_queue_configure(1,path)==PLQ_OK);
  CHECK(phone_log_queue_retry()==PLQ_OK&&writes==before);
  CHECK(drain()==PLQ_OK);
 }else if(mode==2){
  for(i=100;i<102;++i){
   CHECK(phone_log_queue_start(i,i==100?"ONE":"TWO","5550100",&start)==PLQ_OK);
   CHECK(phone_log_queue_end(i,&finish)==PLQ_OK);
  }
  CHECK(phone_log_queue_inspect(&saved)==PLQ_OK&&saved.queued==4);
  CHECK(phone_log_queue_start(102,"THREE","5550100",&start)==PLQ_FULL);
  CHECK(phone_log_queue_inspect(&view)==PLQ_OK&&memcmp(&view,&saved,sizeof(view))==0);
  CHECK(phone_log_queue_poll()==PLQ_OK);
  CHECK(phone_log_queue_start(102,"THREE","5550100",&start)==PLQ_OK);
  CHECK(phone_log_queue_end(102,&finish)==PLQ_FULL);
  CHECK(phone_log_queue_poll()==PLQ_OK&&phone_log_queue_end(102,&finish)==PLQ_OK);
  CHECK(drain()==PLQ_OK);
 }else if(mode==3){
  CHECK(phone_log_queue_start(9,"LoC LAB","5550100",&start)==PLQ_OK);
  close_next=1;CHECK(phone_log_queue_poll()==PLQ_RECOVERY);
  CHECK(phone_log_queue_inspect(&saved)==PLQ_OK&&saved.queued==1&&saved.active&&saved.recovery_required);
  before=writes;
  CHECK(phone_log_queue_poll()==PLQ_RECOVERY&&phone_log_queue_retry()==PLQ_RECOVERY);
  CHECK(phone_log_queue_end(9,&finish)==PLQ_RECOVERY&&writes==before&&closes==1);
  CHECK(phone_log_queue_inspect(&view)==PLQ_OK&&memcmp(&view,&saved,sizeof(view))==0);
 }else if(mode==4){
  CHECK(phone_log_queue_start(0xffffffffUL,"MAX","5550100",&start)==PLQ_OK);
  invalid=start;--invalid.second;
  CHECK(phone_log_queue_end(0xffffffffUL,&invalid)==PLQ_CLOCK);
  CHECK(phone_log_queue_end(0xffffffffUL,&finish)==PLQ_OK&&drain()==PLQ_OK);
  CHECK(phone_log_queue_start(0xfffffffeUL,"STALE","5550100",&start)==PLQ_STATE);
  CHECK(phone_log_queue_start(1,"WRAP","5550100",&start)==PLQ_OK);
  CHECK(phone_log_queue_end(0xffffffffUL,0)==PLQ_DUPLICATE);
  CHECK(phone_log_queue_end(1,&finish)==PLQ_OK&&drain()==PLQ_OK);
 }else if(mode==5){
  for(i=0;i<63;++i){name[i]=(char)219;number[i]='N';}name[63]=number[63]=0;
  CHECK(phone_log_queue_start(50,name,number,&long_start)==PLQ_OK);
  CHECK(phone_log_queue_end(50,&long_end)==PLQ_OK&&drain()==PLQ_OK);
 }else if(mode==6){
  CHECK(phone_log_queue_start(60,"GUARDS","5550100",&start)==PLQ_OK);
  CHECK(phone_log_queue_inspect(&saved)==PLQ_OK);before=writes;
  CHECK(phone_log_queue_configure(1,"CALLS.FON")==PLQ_ARGUMENT);
  CHECK(phone_log_queue_start(61,"BAD\n","5550100",&start)==PLQ_STATE);
  CHECK(phone_log_queue_end(60,0)==PLQ_ARGUMENT);
  CHECK(phone_log_queue_inspect((phone_log_queue_snapshot *)0xfffe)==PLQ_ARGUMENT);
  for(i=0;i<666;++i)raw[i]=phone_log_queue_store[i];
  for(i=0;i<3;++i){
   words[3+i]=i==0?4:i==1?5:2;
   CHECK(phone_log_queue_poll()==PLQ_STATE);
   for(j=0;j<666;++j)phone_log_queue_store[j]=raw[j];
  }
  words[53]=132;CHECK(phone_log_queue_poll()==PLQ_STATE);
  for(j=0;j<666;++j)phone_log_queue_store[j]=raw[j];
  CHECK(phone_log_queue_inspect(&view)==PLQ_OK&&memcmp(&view,&saved,sizeof(view))==0&&writes==before);
  location=((unsigned long)context[2]<<4)+context[3];base=(unsigned long)context[0]<<4;
  if(location>=base&&location+sizeof(view)<=base+65536UL){
   CHECK(phone_log_queue_inspect((phone_log_queue_snapshot *)(unsigned)(location-base))==PLQ_ARGUMENT);alias=1;
  }
  CHECK(phone_log_queue_end(60,&finish)==PLQ_OK&&drain()==PLQ_OK);
  CHECK(phone_log_queue_inspect(&saved)==PLQ_OK);before=writes;
  CHECK(phone_log_queue_start(61,"BAD\n","5550100",&start)==PLQ_ARGUMENT);
  CHECK(phone_log_queue_inspect(&view)==PLQ_OK&&memcmp(&view,&saved,sizeof(view))==0&&writes==before);
 }else if(mode==7){
  for(i=0;i<sizeof(prm);++i)prm[i]=(unsigned char)(i*37);
  for(j=0;j<4;++j){
   unsigned raw_flag=j==0?0:j==1?1:j==2?256:65535;
   prm[0x1e6]=(unsigned char)raw_flag;prm[0x1e7]=(unsigned char)(raw_flag>>8);memcpy(prm_copy,prm,sizeof(prm));
   CHECK(phone_log_decode_enabled(prm,sizeof(prm),&flag)==PLT_OK&&flag==!!raw_flag);
   CHECK(memcmp(prm,prm_copy,sizeof(prm))==0);
  }
  CHECK(phone_log_queue_configure(0,0)==PLQ_OK);
  CHECK(phone_log_queue_start(1,"IGNORED","5550100",&start)==PLQ_DISABLED&&!writes);
 }else{
  CHECK(phone_log_read_stamp(&now)==PLT_OK&&phone_log_stamp_seconds(&now,&seconds)==PLT_OK);
  CHECK(save("STAMP.BIN",&now,sizeof(now)));
  CHECK(phone_log_queue_start(80,"CLOCK","5550100",&now)==PLQ_OK);
  CHECK(phone_log_queue_end(80,&now)==PLQ_OK&&drain()==PLQ_OK);
 }
 CHECK(phone_log_queue_inspect(&view)==PLQ_OK&&!reentry_failed);
 for(i=0;i<20;++i)CHECK(jft_before[i]==jft[i]);
 context[6]=alias;context[7]=reentry_checks;
 CHECK(save("STATE.BIN",&view,sizeof(view))&&save("CONTEXT.BIN",context,sizeof(context)));
 printf("PASS %u queue assertions\n",checks);return 0;
}
