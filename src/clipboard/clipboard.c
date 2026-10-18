#include "clipboard.h"
#include <string.h>
typedef char clip_word[sizeof(unsigned)==2?1:-1];
typedef char clip_state_abi[sizeof(clipboard_state)==214?1:-1];
static unsigned extent(const void *p,unsigned size)
{return p && (unsigned long)(unsigned)p+size<=65536UL;}
static unsigned apart(const void *a,unsigned an,const void *b,unsigned bn)
{return (unsigned long)(unsigned)a+an<=(unsigned)b || (unsigned long)(unsigned)b+bn<=(unsigned)a;}
static unsigned size13(const char *text,unsigned *size)
{
 unsigned i;
 for(i=0;i<13;++i){if(!extent(text,i+1))return 0;if(!text[i]){*size=i;return 1;}}
 return 0;
}
static unsigned valid(const clipboard_state *state)
{
 unsigned i,n;
 if(!extent(state,sizeof(*state)) || state->count>15)return 0;
 for(i=0;i<15;++i)if(!size13(state->names[i],&n))return 0;
 return 1;
}
unsigned __cdecl clip_initialize(clipboard_state *state)
{
 if(!extent(state,sizeof(*state)))return CLIP_ARGUMENT;
 memset(state,0,sizeof(*state));state->separator=13;return CLIP_OK;
}
unsigned __cdecl clip_change(clipboard_state *state,unsigned operation,
 unsigned index,const char *text)
{
 char candidate[13];unsigned n,i;
 if(!valid(state))return CLIP_STATE;
 if(operation==CLIP_ADD && state->count==15)return CLIP_FULL;
 if(operation==CLIP_ADD || operation==CLIP_EDIT){
  if(!size13(text,&n))return CLIP_ARGUMENT;
  memcpy(candidate,text,n+1);
  while(n && candidate[n-1]==' ')candidate[--n]=0;
  if(operation==CLIP_ADD){
   if(!n)return CLIP_EMPTY;
   for(i=0;i<n;++i)if(candidate[i]>='a' && candidate[i]<='z')candidate[i]-=32;
   for(i=0;i<15;++i)if(!strcmp(candidate,state->names[i]))return CLIP_DUPLICATE;
   index=state->count;
  }else if(index>=state->count)return CLIP_ARGUMENT;
  memset(state->names[index],0,13);memcpy(state->names[index],candidate,n+1);
  if(operation==CLIP_ADD){state->tags[index]=0;++state->count;}
  return CLIP_OK;
 }
 if(operation==CLIP_SEPARATOR){if(index>255)return CLIP_ARGUMENT;state->separator=index;return CLIP_OK;}
 if(operation==CLIP_PURGE){
  state->count=0;memset(state->names,0,sizeof(state->names));memset(state->tags,0,sizeof(state->tags));return CLIP_OK;
 }
 if(index>=state->count)return CLIP_ARGUMENT;
 if(operation==CLIP_TAG){state->tags[index]=state->tags[index]?0:16;return CLIP_OK;}
 if(operation!=CLIP_DELETE)return CLIP_ARGUMENT;
 for(i=index;i<14;++i){memcpy(state->names[i],state->names[i+1],13);state->tags[i]=state->tags[i+1];}
 memset(state->names[14],0,13);state->tags[14]=0;--state->count;return CLIP_OK;
}
unsigned __cdecl clip_valid_byte(unsigned value)
{
 unsigned char byte=(unsigned char)value;
 return byte>=0x21 && byte<=0x7e && !strchr(".\"/\\[]:|<>+=;,",byte);
}
unsigned __cdecl clip_extract(const unsigned char *row,unsigned width,
 unsigned dot,char *out,unsigned *first,unsigned *past)
{
 unsigned start,end,n;
 if(!width || width>132 || dot>=width || !extent(row,width) ||
  !extent(out,13) || !extent(first,2) || !extent(past,2) ||
  !apart(out,13,row,width) || !apart(first,2,row,width) || !apart(past,2,row,width) ||
  !apart(out,13,first,2) || !apart(out,13,past,2) || !apart(first,2,past,2))return CLIP_ARGUMENT;
 if(row[dot]!='.' || dot+1==width || !clip_valid_byte(row[dot+1]))return CLIP_NO_FILENAME;
 start=dot;while(start && clip_valid_byte(row[start-1]))--start;
 if(dot-start<1 || dot-start>8)return CLIP_NO_FILENAME;
 end=dot+1;while(end<width && end-dot<=3 && clip_valid_byte(row[end]))++end;
 n=end-start;memcpy(out,row+start,n);out[n]=0;*first=start;*past=end;return CLIP_OK;
}
unsigned __cdecl clip_prepare(const clipboard_state *state,unsigned mode,
 unsigned char *out,unsigned capacity,unsigned *size)
{
 unsigned need=0,i,n,at=0;
 if(!valid(state))return CLIP_STATE;
 if(mode>CLIP_TAGGED || !extent(size,2) || !apart(size,2,state,sizeof(*state)))return CLIP_ARGUMENT;
 if(state->count){
  if(mode==CLIP_SINGLE){size13(state->names[0],&n);need=n+1;}
  else{
   for(i=0;i<state->count;++i)if(mode==CLIP_ALL || state->tags[i]){
    size13(state->names[i],&n);need+=n+1;
   }
   if(need)++need;
  }
 }
 if(capacity<need)return CLIP_CAPACITY;
 if(need && (!extent(out,need) || !apart(out,need,state,sizeof(*state)) || !apart(out,need,size,2)))return CLIP_ARGUMENT;
 if(need){
  if(mode==CLIP_SINGLE){size13(state->names[0],&n);memcpy(out,state->names[0],n);at=n;}
  else for(i=0;i<state->count;++i)if(mode==CLIP_ALL || state->tags[i]){
   size13(state->names[i],&n);memcpy(out+at,state->names[i],n);at+=n;out[at++]=(unsigned char)state->separator;
  }
  out[at++]=13;
 }
 *size=at;return CLIP_OK;
}
