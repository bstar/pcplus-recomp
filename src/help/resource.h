#ifndef PCPLUS_HELP_RESOURCE_H
#define PCPLUS_HELP_RESOURCE_H
#include "view.h"
#define HELP_RESOURCE_MISSING 16
#define HELP_RESOURCE_CLOSE 17
unsigned __far __cdecl help_resource_open(const char *);
unsigned __far __cdecl help_resource_step(void);
unsigned __far __cdecl help_resource_key(unsigned);
/* Retire only the file/model. The enclosing notice owns view close/discard. */
unsigned __far __cdecl help_resource_close(void);
unsigned __far __cdecl help_resource_active(void);
#endif
