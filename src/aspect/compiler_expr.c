#include "compiler_expr.h"
#include "compiler_decimal.h"
#include <stdlib.h>
#include <string.h>
#include <limits.h>
static unsigned equal(const aspect_compiler_line *line,unsigned index,const char *text)
{
 unsigned i,n;if(index>=line->count)return 0;n=line->tokens[index].length;
 if(strlen(text)!=n)return 0;
 for(i=0;i<n;++i){unsigned char c=line->bytes[line->tokens[index].start+i];if(c>='A'&&c<='Z')c+='a'-'A';if(c!=(unsigned char)text[i])return 0;}
 return 1;
}
void aspect_compiler_expression_error(aspect_compiler_expression *e,unsigned status)
{if(!e->status){e->status=status;e->error_token=e->position;}}
void aspect_compiler_expression_init(aspect_compiler_expression *e,const aspect_compiler_line *line,
 const aspect_compiler_unit *unit,const aspect_compiler_procedure *proc,unsigned first,unsigned last)
{
 memset(e,0,sizeof(*e));e->line=line;e->unit=unit;e->procedure=proc;
 e->first=e->position=first;e->last=last;
 if(!line||first>last||last>line->count)aspect_compiler_expression_error(e,ASPECT_COMPILE_STATE);
}
static unsigned operation(const aspect_compiler_line *line,unsigned token)
{
 static const char *names[]={"=","||","&&","==","!=","<",">","<=",">=","+","-","*","/","%","++","--"};
 unsigned i;for(i=0;i<16;++i)if(equal(line,token,names[i]))return i+1;return 0;
}
static unsigned priority(unsigned op)
{if(op==1)return 1;if(op==2)return 2;if(op==3)return 3;if(op>=4&&op<=9)return 4;if(op==10||op==11)return 5;if(op>=12&&op<=14)return 6;return 0;}
static unsigned node(aspect_compiler_expression *e,unsigned tag,unsigned token)
{
 aspect_compiler_node *n;
 if(e->count==ASPECT_EXPR_NODE_MAX){aspect_compiler_expression_error(e,ASPECT_COMPILE_SYNTAX);return 0;}
 n=&e->nodes[e->count++];memset(n,0,sizeof(*n));n->value.tag=tag;n->value.index=token;n->value.node=e->count;return e->count;
}
static void number(aspect_compiler_expression *e,unsigned index,unsigned token)
{
 unsigned char text[254];unsigned n,i,base=10,digit;unsigned long value=0;
 aspect_compiler_value *v=&e->nodes[index-1].value;
 aspect_compiler_token_copy(e->line,token,text,sizeof(text));n=strlen((char *)text);
 v->explicit_long=n && text[n-1]=='l';if(v->explicit_long)text[--n]=0;
 if(!(n>1&&text[0]=='0'&&text[1]=='x') && (strchr((char *)text,'.')||strchr((char *)text,'e'))){
  v->kind=2;
  if(aspect_compiler_decimal(text,n,v->ieee)){aspect_compiler_expression_error(e,ASPECT_COMPILE_SYNTAX);return;}
  v->nonzero=(v->ieee[7]&127)!=0;
  for(i=0;i<7;++i)if(v->ieee[i])v->nonzero=1;
  return;
 }
 i=0;if(n>1&&text[0]=='0'&&text[1]=='x'){base=16;i=2;}
 for(;i<n;++i){
  digit=text[i]<='9'?text[i]-'0':text[i]-'a'+10;
  if(value>(ULONG_MAX-digit)/base)v->wide=1;
  value=value*base+digit;
  if(digit)v->nonzero=1;
 }
 v->integer=value;v->kind=v->explicit_long||v->wide||value>32767UL?1:0;
}
unsigned aspect_compiler_parse_expression(aspect_compiler_expression *e,unsigned minimum)
{
 unsigned token,op,left=0,right,p;aspect_compiler_node *n;
 if(e->status)return 0;
 if(!minimum){aspect_compiler_expression_error(e,ASPECT_COMPILE_STATE);return 0;}
 if(e->position==e->last){aspect_compiler_expression_error(e,ASPECT_COMPILE_SYNTAX);return 0;}
 token=e->position++;op=operation(e->line,token);
 if(op==ASPECT_OP_SUB||op==ASPECT_OP_INC||op==ASPECT_OP_DEC){
  left=node(e,ASPECT_EXPR_UNARY,token);if(!left)return 0;
  right=aspect_compiler_parse_expression(e,7);n=&e->nodes[left-1];n->operation=op;n->left=right;
 }else if(equal(e->line,token,"(")){
  left=aspect_compiler_parse_expression(e,1);
  if(e->status)return 0;
  if(e->position==e->last || !equal(e->line,e->position,")")){aspect_compiler_expression_error(e,ASPECT_COMPILE_SYNTAX);return 0;}
  ++e->position;
 }else if(e->line->tokens[token].kind==ASPECT_TOKEN_NUMBER){left=node(e,ASPECT_EXPR_CONSTANT,token);if(left)number(e,left,token);}
 else if(e->line->tokens[token].kind==ASPECT_TOKEN_STRING)left=node(e,ASPECT_EXPR_STRING,token);
 else if(e->line->tokens[token].kind==ASPECT_TOKEN_IDENTIFIER)left=node(e,ASPECT_EXPR_SYMBOL,token);
 else{aspect_compiler_expression_error(e,ASPECT_COMPILE_SYNTAX);return 0;}
 while(!e->status&&e->position<e->last){
  op=operation(e->line,e->position);p=priority(op);if(p<minimum)break;
  token=e->position++;right=aspect_compiler_parse_expression(e,op==ASPECT_OP_ASSIGN?p:p+1);
  if(e->status)return 0;
  p=node(e,ASPECT_EXPR_BINARY,token);if(!p)return 0;
  n=&e->nodes[p-1];n->operation=op;n->left=left;n->right=right;left=p;
 }
 return e->status?0:left;
}
unsigned aspect_compiler_expression_symbol(aspect_compiler_expression *e,unsigned index,aspect_compiler_symbol_info *info)
{
 static const char *names[]={"comdata","failure","forever","found","success","waitfor","$d_entry","$d_baud",
 "$d_ldate","$d_kbdfile","$d_metakey","$d_name","$d_note","$d_phone","$d_pword","$d_script","$null","$fattr","$fdate","$fext","$filename","$fname","$ftime","$fsize"};
 static const unsigned slots[]={20,21,22,23,27,28,3,0,0,1,2,3,4,5,6,7,19,9,10,11,12,13,14,1};
 unsigned i;unsigned char text[254];const aspect_compiler_symbol *s;aspect_compiler_node *n;
 if(e->status)return e->status;
 if(!index||index>e->count||!info){aspect_compiler_expression_error(e,ASPECT_COMPILE_STATE);return e->status;}
 n=&e->nodes[index-1];if(n->value.tag!=ASPECT_EXPR_SYMBOL){aspect_compiler_expression_error(e,ASPECT_COMPILE_SYNTAX);return e->status;}
 aspect_compiler_token_copy(e->line,n->value.index,text,sizeof(text));memset(info,0,sizeof(*info));
 for(i=0;i<sizeof(names)/sizeof(names[0]);++i)if(!strcmp((char *)text,names[i])){info->kind=i<7?0:(i==7||i==23)?1:3;info->index=slots[i];info->readonly=info->builtin=1;return 0;}
 if(text[0]=='s'&&text[1]>='0'&&text[1]<='9'&&!text[2]){info->kind=3;info->index=text[1]-'0';info->builtin=2;return 0;}
 s=e->procedure?e->procedure->symbols:0;
 for(;s;s=s->next)if(!strcmp(s->name,(char *)text))break;
 if(!s)for(s=e->unit?e->unit->globals:0;s;s=s->next)if(!strcmp(s->name,(char *)text))break;
 if(!s){aspect_compiler_expression_error(e,ASPECT_COMPILE_SYNTAX);return e->status;}
 info->kind=s->kind;info->space=s->space;info->index=s->index;return 0;
}
int aspect_compiler_expression_kind(aspect_compiler_expression *e,unsigned index)
{
 aspect_compiler_node *n;aspect_compiler_symbol_info info;int a,b;
 if(e->status)return -1;
 if(!index||index>e->count){aspect_compiler_expression_error(e,ASPECT_COMPILE_STATE);return -1;}
 n=&e->nodes[index-1];
 switch(n->value.tag){
 case ASPECT_EXPR_CONSTANT:case ASPECT_EXPR_TEMPORARY:return n->value.kind;
 case ASPECT_EXPR_STRING:return 3;
 case ASPECT_EXPR_SYMBOL:return aspect_compiler_expression_symbol(e,index,&info)?-1:(int)info.kind;
 case ASPECT_EXPR_UNARY:return aspect_compiler_expression_kind(e,n->left);
 case ASPECT_EXPR_BINARY:
  if(n->operation>=ASPECT_OP_OR && n->operation<=ASPECT_OP_GE)return 0;
  a=aspect_compiler_expression_kind(e,n->left);if(n->operation==ASPECT_OP_ASSIGN)return a;
  b=aspect_compiler_expression_kind(e,n->right);return a>b?a:b;
 }
 aspect_compiler_expression_error(e,ASPECT_COMPILE_STATE);return -1;
}
static void negate(aspect_compiler_value *v)
{if(v->kind==2)v->ieee[7]^=128;else if(v->nonzero)v->negative^=1;}
unsigned aspect_compiler_atomic(aspect_compiler_expression *e,unsigned index,aspect_compiler_value *v)
{
 aspect_compiler_node *n;
 if(e->status)return e->status;
 if(!index||index>e->count||!v){aspect_compiler_expression_error(e,ASPECT_COMPILE_STATE);return e->status;}
 n=&e->nodes[index-1];*v=n->value;
 if(v->tag==ASPECT_EXPR_UNARY && n->operation==ASPECT_OP_SUB && e->nodes[n->left-1].value.tag==ASPECT_EXPR_CONSTANT){*v=e->nodes[n->left-1].value;negate(v);}
 else if(v->tag!=ASPECT_EXPR_CONSTANT&&v->tag!=ASPECT_EXPR_SYMBOL&&v->tag!=ASPECT_EXPR_STRING)aspect_compiler_expression_error(e,ASPECT_COMPILE_SYNTAX);
 return e->status;
}
unsigned aspect_compiler_word_argument(aspect_compiler_expression *e,unsigned index,aspect_compiler_value *v)
{
 aspect_compiler_node *n,*child;int kind;unsigned minimum=0;
 if(aspect_compiler_atomic(e,index,v))return e->status;
 n=&e->nodes[index-1];
 if(n->value.tag==ASPECT_EXPR_UNARY&&n->operation==ASPECT_OP_SUB){
  child=&e->nodes[n->left-1];minimum=child->value.tag==ASPECT_EXPR_CONSTANT && child->value.kind!=2 &&
   !child->value.wide && child->value.integer==32768UL && !child->value.explicit_long;
 }
 kind=aspect_compiler_expression_kind(e,index);
 if(e->status)return e->status;
 if(kind!=0&&!minimum)aspect_compiler_expression_error(e,ASPECT_COMPILE_SYNTAX);
 if(v->tag==ASPECT_EXPR_CONSTANT){
  if(v->wide||v->integer>(v->negative?32768UL:32767UL))aspect_compiler_expression_error(e,ASPECT_COMPILE_SYNTAX);
  v->kind=0;
 }
 return e->status;
}

