/* ASX operands/expressions; positional strings and DWORD branch patches retain
 * the host/original compiler contracts. No statement grammar or final compiler
 * transaction is provided by this component. */
#include "compiler_emit.h"
#include <string.h>
static unsigned ready(aspect_compiler_expression *e,aspect_compiler_output *o)
{return !e->status&&!o->status;}
static void error(aspect_compiler_expression *e)
{aspect_compiler_expression_error(e,ASPECT_COMPILE_SYNTAX);}
static unsigned lvalue(aspect_compiler_expression *e,unsigned index,aspect_compiler_symbol_info *info)
{
 if(aspect_compiler_expression_symbol(e,index,info))return 0;
 if(info->readonly){error(e);return 0;}return 1;
}
static void variable(aspect_compiler_output *o,const aspect_compiler_symbol_info *info)
{
 static const unsigned char globals[4]={0x8d,0x8e,0x8f,0x8c};
 static const unsigned char locals[4]={0xa1,0xa2,0xa3,0xa0};
 static const unsigned char params[4]={0x97,0x98,0x99,0x96};
 if(info->builtin==1){aspect_compiler_emit_byte(o,info->kind==0?0x6f:info->kind==1?0x70:0x6e);aspect_compiler_emit_byte(o,info->index);}
 else if(info->builtin==2){aspect_compiler_emit_byte(o,0x64);aspect_compiler_emit_byte(o,info->index);}
 else if(info->space==ASPECT_SYMBOL_GLOBAL){aspect_compiler_emit_byte(o,globals[info->kind]);aspect_compiler_emit_byte(o,info->index);}
 else{aspect_compiler_emit_byte(o,info->space==ASPECT_SYMBOL_LOCAL?locals[info->kind]:params[info->kind]);aspect_compiler_emit_word(o,info->index);}
}
void aspect_compiler_emit_operand(aspect_compiler_expression *e,aspect_compiler_output *o,const aspect_compiler_value *v,unsigned compact)
{
 static const unsigned char table[13]={0xb3,0x35,0x0b,0xc7,0x47,0x29,0x1d,0xfb,0x1f,0x7f,0x05,0x59,0x17};
 aspect_compiler_symbol_info info;aspect_compiler_token token;
 unsigned i,n,parity,stride,t;unsigned long wire;unsigned char c;
 if(!ready(e,o))return;
 switch(v->tag){
 case ASPECT_EXPR_CONSTANT:
  if(v->kind==2){aspect_compiler_emit_byte(o,0xad);for(i=0;i<8;++i)aspect_compiler_emit_byte(o,v->ieee[i]);}
  else if(v->kind==1){aspect_compiler_emit_byte(o,0xac);wire=v->negative?0UL-v->integer:v->integer;aspect_compiler_emit_dword(o,wire);}
  else if(v->kind==0){
   wire=v->negative?0UL-v->integer:v->integer;
   if(compact&&!v->negative&&!v->wide&&v->integer<=255UL){aspect_compiler_emit_byte(o,0xb5);aspect_compiler_emit_byte(o,(unsigned)wire);}
   else{aspect_compiler_emit_byte(o,0xab);aspect_compiler_emit_word(o,(unsigned)wire);}
  }else error(e);
  break;
 case ASPECT_EXPR_STRING:
  token=e->line->tokens[v->index];n=token.length-2;
  if(!n){aspect_compiler_emit_byte(o,0x6e);aspect_compiler_emit_byte(o,19);break;}
  if(n>80){error(e);return;}
  for(i=0;i<n;++i)if(!e->line->bytes[token.start+1+i]){error(e);return;}
  aspect_compiler_emit_byte(o,0xaa);parity=(unsigned)(o->position&1UL);
  stride=(unsigned)((o->position+e->line->number)%12UL)+1;
  aspect_compiler_emit_byte(o,0xb3+n);aspect_compiler_emit_byte(o,(parity<<7)|(stride+n));
  for(i=1;i<=n;++i){t=(i*stride)%13;c=e->line->bytes[token.start+i];aspect_compiler_emit_byte(o,(t+parity)%2?c-table[t]:c+table[t]);}
  break;
 case ASPECT_EXPR_SYMBOL:
  if(!aspect_compiler_expression_symbol(e,v->node,&info))variable(o,&info);
  break;
 case ASPECT_EXPR_TEMPORARY:
  if(v->index>255||v->kind>3){error(e);return;}
  aspect_compiler_emit_byte(o,0x79+v->kind);aspect_compiler_emit_byte(o,v->index);break;
 default:error(e);
 }
}
static unsigned long jump(aspect_compiler_output *o,unsigned opcode)
{unsigned long offset;aspect_compiler_emit_byte(o,opcode);offset=o->position;aspect_compiler_emit_dword(o,0);return offset;}
static void temporary(aspect_compiler_value *v,unsigned kind,unsigned slot)
{memset(v,0,sizeof(*v));v->tag=ASPECT_EXPR_TEMPORARY;v->kind=kind;v->index=slot;}
static void negate(aspect_compiler_value *v)
{if(v->kind==2)v->ieee[7]^=128;else if(v->nonzero)v->negative^=1;}
/* Branch lists are caller-owned fixed storage, bounded by the source token
 * count. Each nested short-circuit scope retires its own list after patching. */
