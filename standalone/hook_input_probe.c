#include "../src/config/hook_input.h"
#include "../src/config/hook_modem.h"
#include "../src/terminal/hook_transaction.h"
#include "../src/terminal/session_projection.h"
#include "../src/terminal/register_owner.h"
#include <dos.h>
extern unsigned __far __cdecl hook_probe_write(const char *,const void __far *,unsigned);
extern unsigned __far __cdecl hook_input_probe_read(const char *,void *,unsigned);
extern unsigned __far __cdecl hook_input_probe_cwd(char *);
extern unsigned __far __cdecl xlt_live_editor_far(unsigned,char *,char *);
extern unsigned char * __far __cdecl hook_probe_stack(void);
extern const char __far hook_input_probe_names[21][20];
extern unsigned char __far terminal_baseline_storage[];
extern prm_dos_image __far terminal_hook_before;
extern unsigned char terminal_keymap[948],terminal_translation_table[256];
extern unsigned csi_terminal_id,terminal_translation_mode,terminal_translation_enabled,uart_rx_mask;
extern unsigned process_psp;
#pragma aux process_psp "process_psp";
#pragma aux terminal_baseline_storage "terminal_baseline_storage";
#pragma aux terminal_keymap "terminal_keymap";
#pragma aux terminal_translation_table "terminal_translation_table";
#pragma aux csi_terminal_id "csi_terminal_id";
#pragma aux terminal_translation_mode "terminal_translation_mode";
#pragma aux terminal_translation_enabled "terminal_translation_enabled";
#pragma aux uart_rx_mask "uart_rx_mask";
static void name(char *out,unsigned index)
{unsigned i;for(i=0;i<20;++i)out[i]=hook_input_probe_names[index][i];}
static unsigned write(unsigned index,const void __far *data,unsigned bytes)
{char path[20];name(path,index);return hook_probe_write(path,data,bytes);}
static unsigned snapshot(unsigned after)
{
 unsigned live[4],i;
 struct {unsigned status;char executable[64],tail[68];} editor;
 for(i=0;i<132;++i)((unsigned char *)&editor)[2+i]='X';
 editor.status=xlt_live_editor_far(process_psp,editor.executable,editor.tail);
 live[0]=csi_terminal_id;live[1]=terminal_translation_mode;
 live[2]=terminal_translation_enabled;live[3]=uart_rx_mask;
 return write(after?5:2,(const void __far *)terminal_keymap,948) ||
  write(after?6:3,(const void __far *)terminal_translation_table,256) ||
  write(after?7:4,(const void __far *)live,8) || write(after?20:19,(const void __far *)&editor,134);
}
static unsigned project(void)
{prm_dos_image image;if(terminal_session_project_bound(&image))return 1;return write(13,(const void __far *)&image,1264);}
unsigned __far __cdecl terminal_hook_input_probe(void)
{
 unsigned request[3],i,expected,status,phase;unsigned char *guard=hook_probe_stack();
 terminal_hook_result child;hook_modem_result modem;hook_input_result result,busy;
 char path[64],cwd[64];unsigned char __far *offer=(unsigned char __far *)&terminal_hook_input_offer;
 for(i=0;i<256;++i)guard[i]=0xa5;
 for(i=0;i<1212;++i)offer[i]='X';
 name(path,0);if(hook_input_probe_read(path,request,6))return 31;
 expected=request[1];phase=request[2];
 if(snapshot(0) || write(10,terminal_baseline_storage,1272) || write(16,terminal_register_owner.accepted,830))return 32;
 name(path,1);status=terminal_hook_execute(path,(long)request[0],&child);
 if(status || terminal_hook_phase!=2)return 33;
 for(i=0;i<64;++i)cwd[i]=0;
 if(hook_input_probe_cwd(cwd) || write(18,(const void __far *)cwd,64))return 43;
 if(write(12,&terminal_hook_before,1264) || write(9,&terminal_hook_proposal,2584))return 34;
 if(terminal_hook_prepare_modem(&modem) || terminal_hook_phase!=3)return 35;
 status=terminal_hook_prepare_input(&result);
 if(status!=expected || result.status!=expected || terminal_hook_phase!=phase)return 36;
 if(!status){if(terminal_hook_prepare_input(&busy)!=HOOK_INPUT_STATE || terminal_hook_phase!=4)return 37;}
 if(write(8,&terminal_hook_input_offer,1212) || write(14,(const void __far *)&result,12))return 38;
 if(project() || snapshot(1))return 39;
 if(terminal_hook_discard() || terminal_hook_phase)return 40;
 if(write(11,terminal_baseline_storage,1272) || write(15,(const void __far *)guard,256) || write(17,terminal_register_owner.accepted,830))return 41;
 for(i=0;i<256;++i)if(guard[i]!=0xa5)return 42;
 return 0;
}
