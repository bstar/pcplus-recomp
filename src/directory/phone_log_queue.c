#include "phone_log_queue.h"
#include "phone_log_file.h"
#if defined(PHONE_LOG_HOST)
#include <stdint.h>
#define QFAR
typedef uintptr_t span_value;
#else
#include <dos.h>
typedef unsigned long span_value;
#if defined(PHONE_LOG_QUEUE_FAR)
#define QFAR __far
#else
#define QFAR
#endif
static unsigned data_segment(void);
#pragma aux data_segment = "mov ax,ds" value [ax] modify exact [];
#endif
typedef struct queued_record {unsigned count,kind;unsigned long generation;char text[PHONE_LOG_TEXT_CAPACITY];} queued_record;
typedef struct queue_store {
 unsigned cookie,busy,enabled,head,count,active,retry,recovery,file_status;
 unsigned long last_started,last_ended,committed;
 phone_log_stamp started;
 char path[64];
 queued_record records[PHONE_LOG_QUEUE_CAPACITY];
} queue_store;
#if !defined(PHONE_LOG_HOST)
typedef char plq_store666[sizeof(queue_store)==666?1:-1];
typedef char plq_snapshot24[sizeof(phone_log_queue_snapshot)==24?1:-1];
#endif
/* Initialized DATA, not a near BSS assumption. The far build keeps the entire
 * private event/path/timestamp owner outside DGROUP without changing DS/SS. */
