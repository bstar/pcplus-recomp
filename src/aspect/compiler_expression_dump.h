#ifndef PCPLUS_ASPECT_COMPILER_EXPRESSION_DUMP_H
#define PCPLUS_ASPECT_COMPILER_EXPRESSION_DUMP_H
#include <stdio.h>
enum { ASPECT_DIAG_EXPRESSION=0,ASPECT_DIAG_ATOMIC,ASPECT_DIAG_WORD,
 ASPECT_DIAG_ASSIGNMENT,ASPECT_DIAG_CHAINED_ASSIGNMENT };
/* Developer AEX1 fragment protocol, not a complete ASX program. Load the source
 * inventory, select one physical line/scope and token interval, emit to an
 * owned temporary file and publish only a successful fragment. Sources and
 * output remain borrowed; internal inventory/AST/tempfile are always retired.
 * last=FFFF selects the complete line. Return0 success,1 compile failure,
 *2 diagnostic output failure. Absolute prefix exercises actual DWORD fixups. */
int aspect_compiler_expression_dump(FILE *,FILE *,unsigned long line,unsigned first,unsigned last,
 unsigned mode,unsigned long prefix,unsigned slot,unsigned compact);
#endif
