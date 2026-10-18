#include "blocks.h"
#include <string.h>
unsigned __cdecl transfer_crc_buffer_original(const unsigned char *,unsigned);
static unsigned extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
unsigned __cdecl transfer_crc16(const unsigned char *source,unsigned count,unsigned *result)
{
 unsigned crc;
 if(count>32768U)return 2;
 if(!extent(result,2) || (count && !extent(source,count)))return 1;
 crc=transfer_crc_buffer_original(source,count);*result=crc;return 0;
}
unsigned __cdecl transfer_block_encode(const unsigned char *source,unsigned count,
 unsigned block,unsigned crc,unsigned char *destination,unsigned capacity)
{
 unsigned char stage[1029];unsigned i,sum=0,length,value;
 if((count!=128 && count!=1024) || block>255 || crc>1)return 2;
 length=count+(crc?5:4);
 if(capacity<length)return 3;
 if(!extent(source,count) || !extent(destination,capacity))return 1;
 stage[0]=(unsigned char)(count==128?1:2);stage[1]=(unsigned char)block;
 stage[2]=(unsigned char)~block;memcpy(stage+3,source,count);
 if(crc){
  value=transfer_crc_buffer_original(stage+3,count);
  stage[count+3]=(unsigned char)(value>>8);stage[count+4]=(unsigned char)value;
 }else{
  for(i=0;i<count;++i)sum+=stage[3+i];stage[count+3]=(unsigned char)sum;
 }
 memcpy(destination,stage,length);return 0;
}
