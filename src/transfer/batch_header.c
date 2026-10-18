#include "batch_header.h"
#include <stddef.h>
#include <string.h>
typedef char bh_result_size[sizeof(batch_header_result)==36?1:-1];
typedef char bh_size_offset[offsetof(batch_header_result,size)==16?1:-1];
typedef char bh_extension_offset[offsetof(batch_header_result,extension_offset)==32?1:-1];
static unsigned extent(const void *p,unsigned n)
{
#ifdef __WATCOMC__
 return p && (unsigned long)(unsigned)p+n<=65536UL;
#else
 return p && (uintptr_t)p<=UINTPTR_MAX-n;
#endif
}
static unsigned disjoint(const void *a,unsigned an,const void *b,unsigned bn)
{
#ifdef __WATCOMC__
 return (unsigned long)(unsigned)a+an<=(unsigned)b || (unsigned long)(unsigned)b+bn<=(unsigned)a;
#else
 return (uintptr_t)a+an<=(uintptr_t)b || (uintptr_t)b+bn<=(uintptr_t)a;
#endif
}
static unsigned fold(unsigned c){return c>='a' && c<='z'?c-32:c;}
static unsigned leaf(const unsigned char *name,unsigned n)
{
 unsigned i,c,base=0,ext=0,dot=0;char stem[9];
 if(!n || n>12)return 0;
 for(i=0;i<n;++i){
  c=fold(name[i]);if(c=='.'){if(dot || !base)return 0;dot=1;continue;}
  if(!((c>='A' && c<='Z') || (c>='0' && c<='9') || strchr("!#$%&'()-@^_`{}~",c)))return 0;
  if(dot){if(++ext>3)return 0;}else{if(base==8)return 0;stem[base++]=(char)c;}
 }
 if(!base || (dot && !ext))return 0;stem[base]=0;
 if(!strcmp(stem,"CON") || !strcmp(stem,"PRN") || !strcmp(stem,"AUX") || !strcmp(stem,"NUL") || !strcmp(stem,"CLOCK$"))return 0;
 return !(base==4 && stem[3]>='1' && stem[3]<='9' && (!memcmp(stem,"COM",3) || !memcmp(stem,"LPT",3)));
}
unsigned __cdecl batch_header_end(unsigned char *block,unsigned capacity)
{
 if(capacity!=128 || !extent(block,capacity))return BH_ARGUMENT;
 memset(block,0,128);return BH_OK;
}
unsigned __cdecl batch_header_encode(const char *name,unsigned capacity,batch_header_u32 size,unsigned char *block,unsigned block_capacity)
{
 unsigned n,i,j;unsigned char stage[128];char digits[10];
 if(!capacity || capacity>64 || !extent(name,capacity) || block_capacity!=128 || !extent(block,128) || !disjoint(name,capacity,block,128))return BH_ARGUMENT;
 for(n=0;n<capacity && name[n];++n){}
 if(n==capacity || !leaf((const unsigned char *)name,n))return BH_NAME;
 memset(stage,0,128);memcpy(stage,name,n);i=0;
 do{digits[i++]=(char)('0'+size%10);size/=10;}while(size);
 for(j=0;j<i;++j)stage[n+1+j]=(unsigned char)digits[i-1-j];
 memcpy(block,stage,128);return BH_OK;
}
unsigned __cdecl batch_header_decode(const unsigned char *block,unsigned capacity,batch_header_result *result)
{
 batch_header_result stage;batch_header_u32 values[4],value,limit=0xffffffffUL;
 unsigned name_end,end,i,j,field=0,base,digit,start,status=BH_OK;
 if((capacity!=128 && capacity!=1024) || !extent(block,capacity) || !extent(result,sizeof(*result)) || !disjoint(block,capacity,result,sizeof(*result)))return BH_ARGUMENT;
 memset(&stage,0,sizeof(stage));
 for(name_end=0;name_end<capacity && block[name_end];++name_end){}
 if(name_end==capacity)return BH_FORMAT;
 if(!name_end){
  for(i=1;i<capacity;++i)if(block[i])return BH_FORMAT;
  stage.kind=BH_END;memcpy(result,&stage,sizeof(stage));return BH_OK;
 }
 if(!leaf(block,name_end))return BH_NAME;
 stage.kind=BH_FILE;memcpy(stage.name,block,name_end);
 for(end=name_end+1;end<capacity && block[end];++end){}
 if(end==capacity)return BH_FORMAT;
 for(i=end+1;i<capacity;++i)if(block[i])return BH_FORMAT;
 i=name_end+1;
 while(i<end){
  start=i;while(i<end && block[i]!=' '){if(block[i]<33 || block[i]>126)return BH_FORMAT;++i;}
  if(start==i)return BH_FORMAT;
  if(field<4){
   value=0;base=field?8:10;
   for(j=start;j<i;++j){
    if(block[j]<'0' || block[j]>'9')return BH_FORMAT;digit=block[j]-'0';
    if(digit>=base)return BH_FORMAT;
    if(value>(limit-digit)/base)return BH_OVERFLOW;
    value=value*base+digit;
   }
   values[field]=value;stage.flags|=(unsigned short)(1U<<field);
  }else if(field==4){stage.extension_offset=(unsigned short)start;stage.extension_length=(unsigned short)(end-start);stage.flags|=BH_EXTENSION;}
  ++field;
  if(i<end){++i;if(i==end || block[i]==' ')return BH_FORMAT;}
 }
 if(stage.flags&BH_LENGTH)stage.size=values[0];
 if(stage.flags&BH_MTIME)stage.mtime=values[1];
 if(stage.flags&BH_MODE)stage.mode=values[2];
 if(stage.flags&BH_SERIAL)stage.serial=values[3];
 memcpy(result,&stage,sizeof(stage));return status;
}
