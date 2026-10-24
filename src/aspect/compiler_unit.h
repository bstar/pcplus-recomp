#ifndef PCPLUS_ASPECT_COMPILER_UNIT_H
#define PCPLUS_ASPECT_COMPILER_UNIT_H
#include "compiler_lexer.h"
enum { ASPECT_COMPILE_OK=0,ASPECT_COMPILE_LEXICAL,ASPECT_COMPILE_SYNTAX,
       ASPECT_COMPILE_HEAP,ASPECT_COMPILE_STATE };
enum { ASPECT_SYMBOL_GLOBAL=0,ASPECT_SYMBOL_LOCAL,ASPECT_SYMBOL_PARAMETER };
typedef struct aspect_compiler_symbol {
 struct aspect_compiler_symbol *next,*parameter_next;
 unsigned kind,space,index;
 char name[1];
} aspect_compiler_symbol;
typedef struct aspect_compiler_source {
 struct aspect_compiler_source *next;
 unsigned long line,offset;
} aspect_compiler_source;
/* Only initializer ranges need expression/destination metadata. Ordinary
 * body/declaration lines retain the full32-bit source position alone. */
typedef struct aspect_compiler_initializer {
 struct aspect_compiler_initializer *next;
 unsigned long line,offset;
 unsigned first,last,chained;
 aspect_compiler_symbol *destination;
} aspect_compiler_initializer;
typedef struct aspect_compiler_procedure {
 struct aspect_compiler_procedure *next;
 aspect_compiler_symbol *symbols,*symbols_tail,*parameters,*parameters_tail;
 aspect_compiler_source *body,*body_tail;
 aspect_compiler_initializer *initializers,*initializers_tail;
 aspect_compiler_source *declarations,*declarations_tail;
 unsigned size,locals;
 unsigned long parameter_bytes,line,offset;
 char name[1];
} aspect_compiler_procedure;
struct aspect_compiler_allocation;
typedef struct aspect_compiler_unit {
 struct aspect_compiler_allocation *allocations;
 /* Internal workspace adapter lends aligned storage until dispose. Ordinary
  * initialized units leave this empty and retain CRT ownership semantics. */
 void *borrowed;unsigned borrowed_bytes,borrowed_used;
 aspect_compiler_symbol *globals,*globals_tail;
 aspect_compiler_procedure *procedures,*procedures_tail;
 aspect_compiler_source *declarations,*declarations_tail;
 unsigned counts[4],status,lexical_status,loaded;
 unsigned long error_line,error_offset,allocation_calls,live_allocations,peak_allocations,fail_after;
} aspect_compiler_unit;
/* Init only an uninitialized or disposed unit. Load borrows the source FILE
 * from its current position; no close/rewind. Errors retire every allocation.
 * Dispose is idempotent and retains diagnostics/metrics. Explicit init begins
 * a new compile. fail_after is an allocation fault-injection ceiling; default
 * FFFFFFFF. Symbols/source ranges are owned until dispose, never line aliases.
 * This pass does not validate statement/initializer expressions or emit ASX. */
void aspect_compiler_unit_init(aspect_compiler_unit *);
void aspect_compiler_unit_dispose(aspect_compiler_unit *);
unsigned aspect_compiler_unit_load(aspect_compiler_unit *,FILE *);
#endif
