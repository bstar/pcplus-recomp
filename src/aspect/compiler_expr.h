#ifndef PCPLUS_ASPECT_COMPILER_EXPR_H
#define PCPLUS_ASPECT_COMPILER_EXPR_H
#include "compiler_unit.h"
#define ASPECT_EXPR_NODE_MAX ASPECT_COMPILER_TOKEN_MAX
enum { ASPECT_EXPR_CONSTANT=1,ASPECT_EXPR_STRING,ASPECT_EXPR_SYMBOL,
 ASPECT_EXPR_TEMPORARY,ASPECT_EXPR_UNARY,ASPECT_EXPR_BINARY };
enum { ASPECT_OP_ASSIGN=1,ASPECT_OP_OR,ASPECT_OP_AND,ASPECT_OP_EQ,ASPECT_OP_NE,
 ASPECT_OP_LT,ASPECT_OP_GT,ASPECT_OP_LE,ASPECT_OP_GE,ASPECT_OP_ADD,ASPECT_OP_SUB,
 ASPECT_OP_MUL,ASPECT_OP_DIV,ASPECT_OP_MOD,ASPECT_OP_INC,ASPECT_OP_DEC };
typedef struct aspect_compiler_value {
 unsigned tag,kind,index,node,negative,nonzero,wide,explicit_long;
 unsigned long integer;
 unsigned char ieee[8];
} aspect_compiler_value;
typedef struct aspect_compiler_node {
 aspect_compiler_value value;
 unsigned operation,left,right;
} aspect_compiler_node;
typedef struct aspect_compiler_expression {
 const aspect_compiler_line *line;
 const aspect_compiler_unit *unit;
 const aspect_compiler_procedure *procedure;
 unsigned first,last,position,count,status,error_token,fixup_used,fixup_free;
 unsigned long fixup_offsets[ASPECT_EXPR_NODE_MAX];
 unsigned fixup_next[ASPECT_EXPR_NODE_MAX];
 aspect_compiler_node nodes[ASPECT_EXPR_NODE_MAX];
} aspect_compiler_expression;
typedef struct aspect_compiler_symbol_info {
 unsigned kind,space,index,readonly,builtin;
} aspect_compiler_symbol_info;
/* Caller supplies pool storage (about11KiB), outside the recursive stack. The
 * AST borrows token/line and inventory views until the next init. Node0=null.
 * A parse consumes one expression at the requested precedence, retaining the
 * next-token cursor for command arguments. All error states are sticky. */
void aspect_compiler_expression_init(aspect_compiler_expression *,const aspect_compiler_line *,
 const aspect_compiler_unit *,const aspect_compiler_procedure *,unsigned,unsigned);
unsigned aspect_compiler_parse_expression(aspect_compiler_expression *,unsigned minimum);
unsigned aspect_compiler_parse_assignment(aspect_compiler_expression *,unsigned *destination,unsigned *source);
int aspect_compiler_expression_kind(aspect_compiler_expression *,unsigned node);
unsigned aspect_compiler_expression_symbol(aspect_compiler_expression *,unsigned node,aspect_compiler_symbol_info *);
void aspect_compiler_expression_error(aspect_compiler_expression *,unsigned status);
/* Atomic operand/word validation use the original AST to retain the special
 * unsuffixed -32768 boundary rule. Neither operation emits output. */
unsigned aspect_compiler_atomic(aspect_compiler_expression *,unsigned,aspect_compiler_value *);
unsigned aspect_compiler_word_argument(aspect_compiler_expression *,unsigned,aspect_compiler_value *);
#endif
