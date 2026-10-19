/* Maintained direct Script child argument validation, not native scheduling.
 * No DOS, UART or script execution here. DS=SS, bounded near buffers. */
#include "../config/resource_path.h"
static unsigned span(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned apart(const void *a,unsigned n,const void *b,unsigned m)
{return (unsigned long)(unsigned)a+n<=(unsigned)b || (unsigned long)(unsigned)b+m<=(unsigned)a;}
static unsigned folded(unsigned c){return c>='a' && c<='z'?c-32:c;}
static unsigned device(const char *p,unsigned n)
{
 unsigned a=folded(p[0]),b=n>1?folded(p[1]):0,c=n>2?folded(p[2]):0;
 if(n==3 && ((a=='C'&&b=='O'&&c=='N')||(a=='P'&&b=='R'&&c=='N')||
 (a=='A'&&b=='U'&&c=='X')||(a=='N'&&b=='U'&&c=='L')))return 1;
 return n==4 && ((a=='C'&&b=='O'&&c=='M')||(a=='L'&&b=='P'&&c=='T')) && p[3]>='1' && p[3]<='9';
}
unsigned __cdecl terminal_script_prepare(unsigned psp,char *executable,char *tail)
{
 unsigned i=1,start=1,base=0,extension=0,dot=0,c;
 if(!span(executable,64)||!span(tail,68)||!apart(executable,64,tail,68)||tail[0]!=' ')return 1;
 /* Optional drive and root; every following component is a strict DOS83 name.
  * Reject shell syntax, whitespace, traversal and device aliases even though
  * direct EXEC does not invoke a command interpreter. */
 if(((tail[i]>='A'&&tail[i]<='Z')||(tail[i]>='a'&&tail[i]<='z'))&&tail[i+1]==':')i+=2;
 if(tail[i]=='\\')++i;start=i;
 for(;i<65;++i){
  c=(unsigned char)tail[i];
  if(!c || c=='\\'){
   if(!base || (dot&&!extension) || device(tail+start,base))return 1;
   if(!c)return resource_program_path(psp,"ASPECT.EXE",executable)?2:0;
   start=i+1;base=extension=dot=0;continue;
  }
  if(c=='.'){if(!base||dot)return 1;dot=1;continue;}
  c=folded(c);
  if(!((c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_'||c=='-'))return 1;
  if(dot){if(++extension>3)return 1;}else if(++base>8)return 1;
 }
 return 1;
}
