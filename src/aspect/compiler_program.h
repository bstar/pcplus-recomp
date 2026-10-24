#ifndef PCPLUS_ASPECT_COMPILER_PROGRAM_H
#define PCPLUS_ASPECT_COMPILER_PROGRAM_H
#include "compiler_emit.h"
typedef struct aspect_compiler_report {
 unsigned status,lexical_status,output_status;
 unsigned long line,offset,bytes,procedures,emitted_procedures,allocation_calls,unit_allocation_calls;
} aspect_compiler_report;
typedef struct aspect_compiler_options {unsigned long fail_after,unit_fail_after;} aspect_compiler_options;
/* Compile binary CP437 source into a borrowed binary update FILE. Both must
 * start at offset0. Output is scratch storage and may contain a partial ASX on
 * error. The publisher must commit it only after this call succeeds. */
unsigned aspect_compiler_program(FILE *,FILE *,aspect_compiler_report *);
/* Diagnostic allocation ceilings; NULL uses unlimited production allocation.
 * Includes the context allocation and every owned/phase allocation. The unit
 * ceiling separately covers the already maintained inventory allocator. */
unsigned aspect_compiler_program_options(FILE *,FILE *,aspect_compiler_report *,const aspect_compiler_options *);
/* Caller-owned, suitably aligned workspace for the same compiler. A short,
 * wrapping or overlapping span is rejected. The workspace remains borrowed;
 * its contents are scratch and no allocator may retire it. */
unsigned aspect_compiler_program_workspace(FILE *,FILE *,aspect_compiler_report *,void *,unsigned);
#endif
