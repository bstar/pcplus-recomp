#ifndef PCPLUS_DIRECTORY_ACTIONS_H
#define PCPLUS_DIRECTORY_ACTIONS_H
#include "directory_replace.h"
/* Source-owned application orchestration. No UART or implicit file selection. */
/* TERMINAL_DIRECTORY_STORAGE routes these calls through the shared canonical
 * owner. OWNER14/RECOVERY15 are maintained facade statuses. A held retry
 * returns a fresh result with installed/recovery flags zero, never those of a
 * previous successful installation. Invalid arguments preserve result as
 * before. Call only after foreground UART quiescence or at startup/shutdown. */
directory_replace_status __cdecl directory_save_record(const char *path,unsigned entry,
 const unsigned char *expected,const unsigned char *replacement,
 directory_replace_result *result);
/* Apply bounded date/count patch and persist through the same replacement.
 * baseline is updated only when the replacement was actually installed,
 * including an installed result that reports retained-backup cleanup failure.
 * No change to baseline on pre-install failure. See recovery flags/status. */
directory_replace_status __cdecl directory_save_accounting(const char *path,unsigned entry,
 unsigned char *baseline,unsigned year,unsigned month,unsigned day,unsigned delta,
 directory_replace_result *result);
#endif
