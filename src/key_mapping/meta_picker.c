#include <dos.h>
#include "meta_picker.h"
typedef char picker_layout[sizeof(meta_picker_state)==20?1:-1];
static unsigned span(const void __far *p,unsigned n,unsigned long *a)
{*a=(unsigned long)FP_SEG(p)*16UL+FP_OFF(p);return p && (unsigned long)FP_OFF(p)+n<=65536UL && *a+n<=0x100000UL;}
static unsigned separate(const void __far *p,unsigned n,const void __far *q,unsigned m)
{unsigned long a,b;return span(p,n,&a) && span(q,m,&b) && (a+n<=b || b+m<=a);}
static unsigned valid(const meta_picker_state __far *s)
{
 unsigned long a;
 if(!span(s,sizeof(*s),&a) || s->cookie!=0x4d50 || s->phase>META_PICKER_EMPTY || s->count>META_PICKER_CAPACITY || !separate(s,sizeof(*s),s->names,META_PICKER_BYTES))return 0;
 if(s->phase==META_PICKER_SORT && (s->count<2 || s->limit<2 || s->limit>s->count || !s->index || s->index>=s->limit || s->changed>1))return 0;
 if(s->phase>=META_PICKER_ACTIVE && s->phase<=META_PICKER_CANCEL && (!s->count || s->top>=s->count || s->row>=s->count-s->top || s->row>=15))return 0;
 return 1;
}
static unsigned fold(unsigned c){return c>='A' && c<='Z'?c+32:c;}
unsigned __far __cdecl meta_picker_begin(meta_picker_state __far *s,unsigned char __far *names)
{
 if(!separate(s,sizeof(*s),names,META_PICKER_BYTES))return META_PICKER_ARGUMENT;
 s->cookie=0x4d50;s->phase=META_PICKER_COLLECT;s->count=s->top=s->row=s->index=s->limit=s->changed=0;s->names=names;return META_PICKER_OK;
}
unsigned __far __cdecl meta_picker_add(meta_picker_state __far *s,const char __far *stem)
{
 unsigned i,n,at;
 if(!valid(s) || !separate(s,sizeof(*s),stem,9) || !separate(s->names,META_PICKER_BYTES,stem,9))return META_PICKER_ARGUMENT;
 if(s->phase!=META_PICKER_COLLECT)return META_PICKER_BUSY;
 if(s->count==META_PICKER_CAPACITY)return META_PICKER_LIMIT;
 for(n=0;n<9 && stem[n];++n){}if(!n || n>8)return META_PICKER_ARGUMENT;
 at=s->count*9;for(i=0;i<n;++i)s->names[at+i]=(unsigned char)stem[i];for(;i<9;++i)s->names[at+i]=0;++s->count;return META_PICKER_OK;
}
unsigned __far __cdecl meta_picker_seal(meta_picker_state __far *s)
{
 if(!valid(s))return META_PICKER_ARGUMENT;if(s->phase!=META_PICKER_COLLECT)return META_PICKER_BUSY;
 s->phase=!s->count?META_PICKER_EMPTY:s->count==1?META_PICKER_ACTIVE:META_PICKER_SORT;s->index=1;s->limit=s->count;s->changed=0;return META_PICKER_OK;
}
unsigned __far __cdecl meta_picker_sort_step(meta_picker_state __far *s,unsigned budget)
{
 unsigned i,a,b,left,right;unsigned char temp;
 if(!valid(s) || !budget || budget>64)return META_PICKER_ARGUMENT;
 if(s->phase!=META_PICKER_SORT)return META_PICKER_BUSY;
 while(budget-- && s->phase==META_PICKER_SORT){
  a=(s->index-1)*9;b=s->index*9;
  for(i=0;i<8;++i){left=fold(s->names[a+i]);right=fold(s->names[b+i]);if(left!=right || !left)break;}
  if(left>right){for(i=0;i<9;++i){temp=s->names[a+i];s->names[a+i]=s->names[b+i];s->names[b+i]=temp;}s->changed=1;}
  if(++s->index==s->limit){
   if(!s->changed || --s->limit<2)s->phase=META_PICKER_ACTIVE;
   else{s->index=1;s->changed=0;}
  }
 }return META_PICKER_OK;
}
unsigned __far __cdecl meta_picker_key(meta_picker_state __far *s,unsigned key)
{
 if(!valid(s))return META_PICKER_ARGUMENT;if(s->phase!=META_PICKER_ACTIVE)return META_PICKER_BUSY;
 if(key==13)s->phase=META_PICKER_ACCEPT;
 else if(key==27)s->phase=META_PICKER_CANCEL;
 else if(key==0x4700){s->top=s->row=0;}
 else if(key==0x4f00){s->top=s->count>15?s->count-15:0;s->row=0;}
 else if(key==0x4800){if(s->row)--s->row;else if(s->top)--s->top;}
 else if(key==0x5000){if(s->top+s->row+1<s->count){if(s->row<14)++s->row;else ++s->top;}}
 else if(key==0x4900){if(s->top){s->top=s->top<15?0:s->top-15;s->row=0;}}
 else if(key==0x5100){if(s->top+15<s->count){s->top+=15;s->row=0;}}
 else return META_PICKER_BELL;
 return META_PICKER_OK;
}
unsigned __far __cdecl meta_picker_selected(const meta_picker_state __far *s,char __far *out)
{
 unsigned i,at;
 if(!valid(s) || !separate(s,sizeof(*s),out,9) || !separate(s->names,META_PICKER_BYTES,out,9))return META_PICKER_ARGUMENT;
 if(s->phase!=META_PICKER_ACCEPT)return META_PICKER_BUSY;
 at=(s->top+s->row)*9;for(i=0;i<9;++i)out[i]=(char)s->names[at+i];return META_PICKER_OK;
}
unsigned __far __cdecl meta_picker_draw(const meta_picker_state __far *s,unsigned __far *frame,unsigned attr)
{
 unsigned r,c,i,at,a,index;
 if(!valid(s) || attr>255 || !separate(s,sizeof(*s),frame,4000) || !separate(s->names,META_PICKER_BYTES,frame,4000))return META_PICKER_ARGUMENT;
 if(s->phase!=META_PICKER_ACTIVE)return META_PICKER_BUSY;
 for(r=3;r<=21;++r)for(c=32;c<=47;++c)frame[r*80+c]=(attr<<8)|' ';
 for(c=33;c<47;++c)frame[3*80+c]=frame[21*80+c]=(attr<<8)|205;
 for(r=4;r<21;++r)frame[r*80+32]=frame[r*80+47]=(attr<<8)|186;
 frame[3*80+32]=(attr<<8)|201;frame[3*80+47]=(attr<<8)|187;frame[21*80+32]=(attr<<8)|200;frame[21*80+47]=(attr<<8)|188;
 for(r=0;r<15;++r){index=s->top+r;if(index>=s->count)break;a=r==s->row?((attr&7)<<4)|((attr&0x70)>>4):attr;at=index*9;
  for(i=0;i<8 && s->names[at+i];++i)frame[(r+5)*80+35+i]=(a<<8)|s->names[at+i];
  for(;i<8;++i)frame[(r+5)*80+35+i]=(a<<8)|' ';
 }return META_PICKER_OK;
}
