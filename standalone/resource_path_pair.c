/* Compare the shared scanner with the unchanged default, in real DOS memory.
 * Synthetic MCB lives inside an owned block; actual DOS heap metadata is never
 * modified. Both versions receive identical pointers and initial output bytes. */
#include <dos.h>
#include <stdio.h>
#include <string.h>
#include "../src/config/resource_path.h"
extern unsigned __cdecl control_pcplus(unsigned,const char *,char *);
extern unsigned __cdecl control_program(unsigned,const char *,char *);
static unsigned char guarded[66],expected[66];
static unsigned char __far *env;
static unsigned char __far *fake;
static unsigned psp,arena,segment,cases,failures;
static unsigned long seed=1234567UL;
static unsigned random_byte(void){seed=seed*1664525UL+1013904223UL;return (unsigned)(seed>>24);}
static void reset(unsigned paragraphs)
{
 unsigned i;for(i=0;i<512;++i)env[i]=0;
 fake[0]='M';fake[3]=(unsigned char)paragraphs;fake[4]=(unsigned char)(paragraphs>>8);
}
static void copy(unsigned at,const char *s,unsigned n)
{unsigned i;for(i=0;i<n;++i)env[at+i]=(unsigned char)s[i];}
static void pair(const char *name)
{
 unsigned a,b,k;char *out=(char *)guarded+1;
 for(k=0;k<2;++k){
  memset(guarded,0xa5,66);
  a=k?control_program(psp,name,out):control_pcplus(psp,name,out);memcpy(expected,guarded,66);
  memset(guarded,0xa5,66);
  b=k?resource_program_path(psp,name,out):resource_pcplus_path(psp,name,out);
  ++cases;if(a!=b||memcmp(expected,guarded,66)){++failures;printf("FAIL pair=%u mode=%u old=%u new=%u\n",cases,k,a,b);}
 }
}
int main(void)
{
 unsigned n,i,c;unsigned long at;
 if(_dos_allocmem(16,&psp)||_dos_allocmem(4097,&arena))return 2;
 segment=arena+1;fake=MK_FP(arena,0);env=MK_FP(segment,0);
 *(unsigned __far *)MK_FP(psp,0x2c)=segment;
 for(n=0;n<=72;++n){
  reset(32);copy(0,"PCPLUS=C:\\",10);for(i=0;i<n;++i)env[10+i]='A';
  at=12+n;env[(unsigned)at]=1;copy((unsigned)at+2,"C:\\PCPLUS\\PCPLUS.EXE",21);
  pair("PCHELP.RTE");pair("A.X");
  reset(32);env[2]=1;copy(4,"C:\\",3);for(i=0;i<n;++i)env[7+i]='A';
  copy(7+n,"\\PCPLUS.EXE",12);pair("PCPLUS.HLP");
 }
 for(c=0;c<256;++c){
  reset(32);copy(0,"PCPLUS=C:\\ABCD\0\0\1\0C:\\ONE\\PCPLUS.EXE",sizeof("PCPLUS=C:\\ABCD\0\0\1\0C:\\ONE\\PCPLUS.EXE"));env[11]=(unsigned char)c;pair("PCHELP.RTE");
  reset(32);env[2]=1;copy(4,"C:\\ABCD\\PCPLUS.EXE",19);env[8]=(unsigned char)c;pair("PCPLUS.HLP");
 }
 for(n=0;n<600;++n){
  reset(32);for(i=0;i<512;++i){c=random_byte();env[i]=(unsigned char)(c<16?0:c);}
  pair(n&1?"PCHELP.RTE":"A");
 }
 reset(32);copy(0,"PCPLUS=\0PCPLUS=C:\\CFG\0\0\1\0C:\\APP\\PCPLUS.EXE",sizeof("PCPLUS=\0PCPLUS=C:\\CFG\0\0\1\0C:\\APP\\PCPLUS.EXE"));pair("PCHELP.RTE");
 pair(0);pair("");pair("../BAD");pair("TOOLONG99.XLT");pair("A..B");
 reset(32);for(i=0;i<512;++i)env[i]='A';copy(0,"PCPLUS=C:\\CFG",sizeof("PCPLUS=C:\\CFG"));env[510]=env[511]=0;pair("PCHELP.RTE");
 env[510]='A';pair("PCHELP.RTE"); /* Found variable, but no complete terminator. */
 reset(32);for(i=0;i<512;++i)env[i]='A';env[490]=env[491]=0;env[492]=1;env[493]=0;copy(494,"C:\\APP\\PCPLUS.EXE",sizeof("C:\\APP\\PCPLUS.EXE"));pair("PCPLUS.HLP");
 for(n=0;n<4;++n){
  reset(4096);for(at=0;at<65536UL;++at)env[(unsigned)at]='A';
  if(n){env[65535U]=0;if(n>1)env[65534U]=0;if(n>2)env[0]=0;}
  pair("PCHELP.RTE");
 }
 if(_dos_freemem(arena)||_dos_freemem(psp))return 3;
 printf("RESOURCEPAIR cases=%u failures=%u\n",cases,failures);return failures?1:0;
}
