#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(int argc,char **argv)
{
 FILE *f;char *value=getenv("LABVAR");
 if(!value||strcmp(value,"OWNED")||argc!=3||strcmp(argv[1],"/Q")||strcmp(argv[2],"SYNTH"))return 99;
 f=fopen("EXE.OUT","wb");if(!f)return 98;
 if(fwrite("OWNED /Q SYNTH",1,14,f)!=14||fclose(f))return 97;
 return 37;
}
