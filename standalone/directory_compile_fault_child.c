/* Explicit fault fixture, never used for successful compiler acceptance. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(int argc,char **argv)
{
 char out[64];FILE *f;unsigned mode;
 if(argc!=2 || strlen(argv[1])>63)return 64;
 mode=(unsigned)atoi(getenv("LOCFAULT")?getenv("LOCFAULT"):"0");
 strcpy(out,argv[1]);out[strlen(out)-1]='X';
 if(mode==11){f=fopen(argv[1],"ab");if(!f)return 2;fputs("; changed by declared fault child\n",f);if(fclose(f))return 2;}
 if(mode!=12){f=fopen(out,"wb");if(!f)return 2;fputc(mode==14?129:0,f);if(fclose(f))return 2;}
 return mode==13?1:0;
}
