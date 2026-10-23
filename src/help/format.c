#include "format.h"
static unsigned word(const unsigned char *p)
{return p[0]|((unsigned)p[1]<<8);}
static unsigned long dword(const unsigned char *p)
{return (unsigned long)word(p)|((unsigned long)word(p+2)<<16);}
unsigned help_pointer_parse(const char *text,unsigned long *out)
{
 unsigned long value=0;unsigned digit,count=0;
 if(!text||!out)return HELP_ARGUMENT;
 while(*text){
  if(*text<'0'||*text>'9'||++count>10)return HELP_FORMAT;
  digit=*text++-'0';
  if(value>429496729UL||(value==429496729UL&&digit>5))return HELP_RANGE;
  value=(value<<3)+(value<<1)+digit;
 }
 /* An18-byte descriptor must fit in its16-bit parent segment. Parsing is
  * validation only: no foreign pointer is dereferenced by this module. */
 if(!count||!(value>>16)||(value&65535UL)>65536UL-HELP_CONTEXT_BYTES)return HELP_RANGE;
 *out=value;return HELP_OK;
}
unsigned help_context_decode(const unsigned char *data,unsigned bytes,help_context *out)
{
 help_context candidate;unsigned i;
 if(!data||!out)return HELP_ARGUMENT;
 if(bytes!=HELP_CONTEXT_BYTES)return HELP_FORMAT;
 candidate.path_offset=word(data);candidate.title_offset=word(data+2);
 candidate.topic=word(data+4);
 for(i=0;i<6;++i)candidate.ui_words[i]=word(data+6+i*2);
 /* Path/title strings require a later bounded copy from the validated
  * parent's segment. Nonzero offsets alone do not prove their readability. */
 if(!candidate.path_offset||!candidate.title_offset)return HELP_FORMAT;
 *out=candidate;return HELP_OK;
}
unsigned help_header_decode(const unsigned char *data,unsigned bytes,unsigned long file_bytes,help_header *out)
{
 help_header candidate;
 if(!data||!out)return HELP_ARGUMENT;
 if(bytes!=HELP_HEADER_BYTES)return HELP_FORMAT;
 candidate.topics=data[0];candidate.lines=word(data+1);
 candidate.text_start=3UL+(unsigned)(candidate.topics*38U);
 if(!candidate.topics||candidate.text_start>file_bytes)return HELP_FORMAT;
 *out=candidate;return HELP_OK;
}
unsigned help_record_decode(const unsigned char *data,unsigned bytes,const help_header *header,unsigned long file_bytes,help_record *out)
{
 help_record candidate;unsigned i;
 if(!data||!header||!out)return HELP_ARGUMENT;
 if(bytes!=HELP_RECORD_BYTES)return HELP_FORMAT;
 if(!header->topics||header->topics>255||header->text_start!=3UL+(unsigned)(header->topics*38U)||header->text_start>file_bytes)return HELP_FORMAT;
 for(i=0;i<32;++i)candidate.title[i]=data[i];
 candidate.title[32]=0;
 candidate.lines=word(data+32);candidate.offset=dword(data+34);
 if(candidate.lines>header->lines||candidate.offset<header->text_start||candidate.offset>file_bytes||
    candidate.lines>file_bytes-candidate.offset)return HELP_RANGE;
 *out=candidate;return HELP_OK;
}
unsigned help_index_validate(const unsigned char *data,unsigned bytes,unsigned long file_bytes)
{
 help_header header;help_record current;unsigned i,status;
 unsigned long sum=0,previous=0,previous_lines=0;
 if(!data)return HELP_ARGUMENT;
 if(bytes<HELP_HEADER_BYTES)return HELP_FORMAT;
 status=help_header_decode(data,HELP_HEADER_BYTES,file_bytes,&header);if(status)return status;
 if(bytes!=header.text_start)return HELP_FORMAT;
 for(i=0;i<header.topics;++i){
  status=help_record_decode(data+3+i*38,HELP_RECORD_BYTES,&header,file_bytes,&current);
  if(status)return status;
  if(i&&current.offset<previous+previous_lines)return HELP_FORMAT;
  previous=current.offset;previous_lines=current.lines;sum+=current.lines;
 }
 return sum==header.lines?HELP_OK:HELP_FORMAT;
}
unsigned help_topic_select(unsigned requested,unsigned topics)
{
 /* Original helper02CC compares a signed topic against the index count. */
 return requested>=32768U||requested>=topics?0:requested;
}
