#ifndef PCPLUS_ASPECT_COMPILER_UNIT_DUMP_H
#define PCPLUS_ASPECT_COMPILER_UNIT_DUMP_H
#include <stdio.h>
/* Diagnostic inventory protocol, not ASX. The borrowed source stays open.
 * Return0 inventory success,1 compiler/input failure,2 output failure. */
int aspect_compiler_unit_dump(FILE *,FILE *);
#endif
