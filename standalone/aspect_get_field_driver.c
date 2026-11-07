/* Independent frozen original field observations, source-built DOS8086. */
#include <stdio.h>
#include <string.h>
#include <dos.h>
#include "get_field.h"
static get_field_state state,saved;
static unsigned char initial[82],original[82],output[82],expected[82],frame[82],rendered[82];
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
 FILE *f=fopen("CASES.BIN","rb");unsigned count,index,n,i,key,cursor,shape,visible,bells,seen,status,result,final_bells,final_shape,final_visible;
 unsigned width,numeric,masked,start_visible,start_shape,has_initial,guards=0;unsigned long states=0;
 if(FP_SEG(get_field_key)==code_segment() || data_segment()!=stack_segment())return 28;
 if(!f || word(f)!=0x4746)return 1;count=word(f);
 for(index=0;index<count;++index){
  width=word(f);numeric=word(f);masked=word(f);start_visible=word(f);start_shape=word(f);has_initial=word(f);
  if(!get(f,initial,82))return 2;memcpy(original,initial,82);n=word(f);seen=0;memset(output,0xa5,82);
  if(get_field_begin(&state,has_initial?(const unsigned char __far *)initial:(const unsigned char __far *)0,width,numeric,masked,start_visible,start_shape)!=GET_FIELD_ACTIVE)return 3;
  for(i=0;i<n;++i){
   key=word(f);if(!get(f,frame,width))return 4;cursor=word(f);shape=word(f);visible=word(f);bells=word(f);
   status=get_field_render(&state,rendered);
   if(status!=GET_FIELD_ACTIVE || memcmp(rendered,frame,width) || rendered[width] || state.cursor!=cursor || get_field_shape(&state)!=shape || get_field_visible(&state)!=visible || seen!=bells){printf("FAIL state %u/%u cursor %u/%u shape %u/%u bells %u/%u\r\n",index,i,state.cursor,cursor,get_field_shape(&state),shape,seen,bells);printf("render=%u bytes=%u/%u nul=%u visible=%u/%u size=%u raw=%u width=%u masked=%u\r\n",status,rendered[0],frame[0],rendered[width],get_field_visible(&state),visible,sizeof(state),state.field[0],state.width,state.masked);return 5;}
   status=get_field_key(&state,key);if(status==GET_FIELD_BELL)++seen;else if(status==GET_FIELD_ARGUMENT)return 6;++states;
  }
  if(!get(f,expected,82))return 7;result=word(f);final_bells=word(f);final_shape=word(f);final_visible=word(f);
  if(memcmp(initial,original,82))return 8;
  for(i=0;i<82;++i)if(output[i]!=0xa5)return 31;
  if(state.phase==GET_FIELD_ACCEPT){if(get_field_commit(&state,output)!=GET_FIELD_ACCEPT)return 9;}
  else if(state.phase!=GET_FIELD_CANCEL || get_field_commit(&state,output)!=GET_FIELD_ARGUMENT)return 10;
  if(memcmp(output,expected,82) || state.result!=result || seen!=final_bells || get_field_shape(&state)!=final_shape || get_field_visible(&state)!=final_visible){printf("FAIL finish %u result %u/%u bells %u/%u\r\n",index,state.result,result,seen,final_bells);return 11;}
 }
 if(fgetc(f)!=EOF || fclose(f))return 12;
 memset(&state,0xa5,sizeof(state));memcpy(&saved,&state,sizeof(state));memset(initial,0,82);
#define REJECT_BEGIN(source,w,num,mask,vis) do {if(get_field_begin(&state,source,w,num,mask,vis,0x0607)!=GET_FIELD_ARGUMENT || memcmp(&state,&saved,sizeof(state)))return 13;++guards;}while(0)
 REJECT_BEGIN(initial,0,0,0,1);REJECT_BEGIN(initial,82,0,0,1);REJECT_BEGIN(initial,65535,0,0,1);
 REJECT_BEGIN(initial,10,2,0,1);REJECT_BEGIN(initial,10,0,2,1);REJECT_BEGIN(initial,10,0,0,2);
 REJECT_BEGIN((unsigned char __far *)&state,10,0,0,1);
 REJECT_BEGIN((unsigned char __far *)MK_FP(FP_SEG(&state)-1,FP_OFF(&state)+16),10,0,0,1);
 REJECT_BEGIN((unsigned char __far *)MK_FP(FP_SEG(initial),0xfff0),10,0,0,1);
 memset(initial,'a',82);REJECT_BEGIN(initial,81,0,0,1);
 initial[11]=0;REJECT_BEGIN(initial,10,0,0,1);initial[0]=0;
 if(get_field_begin((get_field_state __far *)MK_FP(FP_SEG(&state),0xfff0),initial,10,0,0,1,0x0607)!=GET_FIELD_ARGUMENT)return 14;++guards;
 if(get_field_key(&state,13)!=GET_FIELD_ARGUMENT || get_field_shape(&state)!=0xffff || get_field_visible(&state)!=0xffff || memcmp(&state,&saved,sizeof(state)))return 15;++guards;
 if(get_field_begin(&state,initial,10,0,0,1,0x0607))return 16;memcpy(&saved,&state,sizeof(state));
 if(get_field_commit(&state,output)!=GET_FIELD_ARGUMENT || memcmp(&state,&saved,sizeof(state)))return 17;++guards;
 if(get_field_render(&state,(unsigned char __far *)&state)!=GET_FIELD_ARGUMENT || memcmp(&state,&saved,sizeof(state)))return 18;++guards;
 if(get_field_render(&state,0)!=GET_FIELD_ARGUMENT || memcmp(&state,&saved,sizeof(state)))return 19;++guards;
 state.cursor=10;memcpy(&saved,&state,sizeof(state));if(get_field_key(&state,'x')!=GET_FIELD_ARGUMENT || memcmp(&state,&saved,sizeof(state)))return 20;++guards;
 if(get_field_begin(&state,initial,10,0,0,1,0x0607) || get_field_key(&state,13)!=GET_FIELD_ACCEPT)return 21;memcpy(&saved,&state,sizeof(state));
 if(get_field_commit(&state,(unsigned char __far *)&state)!=GET_FIELD_ARGUMENT || memcmp(&state,&saved,sizeof(state)))return 22;++guards;
 if(get_field_commit(&state,(unsigned char __far *)MK_FP(FP_SEG(output),0xfff0))!=GET_FIELD_ARGUMENT)return 23;++guards;
 if(get_field_commit(&state,0)!=GET_FIELD_ARGUMENT)return 24;++guards;
 if(data_segment()!=stack_segment())return 29;
 printf("PASS %u cases; %lu native key states; %u API guards; separate CS and DS=SS\r\n",count,states,guards);return 0;
}
