#include "recorder.h"
#include <string.h>

/* DOS templates belong to this module's code segment, not scarce DGROUP.
 * Only explicit far reads cross into them; output callbacks still receive
 * ordinary near DS=SS spans with unchanged write boundaries. */
#ifdef __WATCOMC__
#define AR_LITERAL __based(__segname("_CODE"))
#else
#define AR_LITERAL
#endif
static const char AR_LITERAL hex[]="0123456789ABCDEF";
static const char AR_LITERAL tx_prefix[]="transmitraw \"";
static const char AR_LITERAL rx_prefix[]="strcpy loc_prompt \"";
static const char AR_LITERAL poke_prefix[]="strpoke loc_prompt ";
static const char AR_LITERAL poke_quote[]=" 34\r\n";
static const char AR_LITERAL wait_prefix[]="waitfor loc_prompt ";
static const char AR_LITERAL timeout_guard[]="if waitfor == 0\r\nexit\r\nendif\r\n";
static const char AR_LITERAL record_header[]="; LoC ASPECT recording - maintained runtime required\r\nstring loc_prompt\r\nproc main\r\n";
static const char AR_LITERAL record_footer[]="endproc\r\n";
static void literal_copy(char *to,const char AR_FAR *from,unsigned count)
{unsigned i;for(i=0;i<count;++i)to[i]=from[i];}

static unsigned enter(aspect_recorder *s)
{
 if(!s||!s->active||!s->owned||s->busy)return AR_STATE;
 if(s->status)return s->status;
 s->busy=1;return AR_OK;
}
static unsigned leave(aspect_recorder *s)
{s->busy=0;return s->status;}
static unsigned write_bytes(aspect_recorder *s,const char *data,unsigned count)
{
 unsigned actual,error;
 if(s->source_bytes>0xffffffffUL-count){s->status=AR_WRITE;return s->status;}
 while(count&&!s->status){
  actual=0;error=s->ops.write(s->context,data,count,&actual);
  if(error||!actual||actual>count){s->status=AR_WRITE;s->write_error=error;break;}
  s->source_bytes+=actual;data+=actual;count-=actual;
 }
 return s->status;
}
static unsigned text(aspect_recorder *s,const char AR_FAR *data,unsigned count)
{
 char bytes[sizeof(record_header)-1];
 literal_copy(bytes,data,count);return write_bytes(s,bytes,count);
}
static unsigned decimal(unsigned value,char *out)
{
 char reverse[5];unsigned count=0,i;
 do{reverse[count++]=(char)('0'+value%10);value/=10;}while(value);
 for(i=0;i<count;++i)out[i]=reverse[count-1-i];
 return count;
}
static unsigned flush_tx(aspect_recorder *s)
{
 char line[97];unsigned i,n=13;
 if(!s->tx_count)return s->status;
 literal_copy(line,tx_prefix,13);
 for(i=0;i<s->tx_count;++i){line[n++]=hex[s->tx[i]>>4];line[n++]=hex[s->tx[i]&15];}
 line[n++]='"';line[n++]=13;line[n++]=10;
 if(!write_bytes(s,line,n))s->tx_count=0;
 return s->status;
}
static unsigned folded(unsigned c)
{return c>='a'&&c<='z'?c-32:c;}
/* Native WAITFOR falls back only to zero/one matched byte. For every proper
 * border of a prefix, extending that border with a different next byte would
 * require a longer fallback. Select the longest observed suffix without such
 * a case; preserve the native matcher rather than generating a prompt it can
 * miss. Pure repeated-byte prompts are safe and retain their full length. */
