#include "zmodem_autostart.h"
#include <stdio.h>
#include <string.h>
static unsigned char input[2048],expected[2048],actual[2048],out[22];
static unsigned wanted[103],positions[103];
static za_state state,saved;
static unsigned word(FILE *f)
{unsigned lo=(unsigned)fgetc(f);return lo|((unsigned)fgetc(f)<<8);}
int main(void)
{
 FILE *f;unsigned first,length,n,events,i,j,count,status,total,found,vectors=0;
 f=fopen("VECTORS.BIN","rb");if(!f)return 1;
 while((first=(unsigned)fgetc(f))!=0xffffU){
  length=first|((unsigned)fgetc(f)<<8);n=word(f);events=word(f);
  if(length>2048 || n>2048 || events>103)return 2;
  if(fread(input,1,length,f)!=length || fread(expected,1,n,f)!=n)return 2;
  for(i=0;i<events;++i)wanted[i]=word(f);
  za_reset(&state);total=0;found=0;
  for(i=0;i<length;++i){
   memset(out,0xa5,sizeof(out));count=999;
   status=za_feed(&state,input[i],out+1,&count);
   if(status>ZA_START || count>20 || state.count>=20)return 3;
   if(out[0]!=0xa5 || out[21]!=0xa5 || total+count>2048)return 4;
   for(j=count+1;j<sizeof(out);++j)if(out[j]!=0xa5)return 5;
   memcpy(actual+total,out+1,count);total+=count;
   if(status==ZA_START){if(found>=103)return 6;positions[found++]=i;}
  }
  count=za_flush(&state,out+1);
  if(count>19 || total+count>2048 || state.count)return 7;
  memcpy(actual+total,out+1,count);total+=count;
  if(total!=n || found!=events || memcmp(actual,expected,n) || memcmp(positions,wanted,events*sizeof(unsigned))){
   printf("FAIL vector %u\n",vectors);return 8;
  }
  ++vectors;
 }
 fclose(f);
 za_reset(&state);saved=state;count=777;memset(out,0xa5,sizeof(out));
 if(za_feed(&state,256,out,&count)!=ZA_ARGUMENT || count!=777 || memcmp(&state,&saved,sizeof(state)) || out[0]!=0xa5)return 9;
 printf("%u vectors; state %u bytes; PASS\n",vectors,(unsigned)sizeof(state));
 return 0;
}
