#include "gateway_files.h"
#include "hook_lookup.h"
#include "process_handles.h"
#include "../capture/capture_session.h"
#include "../printer/printer_device.h"
#include "../directory/phone_log_file.h"
extern unsigned terminal_printer_count,terminal_printer_closing;
#pragma aux terminal_printer_count "terminal_printer_count";
#pragma aux terminal_printer_closing "terminal_printer_closing";
extern process_result terminal_program_result;
#pragma aux terminal_program_result "terminal_program_result";
/* The existing context/PSP service is in HOOK_CODE; an explicit far adapter
 * below avoids treating its near implementation as a cross-bank call. */
extern unsigned __far __cdecl gateway_files_context(void);
typedef struct gateway_state {unsigned cookie,active,recovery;} gateway_state;
gateway_state __based(__segname("_CODE")) gateway_files_storage={0x4746,0,0};
#define G gateway_files_storage
static unsigned apart(const void *a,unsigned n,const void *b,unsigned m)
{return (unsigned long)(unsigned)a+n<=(unsigned)b || (unsigned long)(unsigned)b+m<=(unsigned)a;}
static unsigned failed(process_result *r,unsigned status)
{r->status=status;r->dos_error=r->child_status=r->retained_paragraphs=0;return status;}
unsigned __far __cdecl gateway_files_owned(void)
{return G.cookie!=0x4746 || G.active || G.recovery || process_handles_active_query();}
unsigned __far __cdecl gateway_files_run(process_result *r)
{
 unsigned descriptors[5],count=0,index,handle,status,restore;
 if(!gateway_files_context() || r!=&terminal_program_result || !apart(r,sizeof(*r),descriptors,sizeof(descriptors)))return PROCESS_ARGUMENT;
 if(G.cookie!=0x4746 || G.recovery)return failed(r,GATEWAY_FILES_RECOVERY);
 if(G.active || process_handles_active_query())return failed(r,PROCESS_BUSY);
 if(terminal_printer_count || terminal_printer_closing || !phone_log_file_child_ready())return failed(r,PROCESS_BUSY);
 for(index=0;index<5;++index){
  handle=index<4?capture_file_child_handle(index):printer_device_child_handle();
  if(handle==0xfffe)return failed(r,PROCESS_BUSY);
  if(handle!=0xffff)descriptors[count++]=handle;
 }
 G.active=1;
 if(capture_session_child_flush()){G.active=0;return failed(r,PROCESS_BUSY);}
 if(count && process_handles_begin(descriptors,count)){G.active=0;return failed(r,PROCESS_BUSY);}
 status=gateway_lookup_run(r);
 restore=count?process_handles_end():0;
 if(G.cookie!=0x4746 || G.active!=1 || G.recovery)restore=1;
 G.active=0;
 if(restore){G.recovery=1;r->status=GATEWAY_FILES_RECOVERY;return GATEWAY_FILES_RECOVERY;}
 r->status=status;
 return status;
}
