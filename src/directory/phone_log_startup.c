#include "phone_log_startup.h"
#include "phone_log_format.h"
#include "phone_log_queue.h"
#include "phone_log_file.h"
#include "../capture/capture_fs.h"
#include "../config/resource_path.h"

unsigned __cdecl phone_log_startup_configure(const unsigned char *image,
 unsigned count,unsigned psp)
{
 static const char leaf[]="PCPLUS.FON";
 char selected[64],absolute[128];
 const char *path=leaf;
 unsigned enabled,status,attributes,n,cut;
 char saved;
 status=phone_log_decode_enabled(image,count,&enabled);
 if(status)return PLS_ARGUMENT;
 if(!enabled){status=phone_log_queue_configure(0,0);return status?PLS_QUEUE_BASE+status:PLS_OK;}
 status=capture_fs_attributes(leaf,&attributes);
 if(status==2){
  status=resource_pcplus_path(psp,leaf,selected);
  if(status!=RESOURCE_PATH_ABSENT){
   if(status)return PLS_RESOURCE;
   path=selected;
   status=capture_fs_attributes(path,&attributes);
  }else status=2;
 }
 if(status&&status!=2)return PLS_FILESYSTEM;
 if(!status&&(attributes&(1U|8U|16U|64U)))return PLS_FILESYSTEM;
 if(capture_fs_canonical(path,absolute))return PLS_PATH;
 for(n=0;n<64&&absolute[n];++n){}
 if(n==64||n<3||absolute[1]!=':'||absolute[2]!='\\'||
    !phone_log_file_validate_path(absolute))return PLS_PATH;
 /* Some DOS filesystems report missing leaf and parent with the same error.
  * Verify the selected parent explicitly before retaining a future target. */
 cut=n;while(cut>2&&absolute[cut]!='\\')--cut;
 if(cut==2)cut=3;
 saved=absolute[cut];absolute[cut]=0;
 status=capture_fs_attributes(absolute,&attributes);absolute[cut]=saved;
 if(status||!(attributes&16U)||(attributes&(8U|64U)))return PLS_FILESYSTEM;
 status=phone_log_queue_configure(1,absolute);
 return status?PLS_QUEUE_BASE+status:PLS_OK;
}
