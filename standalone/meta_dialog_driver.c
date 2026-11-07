/* Composed source controller versus frozen native dispatcher/row/field traces. */
#include <stdio.h>
#include <string.h>
#include <dos.h>
#include "meta_dialog.h"
extern meta_dialog_state __far external_state;
#define state external_state
static meta_dialog_state saved;
static unsigned char original[540],expected[540],loaded[540],field[50];
static char name[64],initial_name[64]="LAB.KEY",load_name[64]="NEXT.KEY";
static unsigned frame[2000],before[2000];
static unsigned word(FILE *f){unsigned v;if(fread(&v,2,1,f)!=1)return 0xffff;return v;}
static int get(FILE *f,void *p,unsigned n){return fread(p,1,n,f)==n;}
static unsigned code_segment(void);
#pragma aux code_segment = "mov ax,cs" value [ax] modify [];
static unsigned data_segment(void);
#pragma aux data_segment = "mov ax,ds" value [ax] modify [];
static unsigned stack_segment(void);
#pragma aux stack_segment = "mov ax,ss" value [ax] modify [];
static int view(void)
{
 unsigned i,row,col,at,n,ch,kind,attr;const char *label;
 for(i=0;i<2000;++i)before[i]=frame[i]=0x2700|(i%224+32);
 i=meta_dialog_draw(&state,frame,0x1f);if(i){printf("DRAW status %u\r\n",i);return 0;}
 for(i=0;i<2000;++i)if((i/80<3 || i/80>19 || i%80<7 || i%80>76) && frame[i]!=before[i]){printf("OUTSIDE %u\r\n",i);return 0;}
 for(row=0;row<10;++row){
  attr=row==state.row?0x71:0x1f;at=(row+6)*80;kind=row==state.row && (state.phase==META_DIALOG_KIND || state.phase==META_DIALOG_TEXT)?state.kind:expected[row*54];
  label=kind==0?"ASPECT":kind==1?"PROGRAM":kind==2?"HOOK":"TEXT";n=strlen(label);
  for(col=0;col<7;++col)if(frame[at+17+col]!=((attr<<8)|(col<n?label[col]:' '))){printf("KIND row %u col %u actual %x expected %x\r\n",row,col,frame[at+17+col],(attr<<8)|(col<n?label[col]:' '));return 0;}
  n=0;while(n<50 && expected[row*54+2+n])++n;
  for(col=0;col<50;++col){
   ch=row==state.row && state.phase==META_DIALOG_TEXT?field[col]:col<n?expected[row*54+2+col]:' ';
   if(frame[at+25+col]!=((attr<<8)|ch)){printf("TEXT row %u col %u actual %x expected %x\r\n",row,col,frame[at+25+col],(attr<<8)|ch);return 0;}
  }
 }return 1;
}
int main(void)
{
 FILE *f=fopen("CASES.BIN","rb");unsigned count,index,n,i,key,phase,row,kind,bells,cursor,shape,has_field,loads,saves,seen_l,seen_s,status,guards=0;
 unsigned long states=0;
 if(!f || word(f)!=0x4d44 || !get(f,loaded,540))return 1;count=word(f);
 if(FP_SEG(meta_dialog_key)==code_segment() || data_segment()!=stack_segment() || FP_SEG(&state)==data_segment())return 2;
 for(index=0;index<count;++index){
  if(!get(f,original,540))return 3;n=word(f);seen_l=seen_s=0;
  if(meta_dialog_open(&state,original,initial_name,0x0607))return 4;
  for(i=0;i<n;++i){
   key=word(f);phase=word(f);row=word(f);kind=word(f);if(!get(f,expected,540))return 5;
   bells=word(f);cursor=word(f);shape=word(f);has_field=word(f);
   if(has_field && !get(f,field,50))return 6;if(!get(f,name,64))return 7;loads=word(f);saves=word(f);
   if(state.phase!=phase || state.row!=row || state.kind!=kind || _fmemcmp(state.records,expected,540) || state.bells!=bells || meta_dialog_cursor(&state)!=cursor || meta_dialog_shape(&state)!=shape || _fstrcmp(state.name,name) || seen_l!=loads || seen_s!=saves || (has_field && _fmemcmp(state.text.field,field,50))){
    printf("FAIL controller %u/%u phase %u/%u row %u/%u kind %u/%u\r\n",index,i,state.phase,phase,state.row,row,state.kind,kind);return 8;
   }
   if(!view()){printf("FAIL view %u/%u\r\n",index,i);return 9;}
   status=meta_dialog_key(&state,key);
   if(status==META_DIALOG_LOAD){++seen_l;if(meta_dialog_complete(&state,0,loaded,load_name))return 10;}
   else if(status==META_DIALOG_SAVE){++seen_s;if(meta_dialog_complete(&state,0,0,0))return 11;}
   else if(status!=META_DIALOG_OK && status!=META_DIALOG_BELL)return 12;
   ++states;
  }
  if(!get(f,expected,540))return 13;bells=word(f);loads=word(f);saves=word(f);if(!get(f,name,64))return 14;
  if(state.phase!=META_DIALOG_CLOSED || _fmemcmp(state.records,expected,540) || state.bells!=bells || _fstrcmp(state.name,name) || seen_l!=loads || seen_s!=saves)return 15;
 }
 if(fgetc(f)!=EOF || fclose(f))return 16;
 _fmemcpy(original,loaded,540);_fmemcpy(expected,original,540);original[1]=1;_fmemcpy(&saved,&state,sizeof(state));
 if(meta_dialog_open(&state,original,initial_name,0x0607)!=META_DIALOG_ARGUMENT || _fmemcmp(&state,&saved,sizeof(state)))return 17;++guards;
 _fmemcpy(original,expected,540);if(meta_dialog_open(&state,original,initial_name,0x0607))return 18;
 _fmemcpy(&saved,&state,sizeof(state));
 if(meta_dialog_open(&state,state.records,initial_name,0x0607)!=META_DIALOG_ARGUMENT || _fmemcmp(&state,&saved,sizeof(state)))return 19;++guards;
 if(meta_dialog_draw(&state,(unsigned __far *)&state,0x1f)!=META_DIALOG_ARGUMENT || _fmemcmp(&state,&saved,sizeof(state)))return 20;++guards;
 if(meta_dialog_key(&state,'L')!=META_DIALOG_LOAD)return 21;_fmemcpy(&saved,&state,sizeof(state));
 if(meta_dialog_key(&state,27)!=META_DIALOG_BUSY || _fmemcmp(&state,&saved,sizeof(state)))return 22;++guards;
 original[1]=1;
 if(meta_dialog_complete(&state,0,original,load_name)!=META_DIALOG_ARGUMENT || _fmemcmp(&state,&saved,sizeof(state)))return 23;++guards;
 if(meta_dialog_complete(&state,1,0,0) || _fmemcmp(state.records,expected,540) || state.status!=1)return 24;++guards;
 if(meta_dialog_key(&state,'S')!=META_DIALOG_SAVE || meta_dialog_complete(&state,0,0,0) || _fmemcmp(state.records,expected,540))return 25;++guards;
 if(meta_dialog_key(&state,'R') || meta_dialog_key(&state,13))return 26;state.text.cursor=50;_fmemcpy(&saved,&state,sizeof(state));
 if(meta_dialog_key(&state,'X')!=META_DIALOG_ARGUMENT || _fmemcmp(&state,&saved,sizeof(state)))return 27;++guards;
 if(data_segment()!=stack_segment())return 28;
 printf("PASS %u dialog cases; %lu native key states and views; %u guards\r\n",count,states,guards);return 0;
}
