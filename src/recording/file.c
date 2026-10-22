#include "file.h"
#include <string.h>
static unsigned fail(recording_file *s,unsigned status,unsigned error)
{if(!s->status){s->status=status;s->dos_error=error;}return s->status;}
static unsigned finish_call(recording_file *s)
{s->busy=0;return s->status;}
static unsigned valid_leaf(const char *p,unsigned n)
{
 char stem[9];unsigned i,base=0,ext=0,dot=0,c;
 for(i=0;i<n;++i){
  c=(unsigned char)p[i];
  if(c=='.'){if(dot||!base)return 0;dot=1;continue;}
  if(!((c>='A'&&c<='Z')||(c>='0'&&c<='9')||strchr("!#$%&'()-@^_`{}~",c)))return 0;
  if(dot){if(++ext>3)return 0;}else{if(base==8)return 0;stem[base++]=(char)c;}
 }
 if(!base||(dot&&!ext))return 0;stem[base]=0;
 if(!strcmp(stem,"CON")||!strcmp(stem,"PRN")||!strcmp(stem,"AUX")||!strcmp(stem,"NUL")||!strcmp(stem,"CLOCK$"))return 0;
 return !(base==4&&stem[3]>='1'&&stem[3]<='9'&&(!memcmp(stem,"COM",3)||!memcmp(stem,"LPT",3)));
}
static unsigned path(const char *input,char *out)
{
 unsigned i,start=0,end,c;
 if(!input)return 0;
 for(i=0;i<64;++i){c=(unsigned char)input[i];if(c>='a'&&c<='z')c-=32;if(c=='/')c='\\';out[i]=(char)c;if(!c)break;}
 if(!i||i==64)return 0;
 if(i>=2&&out[1]==':'){if(out[0]<'A'||out[0]>'Z')return 0;start=2;}
 if(out[start]=='\\')++start;
 for(end=start;;++end)if(out[end]=='\\'||!out[end]){
  if(!valid_leaf(out+start,end-start))return 0;
  if(!out[end])break;start=end+1;
 }
 return i>=4&&!strcmp(out+i-4,".ASP");
}
static unsigned canonical(recording_file *s)
{
 unsigned i,c;
 for(i=0;i<128;++i){c=(unsigned char)s->target[i];if(!c)break;if(c>='a'&&c<='z')c-=32;if(c=='/')c='\\';s->target[i]=(char)c;}
 if(i<4||i==128)return 0;
 if(!((s->target[0]>='A'&&s->target[0]<='Z'&&s->target[1]==':'&&s->target[2]=='\\')||
      (s->target[0]=='\\'&&s->target[1]=='\\'&&s->target[2]!='\\')))return 0;
 s->directory_length=0;
 for(c=0;c<i;++c)if(s->target[c]=='\\')s->directory_length=c+1;
 return s->directory_length<=115&&!strcmp(s->target+i-4,".ASP");
}
static void sibling(const recording_file *s,const char *leaf,char *full)
{memcpy(full,s->target,s->directory_length);strcpy(full+s->directory_length,leaf);}
unsigned AR_FAR AR_CALL recording_file_conflict(const recording_file *s,const char *identity)
{
 unsigned i;
 if(!s||!identity)return 1;
 if(!strcmp(identity,s->target))return 1;
 for(i=0;i<s->directory_length;++i)if(!identity[i]||identity[i]!=s->target[i])return 0;
 return (s->stage[0]&&!strcmp(identity+i,s->stage))||(s->backup[0]&&!strcmp(identity+i,s->backup));
}
static void leaf_name(recording_file *s,char *out,const char *extension)
{
 static const char hex[]="0123456789ABCDEF";
 unsigned value,i;
 s->sequence=(s->sequence+1U)&65535U;value=s->sequence;
 memcpy(out,"LPR00000.",9);
 for(i=8;i>3;){--i;out[i]=hex[value&15];value>>=4;}
 memcpy(out+9,extension,3);out[12]=0;
}
static unsigned reserve(recording_file *s)
{unsigned error=s->ops.reserve(s->context,s);if(!error)s->claimed=1;return error;}
static unsigned release(recording_file *s)
{
 unsigned error;
 if(!s->claimed)return 0;
 error=s->ops.release(s->context,s);
 if(error){s->reservation_error=error;fail(s,RF_RELEASE,0);return error;}
 s->claimed=0;return 0;
}
static unsigned AR_FAR AR_CALL sink_write(void *context,const void *data,unsigned count,unsigned *actual)
{
 recording_file *s=context;unsigned error;
 if(s->handle_state!=1){*actual=0;return 6;}
 error=s->ops.write(s->context,s->handle,data,count,actual);
 if(error&&!s->dos_error)s->dos_error=error;
 return error;
}
static unsigned AR_FAR AR_CALL sink_close(void *context)
{
 recording_file *s=context;unsigned error;
 if(s->handle_state!=1)return 6;
 s->handle_state=0;error=s->ops.close(s->context,s->handle);s->close_error=error;
 if(error)s->handle_state=2;
 return error;
}
static void core_error(recording_file *s,unsigned status)
{
 if(status==AR_WRITE)fail(s,RF_WRITE,s->dos_error);
 else if(status==AR_CLOSE)fail(s,RF_CLOSE,s->close_error);
 else if(status==AR_CANCELLED)fail(s,RF_CANCELLED,0);
 else if(status==AR_ARGUMENT)fail(s,RF_OVERFLOW,0); /* Counts and null data already checked. */
 else if(status)fail(s,RF_STATE,0);
}
static unsigned clean(recording_file *s)
{
 char name[128];unsigned error;
 if(s->handle_state==2){s->state=RF_RECOVERY_STATE;return RF_RECOVERY;}
 if(s->handle_state==1)return RF_BUSY;
 if(s->backup_owned&&!s->published){s->state=RF_RECOVERY_STATE;return RF_RECOVERY;}
 if(s->backup_owned){
  sibling(s,s->backup,name);error=s->ops.remove(s->context,name);
  if(error){s->cleanup_error=error;fail(s,RF_CLEANUP,error);s->state=RF_RECOVERY_STATE;return RF_RECOVERY;}
  s->backup_owned=0;
 }
 if(s->stage_owned){
  sibling(s,s->stage,name);error=s->ops.remove(s->context,name);
  if(error){s->cleanup_error=error;fail(s,RF_CLEANUP,error);s->state=RF_RECOVERY_STATE;return RF_RECOVERY;}
  s->stage_owned=0;
 }
 if(release(s)){s->state=RF_RECOVERY_STATE;return RF_RECOVERY;}
 s->state=s->published?RF_SAVED:s->status==RF_CANCELLED?RF_CANCELLED_STATE:RF_FAILED;
 return 0;
}
static void abort_stream(recording_file *s,unsigned status)
{
 core_error(s,status);
 if(s->recorder.owned)core_error(s,aspect_recorder_stop(&s->recorder));
 clean(s);
}
unsigned AR_FAR AR_CALL recording_file_begin(recording_file *s,const recording_file_ops *ops,void *context,const char *name,unsigned mode,unsigned timeout)
{
 recording_file_ops chosen;aspect_recorder_ops sink;
 char input[64],full[128];unsigned sequence,error,attr,tries,status;
 if(!s||!ops)return RF_ARGUMENT;
 if(s->busy)return RF_BUSY;
 if(s->state==RF_RECOVERY_STATE&&(s->handle_state||s->claimed||s->stage_owned||s->backup_owned))return RF_RECOVERY;
 if(s->handle_state||s->claimed||s->stage_owned||s->backup_owned)return RF_BUSY;
 if(!ops->canonical||!ops->attributes||!ops->create||!ops->write||!ops->close||!ops->rename||!ops->remove||!ops->reserve||!ops->release||
    (mode!=RF_NEW&&mode!=RF_REPLACE)||!timeout||timeout>32767||!path(name,input))return RF_ARGUMENT;
 chosen=*ops;sequence=s->sequence;memset(s,0,sizeof(*s));s->ops=chosen;s->sequence=sequence;
 s->context=context;s->mode=mode;s->busy=1;s->handle=-1;
 error=s->ops.canonical(context,input,s->target);
 if(error||!canonical(s)){fail(s,RF_CANONICAL,error?error:13);s->state=RF_FAILED;return finish_call(s);}
 error=reserve(s);
 if(error){s->reservation_error=error;fail(s,RF_BUSY,0);s->state=RF_FAILED;return finish_call(s);}
 error=s->ops.attributes(context,s->target,&attr);
 if((!error&&mode==RF_NEW)||(error&&error!=2)||(!error&&(attr&0x59))){
  fail(s,!error?(mode==RF_NEW?RF_CONFLICT:RF_ARGUMENT):RF_INSPECT,!error?(mode==RF_NEW?80:0):error);clean(s);return finish_call(s);
 }
 for(tries=0;tries<256;++tries){
  leaf_name(s,s->stage,"TMP");if(reserve(s))continue;
  sibling(s,s->stage,full);error=s->ops.create(context,full,&s->handle);
  if(error==80)continue;
  if(error){fail(s,RF_CREATE,error);clean(s);return finish_call(s);}
  s->stage_owned=1;s->handle_state=1;s->state=RF_RECORDING;
  sink.write=sink_write;sink.close=sink_close;
  status=aspect_recorder_start(&s->recorder,&sink,s,timeout);
  if(status)abort_stream(s,status);
  return finish_call(s);
 }
 fail(s,RF_CONFLICT,80);clean(s);return finish_call(s);
}
static unsigned feed(recording_file *s,const void *data,unsigned count,unsigned receive)
{
 unsigned status;
 if(!s)return RF_ARGUMENT;
 if(s->busy)return RF_BUSY;
 if(count>(receive?16U:40U)||(!data&&count))return RF_ARGUMENT;
 if(s->state!=RF_RECORDING)return s->status?s->status:RF_STATE;
 s->busy=1;
 status=receive?aspect_recorder_receive(&s->recorder,data,count):aspect_recorder_transmit(&s->recorder,data,count);
 if(status)abort_stream(s,status);
 return finish_call(s);
}
unsigned AR_FAR AR_CALL recording_file_transmit(recording_file *s,const void *data,unsigned count)
{return feed(s,data,count,0);}
unsigned AR_FAR AR_CALL recording_file_receive(recording_file *s,const void *data,unsigned count)
{return feed(s,data,count,1);}
unsigned AR_FAR AR_CALL recording_file_flush(recording_file *s)
{
 unsigned status;
 if(!s)return RF_ARGUMENT;if(s->busy)return RF_BUSY;
 if(s->state!=RF_RECORDING)return s->status?s->status:RF_STATE;
 s->busy=1;status=aspect_recorder_flush(&s->recorder);if(status)abort_stream(s,status);
 return finish_call(s);
}
static unsigned publish(recording_file *s)
{
 char stage[128],backup[128];unsigned error,attr,tries;
 sibling(s,s->stage,stage);
 error=s->ops.attributes(s->context,s->target,&attr);
 if(error&&error!=2)return fail(s,RF_INSPECT,error);
 if(!error&&s->mode==RF_NEW)return fail(s,RF_CONFLICT,80);
 if(!error){
  if(attr&0x59)return fail(s,RF_ARGUMENT,0);
  for(tries=0;tries<256;++tries){
   leaf_name(s,s->backup,"BAK");if(reserve(s))continue;
   sibling(s,s->backup,backup);error=s->ops.attributes(s->context,backup,&attr);
   if(!error)continue;if(error!=2)return fail(s,RF_INSPECT,error);
   error=s->ops.rename(s->context,s->target,backup);
   if(error==80)continue;
   if(error){s->publish_error=error;return fail(s,RF_PUBLISH,error);}
   s->backup_owned=1;break;
  }
  if(!s->backup_owned)return fail(s,RF_CONFLICT,80);
 }
 error=s->ops.rename(s->context,stage,s->target);
 if(error){
  s->publish_error=error;fail(s,RF_PUBLISH,error);
  if(s->backup_owned){
   sibling(s,s->backup,backup);s->restore_error=s->ops.rename(s->context,backup,s->target);
   if(!s->restore_error)s->backup_owned=0;
  }
  return s->status;
 }
 s->stage_owned=0;s->published=1;
 clean(s);return s->status;
}
unsigned AR_FAR AR_CALL recording_file_stop(recording_file *s)
{
 unsigned status;
 if(!s)return RF_ARGUMENT;if(s->busy)return RF_BUSY;
 if(s->state==RF_SAVED)return s->status;
 if(s->state!=RF_RECORDING)return s->status?s->status:RF_STATE;
 s->busy=1;status=aspect_recorder_stop(&s->recorder);
 if(status)abort_stream(s,status);
 else if(publish(s)){s->state=RF_RECOVERY_STATE;}
 return finish_call(s);
}
unsigned AR_FAR AR_CALL recording_file_cancel(recording_file *s)
{
 if(!s)return RF_ARGUMENT;if(s->busy)return RF_BUSY;
 if(s->state==RF_IDLE)return RF_STATE;
 s->busy=1;
 if(s->recorder.owned)core_error(s,aspect_recorder_cancel(&s->recorder));
 clean(s);return finish_call(s);
}
unsigned AR_FAR AR_CALL recording_file_cleanup(recording_file *s)
{
 if(!s)return RF_ARGUMENT;if(s->busy)return RF_BUSY;
 if(s->state==RF_IDLE)return 0;
 if(s->state==RF_RECORDING)return RF_BUSY;
 s->busy=1;clean(s);return finish_call(s);
}
