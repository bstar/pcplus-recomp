#include "document.h"
static unsigned exact(help_document *d,unsigned long at,unsigned char *out,unsigned bytes)
{
 unsigned got=0;
 if(at>d->bytes||bytes>d->bytes-at)return HELP_DOC_FORMAT;
 if(d->read(d->cookie,at,out,bytes,&got)||got!=bytes)return HELP_DOC_IO;
 return HELP_DOC_OK;
}
static unsigned record(help_document *d,unsigned topic,help_record *out)
{
 unsigned char raw[38];unsigned status;
 status=exact(d,3UL+(unsigned)(topic*38U),raw,38);if(status)return status;
 return help_record_decode(raw,38,&d->header,d->bytes,out)?HELP_DOC_FORMAT:HELP_DOC_OK;
}
unsigned HELP_DOC_CODE HELP_DOC_CALL help_document_begin(help_document *d,help_read_at read,void *cookie,unsigned long bytes)
{
 unsigned char raw[3];unsigned status;
 if(!d||!read)return HELP_DOC_ARGUMENT;
 d->phase=0;d->read=read;d->cookie=cookie;d->bytes=bytes;
 if(bytes>0x7fffffffUL)return HELP_DOC_RANGE;
 status=exact(d,0,raw,3);if(status)return status;
 if(help_header_decode(raw,3,bytes,&d->header))return HELP_DOC_FORMAT;
 d->index=0;d->total=0;d->minimum=d->header.text_start;d->phase=1;
 return HELP_DOC_PENDING;
}
unsigned HELP_DOC_CODE HELP_DOC_CALL help_document_step(help_document *d)
{
 help_record r;unsigned status;
 if(!d||!d->phase)return HELP_DOC_ARGUMENT;
 if(d->phase==2)return HELP_DOC_OK;
 if(d->phase!=1)return HELP_DOC_FORMAT;
 status=record(d,d->index,&r);
 if(status){d->phase=3;return status;}
 if(r.offset<d->minimum){d->phase=3;return HELP_DOC_FORMAT;}
 d->minimum=r.offset+r.lines;d->total+=r.lines;++d->index;
 if(d->index<d->header.topics)return HELP_DOC_PENDING;
 if(d->total!=d->header.lines){d->phase=3;return HELP_DOC_FORMAT;}
 d->phase=2;return HELP_DOC_OK;
}
unsigned HELP_DOC_CODE HELP_DOC_CALL help_cursor_begin(help_cursor *c,help_document *d,unsigned topic)
{
 help_record next;unsigned status;
 if(!c||!d||d->phase!=2||topic>=d->header.topics)return HELP_DOC_ARGUMENT;
 c->document=0;
 status=record(d,topic,&c->record);if(status)return status;
 c->end=d->bytes;
 if(topic+1<d->header.topics){status=record(d,topic+1,&next);if(status)return status;c->end=next.offset;}
 if(c->end<c->record.offset||c->record.lines>c->end-c->record.offset)return HELP_DOC_FORMAT;
 c->document=d;c->topic=topic;c->number=c->used=c->available=c->length=0;
 c->offset=c->record.offset;c->line[0]=0;return HELP_DOC_OK;
}
unsigned HELP_DOC_CODE HELP_DOC_CALL help_cursor_step(help_cursor *c)
{
 unsigned bytes,status;unsigned char value;
 if(!c||!c->document||c->document->phase!=2)return HELP_DOC_ARGUMENT;
 if(c->number>=c->record.lines)return HELP_DOC_END;
 if(c->used==c->available){
  if(c->offset>=c->end)return HELP_DOC_FORMAT;
  bytes=c->end-c->offset>80?80:(unsigned)(c->end-c->offset);
  status=exact(c->document,c->offset,c->buffer,bytes);if(status)return status;
  c->offset+=bytes;c->available=bytes;c->used=0;
 }
 while(c->used<c->available){
  value=c->buffer[c->used++];
  if(value==10){
   bytes=c->length;
   if(bytes&&c->line[bytes-1]==13)--bytes;
   if(bytes>80)return HELP_DOC_RANGE;
   c->line[bytes]=0;c->length=0;++c->number;return HELP_DOC_LINE;
  }
  if(!value)return HELP_DOC_FORMAT;
  if(c->length>=81)return HELP_DOC_RANGE;
  c->line[c->length++]=(char)value;
 }
 return HELP_DOC_PENDING;
}
static unsigned fold(unsigned c){return c>='a'&&c<='z'?c-32:c;}
static unsigned matches(const char *text,const char *query,unsigned length)
{
 unsigned i;const char *p;
 for(p=text;*p;++p){
  for(i=0;i<length&&p[i]&&fold((unsigned char)p[i])==fold((unsigned char)query[i]);++i){}
  if(i==length)return 1;
 }
 return 0;
}
unsigned HELP_DOC_CODE HELP_DOC_CALL help_find_begin(help_find *f,help_document *d,const char *query,unsigned topic,unsigned long position)
{
 unsigned i;
 if(!f||!d||d->phase!=2||!query||topic>=d->header.topics||position>65536UL)return HELP_DOC_ARGUMENT;
 f->active=0;
 for(i=0;i<32&&query[i];++i){if((unsigned char)query[i]<32||(unsigned char)query[i]==127)return HELP_DOC_ARGUMENT;}
 if(!i||i==32)return HELP_DOC_ARGUMENT;
 for(f->length=0;f->length<=i;++f->length)f->query[f->length]=query[f->length];
 f->length=i;f->document=d;f->topic=f->anchor_topic=topic;f->anchor_line=position;
 f->wrapped=f->stage=0;f->active=1;return HELP_DOC_PENDING;
}
void HELP_DOC_CODE HELP_DOC_CALL help_find_cancel(help_find *f)
{if(f)f->active=0;}
unsigned HELP_DOC_CODE HELP_DOC_CALL help_find_step(help_find *f)
{
 unsigned status;unsigned long position,minimum;
 if(!f||!f->active)return HELP_DOC_ARGUMENT;
 minimum=!f->wrapped&&f->topic==f->anchor_topic?f->anchor_line:0;
 if(!f->stage){
  if(f->wrapped&&f->topic==f->anchor_topic&&!f->anchor_line){f->active=0;return HELP_DOC_END;}
  status=help_cursor_begin(&f->cursor,f->document,f->topic);
  if(status){f->active=0;return status;}
  f->stage=1;
  if(!minimum&&matches(f->cursor.record.title,f->query,f->length)){
   f->match_topic=f->topic;f->match_line=0;f->active=0;return HELP_DOC_FOUND;
  }
  return HELP_DOC_PENDING;
 }
 position=(unsigned long)f->cursor.number+1;
 if(f->wrapped&&f->topic==f->anchor_topic&&position>=f->anchor_line){f->active=0;return HELP_DOC_END;}
 status=help_cursor_step(&f->cursor);
 if(status==HELP_DOC_LINE){
  if(position>=minimum&&matches(f->cursor.line,f->query,f->length)){
   f->match_topic=f->topic;f->match_line=position;f->active=0;return HELP_DOC_FOUND;
  }
  return HELP_DOC_PENDING;
 }
 if(status==HELP_DOC_PENDING)return status;
 if(status!=HELP_DOC_END){f->active=0;return status;}
 if(f->wrapped&&f->topic==f->anchor_topic){f->active=0;return HELP_DOC_END;}
 if(++f->topic==f->document->header.topics)f->topic=0;
 if(f->topic==f->anchor_topic)f->wrapped=1;
 f->stage=0;return HELP_DOC_PENDING;
}
