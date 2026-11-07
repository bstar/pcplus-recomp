#include <stdio.h>
#include <string.h>
#include "keymap_field.h"
static FILE *input;
static unsigned word(void){unsigned char a,b;if(fread(&a,1,1,input)!=1 || fread(&b,1,1,input)!=1)return 65535;return a+256U*b;}
int main(void)
{
 unsigned count,j,k,length,steps,key,cursor,shape,oldbells,bells,result,expected_shape,status,total=0;
 int expected,actual;
 unsigned char initial[11],frame[10],target[40],output[40];
 keymap_field_state state,before;
 input=fopen("CASES.BIN","rb");if(!input || word()!=0x4b46)return 1;count=word();
 for(j=0;j<count;++j){
  length=word();if(fread(initial,1,10,input)!=10)return 2;steps=word();
  if(keymap_field_begin(&state,initial,length,6,7)!=0)return 3;bells=0;
  for(k=0;k<steps;++k){
   key=word();if(fread(frame,1,10,input)!=10)return 4;cursor=word();shape=word();oldbells=word();
   if(memcmp(frame,state.field,10) || cursor!=state.cursor || shape!=(keymap_field_shape(&state)>>8) || oldbells!=bells){printf("FAIL case %u state %u\n",j,k);return 5;}
   status=keymap_field_key(&state,key);if(status==KEYMAP_FIELD_BELL)++bells;++total;
  }
  result=word();oldbells=word();expected_shape=word();expected=(int)word();if(fread(output,1,40,input)!=40)return 6;
  if(state.phase!=(result==65535?KEYMAP_FIELD_CANCEL:KEYMAP_FIELD_ACCEPT) || bells!=oldbells || (keymap_field_shape(&state)>>8)!=expected_shape)return 7;
  memset(target,0xa5,40);actual=keymap_field_commit(&state,target,40);
  if(actual!=expected || memcmp(target,output,40))return 8;
 }
 if(fgetc(input)!=EOF || fclose(input))return 9;
 for(j=0;j<3;++j){
  if(keymap_field_begin(&state,(const unsigned char *)"ABCDEFGHIJ",10,6,7)!=0)return 10;
  keymap_field_key(&state,0x4f00);before=state;
  if(state.cursor!=10 || keymap_field_key(&state,j==0?65:j==1?0x5300:0x1e)!=KEYMAP_FIELD_BELL || memcmp(&state,&before,sizeof(state)))return 11;
 }
 memset(&state,0xa5,sizeof(state));before=state;
 if(keymap_field_begin(&state,(const unsigned char *)"ABCDEFGHIJK",11,6,7)!=KEYMAP_FIELD_ARGUMENT || memcmp(&state,&before,sizeof(state)))return 12;
 printf("PASS %u FIELD CASES %u STATES; 4 SAFETY GUARDS\n",count,total);return 0;
}
