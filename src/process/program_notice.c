/* Banked source-owned presentation for the native PROGRAM errno switch.
 * It never changes the native process result or the raw child return word. */
#include "program_notice.h"
#include "../ui/notice_unwind.h"
#include "../ui/notice_window.h"
#include "../aspect/runtime.h"
extern unsigned runtime_external_invocation_active,runtime_external_scope_storage;
extern unsigned __far __cdecl program_bank_notice_retry(void);
extern void __far __cdecl program_bank_notice_finish(void);
notice_result program_notice_result;
unsigned program_notice_calls,program_notice_errno;
static notice_options options={0x70,0,74,1000000UL,0,0};
#if defined(PROGRAM_NOTICE_DIAGNOSTIC)
extern void __cdecl notice_fault_phase(unsigned);
#endif
unsigned __far __cdecl program_notice_error(unsigned error)
{
 const char *message;unsigned status;
 switch(error){
 case 2:message="Program not found.";break;
 case 7:message="Command line is too long.";break;
 case 8:message="Invalid executable format.";break;
 case 12:message="Insufficient memory to run program.";break;
 default:message="Unable to execute program.";break;
 }
 ++program_notice_calls;program_notice_errno=error;
#if defined(PROGRAM_NOTICE_DIAGNOSTIC)
 notice_fault_phase(1);
#endif
 options.service=program_notice_callback();
 status=notice_show(message,1,&options,&program_notice_result);
#if defined(PROGRAM_NOTICE_DIAGNOSTIC)
 notice_fault_phase(3);
#endif
 return status;
}
unsigned __far __cdecl program_notice_unwind(void)
{
 unsigned status=NOTICE_OK;
 if(notice_active())status=notice_unwind(&program_notice_result);
 return notice_window_phase()?(status?status:NOTICE_BUSY):status;
}
unsigned __far __cdecl program_notice_active(void)
{return notice_active()||notice_window_phase();}
unsigned __far __cdecl program_notice_retry(void)
{
 unsigned status;
 /* Only the stopped invocation's owner may retry; never a live callback. */
 if(runtime_external_invocation_active||!runtime_external_scope_storage)return ASPECT_RUN_STATE;
 status=program_bank_notice_retry();if(status)return status;
 program_bank_notice_finish();
 return runtime_external_scope_storage||program_notice_active()?ASPECT_RUN_STATE:0;
}
