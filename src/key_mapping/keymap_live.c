/* CONFIG bank; no new DGROUP state. Frozen active selector lives in the
 * existing keyboard path; command/result buffers belong to PROGRAM kind13. */
#include <string.h>
#include "keymap_dos.h"
#include "../config/resource_path.h"
#include "../capture/capture_file.h"
#include "../capture/capture_reservation.h"
extern unsigned terminal_option_mask,csi_terminal_id,terminal_keyboard_status,reset_ready;
extern char terminal_keyboard_path[64];
extern unsigned char terminal_keymap[948],reset_keymap[948];
extern keymap_dos_result terminal_keyboard_io;
#pragma aux terminal_option_mask "terminal_option_mask";
#pragma aux csi_terminal_id "csi_terminal_id";
#pragma aux terminal_keyboard_status "terminal_keyboard_status";
#pragma aux terminal_keyboard_path "terminal_keyboard_path";
#pragma aux terminal_keymap "terminal_keymap";
#pragma aux terminal_keyboard_io "terminal_keyboard_io";
#pragma aux reset_keymap "reset_keymap";
#pragma aux reset_ready "reset_ready";
extern unsigned capture_fs_canonical(const char *,char *);
static unsigned absolute(const char *source,char *out)
{
 char path[128];unsigned n,c,error;
 memset(path,0,sizeof(path));error=capture_fs_canonical(source,path);if(error)return 1;
 for(n=0;n<64 && path[n];++n){c=(unsigned char)path[n];if(c>='a' && c<='z')c-=32;path[n]=(char)(c=='/'?'\\':c);}
 if(!n || n==64 || path[1]!=':' || path[2]!='\\' || !capture_file_validate_path(path,0))return 1;
 memset(out,0,64);memcpy(out,path,n+1);return 0;
}
unsigned __cdecl keymap_live_bind(void)
{
 static const char __based(__segname("_CODE")) name[]="PCPLUS.KBD";
 char input[sizeof(name)],bound[64];unsigned i,explicit_path=terminal_option_mask&512;
 for(i=0;i<sizeof(name);++i)input[i]=name[i];
 if(absolute(explicit_path?terminal_keyboard_path:input,bound)){if(!explicit_path)terminal_keyboard_path[0]=0;return explicit_path?1:0;}
 memcpy(terminal_keyboard_path,bound,64);return 0;
}
unsigned __cdecl keymap_live_prepare(unsigned psp,char *executable,char *tail)
{
 static const char __based(__segname("_CODE")) name[]="PCKEYMAP.EXE";
 char leaf[13],program[64],command[96];unsigned i,n,j;
 if(!executable || !tail || csi_terminal_id>=33 || !terminal_keyboard_path[0] ||
  terminal_keyboard_path[1]!=':' || terminal_keyboard_path[2]!='\\' ||
  !capture_file_validate_path(terminal_keyboard_path,0) || capture_file_reserved(terminal_keyboard_path))return 1;
 for(i=0;i<sizeof(name);++i)leaf[i]=name[i];
 memset(program,0,64);
 if(resource_program_path(psp,leaf,program))return 1;
 n=strlen(terminal_keyboard_path); /* Already bounded by validate_path. */
 memset(command,0,96);j=0;command[j++]=' ';
 if(csi_terminal_id>=10)command[j++]=(char)('0'+csi_terminal_id/10);
 command[j++]=(char)('0'+csi_terminal_id%10);command[j++]=' ';command[j++]='"';
 for(i=0;i<n;++i)command[j++]=terminal_keyboard_path[i];command[j++]='"';
 memcpy(executable,program,64);memcpy(tail,command,96);return 0;
}
unsigned __cdecl keymap_live_reload(void)
{
 unsigned status;
 if(!terminal_keyboard_path[0] || capture_file_reserved(terminal_keyboard_path))return 1;
 status=keymap_dos_read(terminal_keyboard_path,csi_terminal_id,terminal_keymap,&terminal_keyboard_io);
 terminal_keyboard_status=status;
 if(terminal_keyboard_io.close_error)return 14;
 if(status)return 1;
 if(reset_ready==1)memcpy(reset_keymap,terminal_keymap,948);
 terminal_option_mask|=512;return 0;
}
