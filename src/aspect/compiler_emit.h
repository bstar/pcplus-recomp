#ifndef PCPLUS_ASPECT_COMPILER_EMIT_H
#define PCPLUS_ASPECT_COMPILER_EMIT_H
#include "compiler_expr.h"
#include "compiler_output.h"
void aspect_compiler_emit_operand(aspect_compiler_expression *,aspect_compiler_output *,const aspect_compiler_value *,unsigned compact);
void aspect_compiler_emit_expression(aspect_compiler_expression *,aspect_compiler_output *,unsigned node,unsigned slot,aspect_compiler_value *);
void aspect_compiler_emit_assignment(aspect_compiler_expression *,aspect_compiler_output *,unsigned destination,unsigned source,unsigned chained);
/* Validate a writable symbol and emit its wire reference. */
unsigned aspect_compiler_emit_destination(aspect_compiler_expression *,aspect_compiler_output *,unsigned node,unsigned *kind);
#endif
