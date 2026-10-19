#include "zmodem_autostart.h"
#include <string.h>

static unsigned nibble(unsigned v)
{
 if(v>='0' && v<='9')return v-'0';
 if(v>='a' && v<='f')return v-'a'+10;
 if(v>='A' && v<='F')return v-'A'+10;
 return 16;
}
static unsigned prefix(const za_state *s)
{
 unsigned i,v;
 for(i=0;i<s->count;++i){
  v=s->held[i];
  if(i<2){if(v!='*')return 0;}
  else if(i==2){if(v!=24)return 0;}
  else if(i==3){if(v!='B')return 0;}
  else if(i<6){if(v!='0')return 0;} /* ZRQINIT, never ZRINIT/ZFILE. */
  else if(i<18){if(nibble(v)>15)return 0;}
  else if(i==18){if(v!=13)return 0;}
  else if((v&127)!=10)return 0;
 }
 return 1;
}
static unsigned valid(const za_state *s)
{
 unsigned crc=0,i,j,v;
 /* A direct CCITT remainder over the five header bytes and big-endian CRC
  * must be zero. Mask on every step: host unsigned may be wider than DOS. */
 for(i=4;i<18;i+=2){
  v=(nibble(s->held[i])<<4)|nibble(s->held[i+1]);
  crc^=v<<8;
  for(j=0;j<8;++j)crc=((crc<<1)^((crc&32768U)?4129U:0))&65535U;
 }
 /* ZF0 is the final header byte. Command invitations are a distinct
  * application service, not a request to start the file receiver. */
 return crc==0 && s->held[12]=='0' && s->held[13]=='0';
}
void __cdecl za_reset(za_state *s)
{s->count=0;}
unsigned __cdecl za_feed(za_state *s,unsigned value,unsigned char *out,unsigned *released)
{
 unsigned n=0;
 if(value>255 || s->count>=ZA_HELD_MAX)return ZA_ARGUMENT;
 s->held[s->count++]=(unsigned char)value;
 while(s->count){
  if(prefix(s)){
   if(s->count<ZA_HELD_MAX)break;
   if(valid(s)){s->count=0;*released=n;return ZA_START;}
  }
  out[n++]=s->held[0];
  --s->count;
  memmove(s->held,s->held+1,s->count);
 }
 *released=n;
 return ZA_MORE;
}
unsigned __cdecl za_flush(za_state *s,unsigned char *out)
{
 unsigned n=s->count;
 memcpy(out,s->held,n);s->count=0;return n;
}
