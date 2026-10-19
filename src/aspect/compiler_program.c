#include "compiler_program_internal.h"
#include <stdlib.h>
#include <string.h>
#include <io.h>
#include <limits.h>
#define PC_OUTPUT_ERROR 5
#define BLOCK_IF 1
#define BLOCK_WHILE 2
#define BLOCK_SWITCH 3
struct pc_allocation {struct pc_allocation *next;unsigned long alignment;unsigned char bytes[1];};
void pc_error(pc_compiler *c,unsigned status)
{if(!c->report->status){c->report->status=status;c->report->line=c->line.number;c->report->offset=c->line.offset;}}
void *pc_allocate(pc_compiler *c,unsigned bytes,unsigned phase)
{
 struct pc_allocation *p;
 if(c->report->status)return 0;
 if(c->report->allocation_calls++>=c->fail_after){pc_error(c,ASPECT_COMPILE_HEAP);return 0;}
 p=malloc(sizeof(*p)-1+bytes);if(!p){pc_error(c,ASPECT_COMPILE_HEAP);return 0;}
 if(phase){p->next=c->phase;c->phase=p;}else{p->next=c->owned;c->owned=p;}
 memset(p->bytes,0,bytes);return p->bytes;
}
static void release(struct pc_allocation **head)
{struct pc_allocation *p=*head,*next;while(p){next=p->next;free(p);p=next;}*head=0;}
unsigned pc_ready(pc_compiler *c)
{
 if(c->expression.status)pc_error(c,c->expression.status);
 if(c->output.status){c->report->output_status=c->output.status;pc_error(c,PC_OUTPUT_ERROR);}
 return !c->report->status;
}
unsigned pc_equal(pc_compiler *c,unsigned index,const char *name)
{
 const aspect_compiler_line *line=c->expression.line;unsigned char text[254];
 if(!line||index>=line->count)return 0;
 return aspect_compiler_token_copy(line,index,text,sizeof(text))>=0&&!strcmp((char *)text,name);
}
pc_proc *pc_procedure(pc_compiler *c,unsigned token)
{
 pc_proc *p;unsigned char name[254];
 if(aspect_compiler_token_copy(c->expression.line,token,name,sizeof(name))<0)return 0;
 for(p=c->procedures;p;p=p->next)if(!strcmp(p->source->name,(char *)name))return p;
 return 0;
}
unsigned long pc_jump(pc_compiler *c,unsigned opcode)
{unsigned long offset;aspect_compiler_emit_byte(&c->output,opcode);offset=c->output.position;aspect_compiler_emit_dword(&c->output,0);return offset;}
void pc_call_patch(pc_compiler *c,unsigned long offset,pc_proc *target)
{
 pc_call *p=pc_allocate(c,sizeof(*p),1);if(!p)return;p->target=target;p->offset=offset;p->next=c->calls;c->calls=p;
}
static void patch(pc_compiler *c,unsigned long offset,unsigned long target)
{aspect_compiler_patch_dword(&c->output,offset,target);}
static void exits(pc_compiler *c,pc_patch *list)
{for(;list;list=list->next)patch(c,list->offset,c->output.position);}
static void add_exit(pc_compiler *c,pc_block *b,unsigned long offset)
{pc_patch *p=pc_allocate(c,sizeof(*p),1);if(!p)return;p->offset=offset;p->next=b->exits;b->exits=p;}
static void emit(pc_compiler *c,unsigned v){aspect_compiler_emit_byte(&c->output,v);}
static void bad(pc_compiler *c){pc_error(c,ASPECT_COMPILE_SYNTAX);}
static unsigned load(pc_compiler *c,const aspect_compiler_source *source)
{
 aspect_compiler_reader reader;
 if(source->offset>LONG_MAX||fseek(c->input,(long)source->offset,SEEK_SET)){pc_error(c,ASPECT_COMPILE_LEXICAL);c->report->lexical_status=ASPECT_LEX_IO;return 0;}
 aspect_compiler_reader_init(&reader,c->input);reader.number=source->line;reader.offset=source->offset;
 if(aspect_compiler_next_line(&reader,&c->line)!=1){pc_error(c,ASPECT_COMPILE_LEXICAL);c->report->lexical_status=reader.status;return 0;}
 aspect_compiler_expression_init(&c->expression,&c->line,&c->unit,c->current?c->current->source:0,0,c->line.count);
 return 1;
}
static pc_block *block(pc_compiler *c,unsigned type)
{
 pc_block *p=pc_allocate(c,sizeof(*p),1);if(!p)return 0;
 p->type=type;p->parent=c->blocks;c->blocks=p;return p;
}
static unsigned expression(pc_compiler *c,unsigned first,unsigned last)
{
 unsigned root;c->expression.position=first;c->expression.last=last;
 root=aspect_compiler_parse_expression(&c->expression,1);
 if(c->expression.position!=last)bad(c);return root;
}
static unsigned long condition(pc_compiler *c)
{
 unsigned root;int kind;aspect_compiler_value value;unsigned long offset;
 root=expression(c,1,c->line.count);kind=aspect_compiler_expression_kind(&c->expression,root);
 if(!pc_ready(c))return 0;if(kind==3){bad(c);return 0;}
 aspect_compiler_emit_expression(&c->expression,&c->output,root,0,&value);
 if(value.tag!=ASPECT_EXPR_TEMPORARY){
  emit(c,0x5b);emit(c,kind);emit(c,0x79);emit(c,0);aspect_compiler_emit_operand(&c->expression,&c->output,&value,0);
 }
 offset=pc_jump(c,0x15);emit(c,0x79);emit(c,0);return offset;
}
static unsigned switch_operand(pc_compiler *c,aspect_compiler_value *value)
{
 unsigned root;int kind;
 if(c->line.count<2||pc_equal(c,1,"(")||pc_equal(c,1,",")){bad(c);return 65535U;}
 c->expression.position=1;root=aspect_compiler_parse_expression(&c->expression,7);
 if(c->expression.position!=c->line.count){bad(c);return 65535U;}
 kind=aspect_compiler_expression_kind(&c->expression,root);
 if(kind==3)aspect_compiler_atomic(&c->expression,root,value);else aspect_compiler_word_argument(&c->expression,root,value);
 return kind==3?3:0;
}
static void switch_statement(pc_compiler *c)
{
 pc_block *b=c->blocks;aspect_compiler_value value;unsigned kind;unsigned long shared=0;
 if(pc_equal(c,0,"switch")){
  kind=switch_operand(c,&value);if(!pc_ready(c))return;
  emit(c,0xb8);aspect_compiler_emit_operand(&c->expression,&c->output,&value,1);
  b=block(c,BLOCK_SWITCH);if(!b)return;b->kind=kind;b->branch=c->output.position;aspect_compiler_emit_dword(&c->output,0);return;
 }
 if(!b||b->type!=BLOCK_SWITCH){bad(c);return;}
 if(pc_equal(c,0,"case")||pc_equal(c,0,"default")){
  if(pc_equal(c,0,"default")&&(c->line.count!=1||b->has_default)){bad(c);return;}
  if(b->active&&pc_equal(c,0,"case"))shared=pc_jump(c,0x62);
  if(pc_equal(c,0,"case")){
   kind=switch_operand(c,&value);if(!pc_ready(c))return;if(kind!=b->kind){bad(c);return;}
   patch(c,b->has_next?b->next:b->branch,c->output.position);emit(c,0x0f);
   b->next=c->output.position;b->has_next=1;aspect_compiler_emit_dword(&c->output,0);
   aspect_compiler_emit_operand(&c->expression,&c->output,&value,1);if(shared)patch(c,shared,c->output.position);
  }else{b->has_default=1;b->default_at=c->output.position;}
  b->active=1;
 }else if(pc_equal(c,0,"endcase")){
  if(c->line.count!=1||!b->active){bad(c);return;}add_exit(c,b,pc_jump(c,0x62));b->active=0;
 }else{
  if(c->line.count!=1||b->active){bad(c);return;}
  patch(c,b->has_next?b->next:b->branch,b->has_default?b->default_at:c->output.position);
  exits(c,b->exits);c->blocks=b->parent;
 }
}
static void call(pc_compiler *c)
{
 unsigned args[ASPECT_COMPILER_TOKEN_MAX],count,i;pc_proc *callee;aspect_compiler_symbol *p;aspect_compiler_value value;
 callee=pc_procedure(c,1);
 if(!callee||(c->line.count>2&&!pc_equal(c,2,"with"))){bad(c);return;}
 pc_arguments(c,3,args,&count);if(!pc_ready(c))return;
 i=0;for(p=callee->source->parameters;p;p=p->parameter_next)++i;
 if(count!=i){bad(c);return;}emit(c,0xd0);
 for(i=0,p=callee->source->parameters;p;p=p->parameter_next,++i){
  if(aspect_compiler_expression_kind(&c->expression,args[i])!=(int)p->kind){bad(c);return;}
  emit(c,p->kind==3?0xcd:0xcc);aspect_compiler_atomic(&c->expression,args[i],&value);aspect_compiler_emit_operand(&c->expression,&c->output,&value,1);
 }
 pc_call_patch(c,pc_jump(c,callee->source->size||callee->source->parameters?0xc8:0xc7),callee);
 if(count){emit(c,0xd2);aspect_compiler_emit_word(&c->output,(unsigned)(0UL-callee->source->parameter_bytes));}
}
static void statement(pc_compiler *c)
{
 pc_block *b=c->blocks;unsigned i,dest,root,k;unsigned long start;
 if((pc_equal(c,0,"else")||pc_equal(c,0,"endif")||pc_equal(c,0,"endwhile")||pc_equal(c,0,"exitwhile")||pc_equal(c,0,"loopwhile"))&&c->line.count!=1){bad(c);return;}
 i=pc_equal(c,0,"case")||pc_equal(c,0,"default")||pc_equal(c,0,"endswitch");
 if(b&&b->type==BLOCK_SWITCH&&!b->active&&!i){bad(c);return;}
 if(i||pc_equal(c,0,"switch")||pc_equal(c,0,"endcase")){switch_statement(c);return;}
 if(pc_equal(c,0,"if")){
  start=condition(c);b=block(c,BLOCK_IF);if(b){b->branch=start;b->active=1;}
 }else if(pc_equal(c,0,"else")||pc_equal(c,0,"elseif")){
  if(!b||b->type!=BLOCK_IF||!b->active){bad(c);return;}
  add_exit(c,b,pc_jump(c,0x62));patch(c,b->branch,c->output.position);
  if(pc_equal(c,0,"elseif"))b->branch=condition(c);else b->active=0;
 }else if(pc_equal(c,0,"endif")){
  if(!b||b->type!=BLOCK_IF){bad(c);return;}if(b->active)patch(c,b->branch,c->output.position);exits(c,b->exits);c->blocks=b->parent;
 }else if(pc_equal(c,0,"while")){
  start=c->output.position;i=0;b=block(c,BLOCK_WHILE);if(b){b->start=start;b->branch=condition(c);}
 }else if(pc_equal(c,0,"exitwhile")||pc_equal(c,0,"loopwhile")){
  for(;b&&b->type!=BLOCK_WHILE;b=b->parent){}
  if(!b){bad(c);return;}start=pc_jump(c,0x62);
  if(pc_equal(c,0,"exitwhile"))add_exit(c,b,start);else patch(c,start,b->start);
 }else if(pc_equal(c,0,"endwhile")){
  if(!b||b->type!=BLOCK_WHILE){bad(c);return;}
  patch(c,pc_jump(c,0x62),b->start);patch(c,b->branch,c->output.position);exits(c,b->exits);c->blocks=b->parent;
 }else if(pc_equal(c,0,"call")||pc_equal(c,0,"gosub"))call(c);
 else if(c->line.count==2&&(pc_equal(c,0,"++")||pc_equal(c,0,"--")||pc_equal(c,1,"++")||pc_equal(c,1,"--"))){
  i=pc_equal(c,0,"++")||pc_equal(c,0,"--");k=pc_equal(c,i?0:1,"++");
  c->expression.position=i?1:0;c->expression.last=c->expression.position+1;
  root=aspect_compiler_parse_expression(&c->expression,7);
  if(aspect_compiler_expression_kind(&c->expression,root)==3){bad(c);return;}
  emit(c,k?0x5a:0x1e);aspect_compiler_emit_destination(&c->expression,&c->output,root,&dest);
 }else if(c->line.count>2&&(pc_equal(c,1,"=")||pc_equal(c,1,"+=")||pc_equal(c,1,"-=")||pc_equal(c,1,"*=")||pc_equal(c,1,"/=")||pc_equal(c,1,"%="))){
  dest=root=0;aspect_compiler_parse_assignment(&c->expression,&dest,&root);aspect_compiler_emit_assignment(&c->expression,&c->output,dest,root,0);
 }else pc_commands(c);
}
static unsigned graph(pc_compiler *c)
{
 aspect_compiler_procedure *p;aspect_compiler_source *s;pc_proc *info,*target;pc_edge *edge;unsigned i,changed;
 for(p=c->unit.procedures;p;p=p->next){
  info=pc_allocate(c,sizeof(*info),0);if(!info)return 0;info->source=p;info->selected=1;
  if(c->tail)c->tail->next=info;else c->procedures=info;c->tail=info;++c->report->procedures;
 }
 for(info=c->procedures;info;info=info->next){
  c->current=info;
  for(s=info->source->body;s;s=s->next){
   if(!load(c,s))return 0;
   if(pc_equal(c,0,"call")||pc_equal(c,0,"gosub")){
    target=pc_procedure(c,1);if(target){edge=pc_allocate(c,sizeof(*edge),0);if(!edge)return 0;edge->target=target;edge->next=info->calls;info->calls=edge;}
   }else if(pc_equal(c,0,"when"))for(i=1;i+1<c->line.count;++i)if(pc_equal(c,i,"call")){
    target=pc_procedure(c,i+1);if(target){edge=pc_allocate(c,sizeof(*edge),0);if(!edge)return 0;edge->target=target;edge->next=info->calls;info->calls=edge;}
   }
  }
 }
 do{
  changed=0;for(info=c->procedures;info;info=info->next)info->referenced=0;
  for(info=c->procedures;info;info=info->next)if(info->selected)for(edge=info->calls;edge;edge=edge->next)edge->target->referenced=1;
  for(info=c->procedures;info;info=info->next)if(info->selected&&!info->referenced&&strcmp(info->source->name,"main")){info->selected=0;changed=1;}
 }while(changed);
 for(info=c->procedures;info;info=info->next)if(info->selected)++c->report->emitted_procedures;
 return 1;
}
static unsigned declarations(pc_compiler *c,aspect_compiler_source *s)
{
 unsigned i;int depth;
 for(;s;s=s->next){
  if(!load(c,s))return 0;depth=0;
  for(i=0;i<c->line.count;++i){
   if(pc_equal(c,i,"("))++depth;else if(pc_equal(c,i,")"))--depth;
   if(depth<0){bad(c);return 0;}
  }
  if(depth){bad(c);return 0;}
 }
 return 1;
}
static void procedures(pc_compiler *c,unsigned all)
{
 pc_proc *p,*main;pc_call *fixup;aspect_compiler_source *s;unsigned dest,root;
 emit(c,c->unit.counts[3]);
 if(strcmp(c->procedures->source->name,"main")){
  for(main=c->procedures;main&&strcmp(main->source->name,"main");main=main->next){}
  pc_call_patch(c,pc_jump(c,0x62),main);
 }
 for(p=c->procedures;p&&pc_ready(c);p=p->next){
  if(!all&&!p->selected)continue;c->current=p;p->address=c->output.position;c->blocks=0;
  if(p->source->size){emit(c,0xd2);aspect_compiler_emit_word(&c->output,p->source->size);}
  for(s=p->source->initializers;s&&pc_ready(c);s=s->next){
   if(!load(c,s))return;
   c->expression.first=c->expression.position=s->first-2;c->expression.last=s->last;
   dest=root=0;aspect_compiler_parse_assignment(&c->expression,&dest,&root);aspect_compiler_emit_assignment(&c->expression,&c->output,dest,root,s->chained);
  }
  emit(c,0xcf);
  for(s=p->source->body;s&&pc_ready(c);s=s->next){if(!load(c,s))return;statement(c);}
  if(c->blocks){bad(c);return;}emit(c,p->source->size||p->source->parameters?0x95:0x94);
 }
 for(fixup=c->calls;fixup&&pc_ready(c);fixup=fixup->next)patch(c,fixup->offset,fixup->target->address);
}
unsigned aspect_compiler_program_options(FILE *input,FILE *output,aspect_compiler_report *report,const aspect_compiler_options *options)
{
 pc_compiler *c;aspect_compiler_procedure *p;unsigned status;
 if(!report)return ASPECT_COMPILE_STATE;memset(report,0,sizeof(*report));report->line=1;
 if(!input||!output||input==output||ftell(input)!=0||ftell(output)!=0){report->status=ASPECT_COMPILE_STATE;return report->status;}
 report->allocation_calls=1;
 c=options&&!options->fail_after?0:malloc(sizeof(*c));if(!c){report->status=ASPECT_COMPILE_HEAP;return report->status;}
 memset(c,0,sizeof(*c));c->input=input;c->report=report;c->line.number=1;
 c->fail_after=options?options->fail_after:ULONG_MAX;
 aspect_compiler_unit_init(&c->unit);aspect_compiler_output_init(&c->output,output);
 if(options)c->unit.fail_after=options->unit_fail_after;
 status=aspect_compiler_unit_load(&c->unit,input);
 if(status){report->status=status;report->lexical_status=c->unit.lexical_status;report->line=c->unit.error_line;report->offset=c->unit.error_offset;}
 else{
  declarations(c,c->unit.declarations);
  for(p=c->unit.procedures;p&&!report->status;p=p->next)declarations(c,p->declarations);
 }
 if(!report->status&&(fflush(output)||chsize(fileno(output),0)||fseek(output,0L,SEEK_SET))){c->output.status=ASPECT_OUTPUT_IO;pc_ready(c);}
 if(!report->status&&graph(c)){
  procedures(c,1);
  if(pc_ready(c)&&report->procedures!=report->emitted_procedures){
   aspect_compiler_output_flush(&c->output);pc_ready(c);
   if(!report->status&&(chsize(fileno(output),0)||fseek(output,0L,SEEK_SET)))pc_error(c,PC_OUTPUT_ERROR);
   release(&c->phase);c->calls=0;c->blocks=0;
   if(!report->status){aspect_compiler_output_init(&c->output,output);procedures(c,0);}
  }
 }
 aspect_compiler_output_flush(&c->output);pc_ready(c);report->bytes=c->output.position;
 report->unit_allocation_calls=c->unit.allocation_calls;
 release(&c->phase);release(&c->owned);aspect_compiler_unit_dispose(&c->unit);free(c);return report->status;
}
unsigned aspect_compiler_program(FILE *input,FILE *output,aspect_compiler_report *report)
{return aspect_compiler_program_options(input,output,report,0);}