queue_store QFAR phone_log_queue_store={0x514c};
#define owner phone_log_queue_store
static unsigned extent(const void *p,unsigned n)
{
 if(!p)return 0;
#if defined(PHONE_LOG_HOST)
 return (uintptr_t)p<=UINTPTR_MAX-n;
#else
 return (unsigned long)(unsigned)p+n<=65536UL;
#endif
}
static span_value near_address(const void *p)
{
#if defined(PHONE_LOG_HOST)
 return (uintptr_t)p;
#else
 return ((unsigned long)data_segment()<<4)+(unsigned)p;
#endif
}
static unsigned safe(const void *p,unsigned n)
{
 span_value a,b;
 if(!extent(p,n))return 0;a=near_address(p);
#if defined(PHONE_LOG_HOST)
 b=(uintptr_t)&owner;
#else
 b=((unsigned long)FP_SEG((void __far *)&owner)<<4)+FP_OFF((void __far *)&owner);
#endif
 return a+n<=b||b+sizeof(owner)<=a;
}
static unsigned bootstrap(void)
{
 unsigned i;queued_record QFAR *record;unsigned char QFAR *bytes=(unsigned char QFAR *)&owner;
 if(owner.busy)return PLQ_BUSY;
 if(owner.cookie==0x514c){for(i=0;i<sizeof(owner);++i)bytes[i]=0;owner.cookie=0x514d;}
 if(owner.cookie!=0x514d)return PLQ_STATE;
 if(owner.enabled>1||owner.head>=PHONE_LOG_QUEUE_CAPACITY||owner.count>PHONE_LOG_QUEUE_CAPACITY||
    owner.active>1||owner.retry>1||owner.recovery>1||(owner.active&&!owner.last_started)||
    (owner.count&&!owner.enabled))return PLQ_STATE;
 for(i=0;i<owner.count;++i){
  record=&owner.records[(owner.head+i)%PHONE_LOG_QUEUE_CAPACITY];
  if(!record->count||record->count>=PHONE_LOG_TEXT_CAPACITY||(record->kind!=1&&record->kind!=2)||
     !record->generation||record->text[record->count])return PLQ_STATE;
 }
 return PLQ_OK;
}
unsigned __cdecl phone_log_queue_initialize(void)
{unsigned status=bootstrap();return status?status:owner.recovery?PLQ_RECOVERY:PLQ_OK;}
static unsigned copy_path(const char *path,char *out)
{
 unsigned n;
 for(n=0;n<64;++n){
  if(!safe(path,n+1))return 0;out[n]=path[n];
  if(out[n]>='a'&&out[n]<='z')out[n]-=32;if(out[n]=='/')out[n]='\\';
  if(!out[n])return n>=3&&out[0]>='A'&&out[0]<='Z'&&out[1]==':'&&out[2]=='\\';
 }
 return 0;
}
unsigned __cdecl phone_log_queue_configure(unsigned enabled,const char *path)
{
 char candidate[64];unsigned i,status,same=1;
 status=phone_log_queue_initialize();if(status)return status;enabled=!!enabled;
 if(enabled){if(!copy_path(path,candidate)||!phone_log_file_validate_path(candidate))return PLQ_ARGUMENT;}
 else candidate[0]=0;
 for(i=0;i<64;++i){if(owner.path[i]!=candidate[i]){same=0;break;}if(!candidate[i])break;}
 if(owner.active||owner.count)return owner.enabled==enabled&&same?PLQ_OK:PLQ_BUSY;
 status=phone_log_file_initialize();if(status){owner.file_status=status;return status==PLF_RECOVERY?PLQ_RECOVERY:PLQ_FILE;}
 for(i=0;i<64;++i){owner.path[i]=candidate[i];if(!candidate[i])break;}
 owner.enabled=enabled;return PLQ_OK;
}
static unsigned enqueue(unsigned kind,unsigned long generation,const char *text,unsigned count)
{
 unsigned tail=(owner.head+owner.count)%PHONE_LOG_QUEUE_CAPACITY,i;
 queued_record QFAR *record=&owner.records[tail];
 if(owner.count==PHONE_LOG_QUEUE_CAPACITY)return PLQ_FULL;
 for(i=0;i<=count;++i)record->text[i]=text[i];
 record->count=count;record->kind=kind;record->generation=generation;++owner.count;return PLQ_OK;
}
static unsigned generation_valid(unsigned long generation)
{
#if defined(PHONE_LOG_HOST)
 if(generation>0xffffffffUL)return 0;
#endif
 return generation!=0;
}
unsigned __cdecl phone_log_queue_start(unsigned long generation,const char *name,const char *number,const phone_log_stamp *stamp)
{
 char text[PHONE_LOG_TEXT_CAPACITY];unsigned status,count,names,numbers,i;unsigned long distance;
 status=phone_log_queue_initialize();if(status)return status;
 if(!owner.enabled)return PLQ_DISABLED;
 if(!generation_valid(generation))return PLQ_ARGUMENT;
 if(generation==owner.last_started)return PLQ_DUPLICATE;
 if(owner.active)return PLQ_STATE;
 if(owner.last_started){distance=(generation-owner.last_started)&0xffffffffUL;if(distance>=0x80000000UL)return PLQ_STATE;}
 if(!safe(stamp,sizeof(*stamp)))return PLQ_ARGUMENT;
 for(names=0;names<64;++names){if(!safe(name,names+1))return PLQ_ARGUMENT;if(!name[names])break;}
 for(numbers=0;numbers<64;++numbers){if(!safe(number,numbers+1))return PLQ_ARGUMENT;if(!number[numbers])break;}
 if(names==64||numbers==64)return PLQ_ARGUMENT;
 status=phone_log_format_start(name,number,stamp,text,sizeof(text),&count);
 if(status)return status==PLT_CLOCK?PLQ_CLOCK:PLQ_ARGUMENT;
 status=enqueue(1,generation,text,count);if(status)return status;
 for(i=0;i<6;++i)((unsigned QFAR *)&owner.started)[i]=((const unsigned *)stamp)[i];
 owner.last_started=generation;owner.active=1;return PLQ_OK;
}
unsigned __cdecl phone_log_queue_end(unsigned long generation,const phone_log_stamp *stamp)
{
 char text[PHONE_LOG_TEXT_CAPACITY];phone_log_stamp start;unsigned status,count,i;
 status=phone_log_queue_initialize();if(status)return status;
 if(!owner.enabled)return PLQ_DISABLED;
 if(!generation_valid(generation))return PLQ_ARGUMENT;
 if(generation==owner.last_ended)return PLQ_DUPLICATE;
 if(!owner.active||generation!=owner.last_started)return PLQ_STATE;
 if(!safe(stamp,sizeof(*stamp)))return PLQ_ARGUMENT;
 for(i=0;i<6;++i)((unsigned *)&start)[i]=((const unsigned QFAR *)&owner.started)[i];
 status=phone_log_format_end(&start,stamp,text,sizeof(text),&count);
 if(status)return status==PLT_CLOCK?PLQ_CLOCK:PLQ_ARGUMENT;
 status=enqueue(2,generation,text,count);if(status)return status;
 owner.last_ended=generation;owner.active=0;return PLQ_OK;
}
unsigned __cdecl phone_log_queue_poll(void)
{
 char path[64],text[PHONE_LOG_TEXT_CAPACITY];unsigned status,count,i;
 queued_record QFAR *record;
 status=phone_log_queue_initialize();if(status)return status;
 if(owner.retry)return PLQ_RETRY;
 if(!owner.count)return PLQ_OK;
 owner.busy=1;record=&owner.records[owner.head];count=record->count;
 for(i=0;i<64;++i){path[i]=owner.path[i];if(!path[i])break;}
 for(i=0;i<count;++i)text[i]=record->text[i];
 status=phone_log_file_append(path,phone_log_heading,phone_log_heading_count,text,count);
 owner.file_status=status;
 if(!status&&phone_log_file_result.committed){
  for(i=0;i<PHONE_LOG_TEXT_CAPACITY;++i)record->text[i]=0;
  record->count=record->kind=0;record->generation=0;
  owner.head=(owner.head+1)%PHONE_LOG_QUEUE_CAPACITY;--owner.count;owner.committed=(owner.committed+1)&0xffffffffUL;
 }else{
  if(!status)owner.file_status=PLF_STATE;
  owner.retry=1;
  if(phone_log_file_result.recovery_required)owner.recovery=1;
 }
 owner.busy=0;
 return owner.recovery?PLQ_RECOVERY:owner.retry?PLQ_FILE:PLQ_OK;
}
unsigned __cdecl phone_log_queue_retry(void)
{
 unsigned status=phone_log_queue_initialize();if(status)return status;
 if(!owner.retry)return PLQ_STATE;
 status=phone_log_file_initialize();
 if(status){owner.file_status=status;if(status==PLF_RECOVERY)owner.recovery=1;return owner.recovery?PLQ_RECOVERY:PLQ_FILE;}
 owner.retry=0;return PLQ_OK;
}
unsigned __cdecl phone_log_queue_inspect(phone_log_queue_snapshot *out)
{
 unsigned status=bootstrap();if(status)return status;
 if(!safe(out,sizeof(*out)))return PLQ_ARGUMENT;
 out->enabled=owner.enabled;out->active=owner.active;out->queued=owner.count;
 out->retry_required=owner.retry;out->recovery_required=owner.recovery;out->file_status=owner.file_status;
 out->last_started=owner.last_started;out->last_ended=owner.last_ended;out->committed_events=owner.committed;
 return PLQ_OK;
}
