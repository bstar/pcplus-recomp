/* Maintained bounded equivalent of native353d's directory concatenation. */
#include "resource_path.h"
#include <dos.h>
#include <string.h>
static unsigned extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned separate(const void *a,unsigned an,const void *b,unsigned bn)
{return (unsigned long)(unsigned)a+an<=(unsigned)b || (unsigned long)(unsigned)b+bn<=(unsigned)a;}
static unsigned name_size(const char *leaf)
{
 unsigned i,c,base=0,extension=0,dot=0;
 if(!leaf)return 0;
 for(i=0;i<13;++i){
  if(!extent(leaf,i+1))return 0;c=(unsigned char)leaf[i];
  if(!c)return base && (!dot || extension)?i:0;
  if(c=='.'){if(dot || !base)return 0;dot=1;continue;}
  if(!((c>='A' && c<='Z') || (c>='a' && c<='z') || (c>='0' && c<='9') || c=='_' || c=='-'))return 0;
  if(dot){if(++extension>3)return 0;}else if(++base>8)return 0;
 }return 0;
}
static unsigned overlap(unsigned long a,unsigned long n,unsigned long b,unsigned long m)
{return a<b+m && b<a+n;}
unsigned __cdecl resource_pcplus_path(unsigned psp,const char *leaf,char *output)
{
 const unsigned char __far *bytes;
 const unsigned char __far *mcb;
 unsigned segment,paragraphs,n,start,size=0,found=0,selected=0,used,i,c;
 unsigned long at,end,limit,out_linear;
 char stage[RESOURCE_PATH_CAPACITY];
 n=name_size(leaf);
 if(!n || !extent(output,RESOURCE_PATH_CAPACITY) || !separate(leaf,n+1,output,RESOURCE_PATH_CAPACITY))return RESOURCE_PATH_ARGUMENT;
 out_linear=(unsigned long)FP_SEG((char __far *)output)*16UL+FP_OFF((char __far *)output);
 if(!psp || (unsigned long)psp*16UL+256UL>1048576UL || overlap(out_linear,64,(unsigned long)psp*16UL,256))return RESOURCE_PATH_ENVIRONMENT;
 segment=*(const unsigned __far *)MK_FP(psp,0x2c);
 if(!segment)return RESOURCE_PATH_ABSENT;
 mcb=(const unsigned char __far *)MK_FP(segment-1,0);
 paragraphs=mcb[3]|((unsigned)mcb[4]<<8);
 if((mcb[0]!='M' && mcb[0]!='Z') || !paragraphs || (unsigned long)segment+paragraphs>65536UL)return RESOURCE_PATH_ENVIRONMENT;
 limit=(unsigned long)paragraphs*16UL;if(limit>65536UL)limit=65536UL;
 if(overlap(out_linear,64,(unsigned long)segment*16UL,limit))return RESOURCE_PATH_ENVIRONMENT;
 bytes=(const unsigned char __far *)MK_FP(segment,0);at=0;
 while(at<limit){
  if(!bytes[(unsigned)at]){
   if(!at && (limit<2 || bytes[1]))return RESOURCE_PATH_ENVIRONMENT;
   break;
  }
  start=(unsigned)at;end=at;
  while(end<limit && bytes[(unsigned)end])++end;
  if(end==limit)return RESOURCE_PATH_ENVIRONMENT;
  if(!found && end-at>=7 && bytes[start]=='P' && bytes[start+1]=='C' &&
     bytes[start+2]=='P' && bytes[start+3]=='L' && bytes[start+4]=='U' &&
     bytes[start+5]=='S' && bytes[start+6]=='='){
   found=1;selected=start+7;size=(unsigned)(end-at-7);
  }
  at=end+1;
 }
 if(at==limit)return RESOURCE_PATH_ENVIRONMENT;
 if(!found || !size)return RESOURCE_PATH_ABSENT;
 if(size>=RESOURCE_PATH_CAPACITY)return RESOURCE_PATH_SIZE;
 used=size;if(bytes[selected+size-1]!='\\')++used;
 if(used+n>=RESOURCE_PATH_CAPACITY)return RESOURCE_PATH_SIZE;
 for(i=0;i<size;++i){
  c=bytes[selected+i];
  if(c<33 || c>126 || c=='"' || c=='*' || c=='?' || c==';' || c=='<' || c=='>' || c=='|' || c=='=')return RESOURCE_PATH_ENVIRONMENT;
  stage[i]=(char)c;
 }
 if(used>size)stage[size]='\\';
 memcpy(stage+used,leaf,n+1);memcpy(output,stage,used+n+1);
 return RESOURCE_PATH_OK;
}
