#include "compiler_unit_dump.h"
#include <io.h>
#include <fcntl.h>
int main(int argc,char **argv)
{
 FILE *input;int result;
 if(argc!=2){fputs("Usage: ASPINV source.ASP >unit.AUN\n",stderr);return 64;}
 input=fopen(argv[1],"rb");
 if(!input){fputs("ASPINV: cannot open source\n",stderr);return 1;}
 if(setmode(fileno(stdout),O_BINARY)<0){fclose(input);return 2;}
 result=aspect_compiler_unit_dump(input,stdout);
 if(fclose(input) && !result)result=1;
 return result;
}
