#include <dos.h>
#include "meta_file_prompt.h"
typedef char prompt_layout[sizeof(meta_file_prompt)==92?1:-1];
static unsigned span(const void __far *p,unsigned n,unsigned long *a)
{*a=(unsigned long)FP_SEG(p)*16UL+FP_OFF(p);return p && (unsigned long)FP_OFF(p)+n<=65536UL && *a+n<=0x100000UL;}
static unsigned valid(const meta_file_prompt __far *s)
{unsigned long a;return span(s,sizeof(*s),&a) && s->cookie==0x4d46 && s->phase<=META_FILE_CANCELED && (s->operation==META_FILE_LOAD || s->operation==META_FILE_SAVE);}
static void normalize(meta_file_prompt __far *s)
{
 unsigned i,c,n,dot=0;
 for(n=0;s->candidate[n];++n){c=(unsigned char)s->candidate[n];if(c>='a' && c<='z')c-=32;s->candidate[n]=(char)c;if(c=='.')dot=1;}
 if(!dot){s->candidate[n++]='.';s->candidate[n++]='K';s->candidate[n++]='E';s->candidate[n++]='Y';s->candidate[n]=0;}
 for(i=n+1;i<64;++i)s->candidate[i]=0;s->phase=META_FILE_READY;
}
unsigned __far __cdecl meta_file_prompt_begin(meta_file_prompt __far *s,unsigned load,unsigned shape)
{
 unsigned i;unsigned long a;
 if(!span(s,sizeof(*s),&a) || load>1)return META_FILE_ARGUMENT;
 s->cookie=0x4d46;s->phase=load?META_FILE_NAME:META_FILE_READY;s->operation=load?META_FILE_LOAD:META_FILE_SAVE;
 for(i=0;i<64;++i)s->candidate[i]=0;
 if(load){meta_filename_begin(&s->editor,shape);return META_FILE_OK;}
 return META_FILE_SAVE;
}
unsigned __far __cdecl meta_file_prompt_key(meta_file_prompt __far *s,unsigned key)
{
 unsigned result;
 if(!valid(s) || s->phase==META_FILE_CANCELED)return META_FILE_ARGUMENT;
 if(s->phase!=META_FILE_NAME)return META_FILE_BUSY;
 result=meta_filename_key(&s->editor,key);
 if(result==META_FILENAME_BELL)return META_FILE_BELL;
 if(result==META_FILENAME_ARGUMENT)return META_FILE_ARGUMENT;
 if(result==META_FILENAME_CANCEL){s->phase=META_FILE_CANCELED;return META_FILE_CANCEL;}
 if(result!=META_FILENAME_ACCEPT)return META_FILE_OK;
 if(!s->editor.result){s->phase=META_FILE_PICKER;return META_FILE_PICK;}
 if(meta_filename_commit(&s->editor,(unsigned char __far *)s->candidate)!=META_FILENAME_ACCEPT)return META_FILE_ARGUMENT;
 normalize(s);return META_FILE_LOAD;
}
unsigned __far __cdecl meta_file_prompt_pick(meta_file_prompt __far *s,unsigned accepted,const char __far *stem)
{
 unsigned i,n;unsigned long a,b;
 if(!valid(s) || s->phase!=META_FILE_PICKER || accepted>1)return META_FILE_ARGUMENT;
 if(!accepted){s->phase=META_FILE_CANCELED;return META_FILE_CANCEL;}
 if(!span(stem,9,&a) || !span(s,sizeof(*s),&b) || !(a+9<=b || b+sizeof(*s)<=a))return META_FILE_ARGUMENT;
 for(n=0;n<9 && stem[n];++n){}if(!n || n>8)return META_FILE_ARGUMENT;
 for(i=0;i<n;++i)s->candidate[i]=stem[i];s->candidate[n]=0;normalize(s);return META_FILE_LOAD;
}
