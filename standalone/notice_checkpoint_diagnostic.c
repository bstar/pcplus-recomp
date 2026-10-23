#include <stdio.h>
extern unsigned __far __cdecl notice_checkpoint_probe(unsigned);
extern void __far __cdecl notice_checkpoint_invalid(void);
static unsigned calls,errors;
static unsigned code_segment(void);
#pragma aux code_segment = "mov ax,cs" value [ax] modify [];
static unsigned data_segment(void);
#pragma aux data_segment = "mov ax,ds" value [ax] modify [];
static unsigned stack_segment(void);
#pragma aux stack_segment = "mov ax,ss" value [ax] modify [];
static unsigned __cdecl near_peer(unsigned mode){++calls;return 0x6000+mode;}
unsigned __far __cdecl notice_checkpoint_peer(unsigned mode,unsigned bank)
{
 if(code_segment()==bank||data_segment()!=stack_segment())++errors;
 return near_peer(mode);
}
int main(int argc,char **argv)
{
 unsigned i,status;
 (void)argv;
 if(argc>1){notice_checkpoint_invalid();return 1;}
 for(i=0;i<2048;++i){
  status=notice_checkpoint_probe(i&15);
  if(status){printf("CHECKPOINT FAIL %u bits%u\n",i,status);return 1;}
 }
 if(calls!=2048||errors){printf("CHECKPOINT PEER FAIL %u %u\n",calls,errors);return 1;}
 printf("CHECKPOINT PASS 2048 calls 2048 far callbacks\n");return 0;
}
