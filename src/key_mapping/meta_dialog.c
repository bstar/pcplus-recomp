#include <dos.h>
#include "meta_dialog.h"
typedef char meta_dialog_layout[sizeof(meta_dialog_state)==684?1:-1];
#define TEXT __based(__segname("_CODE"))
#define LABEL(n,s) static const char TEXT n[]=s
LABEL(title," META KEYS ");LABEL(file_label,"FILE: ");LABEL(type_label,"TYPE");LABEL(definition,"DEFINITION");
LABEL(key_label,"Alt-");LABEL(aspect,"ASPECT");LABEL(program,"PROGRAM");LABEL(hook,"HOOK");LABEL(text,"TEXT");LABEL(unknown,"?");
LABEL(footer,"R) Revise  L) Load  S) Save  C) Clear  Esc) Exit");
LABEL(pending,"File operation pending...");LABEL(failed,"File operation failed. Definitions retained.");
static unsigned span(const void __far *p,unsigned n,unsigned long *at)
{unsigned long a=(unsigned long)FP_SEG(p)*16UL+FP_OFF(p);if(!p || (unsigned long)FP_OFF(p)+n>65536UL || a+n>0x100000UL)return 0;*at=a;return 1;}
static unsigned separate(const void __far *a,unsigned an,const void __far *b,unsigned bn)
{unsigned long x,y;return span(a,an,&x) && span(b,bn,&y) && (x+an<=y || y+bn<=x);}
static unsigned valid(const meta_dialog_state __far *s)
{
 unsigned long a;
 if(!span(s,sizeof(*s),&a) || s->cookie!=0x4d44 || s->phase>META_DIALOG_CLOSED || s->row>=10 || s->kind>=4)return 0;
 if(s->phase==META_DIALOG_WAIT && s->io!=META_DIALOG_LOAD && s->io!=META_DIALOG_SAVE)return 0;
 if(s->phase==META_DIALOG_TEXT && (s->text.cookie!=0x4d54 || s->text.phase!=META_TEXT_ACTIVE || s->text.cursor>=50 || s->text.insert>1 || s->text.full>1 || (s->text.full && s->text.cursor!=49)))return 0;
 return 1;
}
static unsigned schema(const unsigned char __far *records)
{
 unsigned row,i,at;
 for(row=0;row<10;++row){at=row*54;if(records[at+1] || records[at]>3)return 0;
  for(i=0;i<52 && records[at+2+i];++i){}if(i==52)return 0;
 }return 1;
}
static unsigned name_ok(const char __far *name)
{unsigned i;for(i=0;i<64 && name[i];++i)if((unsigned char)name[i]<32 || (unsigned char)name[i]>126)return 0;return i && i<64;}
static unsigned inputs(const meta_dialog_state __far *s,const unsigned char __far *records,const char __far *name)
{return separate(s,sizeof(*s),records,540) && separate(s,sizeof(*s),name,64) && schema(records) && name_ok(name);}
static void copy_in(meta_dialog_state __far *s,const unsigned char __far *records,const char __far *name)
{unsigned i;for(i=0;i<540;++i)s->records[i]=records[i];for(i=0;i<63 && name[i];++i)s->name[i]=name[i];s->name[i]=0;}
static void select_row(meta_dialog_state __far *s,unsigned row)
{s->row=row;s->kind=s->records[row*54];}
static void begin_kind(meta_dialog_state __far *s,unsigned row)
{select_row(s,row);s->phase=META_DIALOG_KIND;}
static unsigned bell(meta_dialog_state __far *s)
{++s->bells;return META_DIALOG_BELL;}
static void finish_kind(meta_dialog_state __far *s)
{s->records[s->row*54]=(unsigned char)s->kind;s->records[s->row*54+1]=0;}
unsigned __far __cdecl meta_dialog_open(meta_dialog_state __far *s,const unsigned char __far *records,const char __far *name,unsigned shape)
{
 if(!inputs(s,records,name))return META_DIALOG_ARGUMENT;
 copy_in(s,records,name);s->cookie=0x4d44;s->phase=META_DIALOG_OVERVIEW;s->row=0;s->kind=s->records[0];
 s->saved_shape=shape;s->bells=s->io=s->status=0;return META_DIALOG_OK;
}
unsigned __far __cdecl meta_dialog_key(meta_dialog_state __far *s,unsigned key)
{
 unsigned i,r,n;
 if(!valid(s) || s->phase==META_DIALOG_CLOSED)return META_DIALOG_ARGUMENT;
 if(s->phase==META_DIALOG_WAIT)return META_DIALOG_BUSY;
 if(s->phase==META_DIALOG_TEXT){
  r=meta_text_key(&s->text,key);
  if(r==META_TEXT_ARGUMENT)return META_DIALOG_ARGUMENT;
  if(r==META_TEXT_BELL)return bell(s);
  if(r==META_TEXT_CANCEL){s->phase=META_DIALOG_OVERVIEW;select_row(s,s->row);}
  else if(r==META_TEXT_ACCEPT){
   if(meta_text_commit(&s->text,s->records+s->row*54+2)!=META_TEXT_ACCEPT)return META_DIALOG_ARGUMENT;
   if(s->text.result==0x0f00)s->phase=META_DIALOG_KIND;
   else{finish_kind(s);if(s->text.result==9)begin_kind(s,(s->row+1)%10);else s->phase=META_DIALOG_OVERVIEW;}
  }return META_DIALOG_OK;
 }
 if(s->phase==META_DIALOG_KIND){
  if(key==27){s->phase=META_DIALOG_OVERVIEW;select_row(s,s->row);}
  else if(key==0x0f00){finish_kind(s);begin_kind(s,s->row?s->row-1:9);}
  else if(key==9 || key==13){
   if(meta_text_begin(&s->text,s->records+s->row*54+2,s->saved_shape)!=META_TEXT_ACTIVE)return META_DIALOG_ARGUMENT;
   s->phase=META_DIALOG_TEXT;
  }else s->kind=(s->kind+1)%4;
  return META_DIALOG_OK;
 }
 if(key>'`' && key<'{')key^=32;
 if(key==27)s->phase=META_DIALOG_CLOSED;
 else if(key==9 || key==0x5000)select_row(s,(s->row+1)%10);
 else if(key==0x0f00 || key==0x4800)select_row(s,s->row?s->row-1:9);
 else if(key=='R')begin_kind(s,s->row);
 else if(key=='C'){
  for(i=0;i<10;++i){n=i*54;s->records[n]=3;s->records[n+1]=s->records[n+2]=0;}
  select_row(s,s->row);
 }else if(key=='L' || key=='S'){
  s->io=key=='L'?META_DIALOG_LOAD:META_DIALOG_SAVE;s->phase=META_DIALOG_WAIT;s->status=0;return s->io;
 }else return bell(s);
 return META_DIALOG_OK;
}
unsigned __far __cdecl meta_dialog_complete(meta_dialog_state __far *s,unsigned status,const unsigned char __far *records,const char __far *name)
{
 if(!valid(s) || s->phase!=META_DIALOG_WAIT || (s->io!=META_DIALOG_LOAD && s->io!=META_DIALOG_SAVE))return META_DIALOG_ARGUMENT;
 if(!status && s->io==META_DIALOG_LOAD){if(!inputs(s,records,name))return META_DIALOG_ARGUMENT;copy_in(s,records,name);}
 s->status=status;s->io=0;s->phase=META_DIALOG_OVERVIEW;select_row(s,s->row);return META_DIALOG_OK;
}
unsigned __far __cdecl meta_dialog_cursor(const meta_dialog_state __far *s)
{
 if(!valid(s) || s->phase==META_DIALOG_CLOSED || s->phase==META_DIALOG_WAIT)return 0xffff;
 if(s->phase==META_DIALOG_OVERVIEW)return 0x110c;
 return ((s->row+6)<<8)|(s->phase==META_DIALOG_TEXT?25+s->text.cursor:17);
}
unsigned __far __cdecl meta_dialog_shape(const meta_dialog_state __far *s)
{
 if(!valid(s))return 0xffff;
 if(s->phase==META_DIALOG_TEXT)return meta_text_shape(&s->text);
 return s->phase==META_DIALOG_WAIT?s->saved_shape|0x2000:s->saved_shape;
}
static void label(unsigned __far *frame,unsigned at,const char __far *text,unsigned attr,unsigned limit)
{while(limit-- && *text)frame[at++]=(attr<<8)|(unsigned char)*text++;}
unsigned __far __cdecl meta_dialog_draw(const meta_dialog_state __far *s,unsigned __far *frame,unsigned attr)
{
 unsigned r,c,at,a,k,i;const char __far *kind;
 if(!valid(s) || attr>255 || !separate(s,sizeof(*s),frame,4000))return META_DIALOG_ARGUMENT;
 if(s->phase==META_DIALOG_CLOSED)return META_DIALOG_OK;
 for(r=3;r<=19;++r)for(c=7;c<=76;++c)frame[r*80+c]=(attr<<8)|' ';
 for(c=8;c<76;++c)frame[3*80+c]=frame[19*80+c]=(attr<<8)|205;
 for(r=4;r<19;++r)frame[r*80+7]=frame[r*80+76]=(attr<<8)|186;
 frame[3*80+7]=(attr<<8)|201;frame[3*80+76]=(attr<<8)|187;frame[19*80+7]=(attr<<8)|200;frame[19*80+76]=(attr<<8)|188;
 label(frame,3*80+20,title,attr,11);label(frame,4*80+9,file_label,attr,6);label(frame,4*80+15,s->name,attr,60);
 label(frame,5*80+17,type_label,attr,7);label(frame,5*80+25,definition,attr,50);
 for(r=0;r<10;++r){
  a=r==s->row?((attr&7)<<4)|((attr&0x70)>>4):attr;
  k=(r==s->row && (s->phase==META_DIALOG_KIND || s->phase==META_DIALOG_TEXT))?s->kind:s->records[r*54];
  /* Watcom loses the based-code segment through a ternary of these arrays.
   * Separate assignments preserve each explicit CS-to-far conversion. */
  if(k==0)kind=aspect;else if(k==1)kind=program;else if(k==2)kind=hook;else if(k==3)kind=text;else kind=unknown;
  at=(r+6)*80;label(frame,at+9,key_label,attr,4);frame[at+13]=(attr<<8)|(r==9?'0':'1'+r);
  for(c=17;c<75;++c)frame[at+c]=(a<<8)|' ';label(frame,at+17,kind,a,7);
  if(r==s->row && s->phase==META_DIALOG_TEXT){for(c=0;c<50;++c)frame[at+25+c]=(a<<8)|s->text.field[c];}
  else{for(i=0;i<50 && s->records[r*54+2+i];++i)frame[at+25+i]=(a<<8)|s->records[r*54+2+i];}
 }
 label(frame,17*80+12,footer,attr,62);
 if(s->phase==META_DIALOG_WAIT)label(frame,18*80+12,pending,attr,60);
 else if(s->status)label(frame,18*80+12,failed,attr,60);
 return META_DIALOG_OK;
}
