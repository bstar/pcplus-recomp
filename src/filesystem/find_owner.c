#include "find_owner.h"

/* This unit must be built in FILE_CODE/FARCODE. No persistent DGROUP bytes. */
file_find_state __based(__segname("_CODE")) file_find_storage={0,0,{0}};
extern unsigned __cdecl file_find_kernel(unsigned,const char *,unsigned,void __far *);

static unsigned publish(file_find_entry *out)
{
 unsigned i;
 file_find_entry result;
 unsigned char *bytes=(unsigned char *)&result;
 for(i=0;i<sizeof(result);i++)bytes[i]=0;
 /* Validate the DOS 8.3 terminator before publishing any caller bytes. */
 for(i=0;i<13;i++) {
  result.name[i]=(char)file_find_storage.dta[30+i];
  if(!result.name[i])break;
 }
 if(i==13)return FILE_FIND_ARGUMENT;
 result.attributes=file_find_storage.dta[21];
 result.time=(unsigned)file_find_storage.dta[22]|((unsigned)file_find_storage.dta[23]<<8);
 result.date=(unsigned)file_find_storage.dta[24]|((unsigned)file_find_storage.dta[25]<<8);
 result.size=(unsigned long)file_find_storage.dta[26]|
             ((unsigned long)file_find_storage.dta[27]<<8)|
             ((unsigned long)file_find_storage.dta[28]<<16)|
             ((unsigned long)file_find_storage.dta[29]<<24);
 *out=result;
 return 0;
}

static unsigned search(unsigned operation,const char *spec,unsigned attributes,file_find_entry *out)
{
 unsigned error;
 error=file_find_kernel(operation,spec,attributes,(void __far *)file_find_storage.dta);
 if(!error)error=publish(out);
 file_find_storage.error=error;
 return error;
}

unsigned __far __cdecl file_find_begin(const char *spec,unsigned attributes,file_find_entry *out)
{
 unsigned i;
 if(!spec||!out||attributes>255)return FILE_FIND_ARGUMENT;
 if(file_find_storage.active)return FILE_FIND_BUSY;
 for(i=0;i<68&&spec[i];i++);
 if(!i||i==68)return FILE_FIND_ARGUMENT;
 file_find_storage.active=1;
 return search(0x4e00,spec,attributes,out);
}

unsigned __far __cdecl file_find_next(file_find_entry *out)
{
 if(!out)return FILE_FIND_ARGUMENT;
 if(!file_find_storage.active)return FILE_FIND_INACTIVE;
 if(file_find_storage.error)return file_find_storage.error;
 return search(0x4f00,0,0,out);
}

void __far __cdecl file_find_close(void)
{
 file_find_storage.active=0;
 file_find_storage.error=0;
}
