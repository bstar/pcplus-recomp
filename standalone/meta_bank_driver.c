#include <stdio.h>
int meta_bank_flow_main(int,char **);
unsigned __far __cdecl meta_bank_kernel_probe(unsigned __far *);
int main(int argc,char **argv)
{
 unsigned error,checks=0;
 if(argc==1){
  error=meta_bank_kernel_probe(&checks);
  if(error){printf("FAIL bank kernel line %u\r\n",error);return 1;}
  printf("PASS bank kernel %u checks;DS=SS;CRT stack/ES;file IO;interleaved DTA\r\n",checks);
 }
 return meta_bank_flow_main(argc,argv);
}
