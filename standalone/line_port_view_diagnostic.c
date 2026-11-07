#include <stdio.h>
#include "../src/line_port/view.h"
static unsigned frame[2000];
static line_port_values cases[]={{0,5,0,1,8},{0,4,0,1,8},{0,4,2,1,8}};
int main(void)
{
 unsigned i,j;unsigned invalid[]={8,9,5,0,9};FILE *file;char name[]="VIEW0.BIN";line_port_values bad;
 for(i=0;i<3;++i){
  for(j=0;j<2000;++j)frame[j]=0x5a58;
  if(line_port_view(cases+i,frame,2000))return 1;
  name[4]='0'+i;file=fopen(name,"wb");if(!file)return 2;
  if(fwrite(frame,2,2000,file)!=2000)return 3;
  if(fclose(file))return 4;
 }
 for(j=0;j<2000;++j)frame[j]=0x5a58;
 for(i=0;i<5;++i){
  bad=cases[0];((unsigned *)&bad)[i]=invalid[i];
  if(!line_port_view(&bad,frame,2000))return 5;
 }
 if(!line_port_view(cases,frame,1999))return 6;
 if(!line_port_view(0,frame,2000))return 7;
 if(!line_port_view(cases,0,2000))return 8;
 for(j=0;j<2000;++j)if(frame[j]!=0x5a58)return 9;
 return 0;
}
