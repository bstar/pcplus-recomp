/* These two far bridges must share the near runtime/CRT's _TEXT CS. */
#include "runtime.h"
#include "notice_fault.h"
#include <stdlib.h>
const char * __far __cdecl notice_fault_request(void)
{return getenv("PCPNOTICE");}
unsigned __far __cdecl notice_fault_runtime_run(const char *path,unsigned limit)
{return aspect_runtime_run(path,limit);}
