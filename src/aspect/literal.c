#include "literal.h"
#include <string.h>

/* Recovered compiler table at original file1057C, used by function22A9.
 * These are algorithm constants, not a copied executable/resource image. */
static const unsigned char transform[13] = {
    0xb3,0x35,0x0b,0xc7,0x47,0x29,0x1d,0xfb,0x1f,0x7f,0x05,0x59,0x17
};

#if defined(__WATCOMC__)
typedef unsigned long aspect_address;
#else
typedef uintptr_t aspect_address;
#endif
static unsigned span(const void *p,unsigned size)
{
    if(!p)return 0;
#if defined(__WATCOMC__)
    if((unsigned long)(unsigned)p+size>65536UL)return 0;
#else
    if((aspect_address)p+size<(aspect_address)p)return 0;
#endif
    return 1;
}
static aspect_address address(const void *p)
{
#if defined(__WATCOMC__)
    return (unsigned long)(unsigned)p;
#else
    return (aspect_address)p;
#endif
}
static unsigned separate(const void *a,unsigned n,const void *b,unsigned m)
{
    return address(a)+n<=address(b) || address(b)+m<=address(a);
}
static unsigned arguments(const void *input,unsigned n,void *output,unsigned m,
    aspect_literal_result *result)
{
    return span(input,n) && span(output,m) && span(result,sizeof(*result)) &&
        separate(input,n,output,m) && separate(input,n,result,sizeof(*result)) &&
        separate(output,m,result,sizeof(*result));
}
static unsigned delta(unsigned index,unsigned parity)
{
    unsigned value=transform[index];
    return ((index+parity)&1)?(0U-value)&255U:value;
}
unsigned aspect_literal_encode(const unsigned char *text,unsigned length,
    aspect_u32 position,aspect_u32 source_line,unsigned char *wire,
    unsigned capacity,aspect_literal_result *result)
{
    unsigned i,stride,index,parity;
    aspect_u32 sum;
    if(length<1 || length>ASPECT_LITERAL_MAX)return ASPECT_LITERAL_RANGE;
    if(capacity<length+2)return ASPECT_LITERAL_TRUNCATED;
    if(!arguments(text,length,wire,length+2,result))return ASPECT_LITERAL_ARGUMENT;
    for(i=0;i<length;++i)if(!text[i])return ASPECT_LITERAL_FORMAT;
    sum=position+source_line; /* native ADD/ADC wraps at32 bits */
    stride=(unsigned)(sum%12UL)+1;parity=(unsigned)position&1;
    wire[0]=(unsigned char)(0xb3U+length);
    wire[1]=(unsigned char)((length+stride)|(parity<<7));
    index=0;
    for(i=0;i<length;++i){
        index=(index+stride)%13;
        wire[i+2]=(unsigned char)(text[i]+delta(index,parity));
    }
    result->text_length=length;result->wire_length=length+2;result->stride=stride;
    return ASPECT_LITERAL_OK;
}
unsigned aspect_literal_decode(const unsigned char *wire,unsigned available,
    aspect_u32 position,unsigned char *text,unsigned capacity,
    aspect_literal_result *result)
{
    unsigned i,length,stride,index,parity,value;
    unsigned char staged[ASPECT_LITERAL_MAX];
    if(!span(wire,available) || !span(result,sizeof(*result)))return ASPECT_LITERAL_ARGUMENT;
    if(available<2)return ASPECT_LITERAL_TRUNCATED;
    length=(wire[0]-0xb3U)&255U;
    if(length<1 || length>ASPECT_LITERAL_MAX)return ASPECT_LITERAL_FORMAT;
    if(available<length+2 || capacity<length)return ASPECT_LITERAL_TRUNCATED;
    if(!arguments(wire,available,text,length,result))return ASPECT_LITERAL_ARGUMENT;
    value=wire[1]&127U;
    if(value<=length || value>length+12)return ASPECT_LITERAL_FORMAT;
    stride=value-length;parity=(unsigned)position&1;
    if(wire[1]!=(unsigned char)((length+stride)|(parity<<7)))return ASPECT_LITERAL_FORMAT;
    index=0;
    for(i=0;i<length;++i){
        index=(index+stride)%13;
        staged[i]=(unsigned char)(wire[i+2]-delta(index,parity));
        if(!staged[i])return ASPECT_LITERAL_FORMAT;
    }
    memcpy(text,staged,length);
    result->text_length=length;result->wire_length=length+2;result->stride=stride;
    return ASPECT_LITERAL_OK;
}
