#ifndef PCPLUS_PROGRAM_NOTICE_H
#define PCPLUS_PROGRAM_NOTICE_H
#include "../ui/notice.h"
unsigned __far __cdecl program_notice_error(unsigned error);
unsigned __far __cdecl program_notice_unwind(void);
unsigned __far __cdecl program_notice_active(void);
unsigned __far __cdecl program_notice_retry(void);
/* Getter runs in _TEXT; the returned near callback belongs to that CS. */
notice_service __far __cdecl program_notice_callback(void);
extern notice_result program_notice_result;
extern unsigned program_notice_calls,program_notice_errno;
#endif
