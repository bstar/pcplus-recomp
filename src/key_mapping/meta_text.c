#include <dos.h>
#include "meta_text.h"
typedef char meta_text_layout[sizeof(meta_text_state)==64?1:-1];

static unsigned extent(const void __far *p,unsigned size,unsigned long *start)
{
 unsigned long linear=(unsigned long)FP_SEG(p)*16UL+FP_OFF(p);
 if(!p || (unsigned long)FP_OFF(p)+size>65536UL || linear+size>0x100000UL)return 0;
 *start=linear;return 1;
}
static unsigned separate(const void __far *a,unsigned an,const void __far *b,unsigned bn)
{
 unsigned long x,y;
 return extent(a,an,&x) && extent(b,bn,&y) && (x+an<=y || y+bn<=x);
}
static unsigned valid(const meta_text_state __far *s)
{
 unsigned long address;
 return extent(s,sizeof(*s),&address) && s->cookie==0x4d54 && s->phase<=META_TEXT_CANCEL &&
  s->cursor<META_TEXT_WIDTH && s->insert<=1 && s->full<=1 && (!s->full || s->cursor==META_TEXT_WIDTH-1);
}
unsigned __far __cdecl meta_text_begin(meta_text_state __far *s,const unsigned char __far *source,unsigned shape)
{
 unsigned n,i;
 if(!separate(s,sizeof(*s),source,META_TEXT_RECORD_BYTES))return META_TEXT_ARGUMENT;
 for(n=0;n<META_TEXT_RECORD_BYTES && source[n];++n){}
 if(n==META_TEXT_RECORD_BYTES)return META_TEXT_ARGUMENT;
 s->cookie=0x4d54;s->phase=META_TEXT_ACTIVE;s->cursor=s->insert=s->full=s->result=0;s->saved_shape=shape;
 for(i=0;i<META_TEXT_WIDTH;++i)s->field[i]=i<n?source[i]:' ';
 return META_TEXT_ACTIVE;
}
unsigned __far __cdecl meta_text_key(meta_text_state __far *s,unsigned key)
{
 unsigned i,c;
 if(!valid(s) || s->phase!=META_TEXT_ACTIVE)return META_TEXT_ARGUMENT;
 if(key==255)return META_TEXT_ACTIVE; /* Native callback returns-99: consume. */
 if(key==9 || key==0x0f00 || key==13){s->phase=META_TEXT_ACCEPT;s->result=key==13?0:key;return META_TEXT_ACCEPT;}
 if(key==27){s->phase=META_TEXT_CANCEL;s->result=0xffff;return META_TEXT_CANCEL;}
 c=s->cursor;
 if(key==8 || key==0x0e08){
  s->full=0;
  if(!c)return META_TEXT_BELL;
  if(c<META_TEXT_WIDTH-1 || s->field[c]==' '){
   i=c-1;s->cursor=i;
   for(;i<META_TEXT_WIDTH-1;++i)s->field[i]=s->field[i+1];
  }
  s->field[META_TEXT_WIDTH-1]=' ';
 }else if(key==0x0e7f || key==0x2e00){
  s->cursor=s->full=0;for(i=0;i<META_TEXT_WIDTH;++i)s->field[i]=' ';
 }else if(key==0x4700){s->cursor=s->full=0;}
 else if(key==0x4b00){s->full=0;if(!c)return META_TEXT_BELL;s->cursor=c-1;}
 else if(key==0x4d00){if(c==META_TEXT_WIDTH-1)return META_TEXT_BELL;s->cursor=c+1;}
 else if(key==0x4f00){
  s->full=0;i=META_TEXT_WIDTH;while(i && s->field[i-1]==' ')--i;s->cursor=i<META_TEXT_WIDTH?i:META_TEXT_WIDTH-1;
 }else if(key==0x5200)s->insert=!s->insert;
 else if(key==0x5300){
  s->full=0;for(i=c;i<META_TEXT_WIDTH-1;++i)s->field[i]=s->field[i+1];s->field[META_TEXT_WIDTH-1]=' ';
 }else if(key==0x7500){s->full=0;for(i=c;i<META_TEXT_WIDTH;++i)s->field[i]=' ';}
 else if(key && key<256){
  if(s->insert)for(i=META_TEXT_WIDTH-1;i>c;--i)s->field[i]=s->field[i-1];
  if(s->full)return META_TEXT_BELL;
  s->field[c]=(unsigned char)key;
  if(c==META_TEXT_WIDTH-1)s->full=1;else s->cursor=c+1;
 }else return META_TEXT_BELL;
 return META_TEXT_ACTIVE;
}
unsigned __far __cdecl meta_text_commit(const meta_text_state __far *s,unsigned char __far *target)
{
 unsigned i,n;
 if(!valid(s) || s->phase!=META_TEXT_ACCEPT || !separate(s,sizeof(*s),target,META_TEXT_RECORD_BYTES))return META_TEXT_ARGUMENT;
 n=META_TEXT_WIDTH;while(n && s->field[n-1]==' ')--n;
 for(i=0;i<n;++i)target[i]=s->field[i];target[n]=0;return META_TEXT_ACCEPT;
}
unsigned __far __cdecl meta_text_shape(const meta_text_state __far *s)
{
 unsigned end;
 if(!valid(s))return 0xffff;
 if(s->phase!=META_TEXT_ACTIVE || !s->insert)return s->saved_shape;
 end=s->saved_shape&255;return ((end/2+1)<<8)|end;
}
