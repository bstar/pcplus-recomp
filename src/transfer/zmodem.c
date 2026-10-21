#include "zmodem.h"
#include <string.h>
#define LIMIT 10
enum { ZRQINIT=0,ZRINIT=1,ZSINIT=2,ZACK=3,ZFILE=4,ZSKIP=5,ZNAK=6,
 ZABORT=7,ZFIN=8,ZRPOS=9,ZDATA=10,ZEOF=11,ZFERR=12,ZCRC=13,
 ZCHALLENGE=14,ZCOMPL=15,ZCAN=16,ZFREECNT=17,ZCOMMAND=18 };
static unsigned fail(zm_session *s,unsigned status)
{if(!s->status)s->status=status;return status;}
static unsigned put(zm_session *s,const void *p,unsigned n)
{
 unsigned r=s->ops->write_wire(s->context,p,n);
 return r?fail(s,r==ZM_ABORT?ZM_CANCEL:ZM_IO):0;
}
static unsigned event_for(zm_session *s,unsigned seconds)
{
 unsigned i,r,v;
 for(i=0;i<32768U;++i){
  /* A peer may purge for one second after ZRPOS. A one-second read here can
   * repeatedly expire during that purge and provoke a recovery livelock. */
  v=s->ops->read_byte(s->context,seconds);
  if(v==ZM_WAIT)return ZM_WAIT;
  if(v>255){fail(s,v==ZM_ABORT?ZM_CANCEL:ZM_IO);return ZM_BROKEN;}
  r=zw_feed(&s->decoder,v);
  if(r==ZW_CANCEL){fail(s,ZM_CANCEL);return ZM_BROKEN;}
  if(r)return r;
 }
 return ZW_FORMAT;
}
static unsigned event(zm_session *s){return event_for(s,3);}
static zw_u32 position(zm_session *s)
{
 unsigned char *h=s->decoder.header;
 return (zw_u32)h[1]|((zw_u32)h[2]<<8)|((zw_u32)h[3]<<16)|((zw_u32)h[4]<<24);
}
static unsigned header(zm_session *s,unsigned type,zw_u32 pos,unsigned fmt)
{
 unsigned char h[5];unsigned n;
 h[0]=(unsigned char)type;h[1]=(unsigned char)pos;h[2]=(unsigned char)(pos>>8);
 h[3]=(unsigned char)(pos>>16);h[4]=(unsigned char)(pos>>24);
 n=zw_header_encode(fmt,h,s->control,s->io.wire,sizeof(s->io.wire));
 return n?put(s,s->io.wire,n):fail(s,ZM_PROTOCOL);
}
static unsigned data(zm_session *s,unsigned n,unsigned ending)
{
 unsigned length=zw_data_encode(s->format,s->data,n,ending,s->control,s->io.wire,sizeof(s->io.wire));
 return length?put(s,s->io.wire,length):fail(s,ZM_PROTOCOL);
}
static unsigned receive_init(zm_session *s)
/* A finite credit matches the actual packet workspace. Unlimited overlap lets
 * a fast TCP peer queue retransmissions/EOF ahead of a slow DOS receiver's
 * replies, even when the UART honors RTS. Request a checkpoint within8KiB. */
{return header(s,ZRINIT,0x23002000UL,ZW_HEX);}
/* A slow bridge can still hold timeout-driven data retransmissions when our
 * checked EOF/ZRINIT reaches the sender. The file is already installed: consume
 * those CRC-framed, in-range bytes without reopening, writing or acknowledging
 * them. ZNAK replies here can exhaust the sender's closing attempts and then
 * become keyboard input after its external helper retires. No discarded byte
 * advances position/files or the live accepted-progress watchdog. */
