/* Optional compatibility inspection. Never prints original help text. */
#include "../src/help/format.h"
#include <stdio.h>
#include <stdlib.h>
static unsigned char prefix[3+255*38];
int main(int argc,char **argv)
{
 FILE *file;help_header h;help_record r,next;long size,end;
 unsigned i,j,lines=0;int ch;
 if(argc!=2)return 1;
 file=fopen(argv[1],"rb");if(!file)return 2;
 if(fseek(file,0,SEEK_END)||(size=ftell(file))<0||fseek(file,0,SEEK_SET)||fread(prefix,3,1,file)!=1)return 3;
 if(help_header_decode(prefix,3,(unsigned long)size,&h))return 4;
 if(fread(prefix+3,(unsigned)(h.text_start-3),1,file)!=1||help_index_validate(prefix,(unsigned)h.text_start,(unsigned long)size))return 5;
 for(i=0;i<h.topics;++i){
  if(help_record_decode(prefix+3+i*38,38,&h,(unsigned long)size,&r))return 6;
  end=size;
  if(i+1<h.topics){if(help_record_decode(prefix+3+(i+1)*38,38,&h,(unsigned long)size,&next))return 7;end=(long)next.offset;}
  if(fseek(file,(long)r.offset,SEEK_SET))return 8;
  for(j=0;j<r.lines;++j){
   do{if(ftell(file)>=end||(ch=fgetc(file))==EOF)return 9;}while(ch!='\n');
   ++lines;
  }
 }
 if(fclose(file)||lines!=h.lines)return 10;
 printf("HELP INDEX topics=%u lines=%u bytes=%lu\n",h.topics,lines,(unsigned long)size);
 return 0;
}
