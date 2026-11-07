#include <stdio.h>
extern unsigned __cdecl get_filter_word(unsigned);
extern unsigned get_filter_bells;
int main(void)
{
 unsigned key=0,expected,actual,before;unsigned long cases=0,errors=0;
 do{
  expected=key>=255 || key==8 || key==13 || key==27 || key==45 || key==46 || (key>=48 && key<=57)?0:0xff9d;
  before=get_filter_bells;actual=get_filter_word(key);
  if(actual!=expected || (unsigned)(get_filter_bells-before)!=(expected!=0))++errors;
  ++cases;
 }while(++key);
 printf("GET FILTER cases=%lu errors=%lu\n",cases,errors);
 return errors?1:0;
}
