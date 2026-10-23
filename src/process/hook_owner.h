#ifndef PCPLUS_HOOK_OWNER_H
#define PCPLUS_HOOK_OWNER_H
#include "hook_exchange.h"
#include "dos_exec.h"
#define HOOK_OWNER_SIZE 84U
#define HOOK_OWNER_PARAGRAPHS 133U
/* DOS16 only. Keep this object inside the retained parent PSP block (far code
 * storage is allowed). Caller sets trusted process PSP/minimum/keep limits covering all live code,
 * static/far data, stack and runtime heap allocations.
 * Foreground DS=SS, IF1, DF0. Zero storage before the first initialize; initialize
 * never overwrites an unknown/non-idle owner. This is not a helper sandbox. */
typedef struct hook_owner {
 unsigned signature,phase,psp,segment,generation,dos_error;
 process_result result;
 hook_key_command command;
 char tail[48];
} hook_owner;
enum {HOOK_OWNER_OK,HOOK_OWNER_ARGUMENT,HOOK_OWNER_STATE,HOOK_OWNER_MEMORY,
 HOOK_OWNER_PROCESS,HOOK_OWNER_DATA};
enum {HOOK_OWNER_IDLE,HOOK_OWNER_ACQUIRING,HOOK_OWNER_READY,HOOK_OWNER_EXECUTING,HOOK_OWNER_RETURNED};
unsigned __far __cdecl hook_owner_initialize(hook_owner __far *);
unsigned __far __cdecl hook_owner_open(hook_owner __far *,const unsigned char *,const unsigned char *,const unsigned char *,long);
unsigned __far __cdecl hook_owner_execute(hook_owner __far *,const char *);
/* Collect staging only; caller inspects process result and validates PRM
 * semantics separately. No UART or active application settings are changed. */
unsigned __far __cdecl hook_owner_collect(hook_owner __far *,unsigned char *,unsigned char *,unsigned char *);
unsigned __far __cdecl hook_owner_close(hook_owner __far *);
#endif
