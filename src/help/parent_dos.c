#include <dos.h>
#include "parent.h"
static unsigned copy(void *cookie,unsigned long at,unsigned char *out,unsigned n)
{
 const unsigned char __far *from;unsigned i;
 (void)cookie;
 if(at>=0xa0000UL||n>0xa0000UL-at)return 1;
 from=MK_FP((unsigned)(at>>4),(unsigned)(at&15));
 for(i=0;i<n;++i)out[i]=from[i];
 return 0;
}
unsigned help_parent_read_dos(const char *text,help_parent_context *out)
{
 union REGS r;help_parent_source source;
 r.h.ah=0x51;int86(0x21,&r,&r);
 source.child_psp=r.x.bx;source.cookie=0;source.copy=copy;
 return help_parent_read(&source,text,out);
}
