#include "phone_log_lifecycle.h"
typedef struct lifecycle_owner {
 unsigned cookie;
 unsigned long generation;
 unsigned active,pending,busy,pending_status;
 phone_log_stamp started,ended;
} lifecycle_owner;
/* Explicit initialized DATA; no DOS BSS-zero assumption. */
lifecycle_owner phone_log_lifecycle_store={0x4c45};
#define owner phone_log_lifecycle_store
typedef char lifecycle_owner38[sizeof(lifecycle_owner)==38?1:-1];
typedef char lifecycle_snapshot10[sizeof(phone_log_lifecycle_snapshot)==10?1:-1];
static unsigned safe(const void *p,unsigned n)
{
 unsigned long a=(unsigned)p,b=(unsigned)&owner;
 return p&&a+n<=65536UL&&(a+n<=b||b+sizeof(owner)<=a);
}
static unsigned enter(void)
{
 if(owner.busy)return PLQ_BUSY;
 if(owner.cookie!=0x4c45||owner.active>1||owner.pending>1||
    (owner.pending&&!owner.active)||(owner.active&&!owner.generation))return PLQ_STATE;
 owner.busy=1;return PLQ_OK;
}
static unsigned leave(unsigned status){owner.busy=0;return status;}
static unsigned ready(void)
{
 phone_log_queue_snapshot view;unsigned status;
 if(owner.pending)return PLQ_BUSY;
 if(owner.active)return PLQ_STATE;
 status=phone_log_queue_inspect(&view);if(status)return status;
 if(!view.enabled)return PLQ_DISABLED;
 if(view.recovery_required)return PLQ_RECOVERY;
 if(view.retry_required)return PLQ_RETRY;
 if(view.active||view.last_started!=owner.generation)return PLQ_STATE;
 return view.queued>PHONE_LOG_QUEUE_CAPACITY-2U?PLQ_FULL:PLQ_OK;
}
unsigned __cdecl phone_log_lifecycle_ready(void)
{unsigned status=enter();if(status)return status;return leave(ready());}
unsigned __cdecl phone_log_lifecycle_begin(const char *name,const char *number,const phone_log_stamp *stamp)
{
 unsigned status,i;unsigned long generation;phone_log_stamp captured;
 status=enter();if(status)return status;
 if(owner.pending)return leave(PLQ_BUSY);
 if(owner.active)return leave(PLQ_DUPLICATE);
 status=ready();if(status)return leave(status);
 if(!safe(stamp,sizeof(*stamp)))return leave(PLQ_ARGUMENT);
 for(i=0;i<6;++i)((unsigned *)&captured)[i]=((const unsigned *)stamp)[i];
 generation=owner.generation+1UL;if(!generation)generation=1;
 status=phone_log_queue_start(generation,name,number,&captured);
 if(!status){owner.generation=generation;owner.active=1;owner.started=captured;}
 return leave(status);
}
unsigned __cdecl phone_log_lifecycle_end(const phone_log_stamp *stamp)
{
 unsigned status,count,i;char text[PHONE_LOG_TEXT_CAPACITY];phone_log_stamp captured;
 status=enter();if(status)return status;
 if(owner.pending)return leave(PLQ_DUPLICATE);
 if(!owner.active)return leave(owner.generation?PLQ_DUPLICATE:PLQ_STATE);
 if(!safe(stamp,sizeof(*stamp)))return leave(PLQ_ARGUMENT);
 for(i=0;i<6;++i)((unsigned *)&captured)[i]=((const unsigned *)stamp)[i];
 status=phone_log_format_end(&owner.started,&captured,text,sizeof(text),&count);
 if(status)return leave(status==PLT_CLOCK?PLQ_CLOCK:PLQ_ARGUMENT);
 status=phone_log_queue_end(owner.generation,&captured);
 if(!status){owner.active=0;owner.pending_status=0;return leave(PLQ_OK);}
 owner.ended=captured;owner.pending=1;owner.pending_status=status;
 return leave(PLL_PENDING);
}
unsigned __cdecl phone_log_lifecycle_service(void)
{
 unsigned status=enter();if(status)return status;
 if(!owner.pending)return leave(PLQ_OK);
 status=phone_log_queue_end(owner.generation,&owner.ended);
 owner.pending_status=status;
 if(!status)owner.active=owner.pending=0;
 return leave(status);
}
unsigned __cdecl phone_log_lifecycle_inspect(phone_log_lifecycle_snapshot *out)
{
 unsigned status=enter();if(status)return status;
 if(!safe(out,sizeof(*out)))return leave(PLQ_ARGUMENT);
 out->generation=owner.generation;out->active=owner.active;
 out->pending=owner.pending;out->pending_status=owner.pending_status;
 return leave(PLQ_OK);
}
