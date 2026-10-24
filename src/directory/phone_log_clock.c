#include "phone_log_clock.h"
#include <dos.h>
void __cdecl phone_log_clock_date(unsigned *year,unsigned *month,unsigned *day)
{
 union REGS in,out;in.h.ah=0x2a;intdos(&in,&out);
 *year=out.x.cx;*month=out.h.dh;*day=out.h.dl;
}
void __cdecl phone_log_clock_time(unsigned *hour,unsigned *minute,unsigned *second)
{
 union REGS in,out;in.h.ah=0x2c;intdos(&in,&out);
 *hour=out.h.ch;*minute=out.h.cl;*second=out.h.dh;
}
