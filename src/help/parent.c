#include "parent.h"
#include <string.h>
static unsigned word(const unsigned char *p)
{return p[0]|((unsigned)p[1]<<8);}
static unsigned read(const help_parent_source *s,unsigned long at,unsigned char *out,unsigned n)
{
 if(at>=0xa0000UL||n>0xa0000UL-at)return HELP_PARENT_SPAN;
 return s->copy(s->cookie,at,out,n)?HELP_PARENT_IO:HELP_PARENT_OK;
}
static unsigned inside(unsigned long at,unsigned n,unsigned long first,unsigned long end)
{return at>=first && at<end && n<=end-at;}
static unsigned string(const help_parent_source *s,unsigned ds,unsigned off,
 char *out,unsigned n,unsigned long first,unsigned long end)
{
 unsigned i,status;unsigned long at=(unsigned long)ds*16+off;
 for(i=0;i<n;++i){
  if((unsigned long)off+i>=65536UL||!inside(at+i,1,first,end))return HELP_PARENT_SPAN;
  status=read(s,at+i,(unsigned char *)out+i,1);if(status)return status;
  if(!out[i])return HELP_PARENT_OK;
 }
 return HELP_PARENT_FORMAT;
}
unsigned help_parent_read(const help_parent_source *s,const char *text,help_parent_context *out)
{
 unsigned status,parent,paragraphs,ds,off;
 unsigned char child[24],psp[2],mcb[5],raw[18],again[24];
 unsigned long pointer,first,end,at,mcb_at;
 help_parent_context candidate;
 if(!s||!s->copy||!text||!out)return HELP_PARENT_ARGUMENT;
 if(help_pointer_parse(text,&pointer))return HELP_PARENT_POINTER;
 if(s->child_psp<0x50||s->child_psp>0x9ffe)return HELP_PARENT_PSP;
 status=read(s,(unsigned long)s->child_psp*16,child,sizeof(child));if(status)return status;
 if(child[0]!=0xcd||child[1]!=0x20)return HELP_PARENT_PSP;
 parent=word(child+22);
 if(parent<0x50||parent>0x9ffe||parent==s->child_psp)return HELP_PARENT_PSP;
 mcb_at=(unsigned long)(parent-1)*16;
 status=read(s,mcb_at,mcb,sizeof(mcb));if(status)return status;
 paragraphs=word(mcb+3);
 if((mcb[0]!='M'&&mcb[0]!='Z')||word(mcb+1)!=parent||paragraphs<0x10)return HELP_PARENT_OWNER;
 first=(unsigned long)(parent+0x10)*16;end=(unsigned long)parent*16+(unsigned long)paragraphs*16;
 if(end>0xa0000UL)return HELP_PARENT_OWNER;
 if((unsigned long)parent*16<(unsigned long)s->child_psp*16+256 &&
    end>(unsigned long)s->child_psp*16)return HELP_PARENT_OWNER;
 status=read(s,(unsigned long)parent*16,psp,sizeof(psp));if(status)return status;
 if(psp[0]!=0xcd||psp[1]!=0x20)return HELP_PARENT_PSP;
 ds=(unsigned)(pointer>>16);off=(unsigned)(pointer&65535UL);at=(unsigned long)ds*16+off;
 if(!inside(at,sizeof(raw),first,end))return HELP_PARENT_SPAN;
 status=read(s,at,raw,sizeof(raw));if(status)return status;
 memset(&candidate,0,sizeof(candidate));
 if(help_context_decode(raw,sizeof(raw),&candidate.context))return HELP_PARENT_FORMAT;
 status=string(s,ds,candidate.context.path_offset,candidate.path,sizeof(candidate.path),first,end);
 if(status)return status;
 if(!candidate.path[0])return HELP_PARENT_FORMAT;
 status=string(s,ds,candidate.context.title_offset,candidate.title,sizeof(candidate.title),first,end);
 if(status)return status;
 /* The foreground DOS parent is suspended throughout EXEC. Reject a changed
  * identity/allocation/descriptor rather than publishing a mixed observation. */
 status=read(s,(unsigned long)s->child_psp*16,again,sizeof(child));if(status)return status;
 if(memcmp(child,again,sizeof(child)))return HELP_PARENT_CHANGED;
 status=read(s,mcb_at,again,sizeof(mcb));if(status)return status;
 if(memcmp(mcb,again,sizeof(mcb)))return HELP_PARENT_CHANGED;
 status=read(s,at,again,sizeof(raw));if(status)return status;
 if(memcmp(raw,again,sizeof(raw)))return HELP_PARENT_CHANGED;
 candidate.parent_psp=parent;candidate.parent_ds=ds;candidate.descriptor_offset=off;
 *out=candidate;
 return HELP_PARENT_OK;
}