typedef struct branches {unsigned head,tail;} branches;
static void branch(aspect_compiler_expression *,aspect_compiler_output *,unsigned,unsigned,branches *,unsigned);
static void add_branch(aspect_compiler_expression *e,branches *b,unsigned long offset)
{
 unsigned index;
 if(e->fixup_free){index=e->fixup_free;e->fixup_free=e->fixup_next[index-1];}
 else if(e->fixup_used<ASPECT_EXPR_NODE_MAX)index=++e->fixup_used;
 else{error(e);return;}
 e->fixup_offsets[index-1]=offset;e->fixup_next[index-1]=0;
 if(b->tail)e->fixup_next[b->tail-1]=index;else b->head=index;
 b->tail=index;
}
static void patch_branches(aspect_compiler_expression *e,aspect_compiler_output *o,branches *b)
{
 unsigned index=b->head,next;
 while(index){
  next=e->fixup_next[index-1];aspect_compiler_patch_dword(o,e->fixup_offsets[index-1],o->position);
  e->fixup_next[index-1]=e->fixup_free;e->fixup_free=index;index=next;
 }
 b->head=b->tail=0;
}
static void boolean(aspect_compiler_expression *e,aspect_compiler_output *o,unsigned index,unsigned slot)
{
 branches b;unsigned wanted=e->nodes[index-1].operation==ASPECT_OP_OR;unsigned long end;
 b.head=b.tail=0;branch(e,o,index,wanted,&b,slot);if(!ready(e,o))return;
 aspect_compiler_emit_byte(o,0x5b);aspect_compiler_emit_byte(o,0);aspect_compiler_emit_byte(o,0x79);aspect_compiler_emit_byte(o,slot);aspect_compiler_emit_byte(o,0xab);aspect_compiler_emit_word(o,!wanted);
 end=jump(o,0x62);patch_branches(e,o,&b);
 aspect_compiler_emit_byte(o,0x5b);aspect_compiler_emit_byte(o,0);aspect_compiler_emit_byte(o,0x79);aspect_compiler_emit_byte(o,slot);aspect_compiler_emit_byte(o,0xab);aspect_compiler_emit_word(o,wanted);
 aspect_compiler_patch_dword(o,end,o->position);
}
static void branch(aspect_compiler_expression *e,aspect_compiler_output *o,unsigned index,unsigned wanted,branches *fixups,unsigned slot)
{
 aspect_compiler_node *n=&e->nodes[index-1];aspect_compiler_value value;
 branches local,*list;unsigned natural,opcode;unsigned long offset;
 if(!ready(e,o))return;
 if(n->value.tag==ASPECT_EXPR_BINARY&&(n->operation==ASPECT_OP_OR||n->operation==ASPECT_OP_AND)){
  natural=n->operation==ASPECT_OP_OR;local.head=local.tail=0;list=wanted==natural?fixups:&local;
  branch(e,o,n->left,natural,list,slot);branch(e,o,n->right,natural,list,slot);
  if(wanted!=natural&&ready(e,o)){add_branch(e,fixups,jump(o,0x62));patch_branches(e,o,list);}
  return;
 }
 if(aspect_compiler_expression_kind(e,index)==3){error(e);return;}
 aspect_compiler_emit_expression(e,o,index,slot,&value);if(!ready(e,o))return;
 if(value.tag==ASPECT_EXPR_CONSTANT){if(value.nonzero==wanted)add_branch(e,fixups,jump(o,0x62));}
 else{opcode=wanted?0xbc:0xbd;offset=jump(o,opcode);add_branch(e,fixups,offset);aspect_compiler_emit_operand(e,o,&value,0);}
}
void aspect_compiler_emit_expression(aspect_compiler_expression *e,aspect_compiler_output *o,unsigned index,unsigned slot,aspect_compiler_value *result)
{
 static const unsigned char opcodes[15]={0,0,0,0,0x32,0x7f,0x6d,0x54,0x68,0x48,0x00,0xb5,0x7d,0x26,0x7b};
 aspect_compiler_node *n;aspect_compiler_value left,right;
 aspect_compiler_symbol_info info;int kind,source,a,b;unsigned opcode;
 memset(result,0,sizeof(*result));
 if(!ready(e,o))return;
 if(slot>255||!index||index>e->count){error(e);return;}
 n=&e->nodes[index-1];
 if(n->value.tag==ASPECT_EXPR_CONSTANT||n->value.tag==ASPECT_EXPR_STRING||n->value.tag==ASPECT_EXPR_SYMBOL){*result=n->value;return;}
 if(n->value.tag==ASPECT_EXPR_UNARY){
  if(n->operation==ASPECT_OP_SUB&&e->nodes[n->left-1].value.tag==ASPECT_EXPR_CONSTANT){*result=e->nodes[n->left-1].value;negate(result);return;}
  aspect_compiler_emit_expression(e,o,n->left,slot,&left);kind=aspect_compiler_expression_kind(e,n->left);if(!ready(e,o))return;
  if(kind==3){error(e);return;}
  if(n->operation==ASPECT_OP_INC||n->operation==ASPECT_OP_DEC){
   if(!lvalue(e,n->left,&info))return;
   aspect_compiler_emit_byte(o,n->operation==ASPECT_OP_INC?0x5a:0x1e);variable(o,&info);
   aspect_compiler_emit_byte(o,0x5b);aspect_compiler_emit_byte(o,kind*5);aspect_compiler_emit_byte(o,0x79+kind);aspect_compiler_emit_byte(o,slot);aspect_compiler_emit_operand(e,o,&e->nodes[n->left-1].value,0);
  }else if(left.tag==ASPECT_EXPR_CONSTANT){*result=left;negate(result);return;}
  else{aspect_compiler_emit_byte(o,0x7e);aspect_compiler_emit_byte(o,kind*5);aspect_compiler_emit_operand(e,o,&left,0);aspect_compiler_emit_byte(o,0x79+kind);aspect_compiler_emit_byte(o,slot);}
  temporary(result,(unsigned)kind,slot);return;
 }
 if(n->operation==ASPECT_OP_AND||n->operation==ASPECT_OP_OR){boolean(e,o,index,slot);temporary(result,0,slot);return;}
 if(n->operation==ASPECT_OP_ASSIGN){
  aspect_compiler_emit_expression(e,o,n->right,slot,&right);if(!lvalue(e,n->left,&info))return;
  source=aspect_compiler_expression_kind(e,n->right);if(!ready(e,o))return;
  if(info.kind==3||source==3){error(e);return;}
  aspect_compiler_emit_byte(o,0x5c);aspect_compiler_emit_byte(o,info.kind*4+source);variable(o,&info);aspect_compiler_emit_operand(e,o,&right,0);aspect_compiler_emit_byte(o,0x79+info.kind);aspect_compiler_emit_byte(o,slot);temporary(result,info.kind,slot);return;
 }
 aspect_compiler_emit_expression(e,o,n->left,slot,&left);
 aspect_compiler_emit_expression(e,o,n->right,slot+(left.tag==ASPECT_EXPR_TEMPORARY),&right);
 a=aspect_compiler_expression_kind(e,n->left);b=aspect_compiler_expression_kind(e,n->right);source=a>b?a:b;kind=aspect_compiler_expression_kind(e,index);
 if(!ready(e,o))return;
 if(source==3){error(e);return;}
 opcode=n->operation<15?opcodes[n->operation]:0xff;if(opcode==0xff){error(e);return;}
 aspect_compiler_emit_byte(o,opcode);aspect_compiler_emit_byte(o,kind*4+source);
 aspect_compiler_emit_operand(e,o,&left,0);aspect_compiler_emit_operand(e,o,&right,0);
 aspect_compiler_emit_byte(o,0x79+kind);aspect_compiler_emit_byte(o,slot);temporary(result,(unsigned)kind,slot);
}
void aspect_compiler_emit_assignment(aspect_compiler_expression *e,aspect_compiler_output *o,unsigned dest,unsigned source,unsigned chained)
{
 aspect_compiler_symbol_info info;aspect_compiler_value value;int sourcekind;
 if(!lvalue(e,dest,&info))return;
 aspect_compiler_emit_expression(e,o,source,0,&value);sourcekind=aspect_compiler_expression_kind(e,source);
 if(!ready(e,o))return;
 if(info.kind==3){
  if(sourcekind!=3){error(e);return;}
  aspect_compiler_emit_byte(o,0xac);variable(o,&info);aspect_compiler_emit_operand(e,o,&value,0);aspect_compiler_emit_byte(o,0);
 }else{
  if(sourcekind==3){error(e);return;}
  aspect_compiler_emit_byte(o,chained?0x5c:0x5b);aspect_compiler_emit_byte(o,info.kind*4+sourcekind);variable(o,&info);aspect_compiler_emit_operand(e,o,&value,0);
  if(chained){aspect_compiler_emit_byte(o,0x79+info.kind);aspect_compiler_emit_byte(o,0);}
 }
}
