#ifndef PCPLUS_ASPECT_COMPILER_PROGRAM_INTERNAL_H
#define PCPLUS_ASPECT_COMPILER_PROGRAM_INTERNAL_H
#include "compiler_program.h"
typedef struct pc_proc pc_proc;
typedef struct pc_edge {struct pc_edge *next;pc_proc *target;} pc_edge;
struct pc_proc {
 pc_proc *next;aspect_compiler_procedure *source;pc_edge *calls;
 unsigned selected,referenced;unsigned long address;
};
typedef struct pc_patch {struct pc_patch *next;unsigned long offset;} pc_patch;
typedef struct pc_call {struct pc_call *next;pc_proc *target;unsigned long offset;} pc_call;
typedef struct pc_block {
 struct pc_block *parent;unsigned type,active,kind,has_next,has_default;
 unsigned long branch,start,next,default_at;pc_patch *exits;
} pc_block;
struct pc_allocation;
typedef struct pc_compiler {
 FILE *input;aspect_compiler_unit unit;aspect_compiler_line line,filtered;
 aspect_compiler_expression expression;aspect_compiler_output output;
 aspect_compiler_report *report;pc_proc *procedures,*tail,*current;
 pc_block *blocks,*free_blocks;pc_call *calls;
 struct pc_allocation *owned,*phase;
 unsigned long fail_after;
} pc_compiler;
void *pc_allocate(pc_compiler *,unsigned,unsigned phase);
void pc_error(pc_compiler *,unsigned);
unsigned pc_ready(pc_compiler *);
unsigned pc_equal(pc_compiler *,unsigned,const char *);
pc_proc *pc_procedure(pc_compiler *,unsigned token);
unsigned long pc_jump(pc_compiler *,unsigned);
void pc_call_patch(pc_compiler *,unsigned long,pc_proc *);
void pc_commands(pc_compiler *);
void pc_arguments(pc_compiler *,unsigned first,unsigned *args,unsigned *count);
void pc_filter(pc_compiler *,unsigned first);
#endif
