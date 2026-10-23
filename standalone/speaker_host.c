#include "speaker.h"
#include <stdio.h>
#include <stdlib.h>
extern unsigned speaker_owned,speaker_generation_word;
static unsigned context=1,port,claims,releases,writes,checks;
static unsigned long clock_value;
unsigned speaker_context(void){return context;}
unsigned speaker_claim(unsigned frequency){(void)frequency;++claims;if(port&3)return 1;speaker_generation_word=(speaker_generation_word+1)&65535;if(!speaker_generation_word)++speaker_generation_word;speaker_owned=1;port|=3;++writes;return 0;}
void speaker_release(void){++releases;port&=252;speaker_owned=0;++writes;}
unsigned long speaker_ticks(void){return clock_value;}
#define CK(x) do{++checks;if(!(x)){printf("SPEAKER FAIL %u\n",checks);exit(1);}}while(0)
int main(void)
{
 unsigned before,i;unsigned long start;
 CK(speaker_stop()==SPEAKER_OK&&!speaker_active()&&!writes);
 for(i=0;i<19;++i){before=claims;CK(speaker_start(i,3,100)==SPEAKER_ARGUMENT&&claims==before&&!writes);}
 CK(speaker_start(220,0,1)==SPEAKER_ARGUMENT);CK(speaker_start(220,183,1)==SPEAKER_ARGUMENT);CK(speaker_start(220,3,0)==SPEAKER_ARGUMENT);
 context=0;CK(speaker_start(220,3,100)==SPEAKER_STATE&&!writes);context=1;
 port=0xa3;CK(speaker_start(220,3,100)==SPEAKER_BUSY&&!speaker_active()&&port==0xa3&&!writes);
 for(start=0;start<4;++start){
  port=0xa0;clock_value=start?1573040UL-start:10;
  CK(speaker_start(440,4,10)==SPEAKER_PENDING&&speaker_active()&&port==0xa3);before=claims;
  CK(speaker_start(220,3,100)==SPEAKER_BUSY&&claims==before);
  for(i=0;i<4;++i){CK(speaker_poll()==SPEAKER_PENDING);clock_value=(clock_value+1)%1573040UL;}
  CK(speaker_poll()==SPEAKER_OK&&!speaker_active()&&port==0xa0);
 }
 clock_value=100;CK(speaker_start(65535,1,3)==SPEAKER_PENDING);
 for(i=0;i<3;++i)CK(speaker_poll()==SPEAKER_PENDING);
 CK(speaker_poll()==SPEAKER_BUDGET&&!speaker_active()&&port==0xa0);
 CK(speaker_stop()==SPEAKER_OK);before=releases;CK(speaker_poll()==SPEAKER_OK&&speaker_stop()==SPEAKER_OK&&releases==before);
 CK(speaker_start(19,182,0xffffffffUL)==SPEAKER_PENDING);clock_value+=182;
 CK(speaker_poll()==SPEAKER_OK&&!speaker_active());
 clock_value=1573040UL;before=claims;CK(speaker_start(220,3,10)==SPEAKER_STATE&&claims==before);
 clock_value=0;CK(speaker_start(220,3,10)==SPEAKER_PENDING);clock_value=1573040UL;
 CK(speaker_poll()==SPEAKER_STATE&&!speaker_active()&&port==0xa0);
 speaker_generation_word=65535;clock_value=0;CK(speaker_start(220,3,10)==SPEAKER_PENDING&&speaker_generation()==1);context=0;before=releases;
 CK(speaker_stop()==SPEAKER_STATE&&speaker_poll()==SPEAKER_STATE&&speaker_active()&&releases==before&&port==0xa3);
 context=1;CK(speaker_stop()==SPEAKER_OK&&!speaker_active()&&port==0xa0);
 printf("SPEAKER HOST %u checks\n",checks);return 0;
}
