#include "directory_identity.h"
#include "../directory/directory_live.h"
#include "../capture/capture_file.h"
#include <string.h>
extern unsigned capture_fs_canonical(const char *,char *);
extern unsigned terminal_directory_entry,terminal_directory_context_valid;
extern directory_live_context terminal_directory_context;
#pragma aux terminal_directory_entry "terminal_directory_entry";
#pragma aux terminal_directory_context_valid "terminal_directory_context_valid";
#pragma aux terminal_directory_context "terminal_directory_context";
static unsigned extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
unsigned __cdecl directory_identity_path(const char *path,char *out)
{
 char absolute[128];unsigned n,c;
 if(!extent(path,64) || !extent(out,64) ||
  !((unsigned long)(unsigned)path+64<=(unsigned)out || (unsigned long)(unsigned)out+64<=(unsigned)path))return DI_ARGUMENT;
 for(n=0;n<64 && path[n];++n){}
 if(!n || n==64)return DI_ARGUMENT;
 memset(absolute,0,sizeof(absolute));
 if(capture_fs_canonical(path,absolute))return DI_CANONICAL;
 for(n=0;n<128 && absolute[n];++n){
  c=(unsigned char)absolute[n];if(c>='a' && c<='z')c-=32;if(c=='/')c='\\';absolute[n]=(char)c;
 }
 if(!n || n>63 || absolute[0]<'A' || absolute[0]>'Z' || absolute[1]!=':' || absolute[2]!='\\' ||
  !capture_file_validate_path(absolute,0))return DI_PATH;
 memcpy(out,absolute,64);return DI_OK;
}
unsigned __far __cdecl terminal_directory_account_identity(void)
{
 const char *path=terminal_directory_context.directory_path;unsigned n;
 if(terminal_directory_context_valid!=1 || !terminal_directory_entry || terminal_directory_entry>200 ||
  terminal_directory_context.selection.entry_number!=terminal_directory_entry)return 0;
 for(n=0;n<64 && path[n];++n){}
 if(!n || n==64 || path[0]<'A' || path[0]>'Z' || path[1]!=':' || path[2]!='\\' ||
  !capture_file_validate_path(path,0))return 0;
 return (unsigned)path;
}
