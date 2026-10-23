/* Banked source-owned presentation for the native PROGRAM errno switch.
 * It never changes the native process result or the raw child return word. */
#include "program_notice.h"
#include "../ui/notice_unwind.h"
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
{return notice_unwind(&program_notice_result);}
