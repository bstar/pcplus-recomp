/* Complete maintained batch owner. Framing is deliberately separate from file
 * ownership and metadata parsing. Original ordinary XMODEM remains unchanged.
 * CRC is the linked recovered routine, not an independent replacement. */
#include <string.h>
#include "ymodem.h"
#include "batch_header.h"
#include "batch_download.h"
#include "batch_upload.h"
extern unsigned __cdecl transfer_crc_buffer_original(const unsigned char *,unsigned);
ymodem_result ymodem_current;
#define WORK terminal_batch_buffer
#define META (terminal_batch_buffer+1024)
#define LAST (terminal_batch_buffer+2048)
#define SOH 1
#define STX 2
#define EOT 4
#define ACK 6
#define NAK 21
#define CAN 24
#define CRC_REQUEST 67
#define WAIT 0xffffU
#define BAD 0xfffeU
#define LIMIT 10
static unsigned frame_size,frame_seq,frame_consumed,owner_acquired;
static unsigned fail(unsigned status)
{ if(!ymodem_current.status)ymodem_current.status=status;return status; }
static unsigned put(unsigned value)
{ if(ymodem_io_put(value)||ymodem_io_poll())return fail(YM_IO);return 0; }
static unsigned get(unsigned seconds)
{
 unsigned value=ymodem_io_read(seconds);
 if(ymodem_io_poll()){fail(YM_IO);return WAIT;}
 return value;
}
static void progress(unsigned data,unsigned count)
{
 if(data){
  if(ymodem_current.blocks!=0xffffU)++ymodem_current.blocks;
  if(0xffffffffUL-ymodem_current.bytes<count)ymodem_current.bytes=0xffffffffUL;
  else ymodem_current.bytes+=count;
 }
 ymodem_io_progress();
}
/* Complete frame consumed even on complement/CRC error. On truncation discard
 * only to a bounded quiet interval, never interpret its payload as controls. */
