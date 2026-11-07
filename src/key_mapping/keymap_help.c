#include <dos.h>
#include "keymap_help.h"
#include "../config/resource_path.h"
#include "../help/embedded.h"
static unsigned psp(void)
{union REGS r;r.h.ah=0x51;int86(0x21,&r,&r);return r.x.bx;}
unsigned keymap_help_open(const unsigned short *frame)
{
 char path[64];unsigned attr;
 if(resource_program_path(psp(),"PCPLUS.HLP",path) || _dos_getfileattr(path,&attr) || (attr&0x18))return 1;
 return help_embedded_open(path,"PROCOMM PLUS",17,23,31,113,frame);
}
