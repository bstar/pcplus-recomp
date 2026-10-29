/* Capture command-line provenance before any directory-dependent startup work. */
#include "../directory/directory_resource_cli.h"
#include <string.h>
extern unsigned terminal_option_mask;
extern char terminal_keyboard_path[64],terminal_actions_path[64];
#pragma aux terminal_option_mask "terminal_option_mask";
#pragma aux terminal_keyboard_path "terminal_keyboard_path";
#pragma aux terminal_actions_path "terminal_actions_path";
#ifdef DIRECTORY_TRANSLATION_RESOURCES
extern char terminal_translation_path[64];
#pragma aux terminal_translation_path "terminal_translation_path";
#endif
unsigned __far __cdecl terminal_resource_cli_bind(void)
{
 unsigned status=directory_resource_cli_initialize();
 if(!status)status=directory_resource_cli_bind(terminal_option_mask,terminal_keyboard_path,terminal_actions_path
#ifdef DIRECTORY_TRANSLATION_RESOURCES
 ,terminal_translation_path
#endif
 );
 if(status){
#ifdef DIRECTORY_TRANSLATION_RESOURCES
  if(directory_resource_cli.failed_resource==16384)return 11;
#endif
  return directory_resource_cli.failed_resource==4096?10:9;
 }
 /* Both identities are bound before either active selector changes. */
 if(directory_resource_cli.original_mask&512)memcpy(terminal_keyboard_path,directory_resource_cli.keyboard,64);
 if(directory_resource_cli.original_mask&4096)memcpy(terminal_actions_path,directory_resource_cli.actions,64);
#ifdef DIRECTORY_TRANSLATION_RESOURCES
 if(directory_resource_cli.original_mask&16384)memcpy(terminal_translation_path,directory_resource_cli.translation,64);
#endif
 return 0;
}
