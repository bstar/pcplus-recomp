/* Stack-only decoder for the generated acyclic byte-pair table. DS=SS. */
#include "command_ui_pairs.h"
typedef struct ui_reader {
 const char __far *cursor;
 byte pending[64];
 word count;
} ui_reader;
static void ui_begin(ui_reader *r,const char __far *s)
{r->cursor=s;r->count=0;}
static byte ui_next(ui_reader *r)
{
 byte c=r->count?r->pending[--r->count]:(byte)*r->cursor++;
 while(c>=128 && c<128+UI_PAIR_COUNT){
  if(r->count==64)return 0;
  r->pending[r->count++]=command_ui_pairs[c-128][1];
  c=command_ui_pairs[c-128][0];
 }
 return c;
}
static word ui_matches(const char __far *s)
{
 ui_reader r;byte recent[31],c;word at=0,filled=0,i,k;
 ui_begin(&r,s);
 if(!query_size)return ui_next(&r)!=0;
 if(query_size>31)return 0;
 while((c=ui_next(&r))!=0){
  recent[at]=fold(c);if(++at==query_size)at=0;
  if(filled<query_size)++filled;
  if(filled==query_size){
   k=at;for(i=0;i<query_size;++i){
    if(recent[k]!=fold((byte)query[i]))break;
    if(++k==query_size)k=0;
   }
   if(i==query_size)return 1;
  }
 }
 return 0;
}
