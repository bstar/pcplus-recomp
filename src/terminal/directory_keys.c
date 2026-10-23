/* Startup-only selected-directory binding policy. No UART or user-file writes. */
#include "../directory/directory_live.h"
#include "../config/resource_path.h"
extern directory_live_context terminal_directory_context;
extern unsigned terminal_directory_context_valid,terminal_option_mask,process_psp;
extern char terminal_keyboard_path[64],terminal_actions_path[64];
#pragma aux terminal_directory_context "terminal_directory_context";
#pragma aux terminal_directory_context_valid "terminal_directory_context_valid";
#pragma aux terminal_option_mask "terminal_option_mask";
#pragma aux process_psp "process_psp";
#pragma aux terminal_keyboard_path "terminal_keyboard_path";
#pragma aux terminal_actions_path "terminal_actions_path";
extern unsigned __cdecl directory_binding_probe(const char *);
static void copy(char *to,const char *from)
{unsigned i=0;do{to[i]=from[i];}while(from[i++]);}
/* AX0 exists and closed; DOS2/3 means absent. Other failures stop startup. */
static unsigned lookup(const char *leaf,char *path)
{
 unsigned status,found;
 status=directory_binding_probe(leaf);
 if(!status){copy(path,leaf);return 0;}
 if(status!=2&&status!=3)return 1;
 found=resource_pcplus_path(process_psp,leaf,path);
 if(found==RESOURCE_PATH_ABSENT)return 2;
 if(found!=RESOURCE_PATH_OK)return 1;
 status=directory_binding_probe(path);
 return !status?0:status==2||status==3?2:1;
}
unsigned __far __cdecl terminal_directory_bindings(void)
{
 char key[13],meta[13],key_path[64],meta_path[64];unsigned flags,status,load_key=0,load_meta=0;
 if(!terminal_directory_context_valid)return 0;
 if(directory_binding_name(terminal_directory_context.selection.record+0x56,0,key)||
    directory_binding_name(terminal_directory_context.selection.record+0x5f,1,meta))return 8;
 flags=terminal_option_mask;
 if(!(flags&4096)&&key[0]){
  status=lookup(key,key_path);if(status==1)return 10;load_key=status==0;
 }
 if(!(flags&512)&&meta[0]){
  status=lookup(meta,meta_path);if(status==2){
   meta[0]='P';meta[1]='C';meta[2]='P';meta[3]='L';meta[4]='U';meta[5]='S';
   meta[6]='.';meta[7]='K';meta[8]='B';meta[9]='D';meta[10]=0;
   status=lookup(meta,meta_path);
  }
  if(status==1)return 9;load_meta=status==0;
 }
 /* Publish both selectors after all names and lookup operations succeed. */
 if(load_key){copy(terminal_actions_path,key_path);flags|=4096;}
 if(load_meta){copy(terminal_keyboard_path,meta_path);flags|=512;}
 terminal_option_mask=flags;return 0;
}
