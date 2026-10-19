#include "zmodem_wire.h"
#include <string.h>
/* Protocol: Chuck Forsberg, ZMODEM, 1988-10-14, sections 7-11.
 * Direct CCITT update (no augmented zero updates); reflected IEEE CRC32.
 * These are independently maintained algorithms, not recovered machine code.
 */
static unsigned span(const void *p,unsigned n)
{
#ifdef __WATCOMC__
 return p && (unsigned long)(unsigned)p+n<=65536UL;
#else
 return p && (uintptr_t)p<=UINTPTR_MAX-n;
#endif
}
static unsigned separate(const void *a,unsigned an,const void *b,unsigned bn)
{
#ifdef __WATCOMC__
 return (unsigned long)(unsigned)a+an<=(unsigned)b || (unsigned long)(unsigned)b+bn<=(unsigned)a;
#else
 return (uintptr_t)a+an<=(uintptr_t)b || (uintptr_t)b+bn<=(uintptr_t)a;
#endif
}
static zw_u32 update(zw_u32 crc,unsigned value,unsigned format)
{
 unsigned i;
 if(format==ZW_BIN32){
  crc^=value;
  for(i=0;i<8;++i)crc=(crc>>1)^((crc&1)?0xedb88320UL:0);
 }else{
  crc^=(zw_u32)value<<8;
  for(i=0;i<8;++i)crc=((crc<<1)^((crc&0x8000)?0x1021:0))&0xffff;
 }
 return crc;
}
static zw_u32 initial(unsigned format){return format==ZW_BIN32?0xffffffffUL:0;}
static zw_u32 final(zw_u32 crc,unsigned format){return format==ZW_BIN32?crc^0xffffffffUL:crc;}
static unsigned crc_size(unsigned format){return format==ZW_BIN32?4:2;}
static void packet(zw_decoder *s)
{s->count=0;s->overflow=0;s->escape=0;s->index=0;s->received=0;s->crc=initial(s->format);}
void __cdecl zw_headers(zw_decoder *s)
{s->phase=0;s->index=0;s->escape=0;s->nibble=0;}
unsigned __cdecl zw_init(zw_decoder *s,unsigned char *buffer,unsigned capacity,unsigned control)
{
 if(!span(s,sizeof(*s)) || !capacity || capacity>ZW_RECEIVE_MAX || !span(buffer,capacity) || !separate(s,sizeof(*s),buffer,capacity) || control>1)return ZW_ARGUMENT;
 memset(s,0,sizeof(*s));s->buffer=buffer;s->capacity=capacity;s->control=control;
 return ZW_MORE;
}
unsigned __cdecl zw_data(zw_decoder *s)
{
 if(!span(s,sizeof(*s)) || (s->format!=ZW_HEX && s->format!=ZW_BIN16 && s->format!=ZW_BIN32))return ZW_ARGUMENT;
 packet(s);s->phase=10;return ZW_MORE;
}
static unsigned error(zw_decoder *s,unsigned status)
{zw_headers(s);return status;}
static unsigned hex(unsigned v)
{
 if(v>='0' && v<='9')return v-'0';
 if(v>='a' && v<='f')return v-'a'+10;
 if(v>='A' && v<='F')return v-'A'+10;
 return 255;
}
static void received(zw_decoder *s,unsigned value)
{
 if(s->format==ZW_BIN32)s->received|=(zw_u32)value<<(8*s->index);
 else s->received=(s->received<<8)|value;
 ++s->index;
}
unsigned __cdecl zw_feed(zw_decoder *s,unsigned v)
{
 unsigned x;
 if(!span(s,sizeof(*s)) || v>255)return ZW_ARGUMENT;
 if(s->cans>=5)return ZW_CANCEL;
 if(v==24){if(++s->cans==5)return error(s,ZW_CANCEL);}else s->cans=0;
 /* XON/XOFF are out-of-band even between ZDLE and its quoted suffix. */
 if((v&127)==17 || (v&127)==19)return ZW_MORE;
 if(s->phase==12){
  if(s->ending==ZW_CRCG || s->ending==ZW_CRCQ){packet(s);s->phase=10;}
  else zw_headers(s);
 }
 if(s->phase<=2){
  if(s->phase==0){if(v==42)s->phase=1;return ZW_MORE;}
  if(s->phase==1){if(v==24)s->phase=2;else if(v!=42)s->phase=0;return ZW_MORE;}
  if(v==24)return ZW_MORE;
  if(v!=ZW_BIN16 && v!=ZW_HEX && v!=ZW_BIN32)return error(s,ZW_FORMAT);
  s->format=v;packet(s);s->nibble=0;s->phase=v==ZW_HEX?4:3;return ZW_MORE;
 }
 if(s->phase==5){
  if(v==13)return ZW_MORE;
  if((v&127)!=10)return error(s,ZW_FORMAT);
  zw_headers(s);return ZW_HEADER;
 }
 if(s->phase==4){
  x=hex(v&127);if(x==255)return error(s,ZW_FORMAT);
  if(!s->nibble){s->nibble=x+1;return ZW_MORE;}
  v=((s->nibble-1)<<4)|x;s->nibble=0;
 }else{
  if(s->control && !(v&96) && v!=24)return ZW_MORE;
  if(!s->escape){
   if(v==24){s->escape=1;return ZW_MORE;}
  }else{
   if(v==24)return ZW_MORE;
   s->escape=0;
   if(s->phase==10 && v>=ZW_CRCE && v<=ZW_CRCW){
    s->ending=v;s->crc=update(s->crc,v,s->format);s->phase=11;s->index=0;return ZW_MORE;
   }
   if(v==108)v=127;
   else if(v==109)v=255;
   else if((v&96)==64)v^=64;
   else return error(s,ZW_FORMAT);
  }
 }
 if(s->phase==3 || s->phase==4){
  if(s->count<5){s->header[s->count++]=(unsigned char)v;s->crc=update(s->crc,v,s->format);return ZW_MORE;}
  received(s,v);if(s->index<crc_size(s->format))return ZW_MORE;
  if(s->received!=final(s->crc,s->format))return error(s,ZW_CRC);
  if(s->format==ZW_HEX){s->phase=5;return ZW_MORE;}
  zw_headers(s);return ZW_HEADER;
 }
 if(s->phase==10){
  if(s->count<s->capacity)s->buffer[s->count++]=(unsigned char)v;else s->overflow=1;
  s->crc=update(s->crc,v,s->format);return ZW_MORE;
 }
 received(s,v);if(s->index<crc_size(s->format))return ZW_MORE;
 if(s->received!=final(s->crc,s->format))return error(s,ZW_CRC);
 if(s->overflow)return error(s,ZW_OVERFLOW);
 s->phase=12;return ZW_DATA;
}
/* Count first, then emit. This keeps output atomic on insufficient capacity. */
typedef struct writer {unsigned char *out;unsigned n,control,previous;} writer;
static void raw(writer *w,unsigned v){if(w->out)w->out[w->n]=(unsigned char)v;++w->n;}
static void quote(writer *w,unsigned v)
{
 unsigned escape=v==16 || v==17 || v==19 || v==24 || v==144 || v==145 || v==147 || v==152 ||
  (w->control && !(v&96)) || ((v&127)==13 && (w->previous&127)==64);
 if(v==255){raw(w,24);raw(w,109);}
 else if(escape){raw(w,24);raw(w,v^64);}else raw(w,v);
 w->previous=v;
}
static void checksum(writer *w,zw_u32 crc,unsigned format)
{
 unsigned i;crc=final(crc,format);
 if(format==ZW_BIN32){for(i=0;i<4;++i){quote(w,(unsigned)(crc&255));crc>>=8;}}
 else{quote(w,(unsigned)(crc>>8));quote(w,(unsigned)(crc&255));}
}
static void encode_header(writer *w,unsigned format,const unsigned char *h)
{
 unsigned i,v;zw_u32 crc=initial(format);
 raw(w,42);if(format==ZW_HEX)raw(w,42);raw(w,24);raw(w,format);
 for(i=0;i<5;++i)crc=update(crc,h[i],format);
 if(format==ZW_HEX){
  for(i=0;i<7;++i){
   v=i<5?h[i]:(i==5?(unsigned)(crc>>8):(unsigned)(crc&255));
   raw(w,"0123456789abcdef"[v>>4]);raw(w,"0123456789abcdef"[v&15]);
  }
  raw(w,13);raw(w,10);if(h[0]!=3 && h[0]!=8)raw(w,17);
 }else{for(i=0;i<5;++i)quote(w,h[i]);checksum(w,crc,format);}
}
unsigned __cdecl zw_header_encode(unsigned format,const unsigned char *h,unsigned control,unsigned char *out,unsigned capacity)
{
 writer w;
 if((format!=ZW_BIN16 && format!=ZW_BIN32 && format!=ZW_HEX) || control>1 || !span(h,5) || !span(out,capacity) || !separate(h,5,out,capacity))return 0;
 w.out=0;w.n=0;w.control=control;w.previous=0;encode_header(&w,format,h);
 if(w.n>capacity)return 0;
 w.out=out;w.n=0;w.previous=0;encode_header(&w,format,h);return w.n;
}
static void encode_data(writer *w,unsigned format,const unsigned char *data,unsigned length,unsigned ending)
{
 unsigned i;zw_u32 crc=initial(format);
 for(i=0;i<length;++i){quote(w,data[i]);crc=update(crc,data[i],format);}
 raw(w,24);raw(w,ending);w->previous=ending;
 crc=update(crc,ending,format);checksum(w,crc,format);
 if(ending==ZW_CRCW)raw(w,17);
}
unsigned __cdecl zw_data_encode(unsigned format,const unsigned char *data,unsigned length,unsigned ending,unsigned control,unsigned char *out,unsigned capacity)
{
 writer w;
 if((format!=ZW_BIN16 && format!=ZW_BIN32 && format!=ZW_HEX) || ending<ZW_CRCE || ending>ZW_CRCW || control>1 || length>1024 || (length && !span(data,length)) || !span(out,capacity) || !separate(data,length,out,capacity))return 0;
 /* A preceding header/subpacket can end in @. Conservatively quote initial
  * CR/8d without needing hidden cross-packet writer state. */
 w.out=0;w.n=0;w.control=control;w.previous=64;encode_data(&w,format,data,length,ending);
 if(w.n>capacity)return 0;
 w.out=out;w.n=0;w.previous=64;encode_data(&w,format,data,length,ending);return w.n;
}
