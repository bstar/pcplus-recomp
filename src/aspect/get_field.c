/* Generalized from the recovered Meta field model; independent GET callback
 * and width semantics are checked against original79D4 instruction traces. */
#include <dos.h>
#include "get_field.h"

typedef char get_field_layout[sizeof(get_field_state)==104?1:-1];

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
static unsigned valid(const get_field_state __far *s)
{
 unsigned long address;
 return extent(s,sizeof(*s),&address) && s->cookie==0x4746 && s->phase<=GET_FIELD_CANCEL &&
  s->width>=1 && s->width<=GET_FIELD_MAX && s->numeric<=1 && s->masked<=1 && s->visible<=1 &&
  s->cursor<s->width && s->insert<=1 && s->full<=1 && (!s->full || s->cursor==s->width-1);
}
unsigned __far __cdecl get_field_begin(get_field_state __far *s,const unsigned char __far *source,unsigned width,unsigned numeric,unsigned masked,unsigned visible,unsigned shape)
{
 unsigned n=0,i;unsigned long address;
 if(!extent(s,sizeof(*s),&address) || !width || width>GET_FIELD_MAX || numeric>1 || masked>1 || visible>1)return GET_FIELD_ARGUMENT;
 if(source){
  if(!separate(s,sizeof(*s),source,GET_FIELD_BUFFER))return GET_FIELD_ARGUMENT;
  for(;n<GET_FIELD_BUFFER && source[n];++n){}
  if(n>width)return GET_FIELD_ARGUMENT;
 }
 s->cookie=0x4746;s->phase=GET_FIELD_ACTIVE;s->cursor=s->insert=s->full=s->result=0;s->saved_shape=shape;
 s->width=width;s->numeric=numeric;s->masked=masked;s->visible=visible;
 for(i=0;i<GET_FIELD_MAX;++i)s->field[i]=i<n?source[i]:' ';
 return GET_FIELD_ACTIVE;
}
unsigned __far __cdecl get_field_key(get_field_state __far *s,unsigned key)
{
 unsigned i,c;
 if(!valid(s) || s->phase!=GET_FIELD_ACTIVE)return GET_FIELD_ARGUMENT;
 if(s->numeric && key<255 && key!=8 && key!=13 && key!=27 && key!=45 && key!=46 && (key<48 || key>57))return GET_FIELD_BELL;
 if(key==13){
  i=s->width;while(i && s->field[i-1]==' ')--i;
  s->phase=GET_FIELD_ACCEPT;s->result=s->numeric?0:i;return GET_FIELD_ACCEPT;
 }
 if(key==27){s->phase=GET_FIELD_CANCEL;s->result=0xffff;return GET_FIELD_CANCEL;}
 c=s->cursor;
 if(key==8 || key==0x0e08){
  if(!c && (s->width!=1 || !s->full)){s->full=0;return GET_FIELD_BELL;}
  s->full=0;
  if(c && (c<s->width-1 || s->field[c]==' ')){
   i=c-1;s->cursor=i;
   for(;i<s->width-1;++i)s->field[i]=s->field[i+1];
  }
  s->field[s->width-1]=' ';
 }else if(key==0x0e7f || key==0x2e00){
  s->cursor=s->full=0;for(i=0;i<s->width;++i)s->field[i]=' ';
 }else if(key==0x4700){s->cursor=s->full=0;}
 else if(key==0x4b00){s->full=0;if(!c)return GET_FIELD_BELL;s->cursor=c-1;}
 else if(key==0x4d00){if(c==s->width-1)return GET_FIELD_BELL;s->cursor=c+1;}
 else if(key==0x4f00){
  s->full=0;i=s->width;while(i && s->field[i-1]==' ')--i;s->cursor=i<s->width?i:s->width-1;
 }else if(key==0x5200)s->insert=!s->insert;
 else if(key==0x5300){
  s->full=0;for(i=c;i<s->width-1;++i)s->field[i]=s->field[i+1];s->field[s->width-1]=' ';
 }else if(key==0x7500){s->full=0;for(i=c;i<s->width;++i)s->field[i]=' ';}
 else if(key && key<256){
  if(s->insert)for(i=s->width-1;i>c;--i)s->field[i]=s->field[i-1];
  if(s->full)return GET_FIELD_BELL;
  s->field[c]=(unsigned char)key;
  if(c==s->width-1)s->full=1;else s->cursor=c+1;
 }else return GET_FIELD_BELL;
 return GET_FIELD_ACTIVE;
}
unsigned __far __cdecl get_field_commit(const get_field_state __far *s,unsigned char __far *target)
{
 unsigned i,n;
 if(!valid(s) || s->phase!=GET_FIELD_ACCEPT || !separate(s,sizeof(*s),target,GET_FIELD_BUFFER))return GET_FIELD_ARGUMENT;
 n=s->width;while(n && s->field[n-1]==' ')--n;
 for(i=0;i<n;++i)target[i]=s->field[i];target[n]=0;return GET_FIELD_ACCEPT;
}
unsigned __far __cdecl get_field_shape(const get_field_state __far *s)
{
 unsigned end;
 if(!valid(s))return 0xffff;
 if(s->phase!=GET_FIELD_ACTIVE || !s->insert)return s->saved_shape;
 end=s->saved_shape&255;return ((end/2+1)<<8)|end;
}
unsigned __far __cdecl get_field_render(const get_field_state __far *s,unsigned char __far *target)
{
 unsigned i;
 if(!valid(s) || !separate(s,sizeof(*s),target,GET_FIELD_BUFFER))return GET_FIELD_ARGUMENT;
 for(i=0;i<s->width;++i)target[i]=s->masked && s->field[i]!=' '?'*':s->field[i];
 target[s->width]=0;return s->phase;
}
unsigned __far __cdecl get_field_visible(const get_field_state __far *s)
{
 if(!valid(s))return 0xffff;
 return s->phase==GET_FIELD_ACTIVE?1:s->visible;
}
