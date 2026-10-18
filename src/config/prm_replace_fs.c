/* Direct DOS rename/delete retain DOS error codes and no-overwrite semantics. */
#include <dos.h>
#include "prm_replace_fs.h"
unsigned prm_replace_rename(const char *from,const char *to)
{
 union REGS input,output;
 struct SREGS segments;
 segread(&segments);
 input.h.ah=0x56;
 input.x.dx=(unsigned)from;
 input.x.di=(unsigned)to;
 segments.es=segments.ds;
 intdosx(&input,&output,&segments);
 return output.x.cflag ? output.x.ax : 0;
}
unsigned prm_replace_delete(const char *path)
{
 union REGS input,output;
 input.h.ah=0x41;input.x.dx=(unsigned)path;
 intdos(&input,&output);
 return output.x.cflag ? output.x.ax : 0;
}
