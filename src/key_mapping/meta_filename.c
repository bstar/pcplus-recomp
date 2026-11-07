#include <dos.h>
#include "meta_filename.h"
typedef char meta_filename_layout[sizeof(meta_filename_state)==22?1:-1];

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
static unsigned valid(const meta_filename_state __far *s)
{
 unsigned long address;
 return extent(s,sizeof(*s),&address) && s->cookie==0x4d4e && s->phase<=META_FILENAME_CANCEL &&
  s->cursor<META_FILENAME_WIDTH && s->insert<=1 && s->full<=1 && (!s->full || s->cursor==META_FILENAME_WIDTH-1);
}
unsigned __far __cdecl meta_filename_begin(meta_filename_state __far *s,unsigned shape)
{
 unsigned i;unsigned long address;
 if(!extent(s,sizeof(*s),&address))return META_FILENAME_ARGUMENT;
 s->cookie=0x4d4e;s->phase=META_FILENAME_ACTIVE;s->cursor=s->insert=s->full=s->result=0;s->saved_shape=shape;
 for(i=0;i<META_FILENAME_WIDTH;++i)s->field[i]=' ';
 return META_FILENAME_ACTIVE;
}
unsigned __far __cdecl meta_filename_key(meta_filename_state __far *s,unsigned key)
{
 unsigned i,c;
 if(!valid(s) || s->phase!=META_FILENAME_ACTIVE)return META_FILENAME_ARGUMENT;
 if(key==32 || key==46)return META_FILENAME_ACTIVE; /* Native4aa7 returns-99. */
 if(key==13){
  i=META_FILENAME_WIDTH;while(i && s->field[i-1]==' ')--i;
  s->phase=META_FILENAME_ACCEPT;s->result=i;return META_FILENAME_ACCEPT;
 }
 if(key==27){s->phase=META_FILENAME_CANCEL;s->result=0xffff;return META_FILENAME_CANCEL;}
 c=s->cursor;
 if(key==8 || key==0x0e08){
  s->full=0;
  if(!c)return META_FILENAME_BELL;
  if(c<META_FILENAME_WIDTH-1 || s->field[c]==' '){
   i=c-1;s->cursor=i;
   for(;i<META_FILENAME_WIDTH-1;++i)s->field[i]=s->field[i+1];
  }
  s->field[META_FILENAME_WIDTH-1]=' ';
 }else if(key==0x0e7f || key==0x2e00){
  s->cursor=s->full=0;for(i=0;i<META_FILENAME_WIDTH;++i)s->field[i]=' ';
 }else if(key==0x4700){s->cursor=s->full=0;}
 else if(key==0x4b00){s->full=0;if(!c)return META_FILENAME_BELL;s->cursor=c-1;}
 else if(key==0x4d00){if(c==META_FILENAME_WIDTH-1)return META_FILENAME_BELL;s->cursor=c+1;}
 else if(key==0x4f00){
  s->full=0;i=META_FILENAME_WIDTH;while(i && s->field[i-1]==' ')--i;s->cursor=i<META_FILENAME_WIDTH?i:META_FILENAME_WIDTH-1;
 }else if(key==0x5200)s->insert=!s->insert;
 else if(key==0x5300){
  s->full=0;for(i=c;i<META_FILENAME_WIDTH-1;++i)s->field[i]=s->field[i+1];s->field[META_FILENAME_WIDTH-1]=' ';
 }else if(key==0x7500){s->full=0;for(i=c;i<META_FILENAME_WIDTH;++i)s->field[i]=' ';}
 else if(key && key<256){
  if(s->insert)for(i=META_FILENAME_WIDTH-1;i>c;--i)s->field[i]=s->field[i-1];
  if(s->full)return META_FILENAME_BELL;
  s->field[c]=(unsigned char)key;
  if(c==META_FILENAME_WIDTH-1)s->full=1;else s->cursor=c+1;
 }else return META_FILENAME_BELL;
 return META_FILENAME_ACTIVE;
}
unsigned __far __cdecl meta_filename_commit(const meta_filename_state __far *s,unsigned char __far *target)
{
 unsigned i,n;
 if(!valid(s) || s->phase!=META_FILENAME_ACCEPT || !separate(s,sizeof(*s),target,META_FILENAME_RECORD_BYTES))return META_FILENAME_ARGUMENT;
 n=META_FILENAME_WIDTH;while(n && s->field[n-1]==' ')--n;
 for(i=0;i<n;++i)target[i]=s->field[i];target[n]=0;return META_FILENAME_ACCEPT;
}
unsigned __far __cdecl meta_filename_shape(const meta_filename_state __far *s)
{
 unsigned end;
 if(!valid(s))return 0xffff;
 if(s->phase!=META_FILENAME_ACTIVE || !s->insert)return s->saved_shape;
 end=s->saved_shape&255;return ((end/2+1)<<8)|end;
}
