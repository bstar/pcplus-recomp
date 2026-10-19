#include "compiler_expression_dump.h"
#include <stdlib.h>
#include <string.h>
#include <io.h>
#include <fcntl.h>
#include <limits.h>
int main(int argc,char **argv)
{
 FILE *input;char *digit;unsigned mode=65535;unsigned long line=0;int status;
 if(argc==4){if(!strcmp(argv[3],"EXPR"))mode=0;else if(!strcmp(argv[3],"ATOM"))mode=1;else if(!strcmp(argv[3],"WORD"))mode=2;else if(!strcmp(argv[3],"ASSIGN"))mode=3;else if(!strcmp(argv[3],"CHAIN"))mode=4;}
 if(mode==65535||argc!=4){fputs("Usage: ASPEXP source.ASP line EXPR|ATOM|WORD|ASSIGN|CHAIN\n",stderr);return 64;}
 for(digit=argv[2];*digit>='0'&&*digit<='9';++digit){
  if(line>(ULONG_MAX-(unsigned)(*digit-'0'))/10UL)break;
  line=line*10UL+(unsigned)(*digit-'0');
 }
 if(*digit||!line){fputs("ASPEXP: invalid line\n",stderr);return 64;}
 input=fopen(argv[1],"rb");if(!input){fputs("ASPEXP: cannot open source\n",stderr);return 1;}
 if(setmode(fileno(stdout),O_BINARY)<0){fclose(input);return 2;}
 status=aspect_compiler_expression_dump(input,stdout,line,0,65535U,mode,0,0,mode==1||mode==2);
 if(fclose(input)&&!status)status=1;return status;
}
