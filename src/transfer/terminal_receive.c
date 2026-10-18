/* Maintained live owner around one native ordinary receiver invocation. */
#include "download_file.h"
#include <string.h>
extern char terminal_transfer_filename[64];
extern unsigned terminal_transfer_fault,terminal_transfer_cleanup_status;
extern unsigned terminal_transfer_eot_deferred,terminal_transfer_native_status;
unsigned __cdecl terminal_transfer_native_call(const char *filename);
void __cdecl terminal_transfer_initialize(void)
{ memset(&transfer_download_result,0,sizeof(transfer_download_result)); }
static unsigned stage_path(char *stage)
{
 unsigned i,parent=0;
 for(i=0;i<64 && terminal_transfer_filename[i];++i){
  if(terminal_transfer_filename[i]=='\\' || terminal_transfer_filename[i]=='/' || (i==1 && terminal_transfer_filename[i]==':'))parent=i+1;
 }
 if(!i || i==64 || parent>55)return 0;
 memcpy(stage,terminal_transfer_filename,parent);strcpy(stage+parent,"PCRX.$$$");return 1;
}
unsigned __cdecl terminal_transfer_store(void)
{
 char stage[64];unsigned status,native;
 if(!stage_path(stage)){terminal_transfer_fault=8;return 1;}
 status=transfer_download_begin(terminal_transfer_filename,stage);
 if(status){terminal_transfer_fault=7;if(transfer_download_result.stage_exists || transfer_download_result.handle_uncertain)terminal_transfer_cleanup_status=TF_RECOVERY;return 1;}
 native=terminal_transfer_native_call(transfer_download_result.stage);
 if(native!=1 || !terminal_transfer_eot_deferred || terminal_transfer_fault || transfer_download_result.first_status){
  if(!terminal_transfer_fault)terminal_transfer_fault=transfer_download_result.first_status?7:terminal_transfer_native_status==11?2:terminal_transfer_native_status==15?4:3;
  status=transfer_download_abort();if(status)terminal_transfer_cleanup_status=status;
  return 1;
 }
 status=transfer_download_finish();
 if(status){terminal_transfer_fault=7;terminal_transfer_cleanup_status=status;return 1;}
 return 0;
}
/* Fatal application shutdown may bypass native frames. Hardware is restored
 * first; close/delete an owned partial, retain closed complete/recovery stages. */
unsigned __cdecl terminal_transfer_cleanup(void)
{
 if(transfer_download_result.handle_uncertain)return TF_RECOVERY;
 if(transfer_download_result.handle_open)return transfer_download_abort();
 return transfer_download_result.stage_exists?TF_RECOVERY:TF_OK;
}
