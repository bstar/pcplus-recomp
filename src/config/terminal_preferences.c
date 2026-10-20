#include "terminal_preferences.h"
#include <string.h>
#ifdef TERMINAL_MOUSE
extern unsigned __cdecl terminal_mouse_stage(const unsigned char *,unsigned);
#endif
static unsigned extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned separate(const void *a,unsigned an,const void *b,unsigned bn)
{return (unsigned long)(unsigned)a+an<=(unsigned)b || (unsigned long)(unsigned)b+bn<=(unsigned)a;}
static unsigned path_size(const char *p)
{unsigned n;for(n=0;n<64;++n){if(!extent(p,n+1))return 0;if(!p[n])return n?n+1:0;}return 0;}
static unsigned objects(const void **p,const unsigned *sizes,unsigned n)
{
 unsigned i,j;
 for(i=0;i<n;++i){if(!extent(p[i],sizes[i]))return 0;
  for(j=0;j<i;++j)if(!separate(p[i],sizes[i],p[j],sizes[j]))return 0;}
 return 1;
}
unsigned __cdecl terminal_preferences_read(const char *path,terminal_import_settings *serial,
 modem_import_settings *modem,transfer_import_settings *transfer,prm_dos_result *io)
{
 prm_dos_image image;terminal_import_settings s;modem_import_settings m;
 transfer_import_settings t;unsigned n,status,count=0;
 const void *p[5];unsigned sizes[5];
 n=path_size(path);if(!n)return TERMINAL_IMPORT_ARGUMENT;
 p[count]=path;sizes[count++]=n;p[count]=serial;sizes[count++]=sizeof(*serial);
 p[count]=transfer;sizes[count++]=sizeof(*transfer);
 if(modem){p[count]=modem;sizes[count++]=sizeof(*modem);}
 if(io){p[count]=io;sizes[count++]=sizeof(*io);}
 if(!objects(p,sizes,count))return TERMINAL_IMPORT_ARGUMENT;
 if(prm_dos_load(path,&image,io))return TERMINAL_IMPORT_IO;
 status=terminal_import_decode(&image,&s);if(status)return status;
 if(modem && modem_import_decode(&image,&m))return 7;
 if(transfer_import_decode(&image,&t))return 14;
#ifdef TERMINAL_MOUSE
 if(terminal_mouse_stage(image.bytes,sizeof(image.bytes)))return 15;
#endif
 memcpy(serial,&s,sizeof(s));if(modem)memcpy(modem,&m,sizeof(m));
 memcpy(transfer,&t,sizeof(t));return 0;
}
unsigned __cdecl terminal_directory_preferences_read(const char *path,const char *directory,
 unsigned entry,unsigned codes,terminal_import_settings *serial,modem_import_settings *modem,
 directory_live_plan *plan,directory_live_result *result,directory_live_context *context,
 transfer_import_settings *transfer)
{
 prm_dos_image image;prm_dos_result io;directory_dos_result dio;
 terminal_import_settings s;modem_import_settings m;directory_live_plan d;
 directory_live_context c;transfer_import_settings t;directory_live_result decoded;
 unsigned a,b,status,count=0;const void *p[8];unsigned sizes[8];
 a=path_size(path);b=path_size(directory);
 if(!a || !b || !entry || entry>200 || codes>1)return DIRECTORY_LIVE_ARGUMENT;
 p[count]=path;sizes[count++]=a;p[count]=directory;sizes[count++]=b;
 p[count]=serial;sizes[count++]=sizeof(*serial);p[count]=modem;sizes[count++]=sizeof(*modem);
 p[count]=plan;sizes[count++]=sizeof(*plan);p[count]=result;sizes[count++]=sizeof(*result);
 p[count]=context;sizes[count++]=sizeof(*context);p[count]=transfer;sizes[count++]=sizeof(*transfer);
 if(!objects(p,sizes,count))return DIRECTORY_LIVE_ARGUMENT;
 memset(result,0,sizeof(*result));
 status=prm_dos_load(path,&image,&io);
 if(status){result->source_status=status;result->dos_error=io.dos_error;
  result->close_error=io.close_error;result->bytes_processed=io.bytes_processed;
  status=DIRECTORY_LIVE_PRM_IO;goto failed;}
 if(terminal_import_decode(&image,&s)){status=DIRECTORY_LIVE_SERIAL;goto failed;}
 if(transfer_import_decode(&image,&t)){status=14;goto failed;}
 memset(&c,0,sizeof(c));c.codes=codes;memcpy(c.prm_path,path,a);memcpy(c.directory_path,directory,b);
 status=directory_dos_read(directory,entry,&c.selection,&dio);
 if(status){result->source_status=status;result->dos_error=dio.dos_error;
  result->close_error=dio.close_error;result->bytes_processed=dio.bytes_processed;
  status=DIRECTORY_LIVE_DIRECTORY_IO;goto failed;}
 if(c.selection.entry_number!=entry){status=DIRECTORY_LIVE_RECORD;goto failed;}
 status=directory_live_decode(&image,&c.selection,codes,&s,&m,&d,&decoded);
 memcpy(result,&decoded,sizeof(decoded));if(status)return status;
#ifdef TERMINAL_MOUSE
 if(terminal_mouse_stage(image.bytes,sizeof(image.bytes))){result->status=15;return 15;}
#endif
 memcpy(serial,&s,sizeof(s));memcpy(modem,&m,sizeof(m));memcpy(plan,&d,sizeof(d));
 memcpy(context,&c,sizeof(c));memcpy(transfer,&t,sizeof(t));return 0;
failed:result->status=status;return status;
}
