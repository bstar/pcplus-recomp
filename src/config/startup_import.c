/* One read and transactional staging for live serial + optional modem settings. */
#include "startup_import.h"
#include <string.h>
static unsigned extent(const void *pointer,unsigned length)
{ return pointer && (unsigned long)(unsigned)pointer+length<=65536UL; }
static unsigned disjoint(const void *left,unsigned left_size,const void *right,unsigned right_size)
{
 unsigned long a=(unsigned)left,b=(unsigned)right;
 return a+left_size<=b || b+right_size<=a;
}
unsigned __cdecl terminal_startup_read(const char *path,
 terminal_import_settings *terminal,modem_import_settings *modem,
 prm_dos_result *io)
{
 prm_dos_image image;
 terminal_import_settings serial_stage;
 modem_import_settings modem_stage;
 unsigned status,length;
 if(!extent(terminal,sizeof(*terminal)) || !extent(modem,sizeof(*modem)) ||
  !disjoint(terminal,sizeof(*terminal),modem,sizeof(*modem)))return TERMINAL_IMPORT_ARGUMENT;
 if(io && (!extent(io,sizeof(*io)) ||
  !disjoint(io,sizeof(*io),terminal,sizeof(*terminal)) ||
  !disjoint(io,sizeof(*io),modem,sizeof(*modem))))return TERMINAL_IMPORT_ARGUMENT;
 if(!path)return TERMINAL_IMPORT_ARGUMENT;
 for(length=0;length<64;++length){
  if(!extent(path,length+1))return TERMINAL_IMPORT_ARGUMENT;
  if(!path[length])break;
 }
 if(!length || length==64 ||
  (io && !disjoint(path,length+1,io,sizeof(*io))))return TERMINAL_IMPORT_ARGUMENT;
 if(prm_dos_load(path,&image,io)!=PRM_DOS_OK)return TERMINAL_IMPORT_IO;
 status=terminal_import_decode(&image,&serial_stage);
 if(status!=TERMINAL_IMPORT_OK)return status;
 if(modem_import_decode(&image,&modem_stage)!=MODEM_IMPORT_OK)return 7;
 memcpy(terminal,&serial_stage,sizeof(serial_stage));
 memcpy(modem,&modem_stage,sizeof(modem_stage));
 return TERMINAL_IMPORT_OK;
}
