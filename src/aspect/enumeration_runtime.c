#include "enumeration_runtime.h"
#include <i86.h>
#include <dos.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
extern unsigned enum_first_service(unsigned mask),enum_next_service(unsigned formatted);
extern unsigned enum_extension;
extern unsigned char enum_mask[81],enum_line[44],enum_dta[43],enum_attributes[7];
static unsigned started;
static void __far *get_dta(void)
{
 union REGS in,out;struct SREGS seg;
 in.h.ah=0x2f;intdosx(&in,&out,&seg);return MK_FP(seg.es,out.x.bx);
}
static void set_dta(void __far *pointer)
{
 union REGS in,out;struct SREGS seg;
 segread(&seg);seg.ds=FP_SEG(pointer);in.x.dx=FP_OFF(pointer);in.h.ah=0x1a;
 intdosx(&in,&out,&seg);
}
void runtime_enumeration_reset(void)
{
 started=0;memset(enum_mask,0,81);memset(enum_line,0,44);
 memset(enum_dta,0,43);memset(enum_attributes,0,7);
 /* Empty extension aliases the already empty attribute buffer until search. */
 enum_extension=(unsigned)enum_attributes;
}
unsigned runtime_enum_first(unsigned mask)
{
 void __far *previous=get_dta();unsigned result;
 started=1;result=enum_first_service(mask);set_dta(previous);return result;
}
unsigned runtime_enum_next(unsigned formatted)
{
 void __far *previous;unsigned result;
 if(!started)return 0;
 previous=get_dta();set_dta(enum_dta);
 result=enum_next_service(formatted);set_dta(previous);return result;
}
int runtime_enum_strcmp(const char *a,const char *b){return strcmp(a,b);}
char *runtime_enum_strchr(const char *s,int c){return strchr(s,c);}
void *runtime_enum_memmove(void *to,const void *from,unsigned count){return memmove(to,from,count);}
int runtime_enum_sprintf(char *out,const char *format,...)
{
 int result;va_list args;
 va_start(args,format);result=vsprintf(out,format,args);va_end(args);return result;
}
