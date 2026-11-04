/* Optional startup binding before any live directory changes. No new files,
 * no implicit fallback, no changes to an active resource on a failed bind. */
#include "../terminal/directory_identity.h"
#include "../config/resource_path.h"
extern unsigned terminal_option_mask,process_psp,terminal_macro_active;
extern unsigned terminal_program_pending,terminal_program_active;
extern char terminal_config_path[64],terminal_directory_path[64];
extern char terminal_keyboard_path[64],terminal_actions_path[64],terminal_translation_path[64];
extern char program_setup_executable[64],terminal_setup_tail[68];
#pragma aux terminal_option_mask "terminal_option_mask";
#pragma aux process_psp "process_psp";
#pragma aux terminal_macro_active "terminal_macro_active";
#pragma aux terminal_program_pending "terminal_program_pending";
#pragma aux terminal_program_active "terminal_program_active";
#pragma aux terminal_config_path "terminal_config_path";
#pragma aux terminal_directory_path "terminal_directory_path";
#pragma aux terminal_keyboard_path "terminal_keyboard_path";
#pragma aux terminal_actions_path "terminal_actions_path";
#pragma aux terminal_translation_path "terminal_translation_path";
#pragma aux program_setup_executable "program_setup_executable";
#pragma aux terminal_setup_tail "terminal_setup_tail";
unsigned __far __cdecl terminal_cwd_bind_startup(void)
{
 char stage[5][64];char *path[5];unsigned i,j;
 path[0]=terminal_config_path;path[1]=terminal_directory_path;
 path[2]=terminal_keyboard_path;path[3]=terminal_actions_path;path[4]=terminal_translation_path;
 for(i=0;i<5;++i){
  for(j=0;j<64;++j)stage[i][j]=0;
  if(path[i][0] && directory_identity_path(path[i],stage[i]))return 16;
 }
 /* Canonicalize every nonempty selector before publishing any of them. */
 for(i=0;i<5;++i)for(j=0;j<64;++j)path[i][j]=stage[i][j];
 return 0;
}
unsigned __far __cdecl terminal_cwd_setup_command(void)
{
 char executable[64],tail[68];unsigned n,i;
 if(!(terminal_option_mask&16))return 1;
 if(terminal_macro_active || terminal_program_pending || terminal_program_active)return 2;
 for(n=0;n<64 && terminal_config_path[n];++n){}
 if(n<4 || n==64 || terminal_config_path[0]<'A' || terminal_config_path[0]>'Z' ||
  terminal_config_path[1]!=':' || terminal_config_path[2]!='\\')return 1;
 for(i=0;i<64;++i)executable[i]=0;
 if(resource_program_path(process_psp,"PRMEDIT.EXE",executable))return 1;
 for(i=0;i<68;++i)tail[i]=0;
 tail[0]=' ';for(i=0;i<n;++i)tail[i+1]=terminal_config_path[i];
 for(i=0;i<64;++i)program_setup_executable[i]=executable[i];
 for(i=0;i<68;++i)terminal_setup_tail[i]=tail[i];
 return 0;
}
