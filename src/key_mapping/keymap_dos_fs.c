#include "keymap_dos_fs.h"
#include <dos.h>
/* Actual DOS AH42 seek, kept separate for declared deterministic fault tests. */
unsigned __cdecl keymap_dos_seek(int handle,unsigned long offset,unsigned origin,
 unsigned long *position)
{
 union REGS in,out;
 in.x.ax=0x4200U|origin;in.x.bx=handle;
 in.x.cx=(unsigned)(offset>>16);in.x.dx=(unsigned)offset;
 intdos(&in,&out);
 if(out.x.cflag)return out.x.ax;
 *position=((unsigned long)out.x.dx<<16)|out.x.ax;
 return 0;
}
