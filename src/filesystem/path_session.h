#ifndef PCPLUS_PATH_SESSION_H
#define PCPLUS_PATH_SESSION_H
#include "path_owner.h"
enum { PATH_SESSION_UNBOUND=6,PATH_SESSION_QUARANTINED=7 };
enum { PATH_SESSION_COLD=0x7050,PATH_SESSION_ACTIVE=1,PATH_SESSION_RESTORED=2 };
/* Mutable DOS code-bank storage: compile this unit with -nt=FILE_CODE and
 * -nc=FARCODE. No state occupies DGROUP. The exported layout supports retained
 * memory/map validation, not caller mutation. */
typedef struct path_session_state {
 unsigned state,quarantined,startup_drive,last_dos_error;
 char startup_path[68];
} path_session_state;
extern path_session_state __based(__segname("_CODE")) path_session_storage;
/* Foreground synchronous DOS16, near arguments, DS=SS. Begin freezes once;
 * reentry never replaces it, including after verified restoration. */
unsigned __far __cdecl path_session_begin(void);
/* Lifecycle/quarantine refusal and invalid arguments preserve result. Otherwise
 * path_change supplies its unchanged result contract. Failed rollback latches
 * quarantine; no subsequent changes are admitted until verified restoration. */
unsigned __far __cdecl path_session_change(const char *,path_result *);
/* Cold/restored no-op. Restore the startup absolute directory/default drive,
 * then compare an independent DOS snapshot. Any failure preserves the saved
 * identity and quarantines for retry. Only verified recovery clears quarantine.
 * PATH_CHANGE discards native DOS error; query errors retain last_dos_error. */
unsigned __far __cdecl path_session_restore(void);
/* Query current default-drive absolute directory into a disjoint external68-
 * byte near buffer. Failure preserves output; available in every lifecycle.
 * PATH_DRIVE means failed/invalid DOS query (error retained); ARGUMENT is bad
 * buffer. No directory mutation. */
unsigned __far __cdecl path_session_current(char *);
unsigned __far __cdecl path_session_quarantined(void);
#endif
