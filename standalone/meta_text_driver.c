/* Frozen original-instruction traces, consumed independently of the model. */
#include <stdio.h>
#include <string.h>
#include <dos.h>
#include "meta_text.h"
static meta_text_state state,saved;
static unsigned char source[52],original[52],expected[52],frame[50];
static unsigned code_segment(void);
#pragma aux code_segment = "mov ax,cs" value [ax] modify [];
static unsigned data_segment(void);
#pragma aux data_segment = "mov ax,ds" value [ax] modify [];
static unsigned stack_segment(void);
#pragma aux stack_segment = "mov ax,ss" value [ax] modify [];
static unsigned word(FILE *f){unsigned v;if(fread(&v,2,1,f)!=1)return 0xffff;return v;}
static int get(FILE *f,void *p,unsigned n){return fread(p,1,n,f)==n;}
int main(void)
{
 FILE *f=fopen("CASES.BIN","rb");unsigned count,index,n,i,key,cursor,shape,bells,seen,status,result,final_bells,final_shape,guards=0;
 unsigned long states=0;
 if(FP_SEG(meta_text_key)==code_segment() || data_segment()!=stack_segment())return 28;
 if(!f || word(f)!=0x4d54)return 1;count=word(f);
 for(index=0;index<count;++index){
  if(!get(f,source,52))return 2;memcpy(original,source,52);n=word(f);seen=0;
  if(meta_text_begin(&state,source,0x0607)!=META_TEXT_ACTIVE)return 3;
  for(i=0;i<n;++i){
   key=word(f);if(!get(f,frame,50))return 4;cursor=word(f);shape=word(f);bells=word(f);
   if(memcmp(state.field,frame,50) || state.cursor!=cursor || meta_text_shape(&state)!=shape || seen!=bells){printf("FAIL state %u/%u cursor %u/%u shape %u/%u bells %u/%u\r\n",index,i,state.cursor,cursor,meta_text_shape(&state),shape,seen,bells);return 5;}
   status=meta_text_key(&state,key);if(status==META_TEXT_BELL)++seen;else if(status==META_TEXT_ARGUMENT)return 6;
   ++states;
  }
  if(!get(f,expected,52))return 7;result=word(f);final_bells=word(f);final_shape=word(f);
  if(memcmp(source,original,52))return 8;
  if(state.phase==META_TEXT_ACCEPT){if(meta_text_commit(&state,source)!=META_TEXT_ACCEPT)return 9;}
  else if(state.phase!=META_TEXT_CANCEL)return 10;
  if(memcmp(source,expected,52) || state.result!=result || seen!=final_bells || meta_text_shape(&state)!=final_shape){printf("FAIL finish %u\r\n",index);return 11;}
 }
 if(fgetc(f)!=EOF || fclose(f))return 12;
 memset(source,'a',52);memset(&state,0xa5,sizeof(state));memcpy(&saved,&state,sizeof(state));
 if(meta_text_begin(&state,source,0x0607)!=META_TEXT_ARGUMENT || memcmp(&state,&saved,sizeof(state)))return 13;++guards;
 source[0]=0;
 if(meta_text_begin(&state,(unsigned char __far *)&state,0x0607)!=META_TEXT_ARGUMENT || memcmp(&state,&saved,sizeof(state)))return 14;++guards;
 if(meta_text_begin((meta_text_state __far *)MK_FP(FP_SEG(&state),0xfff0),source,0x0607)!=META_TEXT_ARGUMENT)return 15;++guards;
 if(meta_text_begin(&state,(unsigned char __far *)MK_FP(FP_SEG(source),0xfff0),0x0607)!=META_TEXT_ARGUMENT || memcmp(&state,&saved,sizeof(state)))return 16;++guards;
 if(meta_text_key(&state,13)!=META_TEXT_ARGUMENT || memcmp(&state,&saved,sizeof(state)))return 17;++guards;
 if(meta_text_begin(&state,source,0x0607))return 18;
 memcpy(&saved,&state,sizeof(state));
 if(meta_text_commit(&state,source)!=META_TEXT_ARGUMENT || memcmp(&state,&saved,sizeof(state)))return 19;++guards;
 state.cursor=50;memcpy(&saved,&state,sizeof(state));
 if(meta_text_key(&state,'x')!=META_TEXT_ARGUMENT || memcmp(&state,&saved,sizeof(state)))return 20;++guards;
 if(meta_text_begin(&state,source,0x0607) || meta_text_key(&state,13)!=META_TEXT_ACCEPT)return 21;
 memcpy(&saved,&state,sizeof(state));
 if(meta_text_commit(&state,(unsigned char __far *)&state)!=META_TEXT_ARGUMENT || memcmp(&state,&saved,sizeof(state)))return 22;++guards;
 if(meta_text_begin(&state,(unsigned char __far *)MK_FP(FP_SEG(&state)-1,FP_OFF(&state)+16),0x0607)!=META_TEXT_ARGUMENT || memcmp(&state,&saved,sizeof(state)))return 23;++guards;
 if(meta_text_commit(&state,(unsigned char __far *)MK_FP(FP_SEG(source),0xfff0))!=META_TEXT_ARGUMENT)return 24;++guards;
 if(meta_text_commit(&state,0)!=META_TEXT_ARGUMENT)return 25;++guards;
 if(meta_text_begin(&state,source,0x0607))return 26;state.full=1;memcpy(&saved,&state,sizeof(state));
 if(meta_text_key(&state,'x')!=META_TEXT_ARGUMENT || memcmp(&state,&saved,sizeof(state)))return 27;++guards;
 if(data_segment()!=stack_segment())return 29;
 printf("PASS %u cases; %lu native key states; %u API guards; separate CS and DS=SS\r\n",count,states,guards);return 0;
}