static unsigned completed_replay(zm_session *s,zw_u32 at)
{
 unsigned r,count,ending;
 zw_data(&s->decoder);
 for(;;){
  r=event(s);
  if(r!=ZW_DATA)return s->status?s->status:fail(s,ZM_PROTOCOL);
  count=s->decoder.count;ending=s->decoder.ending;
  if(at>s->position || count>s->position-at)return fail(s,ZM_PROTOCOL);
  at+=count;
  if(ending==ZW_CRCE || ending==ZW_CRCW)return 0;
  if(!count)return fail(s,ZM_PROTOCOL);
 }
}
static unsigned finish(zm_session *s)
{
 unsigned i,r,v,previous=0,closing=0;
 zw_headers(&s->decoder);
 if(!s->sending){
  if(header(s,ZFIN,0,ZW_HEX))return s->status;
  /* The sender may have queued closing retries before our ZFIN crosses the
   * slow carrier. Drain bounded, CRC-valid ZFIN/ZABORT headers before literal
   * OO, not32 raw bytes followed by leaked protocol text. SEXYZ alternates the
   * two headers during get_zfin; an initial abort outside this closing state
   * remains fatal. Send one response, avoiding a second command-input tail
   * after the peer has already accepted it. Per-byte idle and total bounds
   * still report an unconfirmed finish if OO never arrives. */
  for(i=0;i<512;++i){
   v=s->ops->read_byte(s->context,1);
   if(v==ZM_WAIT)return fail(s,ZM_END_UNCONFIRMED);
   if(v==ZM_ABORT || v==ZM_BROKEN)return fail(s,v==ZM_ABORT?ZM_CANCEL:ZM_IO);
   if((v&127)==17 || (v&127)==19)continue;
   if(previous=='O')return v=='O'?0:fail(s,ZM_END_UNCONFIRMED);
   if(s->decoder.phase==0){
    if(v=='O'){previous=v;continue;}
    if(v!=42 && v!=24 && v!=13 && v!=10)return fail(s,ZM_END_UNCONFIRMED);
   }
   r=zw_feed(&s->decoder,v);
   if(r==ZW_CANCEL)return fail(s,ZM_CANCEL);
   if(r==ZW_HEADER){
    if((s->decoder.header[0]!=ZFIN && s->decoder.header[0]!=ZABORT) || position(s)!=0 || ++closing>=LIMIT)
     return fail(s,ZM_END_UNCONFIRMED);
   }else if(r!=ZW_MORE)return fail(s,ZM_END_UNCONFIRMED);
  }
  return fail(s,ZM_END_UNCONFIRMED);
 }
 for(i=0;i<LIMIT && !s->status;++i){
  if(header(s,ZFIN,0,ZW_HEX))break;
  r=event(s);
  if(r==ZW_HEADER && s->decoder.header[0]==ZFIN)return put(s,"OO",2);
  zw_headers(&s->decoder);
 }
 return s->status?s->status:fail(s,ZM_TIMEOUT);
}
static unsigned receive(zm_session *s)
{
 unsigned r,type,count,ending,same;batch_header_result meta;
 if(receive_init(s))return s->status;
 while(!s->status && s->retries<LIMIT){
  s->phase=1;r=event(s);
  if(r!=ZW_HEADER){
   if(s->status)break;++s->retries;zw_headers(&s->decoder);
   if(s->owned)header(s,ZRPOS,s->position,ZW_HEX);else receive_init(s);
   continue;
  }
  type=s->decoder.header[0];
  if(type==ZFIN){if(s->owned)return fail(s,ZM_PROTOCOL);return finish(s);}
  if(type==ZABORT || type==ZFERR || type==ZCAN)return fail(s,ZM_CANCEL);
  if(type==ZCHALLENGE){header(s,ZACK,position(s),ZW_HEX);++s->retries;continue;}
  if(type==ZRQINIT){receive_init(s);++s->retries;continue;}
  if(type==ZFILE || type==ZSINIT){
   if(type==ZSINIT && (s->decoder.header[4]&64))s->decoder.control=1;
   zw_data(&s->decoder);r=event(s);
   if(r!=ZW_DATA || s->decoder.ending!=ZW_CRCW){
    if(s->status)break;++s->retries;zw_headers(&s->decoder);header(s,ZNAK,0,ZW_HEX);continue;
   }
   if(type==ZSINIT){header(s,ZACK,0,ZW_HEX);++s->retries;continue;}
   count=s->decoder.count;
   if(count>1024)return fail(s,ZM_PROTOCOL);
   if(zm_name_decode(s->io.rx,count,s->data,&meta)!=BH_OK || meta.kind!=BH_FILE)return fail(s,ZM_PROTOCOL);
   same=!strcmp(s->name,(const char *)s->io.rx);
   if(s->owned){
    if(!same)return fail(s,ZM_PROTOCOL);
   }else{
    /* Retain identity before a callback or response reuses the wire arena. */
    strcpy(s->name,(const char *)s->io.rx);
    s->owned=1;r=s->ops->open_received(s->context,&meta);
    if(r==ZM_DONE){
     s->owned=0;if(s->skipped!=0xffffU)++s->skipped;
     if(same)++s->retries;else s->retries=0;
     header(s,ZSKIP,0,ZW_HEX);continue;
    }
    if(r)return fail(s,ZM_FILE);
    s->owned=1;s->position=0;s->size=meta.size;s->retries=0;
   }
   header(s,ZRPOS,s->position,ZW_HEX);continue;
  }
  if(type==ZEOF){
   if(!s->owned || position(s)!=s->position){++s->retries;if(s->owned)header(s,ZRPOS,s->position,ZW_HEX);else receive_init(s);continue;}
   if(s->files==0xffffffffUL || 0xffffffffUL-s->bytes<s->position)return fail(s,ZM_PROTOCOL);
   if(s->ops->commit_received(s->context))return fail(s,ZM_FILE);
   s->owned=0;++s->files;s->bytes+=s->position;s->retries=0;receive_init(s);continue;
  }
  if(type==ZDATA && !s->owned && s->files && position(s)<=s->position){
   ++s->retries;
   if(completed_replay(s,position(s)))return s->status;
   continue;
  }
  if(type!=ZDATA || !s->owned || position(s)!=s->position){
   ++s->retries;zw_headers(&s->decoder);
   if(s->owned)header(s,ZRPOS,s->position,ZW_HEX);else header(s,ZNAK,0,ZW_HEX);
   continue;
  }
  zw_data(&s->decoder);
  for(;;){
   s->phase=2;r=event(s);
   if(r!=ZW_DATA){
    if(s->status)break;++s->retries;zw_headers(&s->decoder);header(s,ZRPOS,s->position,ZW_HEX);break;
   }
   count=s->decoder.count;ending=s->decoder.ending;
   if(0xffffffffUL-s->position<count)return fail(s,ZM_PROTOCOL);
   if(count && s->ops->write_received(s->context,s->io.rx,count))return fail(s,ZM_FILE);
   s->position+=count;
   if(count)s->retries=0;else if(++s->retries==LIMIT)return fail(s,ZM_PROTOCOL);
   if(ending==ZW_CRCQ || ending==ZW_CRCW)header(s,ZACK,s->position,ZW_HEX);
   if(s->status || ending==ZW_CRCE || ending==ZW_CRCW)break;
  }
 }
 return s->status?s->status:fail(s,ZM_TIMEOUT);
}
static void negotiate(zm_session *s)
{
 unsigned char *h=s->decoder.header;unsigned capacity=(unsigned)h[1]|((unsigned)h[2]<<8);
 s->format=(h[4]&32)?ZW_BIN32:ZW_BIN16;s->control=(h[4]&64)?1:0;
 s->block=capacity && capacity<1024?capacity:1024;
 s->capacity=capacity;
 s->window=(h[4]&3)==3?(capacity && capacity<8192?capacity:8192):s->block;
}
static unsigned seek(zm_session *s,zw_u32 pos)
{
 if(pos>s->size)return fail(s,ZM_PROTOCOL);
 if(s->ops->seek(s->context,pos))return fail(s,ZM_FILE);
 s->position=pos;return 0;
}
static unsigned source_crc(zm_session *s,zw_u32 length)
{
 zw_u32 crc=0xffffffffUL,left;unsigned n,got,i,j;
 if(length>s->size)return fail(s,ZM_PROTOCOL);
 if(!length)length=s->size;
 if(s->ops->seek(s->context,0))return fail(s,ZM_FILE);
 for(left=length;left;left-=n){
  n=left>1024?1024:(unsigned)left;
  if(s->ops->read_file(s->context,s->data,n,&got) || got!=n)return fail(s,ZM_FILE);
  for(i=0;i<n;++i){crc^=s->data[i];for(j=0;j<8;++j)crc=(crc>>1)^((crc&1)?0xedb88320UL:0);}
 }
 if(s->ops->seek(s->context,s->position))return fail(s,ZM_FILE);
 return header(s,ZCRC,crc^0xffffffffUL,ZW_HEX);
}
static unsigned offer(zm_session *s)
{
 unsigned r,type;
 s->phase=0;
 for(s->retries=0;s->retries<LIMIT && !s->status;++s->retries){
  if(batch_header_encode(s->name,13,s->size,s->data,128)!=BH_OK)return fail(s,ZM_FILE);
  /* No source timestamp is available through this ABI. Advertise unknown
   * explicitly: some SEXYZ receivers use an uninitialized date when the
   * optional field is absent. Keep the shared YMODEM codec unchanged.
   * The checked encoder bounds name+NUL+DWORD length below24 bytes. */
  r=0;while(s->data[r])++r;++r;while(s->data[r])++r;
  s->data[r++]=' ';s->data[r]='0';
  if(header(s,ZFILE,0x01000000UL,s->format) || data(s,128,ZW_CRCW))break;
  for(;;){
   r=event(s);if(r!=ZW_HEADER)break;type=s->decoder.header[0];
   if(type==ZRPOS)return seek(s,position(s));
   if(type==ZSKIP)return ZM_DONE;
   if(type==ZCRC){if(source_crc(s,position(s)))return s->status;if(++s->retries>=LIMIT)break;continue;}
   if(type==ZRINIT){negotiate(s);break;}
   if(type==ZABORT || type==ZFERR || type==ZCAN)return fail(s,ZM_CANCEL);
   if(type==ZCHALLENGE)header(s,ZACK,position(s),ZW_HEX);
   if(++s->retries>=LIMIT)break;
  }
  zw_headers(&s->decoder);
 }
 return s->status?s->status:fail(s,ZM_TIMEOUT);
}
/* Maintained bounded asynchronous sender. position remains peer-confirmed;
 * sent is only wire output. No retransmission buffer: checked seek replays source.
 * Receiver storage capacity is independent of ACK/window credits. */
