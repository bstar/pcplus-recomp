/* Independent diagnostic observer, not a replacement production allocator.
 * Pinned DOS16 heap layout confirmed against allocator bytes and REA:
 * 22-byte segment header;2-byte tagged blocks;6-byte circular free nodes;
 * a four-byte end marker (FFFF,0000).
 * No __based pointers and no allocations, DOS calls or heap mutation. */
#include "compiler_heap_snapshot.h"
#include <dos.h>
extern unsigned __fheapbeg;
static unsigned word(unsigned segment,unsigned offset)
{return *(const volatile unsigned __far *)MK_FP(segment,offset);}
static unsigned block_start(unsigned segment,unsigned target,unsigned long limit)
{
 unsigned long position=22;unsigned tag,size;
 while(position<target && position+2<=limit){
  tag=word(segment,(unsigned)position);size=tag&65534U;
  if(tag==65535U||size<6||position+size>limit-4)return 0;
  position+=size;
 }
 return position==target;
}
unsigned compiler_far_heap_snapshot(struct _heapinfo *entries,unsigned capacity,unsigned *count)
{
 unsigned segment=__fheapbeg,previous=0,next,segments=0,tag,size,used,free_count;
 unsigned cursor,prior,i;
 unsigned long limit,position,free_bytes,list_bytes;
 if(!entries||!count||*count>capacity)return 1;
 while(segment){
  if(++segments>4096 || segment<256 || segment>65534U || word(segment,2)!=previous || word(segment,16))return 1;
  next=word(segment,4);if(next==segment || (previous && previous==next))return 1;
  limit=word(segment,0);if(!limit)limit=65536UL;
  if(limit<30 || (limit&1) || (unsigned long)segment*16UL+limit>1048576UL)return 1;
  used=free_count=0;free_bytes=0;position=22;
  while(position+2<=limit){
   tag=word(segment,(unsigned)position);if(tag==65535U)break;
   size=tag&65534U;
   if(size<6 || position+size>limit-4)return 1;
   if(tag&1){
    ++used;if(*count>=capacity)return 2;
    entries[*count]._pentry=MK_FP(segment,(unsigned)position);
    entries[*count]._size=size;entries[(*count)++]._useflag=_USEDENTRY;
   }else{++free_count;free_bytes+=size;}
   position+=size;
  }
  if(position!=limit-4 || word(segment,(unsigned)position)!=65535U || word(segment,(unsigned)position+2)!=0 ||
     used!=word(segment,12) || free_count!=word(segment,14))return 1;
  cursor=word(segment,20);prior=16;list_bytes=0;
  for(i=0;i<free_count;++i){
   if(cursor<22 || (unsigned long)cursor+6>limit-4 || !block_start(segment,cursor,limit))return 1;
   tag=word(segment,cursor);
   if(tag&1 || word(segment,cursor+2)!=prior)return 1;
   list_bytes+=tag;prior=cursor;cursor=word(segment,cursor+4);
  }
  if(cursor!=16 || word(segment,18)!=prior || list_bytes!=free_bytes)return 1;
  previous=segment;segment=next;
 }
 return 0;
}
