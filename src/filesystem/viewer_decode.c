#include "viewer_decode.h"
#include <dos.h>
typedef unsigned word;
typedef unsigned char byte;
typedef char state_layout[sizeof(viewer_decode_state)==26?1:-1];
#define COOKIE 0x5650U

static unsigned long address(const void __far *p)
{return ((unsigned long)FP_SEG(p)<<4)+FP_OFF(p);}
static word span(const void __far *p,word n)
{
 if(!p||!n)return 0;
 return n-1<=0xffffU-FP_OFF(p)&&address(p)<=0xfffffUL-(n-1);
}
static word overlap(const void __far *a,word an,const void __far *b,word bn)
{return address(a)<address(b)+bn&&address(b)<address(a)+an;}
static word valid(viewer_decode_state __far *s)
{
 word size;
 if(!span(s,sizeof(*s)))return 0;
 if(s->cookie!=COOKIE||!s->width||s->width>132||!s->rows||s->rows>49)return 0;
 size=s->width*s->rows;
 if(!span(s->page,size)||overlap(s,sizeof(*s),s->page,size))return 0;
 if(s->row>s->rows||s->chunk>=133||s->shown>s->width||s->shown>s->chunk||
    s->kept>s->shown||s->nul>1)return 0;
 if(s->phase!=VIEWER_MORE&&s->phase!=VIEWER_PAGE&&s->phase!=VIEWER_EOF&&
    s->phase!=VIEWER_OVERFLOW)return 0;
 if(s->phase==VIEWER_MORE&&s->row==s->rows)return 0;
 if(s->phase==VIEWER_PAGE&&(s->row!=s->rows||s->chunk))return 0;
 return 1;
}
static void line(viewer_decode_state __far *s)
{
 word at=s->row*s->width,i;
 byte __far *page=s->page;
 for(i=s->kept;i<s->shown;i++)page[at+i]=' ';
 s->row++;s->chunk=s->shown=s->kept=s->nul=0;
 if(s->row==s->rows)s->phase=VIEWER_PAGE;
}
unsigned __far __cdecl viewer_decode_init(viewer_decode_state __far *s,
 byte __far *page,word capacity,word width,word rows,unsigned long position)
{
 word size,i;
 if(!span(s,sizeof(*s))||!width||width>132||!rows||rows>49)return VIEWER_ARGUMENT;
 size=width*rows;
 if(capacity<size||!span(page,size)||overlap(s,sizeof(*s),page,size))return VIEWER_ARGUMENT;
 for(i=0;i<size;i++)page[i]=' ';
 s->width=width;s->rows=rows;s->row=s->chunk=s->shown=s->kept=s->nul=0;
 s->phase=VIEWER_MORE;s->position=position;s->page=page;s->cookie=COOKIE;
 return VIEWER_MORE;
}
unsigned __far __cdecl viewer_decode_feed(viewer_decode_state __far *s,
 const byte __far *source,word count,word __far *used)
{
 word n=0,size;byte c;byte __far *page;
 if(count>256||!valid(s)||!span(used,sizeof(*used)))return VIEWER_ARGUMENT;
 size=s->width*s->rows;
 if(overlap(used,sizeof(*used),s,sizeof(*s))||overlap(used,sizeof(*used),s->page,size))return VIEWER_ARGUMENT;
 if(count&&(!span(source,count)||overlap(source,count,s,sizeof(*s))||
    overlap(source,count,s->page,size)||overlap(source,count,used,sizeof(*used))))return VIEWER_ARGUMENT;
 page=s->page;
 while(n<count&&s->phase==VIEWER_MORE){
  if(s->position==0xffffffffUL){s->phase=VIEWER_OVERFLOW;break;}
  c=source[n++];s->position++;
  if(s->chunk<s->width&&!s->nul){
   if(!c)s->nul=1;
   else{
    page[s->row*s->width+s->chunk]=c;s->shown=s->chunk+1;
    if(c>32)s->kept=s->shown;
   }
  }
  s->chunk++;
  if(c==10||s->chunk==133)line(s);
 }
 *used=n;return s->phase;
}
unsigned __far __cdecl viewer_decode_finish(viewer_decode_state __far *s)
{
 if(!valid(s))return VIEWER_ARGUMENT;
 if(s->phase!=VIEWER_MORE)return s->phase;
 if(s->chunk)line(s);
 s->phase=VIEWER_EOF;return VIEWER_EOF;
}
