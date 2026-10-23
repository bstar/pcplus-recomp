#ifndef PCPLUS_NOTICE_UNWIND_H
#define PCPLUS_NOTICE_UNWIND_H
#include "notice.h"
/* Private outer-owner ABI: the caller must have already abandoned the stack
 * containing notice_show and its callbacks. Never call from a live callback.
 * Successful retirement returns OK while preserving the original cause in
 * result; failed cleanup retains the window and keeps notice_active true. */
unsigned NOTICE_CODE __cdecl notice_unwind(notice_result *result);
#endif