static unsigned send_stream(zm_session *s)
{
 unsigned r,type,n,got,ending,open=0,sync=1,waiting,eof,segment=0,query=0;
 zw_u32 sent=s->position,verified=sent,at;
 s->retries=0;
 while(!s->status && s->retries<LIMIT){
  s->phase=3;eof=sent==s->size;waiting=1;
  if(eof){
   if(open && data(s,0,ZW_CRCE))break;open=0;
   if(header(s,ZEOF,sent,s->format))break;
  }else{
   if(!open){if(header(s,ZDATA,sent,s->format))break;open=1;}
   n=s->size-sent>s->block?s->block:(unsigned)(s->size-sent);
   if(n>s->window-(unsigned)(sent-s->position))n=s->window-(unsigned)(sent-s->position);
   if(s->capacity && n>s->capacity-segment)n=s->capacity-segment;
   if(!n)return fail(s,ZM_PROTOCOL);
   if(s->ops->seek(s->context,sent) || s->ops->read_file(s->context,s->data,n,&got) || got!=n)return fail(s,ZM_FILE);
   if(sync || sent-s->position+n==s->window || (s->capacity && segment+n==s->capacity))ending=ZW_CRCW;
   else if(sent+n==s->size)ending=ZW_CRCE;
   else if(query+n>=s->window/4)ending=ZW_CRCQ;
   else ending=ZW_CRCG;
   if(data(s,n,ending))break;sent+=n;
   if(s->capacity)segment+=n;
   query+=n;
   if(ending==ZW_CRCQ || ending==ZW_CRCW)query=0;
   if(ending==ZW_CRCE || ending==ZW_CRCW)open=0;
   waiting=ending==ZW_CRCW;
  }
  for(;;){
   /* Empty polls retain partial headers, including a split ZDLE. */
   r=event_for(s,waiting?3:0);
   if(r==ZM_WAIT && !waiting)break;
   if(r!=ZW_HEADER){
    if(s->status)break;
    ++s->retries;goto replay;
   }
   type=s->decoder.header[0];at=position(s);
   if(type==ZACK){
    if(at>sent)return fail(s,ZM_PROTOCOL);
    if(at>s->position){
     s->position=at;
     /* A forward ACK during a long replay is useful, but must not
      * forgive repeated rewind requests until the old high-water is passed. */
     if(at>verified){verified=at;s->retries=0;}
    }else ++s->retries;
    if(!eof && waiting && at==sent){sync=0;segment=0;break;}
   }else if(type==ZRPOS){
    if(at>s->size)return fail(s,ZM_PROTOCOL);
    if(open && data(s,0,ZW_CRCE))break;open=0;
    if(at>verified){verified=at;s->retries=0;}else ++s->retries;
    if(seek(s,at))break;
    sent=at;segment=query=0;sync=1;zw_headers(&s->decoder);break;
   }else if(type==ZRINIT && eof){s->position=sent;return 0;}
   else if(type==ZSKIP){
    if(open && data(s,0,ZW_CRCE))break;
    return ZM_DONE;
   }else if(type==ZABORT || type==ZFERR || type==ZCAN)return fail(s,ZM_CANCEL);
   else if(type==ZCHALLENGE){
    if(open && data(s,0,ZW_CRCE))break;open=0;
    if(header(s,ZACK,at,ZW_HEX))break;
    ++s->retries;
   }else ++s->retries;
   if(s->retries>=LIMIT)break;
  }
  continue;
replay:
  if(open && data(s,0,ZW_CRCE))break;open=0;
  if(seek(s,s->position))break;
  sent=s->position;segment=query=0;sync=1;zw_headers(&s->decoder);
 }
 return s->status?s->status:fail(s,ZM_TIMEOUT);
}
static unsigned send_file(zm_session *s)
{
 unsigned r,type,n,got;zw_u32 next,verified;
 r=offer(s);if(r)return r;
 if(s->window>s->block)return send_stream(s);
 s->retries=0;verified=s->position;
 while(!s->status && s->retries<LIMIT){
  s->phase=3;next=s->position;
  if(s->position==s->size){if(header(s,ZEOF,s->position,s->format))break;}
  else{
   n=s->size-s->position>s->block?s->block:(unsigned)(s->size-s->position);
   if(s->ops->seek(s->context,s->position) || s->ops->read_file(s->context,s->data,n,&got) || got!=n)return fail(s,ZM_FILE);
   next+=n;
   if(header(s,ZDATA,s->position,s->format) || data(s,n,ZW_CRCW))break;
  }
  for(;;){
   r=event(s);if(r!=ZW_HEADER)break;type=s->decoder.header[0];
   if(type==ZACK && next>s->position && position(s)==next){
    s->position=next;if(next>verified){verified=next;s->retries=0;}break;
   }
   if(type==ZRPOS){
    if(position(s)>verified && position(s)<=s->size){verified=position(s);s->retries=0;}else ++s->retries;
    seek(s,position(s));break;
   }
   if(type==ZRINIT && s->position==s->size)return 0;
   if(type==ZSKIP)return ZM_DONE;
   if(type==ZABORT || type==ZFERR || type==ZCAN)return fail(s,ZM_CANCEL);
   if(type==ZCHALLENGE)header(s,ZACK,position(s),ZW_HEX);
   if(++s->retries>=LIMIT)break;
  }
  if(r!=ZW_HEADER)++s->retries;
  zw_headers(&s->decoder);
 }
 return s->status?s->status:fail(s,ZM_TIMEOUT);
}
static unsigned send(zm_session *s)
{
 unsigned r,i;
 for(i=0;i<LIMIT && !s->status;++i){
  if(header(s,ZRQINIT,0,ZW_HEX))break;
  r=event(s);
  if(r==ZW_HEADER && s->decoder.header[0]==ZRINIT){negotiate(s);break;}
  if(r==ZW_HEADER && s->decoder.header[0]==ZCHALLENGE)header(s,ZACK,position(s),ZW_HEX);
  zw_headers(&s->decoder);
 }
 if(s->status)return s->status;if(i==LIMIT)return fail(s,ZM_TIMEOUT);
 for(;;){
  s->owned=1;r=s->ops->next(s->context,s->name,&s->size);
  if(r==ZM_DONE){s->owned=0;return finish(s);}
  if(r)return fail(s,ZM_FILE);
  s->owned=1;s->position=0;
  r=send_file(s);if(s->status)return s->status;
  { unsigned close_status=s->ops->close_source(s->context,r==0);
   if(close_status){s->cleanup_status=close_status;s->owned=2;return fail(s,ZM_FILE);}
  }
  s->owned=0;
  if(r==ZM_DONE){if(s->skipped!=0xffffU)++s->skipped;continue;}
  if(s->files==0xffffffffUL || 0xffffffffUL-s->bytes<s->size)return fail(s,ZM_PROTOCOL);
  ++s->files;s->bytes+=s->size;
 }
}
unsigned __cdecl zm_run(zm_session *s,const zm_ops *ops,void *context,unsigned sending)
{
 unsigned r,i;unsigned char cancel[18];
 if(!s || !ops || sending>1)return ZM_ARGUMENT;
#ifdef __WATCOMC__
 if((unsigned long)(unsigned)s+sizeof(*s)>65536UL || (unsigned long)(unsigned)ops+sizeof(*ops)>65536UL ||
  !((unsigned long)(unsigned)s+sizeof(*s)<=(unsigned)ops || (unsigned long)(unsigned)ops+sizeof(*ops)<=(unsigned)s))return ZM_ARGUMENT;
#else
 if((uintptr_t)s>UINTPTR_MAX-sizeof(*s) || (uintptr_t)ops>UINTPTR_MAX-sizeof(*ops) ||
  !((uintptr_t)s+sizeof(*s)<=(uintptr_t)ops || (uintptr_t)ops+sizeof(*ops)<=(uintptr_t)s))return ZM_ARGUMENT;
#endif
 if(!ops->read_byte || !ops->write_wire || (sending?(!ops->next || !ops->seek || !ops->read_file || !ops->close_source):
  (!ops->open_received || !ops->write_received || !ops->commit_received || !ops->abort_received)))return ZM_ARGUMENT;
 memset(s,0,sizeof(*s));s->ops=ops;s->context=context;s->sending=sending;
 zw_init(&s->decoder,s->io.rx,sizeof(s->io.rx),0);r=sending?send(s):receive(s);
 if(s->owned==1){
  s->cleanup_status=sending?ops->close_source(context,0):ops->abort_received(context);
  if(!s->cleanup_status)s->owned=0;
 }
 if(r && r!=ZM_END_UNCONFIRMED){
  for(i=0;i<18;++i)cancel[i]=(unsigned char)(i<8?24:8);
  (void)ops->write_wire(context,cancel,sizeof(cancel));
 }
 return r;
}