static unsigned prompt_start(const unsigned char *bytes,unsigned count)
{
 unsigned char prefix[16];unsigned start,size,i,j;
 for(start=0;start<count;++start){
  size=count-start;prefix[0]=0;
  for(i=1;i<size;++i){
   j=prefix[i-1];
   while(j&&folded(bytes[start+i])!=folded(bytes[start+j]))j=prefix[j-1];
   if(folded(bytes[start+i])==folded(bytes[start+j]))++j;
   prefix[i]=(unsigned char)j;
  }
  for(i=1;i<size;++i)
   for(j=prefix[i-1];j;j=prefix[j-1])
    if(folded(bytes[start+j])!=folded(bytes[start+i]))goto unsafe;
  return start;
unsafe:;
 }
 return start;
}
static unsigned flush_rx(aspect_recorder *s)
{
 char encoded[49],line[100];unsigned i,n=0,at=0,has_text=0,leading=1,c,len;
 unsigned char raw[16];unsigned raw_count=0;
 unsigned quotes[16],quote_count=0;
 if(!s->rx_count)return s->status;
 for(i=0;i<s->rx_count;++i)if(s->rx[i]>32)has_text=1;
 for(i=0;i<s->rx_count;++i){
  c=s->rx[i];if(!c)continue;
  if(has_text&&leading&&c<32)continue;
  leading=0;
  raw[raw_count++]=(unsigned char)c;
 }
 for(i=prompt_start(raw,raw_count);i<raw_count;++i){
  c=raw[i];
  if(c<32){encoded[n++]='^';encoded[n++]=(char)(c==30?'~':c+64);}
  else if(c=='^'){encoded[n++]='^';encoded[n++]='^';encoded[n++]='^';}
  else{
   if(c=='"'){quotes[quote_count++]=n;c='?';}
   encoded[n++]=(char)c;
  }
 }
 if(!n){s->rx_count=0;return AR_OK;}
 literal_copy(line,rx_prefix,19);at=19;
 memcpy(line+at,encoded,n);at+=n;line[at++]='"';line[at++]=13;line[at++]=10;
 if(write_bytes(s,line,at))return s->status;
 for(i=0;i<quote_count;++i){
  literal_copy(line,poke_prefix,19);at=19;at+=decimal(quotes[i],line+at);
  literal_copy(line+at,poke_quote,5);at+=5;
  if(write_bytes(s,line,at))return s->status;
 }
 literal_copy(line,wait_prefix,19);len=19;
 len+=decimal(s->timeout,line+len);line[len++]=13;line[len++]=10;
 if(write_bytes(s,line,len)||text(s,timeout_guard,sizeof(timeout_guard)-1))return s->status;
 s->rx_count=0;return AR_OK;
}
unsigned AR_FAR AR_CALL aspect_recorder_start(aspect_recorder *s,const aspect_recorder_ops *ops,void *context,unsigned timeout)
{
 aspect_recorder_ops selected;
 if(!s||!ops||!ops->write||!ops->close||!timeout||timeout>32767)return AR_ARGUMENT;
 if(s->owned||s->busy||s->active)return AR_STATE;
 selected=*ops;memset(s,0,sizeof(*s));s->ops=selected;s->context=context;s->timeout=timeout;
 s->started=s->active=s->owned=s->busy=1;
 text(s,record_header,sizeof(record_header)-1);
 return leave(s);
}
unsigned AR_FAR AR_CALL aspect_recorder_transmit(aspect_recorder *s,const void *data,unsigned count)
{
 const unsigned char *bytes=data;unsigned error,i;
 if(count>40||(!data&&count))return AR_ARGUMENT;
 error=enter(s);if(error)return error;
 if(count&&s->transmitted_bytes>0xffffffffUL-count){s->busy=0;return AR_ARGUMENT;}
 if(count&&!flush_rx(s))for(i=0;i<count&&!s->status;++i){
  s->tx[s->tx_count++]=bytes[i];++s->transmitted_bytes;
  if(s->tx_count==40)flush_tx(s);
 }
 return leave(s);
}
unsigned AR_FAR AR_CALL aspect_recorder_receive(aspect_recorder *s,const void *data,unsigned count)
{
 const unsigned char *bytes=data;unsigned error,i;
 if(count>16||(!data&&count))return AR_ARGUMENT;
 error=enter(s);if(error)return error;
 if(count&&s->received_bytes>0xffffffffUL-count){s->busy=0;return AR_ARGUMENT;}
 if(count&&!flush_tx(s))for(i=0;i<count;++i){
  if(s->rx_count==16){memmove(s->rx,s->rx+1,15);--s->rx_count;}
  s->rx[s->rx_count++]=bytes[i];++s->received_bytes;
 }
 return leave(s);
}
unsigned AR_FAR AR_CALL aspect_recorder_flush(aspect_recorder *s)
{unsigned error=enter(s);if(error)return error;flush_tx(s);return leave(s);}
static unsigned finish(aspect_recorder *s,unsigned cancel)
{
 unsigned close_error;
 if(!s||!s->started||s->busy)return AR_STATE;
 if(!s->owned)return s->active?AR_STATE:s->status;
 s->busy=1;
 if(!s->status){
  if(cancel)s->status=AR_CANCELLED;
  else if(!flush_tx(s)){
   /* Received bytes gate a following user action, never an otherwise complete
    * recording's exit. The resumed terminal renders the final response. */
   s->rx_count=0;text(s,record_footer,sizeof(record_footer)-1);
  }
 }
 s->owned=s->active=0;close_error=s->ops.close(s->context);s->close_error=close_error;
 if(close_error&&!s->status)s->status=AR_CLOSE;
 return leave(s);
}
unsigned AR_FAR AR_CALL aspect_recorder_stop(aspect_recorder *s)
{return finish(s,0);}
unsigned AR_FAR AR_CALL aspect_recorder_cancel(aspect_recorder *s)
{return finish(s,1);}