unsigned aspect_compiler_parse_assignment(aspect_compiler_expression *e,unsigned *destination,unsigned *source)
{
 static const char *names[5]={"+=","-=","*=","/=","%="};
 unsigned last=e->last,op=0,i,root;aspect_compiler_node *n;
 if(e->status)return e->status;
 if(!destination||!source||last-e->first<3){aspect_compiler_expression_error(e,ASPECT_COMPILE_SYNTAX);return e->status;}
 if(!equal(e->line,e->first+1,"=")){
  for(i=0;i<5;++i)if(equal(e->line,e->first+1,names[i]))op=ASPECT_OP_ADD+i;
  if(!op){aspect_compiler_expression_error(e,ASPECT_COMPILE_SYNTAX);return e->status;}
 }
 e->last=e->first+1;e->position=e->first;*destination=aspect_compiler_parse_expression(e,7);
 e->last=last;e->position=e->first+2;*source=aspect_compiler_parse_expression(e,1);
 if(e->position!=last)aspect_compiler_expression_error(e,ASPECT_COMPILE_SYNTAX);
 if(op&&!e->status){root=node(e,ASPECT_EXPR_BINARY,e->first+1);if(root){n=&e->nodes[root-1];n->operation=op;n->left=*destination;n->right=*source;*source=root;}}
 return e->status;
}