static unsigned frame(unsigned lead,unsigned drain)
{
 unsigned i,a,b,crc,hi,lo;
 frame_consumed=1;frame_size=lead==SOH?128:1024;
 a=get(1);if(a==WAIT)goto truncated;++frame_consumed;
 b=get(1);if(b==WAIT)goto truncated;++frame_consumed;
 frame_seq=a;
 for(i=0;i<frame_size;++i){
  lo=get(1);if(lo==WAIT)goto truncated;
  WORK[i]=(unsigned char)lo;++frame_consumed;
 }
 hi=get(1);if(hi==WAIT)goto truncated;++frame_consumed;
 lo=get(1);if(lo==WAIT)goto truncated;++frame_consumed;
 crc=transfer_crc_buffer_original(WORK,frame_size);
 return ((a^b)==255 && crc==((hi<<8)|lo))?0:BAD;
truncated:
 if(drain && !ymodem_current.status){
  for(i=0;i<2048;++i){if(get(1)==WAIT)break;}
 }
 return BAD;
}
/* Double CAN only outside data. Preserve a non-CAN following a lone CAN. */
static unsigned control(unsigned seconds)
{
 unsigned value=get(seconds),next;
 if(value==CAN){
  next=get(1);
  if(next==CAN){fail(YM_CANCEL);return WAIT;}
  if(next!=WAIT && ymodem_io_unread(1))fail(YM_IO);
  return BAD;
 }
 return value;
}
static unsigned send_frame(unsigned seq,const unsigned char *data,unsigned size)
{
 unsigned i,crc=transfer_crc_buffer_original(data,size);
 if(put(size==128?SOH:STX)||put(seq)||put(seq^255))return 1;
 for(i=0;i<size;++i)if(put(data[i]))return 1;
 return put(crc>>8)||put(crc&255);
}
static unsigned file_error(unsigned code)
{
 ymodem_current.last_file_status=code;
 return fail(code==BD_LENGTH && !ymodem_current.direction?YM_LENGTH:YM_FILE);
}
static unsigned receive_end(void)
{
 unsigned tries,value,valid;
 /* A lost final-header ACK must be recoverable. Stop on the first application
  * byte and restore the entire inspected prefix into the actual UART ring.
  * Duplicates do not refresh the accepted-progress watchdog. */
 for(tries=0;tries<LIMIT && !ymodem_current.status;++tries){
  value=get(1);
  if(value==WAIT)continue;
  if(value==SOH || value==STX){
   valid=frame(value,0);
   if(!valid && frame_seq==0 && WORK[0]==0){
    batch_header_result header;
    if(!batch_header_decode(WORK,frame_size,&header) && header.kind==BH_END){
     if(put(ACK))return 1;
     continue;
    }
   }
   if(ymodem_io_unread(frame_consumed))return fail(YM_IO);
  }else if(ymodem_io_unread(1))return fail(YM_IO);
  break;
 }
 return ymodem_current.status;
}
static unsigned receive_batch(const char *path)
{
 batch_header_result header;
 unsigned value,tries=0,expected=1,have_data=0,last_size=0,header_size=0;
 unsigned in_file=0,eot_pending=0,committed=0,code;
 unsigned long before;
 code=batch_download_begin(path);if(code)return file_error(code);
 owner_acquired=1;
 ymodem_current.phase=1;
 if(put(CRC_REQUEST))return 1;
 while(!ymodem_current.status){
  if(++tries>LIMIT)return fail(YM_TIMEOUT);
  value=control(2);
  if(ymodem_current.status)break;
  if(value==WAIT){if(put(in_file?NAK:CRC_REQUEST))break;continue;}
  if(value==EOT){
   if(!in_file){
    if(committed){if(put(ACK)||put(CRC_REQUEST))break;}
    else if(put(CRC_REQUEST))break;
    continue;
   }
   if(!eot_pending){eot_pending=1;if(put(NAK))break;continue;}
   code=batch_download_finish();if(code)return file_error(code);
   if(ymodem_current.files!=0xffffffffUL)++ymodem_current.files;
   in_file=0;committed=1;eot_pending=0;tries=0;
   progress(0,0);ymodem_current.phase=1;
   if(put(ACK)||put(CRC_REQUEST))break;
   continue;
  }
  if(value!=SOH && value!=STX){if(value!=BAD)--tries;continue;}
  if(frame(value,1)){if(ymodem_current.status)break;if(put(NAK))break;continue;}
  if(!in_file){
   if(frame_seq!=0){if(put(NAK))break;continue;}
   code=batch_header_decode(WORK,frame_size,&header);
   if(code)return fail(YM_HEADER);
   if(header.kind==BH_END){
    ymodem_current.phase=3;
    progress(0,0);
    if(put(ACK))return 1;
    return receive_end();
   }
   code=batch_download_open(&header);if(code)return file_error(code);
   memcpy(ymodem_current.name,header.name,13);
   memcpy(META,WORK,frame_size);header_size=frame_size;
   expected=1;have_data=0;last_size=0;in_file=1;committed=0;tries=0;
   ymodem_current.phase=2;progress(0,0);
   if(put(ACK)||put(CRC_REQUEST))break;
   continue;
  }
  /* Exact header retry only before the first data frame, not sequence0 at
   * rollover. An altered retry must never reopen/truncate a staged target. */
  if(!have_data && frame_seq==0 && frame_size==header_size &&
     !memcmp(WORK,META,frame_size)){
   if(put(ACK)||put(CRC_REQUEST))break;
   continue;
  }
  if(frame_seq==((expected-1)&255) && have_data && frame_size==last_size &&
     !memcmp(WORK,LAST,frame_size)){
   if(put(ACK))break;
   continue;
  }
  if(frame_seq!=expected || eot_pending){if(put(NAK))break;continue;}
  before=batch_download_result.stored;
  code=batch_download_append(WORK,frame_size);if(code)return file_error(code);
  memcpy(LAST,WORK,frame_size);last_size=frame_size;have_data=1;
  expected=(expected+1)&255;tries=0;
  progress(1,(unsigned)(batch_download_result.stored-before));
  if(put(ACK))break;
 }
 return ymodem_current.status;
}
static unsigned expect(unsigned wanted)
{
 unsigned tries=0,value;
 while(tries<LIMIT && !ymodem_current.status){
  value=control(2);if(value==wanted)return 0;
  if(value==WAIT || value==BAD || value==NAK)++tries;
 }
 return fail(ymodem_current.status?ymodem_current.status:YM_TIMEOUT);
}
static unsigned transmit_block(unsigned seq,const unsigned char *data,unsigned size)
{
 unsigned tries,value;
 for(tries=0;tries<LIMIT && !ymodem_current.status;++tries){
  if(send_frame(seq,data,size))return 1;
  value=control(2);
  if(value==ACK)return 0;
 }
 return fail(ymodem_current.status?ymodem_current.status:YM_TIMEOUT);
}
static unsigned transmit_end(void)
{
 unsigned tries,value;
 for(tries=0;tries<LIMIT && !ymodem_current.status;++tries){
  if(send_frame(0,WORK,128))return 1;
  value=control(2);
  if(ymodem_current.status)break;
  if(value==ACK)return 0;
  if(value==WAIT || value==NAK || value==CRC_REQUEST || value==BAD)continue;
  /* Some deployed helpers return to the BBS while dropping their buffered
   * final ACK. Preserve the application's first byte and report uncertainty;
   * never inject a repeated binary header or CAN into its menu. All files
   * already received individual EOT ACKs. This is not a fabricated final ACK. */
  if(ymodem_io_unread(1))return fail(YM_IO);
  return fail(YM_END_UNCONFIRMED);
 }
 return fail(ymodem_current.status?ymodem_current.status:YM_TIMEOUT);
}
static unsigned send_batch(const char *path)
{
 unsigned code,value,seq,size,count,tries;
 unsigned long remaining;
 code=batch_upload_begin(path);if(code)return file_error(code);
 owner_acquired=1;
 ymodem_current.phase=1;
 if(expect(CRC_REQUEST))return 1;
 for(;;){
  code=batch_upload_next();
  if(code==BU_DONE){
   if(batch_header_end(WORK,128))return fail(YM_HEADER);
   ymodem_current.phase=3;
   return transmit_end();
  }
  if(code!=BU_FILE)return file_error(code);
  memcpy(ymodem_current.name,batch_upload_current.name,13);
  if(batch_header_encode(batch_upload_current.name,13,batch_upload_current.size,
                         WORK,128))return fail(YM_HEADER);
  if(transmit_block(0,WORK,128))return 1;
  progress(0,0);
  if(expect(CRC_REQUEST))return 1;
  remaining=batch_upload_current.size;seq=1;ymodem_current.phase=2;
  while(remaining){
   size=remaining>=897?1024:128;
   count=remaining<size?(unsigned)remaining:size;
   memset(WORK,26,size);
   code=batch_upload_read(WORK,count,&value);
   if(code || value!=count)return file_error(code?code:BU_SOURCE);
   if(transmit_block(seq,WORK,size))return 1;
   remaining-=count;seq=(seq+1)&255;progress(1,count);
  }
  /* Close the fully consumed source before permitting peer commitment.
   * Enumeration remains parked until this file's EOT acknowledgement. */
  code=batch_upload_close();if(code)return file_error(code);
  for(tries=0;tries<LIMIT && !ymodem_current.status;++tries){
   if(put(EOT))return 1;
   value=control(2);if(value==ACK)break;
  }
  if(tries==LIMIT || ymodem_current.status)return fail(ymodem_current.status?ymodem_current.status:YM_TIMEOUT);
  if(ymodem_current.files!=0xffffffffUL)++ymodem_current.files;
  progress(0,0);ymodem_current.phase=1;
  if(expect(CRC_REQUEST))return 1;
 }
}
unsigned __cdecl ymodem_run(const char *path,unsigned sending)
{
 unsigned code,cleanup;
 memset(&ymodem_current,0,sizeof(ymodem_current));
 owner_acquired=0;
 ymodem_current.direction=sending;
 if(!path || sending>1)return fail(YM_ARGUMENT);
 code=sending?send_batch(path):receive_batch(path);
 if(ymodem_current.status==YM_END_UNCONFIRMED)return YM_END_UNCONFIRMED;
 /* Earlier installed files survive later failure. Only the current owned
  * temporary file/source is resolved; ambiguous close is never retried. */
 if(code || ymodem_current.status){
  cleanup=owner_acquired?(sending?batch_upload_abort():batch_download_cleanup()):0;
  if(cleanup){ymodem_current.last_file_status=cleanup;fail(YM_RECOVERY);}
  return ymodem_current.status?ymodem_current.status:fail(YM_PROTOCOL);
 }
 return 0;
}
