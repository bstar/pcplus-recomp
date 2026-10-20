#include <dos.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(void)
{
 union REGS in,out;unsigned i;FILE *f;char b[8];
 if(!getenv("CTRLVAR")||strcmp(getenv("CTRLVAR"),"OWNED"))return 99;
 for(i=5;i<20;++i){in.x.ax=0x4201;in.x.bx=i;in.x.cx=in.x.dx=0;int86(0x21,&in,&out);if(!out.x.cflag||out.x.ax!=6)return 98;}
 f=fopen("SLOT5.BIN","rb");if(!f)return 99;
 i=fread(b,1,8,f);fclose(f);if(i!=8||memcmp(b,"pending5",8))return 99;
 f=fopen("EXE.OUT","wb");if(!f)return 99;
 fwrite("REAL EXE",1,8,f);fclose(f);return 37;
}
