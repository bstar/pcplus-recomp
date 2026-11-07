#include "persist.h"
#include "../config/prm_dos.h"
#include "../config/live_setup_owner.h"
extern unsigned __far __cdecl line_port_setup_path(char *);
unsigned __far __cdecl line_file_frozen(char *tail)
{return line_port_setup_path(tail);}
unsigned __far __cdecl line_file_read(const char *path,prm_dos_image *image,prm_dos_result *io)
{return prm_dos_load(path,image,io);}
unsigned __far __cdecl line_file_store(const char *path,const unsigned char *old,
 const unsigned char *next,directory_replace_result *result)
{return line_port_persist(path,old,next,result);}
