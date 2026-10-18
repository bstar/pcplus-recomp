#include "printer_fs.h"
#include <dos.h>
#include <fcntl.h>
unsigned printer_fs_open(int *h){return _dos_open("PRN",O_WRONLY,h);}
unsigned printer_fs_get_mode(int h,unsigned *m)
{union REGS a,b;a.x.ax=0x4400;a.x.bx=h;intdos(&a,&b);if(b.x.cflag)return b.x.ax;*m=b.x.dx;return 0;}
/* MS-DOS3.3 Programmer's Reference44/01 requires DH=0. The caller preserves
 * the admitted low driver bits and toggles raw bit5 only. */
unsigned printer_fs_set_mode(int h,unsigned m)
{union REGS a,b;a.x.ax=0x4401;a.x.bx=h;a.x.dx=m&255;intdos(&a,&b);return b.x.cflag?b.x.ax:0;}
unsigned printer_fs_ready(int h,unsigned *r)
{union REGS a,b;a.x.ax=0x4407;a.x.bx=h;intdos(&a,&b);if(b.x.cflag)return b.x.ax;*r=b.h.al;return 0;}
unsigned printer_fs_write(int h,const void *p,unsigned *n){return _dos_write(h,p,1,n);}
unsigned printer_fs_close(int h){return _dos_close(h);}
