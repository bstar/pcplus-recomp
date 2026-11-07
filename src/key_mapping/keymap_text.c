#include "keymap_text.h"

int keymap_text_encode(const unsigned char *source, unsigned length,
                       unsigned char *target, unsigned capacity)
{
 unsigned i,n=0,c,j=0;
 if(!source || !target || length>KEYMAP_STORAGE_MAX)return -1;
 for(i=0;i<length;++i){
  c=source[i];
  /* AE is also the original notation prefix: no lossless spelling exists. */
  if(!c || c==0xae)return -1;
  n+=c==0x1e || c==0x7f || c==0xff ? 3 : c<32 || c=='^' ? 2 : 1;
 }
 if(capacity<=n)return -1;
 for(i=0;i<length;++i){
  c=source[i];
  if(c==0x1e || c==0x7f || c==0xff){
   target[j++]=0xae;target[j++]=(unsigned char)(c==0x1e?'^':c==0x7f?'D':'0');target[j++]=0xaf;
  }else if(c<32){target[j++]='^';target[j++]=(unsigned char)(c+64);}
  else if(c=='^'){target[j++]='^';target[j++]='^';}
  else target[j++]=(unsigned char)c;
 }
 target[j]=0;return (int)j;
}

static int parse(const unsigned char *source,unsigned length,unsigned char *target)
{
 unsigned i=0,n=0,c;
 while(i<length){
  c=source[i++];
  if(c=='^'){
   if(i==length)return -1;
   c=source[i++];
   if(c=='^')c='^';
   else if(c>='a' && c<='z')c-=96;
   else if(c>='A' && c<='_')c-=64;
   else return -1;
  }else if(c==0xae){
   if(length-i<2 || source[i+1]!=0xaf)return -1;
   c=source[i];i+=2;
   if(c=='D')c=0x7f;else if(c=='0')c=0xff;else if(c=='^')c=0x1e;else return -1;
  }else if(c<32 || c==0x7f || c==0xff)return -1;
  if(n==KEYMAP_STORAGE_MAX)return -1;
  if(target)target[n]=(unsigned char)c;
  ++n;
 }
 return (int)n;
}
int keymap_text_decode(const unsigned char *source, unsigned length,
                       unsigned char *target, unsigned capacity)
{
 int n;
 if(!source || !target || length>KEYMAP_NOTATION_MAX)return -1;
 n=parse(source,length,0);
 if(n<0 || capacity<=(unsigned)n)return -1;
 parse(source,length,target);target[n]=0;return n;
}
