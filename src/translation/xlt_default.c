#include "xlt_default.h"
#include "../config/resource_path.h"
#include <string.h>
static const char default_name[]="PCPLUS.XLT";
static unsigned extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned separate(const void *a,unsigned an,const void *b,unsigned bn)
{return (unsigned long)(unsigned)a+an<=(unsigned)b || (unsigned long)(unsigned)b+bn<=(unsigned)a;}
xlt_dos_status __cdecl xlt_dos_read_default(unsigned psp,
 unsigned char *destination,xlt_dos_result *result)
{
 char path[RESOURCE_PATH_CAPACITY];xlt_dos_result stage;unsigned status,lookup;
 if(!extent(destination,256) || !separate(default_name,sizeof(default_name),destination,256) ||
    (result && (!extent(result,sizeof(*result)) || !separate(destination,256,result,sizeof(*result)) ||
    !separate(default_name,sizeof(default_name),result,sizeof(*result)))))return XLT_DOS_ARGUMENT;
 status=xlt_dos_read(default_name,destination,&stage);
 if(status==XLT_DOS_ARGUMENT)return status;
 if(status==XLT_DOS_OPEN && (stage.dos_error==2 || stage.dos_error==3)){
  lookup=resource_pcplus_path(psp,default_name,path);
  if(lookup==RESOURCE_PATH_OK){status=xlt_dos_read(path,destination,&stage);if(status==XLT_DOS_ARGUMENT)return status;}
  else if(lookup!=RESOURCE_PATH_ABSENT){memset(&stage,0,sizeof(stage));stage.status=status=XLT_DOS_RESOURCE;}
 }
 if(result)*result=stage;return status;
}
