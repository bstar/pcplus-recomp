#include "phone_log_fs.h"
#include <dos.h>
unsigned phone_log_fs_seek(int handle,unsigned long position)
{
 union REGS in,out;
 in.x.ax=0x4200;in.x.bx=handle;
 in.x.cx=(unsigned)(position>>16);in.x.dx=(unsigned)position;
 intdos(&in,&out);
 if(out.x.cflag)return out.x.ax;
 return (((unsigned long)out.x.dx<<16)|out.x.ax)==position?0:13;
}
unsigned phone_log_fs_truncate(int handle)
{
 unsigned written=0;char unused=0;
 /* This zero-byte DOS write is intentional and confined to rollback, after
  * a successful absolute seek on this same still-owned handle. */
 return _dos_write(handle,&unused,0,&written);
}
unsigned phone_log_fs_commit(int handle)
{
 union REGS in,out;
 in.x.ax=0x6800;in.x.bx=handle;intdos(&in,&out);
 return out.x.cflag?out.x.ax:0;
}
