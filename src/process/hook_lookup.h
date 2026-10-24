#ifndef PCPLUS_HOOK_LOOKUP_H
#define PCPLUS_HOOK_LOOKUP_H
#include "dos_exec.h"
/* Optional HOOK_CODE policy above the raw EXEC boundary. Input name1..63,
 * tail0..47; disjoint near result8, DS=SS/IF1/DF0. Inherited environment is
 * bounded by its DOS MCB. Native353d exact-read/PCPLUS resolution precedes
 * COM/EXE/BAT and PATH search. Expanded paths are bounded to259 bytes and
 * batch command tails to126. No active settings/register publication here. */
unsigned __far __cdecl hook_lookup_run(const char *,const char *,process_result *);
#endif
