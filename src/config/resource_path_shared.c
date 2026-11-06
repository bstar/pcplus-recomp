/* Same public bounds/status contract as resource_path.c, with one shared
 * argument/environment scanner for PCPLUS= and executable-sibling lookups.
 * The default implementation remains the independent comparison/control. */
#include "resource_path.h"
#include <dos.h>
#include <string.h>
static unsigned extent(const void *p,unsigned n)
{return p&&(unsigned long)(unsigned)p+n<=65536UL;}
static unsigned overlap(unsigned long a,unsigned long n,unsigned long b,unsigned long m)
{return a<b+m&&b<a+n;}
static unsigned name_size(const char *leaf)
{
 unsigned i,c,base=0,extension=0,dot=0;
 if(!leaf)return 0;
 for(i=0;i<13;++i){
  if(!extent(leaf,i+1))return 0;c=(unsigned char)leaf[i];
  if(!c)return base&&(!dot||extension)?i:0;
  if(c=='.'){if(dot||!base)return 0;dot=1;continue;}
  if(!((c>='A'&&c<='Z')||(c>='a'&&c<='z')||(c>='0'&&c<='9')||c=='_'||c=='-'))return 0;
  if(dot){if(++extension>3)return 0;}else if(++base>8)return 0;
 }return 0;
}
static unsigned resolve(unsigned psp,const char *leaf,char *output,unsigned sibling)
{
 const unsigned char __far *bytes;
 const unsigned char __far *mcb;
 unsigned n,segment,paragraphs,found=0,selected=0,size=0,used=0,i,c,ended=0;
 unsigned long at=0,end,start,limit,linear;
 char stage[RESOURCE_PATH_CAPACITY];
 n=name_size(leaf);
 if(!n||!extent(output,64)||overlap((unsigned)leaf,n+1,(unsigned)output,64))return RESOURCE_PATH_ARGUMENT;
 linear=(unsigned long)FP_SEG((char __far *)output)*16+FP_OFF((char __far *)output);
 if(!psp||(unsigned long)psp*16+256>1048576UL||overlap(linear,64,(unsigned long)psp*16,256))return RESOURCE_PATH_ENVIRONMENT;
 segment=*(const unsigned __far *)MK_FP(psp,0x2c);if(!segment)return RESOURCE_PATH_ABSENT;
 mcb=MK_FP(segment-1,0);paragraphs=mcb[3]|((unsigned)mcb[4]<<8);
 if((mcb[0]!='M'&&mcb[0]!='Z')||!paragraphs||(unsigned long)segment+paragraphs>65536UL)return RESOURCE_PATH_ENVIRONMENT;
 limit=(unsigned long)paragraphs*16;if(limit>65536UL)limit=65536UL;
 if(overlap(linear,64,(unsigned long)segment*16,limit))return RESOURCE_PATH_ENVIRONMENT;
 bytes=MK_FP(segment,0);
 while(at<limit){
  if(!bytes[(unsigned)at]){
   if(!at){if(limit<2||bytes[1])return RESOURCE_PATH_ENVIRONMENT;at=2;}else ++at;
   ended=1;break;
  }
  start=at;end=at;
  while(end<limit&&bytes[(unsigned)end])++end;
  if(end==limit)return RESOURCE_PATH_ENVIRONMENT;
  if(!found&&end-start>=7&&bytes[(unsigned)start]=='P'&&bytes[(unsigned)(start+1)]=='C'&&
   bytes[(unsigned)(start+2)]=='P'&&bytes[(unsigned)(start+3)]=='L'&&bytes[(unsigned)(start+4)]=='U'&&
   bytes[(unsigned)(start+5)]=='S'&&bytes[(unsigned)(start+6)]=='='){
   found=1;selected=(unsigned)start+7;size=(unsigned)(end-start-7);
  }
  at=end+1;
 }
 /* The legacy PCPLUS resolver accepts a completed terminator even at the
  * allocation end. The sibling resolver additionally needs its DOS3 trailer. */
 if(!ended)return RESOURCE_PATH_ENVIRONMENT;
 if(!sibling){
  if(!found||!size)return RESOURCE_PATH_ABSENT;
  if(size>=64)return RESOURCE_PATH_SIZE;
  used=size;if(bytes[selected+size-1]!='\\')++used;
  if(used+n>=64)return RESOURCE_PATH_SIZE;
  for(i=0;i<size;++i){c=bytes[selected+i];
   if(c<33||c>126||c=='"'||c=='*'||c=='?'||c==';'||c=='<'||c=='>'||c=='|'||c=='=')return RESOURCE_PATH_ENVIRONMENT;
   stage[i]=(char)c;
  }
  if(used>size)stage[size]='\\';
 }else{
  if(at+2>=limit||bytes[(unsigned)at]!=1||bytes[(unsigned)(at+1)]!=0)return RESOURCE_PATH_ENVIRONMENT;
  start=at+2;end=start;
  while(end<limit&&bytes[(unsigned)end]){
   c=bytes[(unsigned)end];
   if(c<32||c==127||c=='"'||c=='*'||c=='?'||c=='/'||c=='<'||c=='>'||c=='|')return RESOURCE_PATH_ENVIRONMENT;
   if(c=='\\'){if(end-start>=64)return RESOURCE_PATH_SIZE;used=(unsigned)(end-start+1);}
   ++end;
  }
  if(end==limit||end-start<4||used<3||used>=end-start||
   !((bytes[(unsigned)start]>='A'&&bytes[(unsigned)start]<='Z')||(bytes[(unsigned)start]>='a'&&bytes[(unsigned)start]<='z'))||
   bytes[(unsigned)(start+1)]!=':'||bytes[(unsigned)(start+2)]!='\\')return RESOURCE_PATH_ENVIRONMENT;
  if(used+n>=64)return RESOURCE_PATH_SIZE;
  for(i=0;i<used;++i)stage[i]=(char)bytes[(unsigned)(start+i)];
 }
 memcpy(stage+used,leaf,n+1);memcpy(output,stage,used+n+1);return RESOURCE_PATH_OK;
}
unsigned __cdecl resource_pcplus_path(unsigned psp,const char *leaf,char *output)
{return resolve(psp,leaf,output,0);}
unsigned __cdecl resource_program_path(unsigned psp,const char *leaf,char *output)
{return resolve(psp,leaf,output,1);}
