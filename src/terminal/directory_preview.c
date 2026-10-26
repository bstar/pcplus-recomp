#include "directory_preview.h"
#include "session_baseline.h"
extern unsigned __far __cdecl directory_preview_capture(live_configuration_plan *);
extern unsigned terminal_option_mask,terminal_directory_codes;
extern char terminal_config_path[64];
#pragma aux terminal_option_mask "terminal_option_mask";
#pragma aux terminal_directory_codes "terminal_directory_codes";
#pragma aux terminal_config_path "terminal_config_path";
unsigned __far __cdecl directory_preview_stage(const directory_dos_page_data __far *page,
 unsigned entry,const char *path,directory_selection_proposal __far *proposal)
{
 prm_dos_image baseline;
 live_configuration_plan active;
 directory_selection_result result;
 unsigned status;
 status=hook_baseline_copy(&baseline);
 if(status)return 0x1000U|status;
 status=directory_preview_capture(&active);
 if(status)return 0x2000U|status;
 result.status=result.source_status=result.detail=0;
 status=directory_selection_stage(&baseline,page,entry,terminal_directory_codes,
  terminal_option_mask&15,&active,terminal_config_path,path,proposal,&result);
 return status|(result.source_status<<4)|(result.detail<<8);
}
