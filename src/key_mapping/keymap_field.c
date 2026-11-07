#include "keymap_field.h"
#include "keymap_text.h"
static unsigned valid(const keymap_field_state *s)
{
 return s && s->cookie==0x4b46 && s->phase<=KEYMAP_FIELD_CANCEL &&
  s->cursor<=KEYMAP_FIELD_WIDTH && s->insert<=1;
}
unsigned keymap_field_begin(keymap_field_state *s,const unsigned char *text,unsigned length,unsigned start,unsigned end)
{
 unsigned i;
 if(!s || !text || length>KEYMAP_FIELD_WIDTH || start>31 || end>31)return KEYMAP_FIELD_ARGUMENT;
 for(i=0;i<length;++i)if(!text[i])return KEYMAP_FIELD_ARGUMENT;
 s->cookie=0x4b46;s->phase=KEYMAP_FIELD_ACTIVE;s->cursor=s->insert=0;s->saved_start=start;s->saved_end=end;
 for(i=0;i<KEYMAP_FIELD_WIDTH;++i)s->field[i]=i<length?text[i]:' ';
 return KEYMAP_FIELD_ACTIVE;
}
unsigned keymap_field_key(keymap_field_state *s,unsigned key)
{
 unsigned c,i,n;
 unsigned char marker;
 if(!valid(s) || s->phase!=KEYMAP_FIELD_ACTIVE)return KEYMAP_FIELD_ARGUMENT;
 c=s->cursor;
 if(key==13){s->phase=KEYMAP_FIELD_ACCEPT;return s->phase;}
 if(key==27){s->phase=KEYMAP_FIELD_CANCEL;return s->phase;}
 if(key==9){for(i=0;i<KEYMAP_FIELD_WIDTH;++i)s->field[i]=' ';s->cursor=0;}
 else if(key==0x4700)s->cursor=0;
 else if(key==0x4b00){if(!c)return KEYMAP_FIELD_BELL;s->cursor=c-1;}
 else if(key==0x4d00){if(c>=KEYMAP_FIELD_WIDTH-1)return KEYMAP_FIELD_BELL;s->cursor=c+1;}
 else if(key==0x4f00){n=KEYMAP_FIELD_WIDTH;while(n && s->field[n-1]==' ')--n;s->cursor=n;}
 else if(key==0x5200)s->insert=!s->insert;
 else if(key==0x0e08){
  if(!c)return KEYMAP_FIELD_BELL;
  for(i=c-1;i<KEYMAP_FIELD_WIDTH-1;++i)s->field[i]=s->field[i+1];
  s->field[KEYMAP_FIELD_WIDTH-1]=' ';s->cursor=c-1;
 }else if(key==0x5300){
  if(c==KEYMAP_FIELD_WIDTH)return KEYMAP_FIELD_BELL;
  for(i=c;i<KEYMAP_FIELD_WIDTH-1;++i)s->field[i]=s->field[i+1];
  s->field[KEYMAP_FIELD_WIDTH-1]=' ';
 }else if(key==0x7500){for(i=c;i<KEYMAP_FIELD_WIDTH;++i)s->field[i]=' ';}
 else if(key==0x1e || key==0x0300 || key==0x0e7f){
  if(c>KEYMAP_FIELD_WIDTH-3)return KEYMAP_FIELD_BELL;
  if(s->insert)for(i=KEYMAP_FIELD_WIDTH-1;i>=c+3;--i)s->field[i]=s->field[i-3];
  marker=(unsigned char)(key==0x1e?'^':key==0x0300?'0':'D');
  s->field[c]=0xae;s->field[c+1]=marker;s->field[c+2]=0xaf;s->cursor=c+3;
 }else if(key>=32 && key<=254 && key!=127){
  if(c==KEYMAP_FIELD_WIDTH)return KEYMAP_FIELD_BELL;
  if(s->insert)for(i=KEYMAP_FIELD_WIDTH-1;i>c;--i)s->field[i]=s->field[i-1];
  s->field[c]=(unsigned char)key;s->cursor=c<KEYMAP_FIELD_WIDTH-1?c+1:c;
 }else return KEYMAP_FIELD_BELL;
 return KEYMAP_FIELD_ACTIVE;
}
int keymap_field_commit(const keymap_field_state *s,unsigned char *target,unsigned capacity)
{
 unsigned n;
 if(!valid(s) || s->phase!=KEYMAP_FIELD_ACCEPT)return -1;
 n=KEYMAP_FIELD_WIDTH;while(n && s->field[n-1]==' ')--n;
 return keymap_text_decode(s->field,n,target,capacity);
}
unsigned keymap_field_shape(const keymap_field_state *s)
{
 unsigned start;
 if(!valid(s))return 0xffff;
 start=s->phase==KEYMAP_FIELD_ACTIVE && s->insert?s->saved_end/2+1:s->saved_start;
 return (start<<8)|s->saved_end;
}
