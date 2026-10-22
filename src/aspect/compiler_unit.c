/* First pass of the DOS compiler: source/symbol ownership and procedure layout.
 * Subsequent passes must validate all bodies, including discarded procedures. */
#include "compiler_unit.h"
#include <stdlib.h>
#include <stddef.h>
#include <limits.h>
#include <string.h>
struct aspect_compiler_allocation {
 struct aspect_compiler_allocation *next;
 unsigned long alignment;
 unsigned used,capacity;
 unsigned char payload[1];
};
static const unsigned sizes[4]={2,4,8,81};
static void *allocate(aspect_compiler_unit *u,unsigned bytes)
{
 struct aspect_compiler_allocation *block;
 unsigned alignment=(unsigned)sizeof(void *),rounded,capacity;
 unsigned char *result;
 unsigned long call=u->allocation_calls++;
 /* Keep allocation-failure ceilings and metrics per logical object. Small
  * source/symbol objects share bounded arenas instead of a CRT block each. */
 if(call>=u->fail_after || bytes>UINT_MAX-(alignment-1U))return 0;
 rounded=(bytes+alignment-1U)&~(alignment-1U);
 block=u->allocations;
 if(!block || rounded>block->capacity-block->used){
  capacity=rounded>512U?rounded:512U;
  if(capacity>UINT_MAX-(unsigned)offsetof(struct aspect_compiler_allocation,payload))return 0;
  block=malloc(offsetof(struct aspect_compiler_allocation,payload)+capacity);if(!block)return 0;
  block->next=u->allocations;block->used=0;block->capacity=capacity;u->allocations=block;
 }
 result=block->payload+block->used;block->used+=rounded;
 ++u->live_allocations;if(u->live_allocations>u->peak_allocations)u->peak_allocations=u->live_allocations;
 memset(result,0,bytes);return result;
}
void aspect_compiler_unit_init(aspect_compiler_unit *u)
{memset(u,0,sizeof(*u));u->fail_after=0xffffffffUL;}
void aspect_compiler_unit_dispose(aspect_compiler_unit *u)
{
 struct aspect_compiler_allocation *block,*next;
 if(!u)return;
 for(block=u->allocations;block;block=next){next=block->next;free(block);}
 u->allocations=0;u->live_allocations=0;
 u->declarations=u->declarations_tail=0;
 u->globals=u->globals_tail=0;u->procedures=u->procedures_tail=0;
 memset(u->counts,0,sizeof(u->counts));u->loaded=0;
}
static unsigned fail(aspect_compiler_unit *u,unsigned status,const aspect_compiler_line *line)
{
 u->status=status;u->error_line=line->number;u->error_offset=line->offset;
 return status;
}
static int equal(const aspect_compiler_line *line,unsigned index,const char *text)
{
 unsigned char token[254];
 return aspect_compiler_token_copy(line,index,token,sizeof(token))>=0 && !strcmp((char *)token,text);
}
static int type(const aspect_compiler_line *line,unsigned *parameter)
{
 static const char *names[8]={"integer","long","float","string","intparm","longparm","floatparm","strparm"};
 unsigned i;
 for(i=0;i<8;++i)if(equal(line,0,names[i])){*parameter=i>=4;return i&3;}
 return -1;
}
static unsigned reserved(const char *name)
{
 static const char *names[]={"text","comdata","failure","forever","found","success","waitfor",
 "$d_entry","$d_ldate","$d_kbdfile","$d_metakey","$d_name","$d_note","$d_phone","$d_pword","$d_script","$null","$d_baud","$fattr","$fdate","$fext","$filename","$fname","$ftime","$fsize"};
 unsigned i;for(i=0;i<sizeof(names)/sizeof(names[0]);++i)if(!strcmp(name,names[i]))return 1;
 return 0;
}
static unsigned duplicate(aspect_compiler_symbol *symbol,const char *name)
{for(;symbol;symbol=symbol->next)if(!strcmp(symbol->name,name))return 1;return 0;}
static aspect_compiler_source *source(aspect_compiler_unit *u,const aspect_compiler_line *line,
                                     aspect_compiler_source **head,aspect_compiler_source **tail)
{
 aspect_compiler_source *s=allocate(u,sizeof(*s));
 if(!s)return 0;s->line=line->number;s->offset=line->offset;
 if(*tail)(*tail)->next=s;else *head=s;*tail=s;return s;
}
static aspect_compiler_initializer *initializer(aspect_compiler_unit *u,
 const aspect_compiler_line *line,aspect_compiler_procedure *p)
{
 aspect_compiler_initializer *s=allocate(u,sizeof(*s));
 if(!s)return 0;s->line=line->number;s->offset=line->offset;
 if(p->initializers_tail)p->initializers_tail->next=s;else p->initializers=s;
 p->initializers_tail=s;return s;
}
static unsigned declaration(aspect_compiler_unit *u,aspect_compiler_procedure *p,
                            const aspect_compiler_line *line,unsigned kind,unsigned parameter)
{
 unsigned start=1,end,parts=0,i,part=0;int depth=0;
 unsigned char name[254];aspect_compiler_symbol *symbol;aspect_compiler_initializer *init;
 if(parameter && !p)return fail(u,ASPECT_COMPILE_SYNTAX,line);
 /* Count separators exactly like the host, including empty final parts. */
 for(i=1;i<=line->count;++i){
  if((i==line->count || equal(line,i,",")) && !depth){++parts;continue;}
  if(equal(line,i,"("))++depth;
  if(equal(line,i,")"))--depth;
 }
 depth=0;
 for(end=1;end<=line->count;++end){
  if(end==line->count && depth)break;
  if(end<line->count && !(equal(line,end,",") && !depth)){
   if(equal(line,end,"("))++depth;
   if(equal(line,end,")"))--depth;
   continue;
  }
  if(start==end || line->tokens[start].kind!=ASPECT_TOKEN_IDENTIFIER ||
     aspect_compiler_token_copy(line,start,name,sizeof(name))<0 || reserved((char *)name) ||
     duplicate(p?p->symbols:u->globals,(char *)name))return fail(u,ASPECT_COMPILE_SYNTAX,line);
  if((!p || parameter) && end-start!=1)return fail(u,ASPECT_COMPILE_SYNTAX,line);
  if(!p && u->counts[kind]>=128)return fail(u,ASPECT_COMPILE_SYNTAX,line);
  if(p && !parameter && p->locals>=128)return fail(u,ASPECT_COMPILE_SYNTAX,line);
  symbol=allocate(u,(unsigned)(sizeof(*symbol)+strlen((char *)name)));
  if(!symbol)return fail(u,ASPECT_COMPILE_HEAP,line);
  strcpy(symbol->name,(char *)name);symbol->kind=kind;
  if(!p){
   symbol->space=ASPECT_SYMBOL_GLOBAL;symbol->index=u->counts[kind]++;
   if(u->globals_tail)u->globals_tail->next=symbol;else u->globals=symbol;u->globals_tail=symbol;
  }else{
   if(p->symbols_tail)p->symbols_tail->next=symbol;else p->symbols=symbol;p->symbols_tail=symbol;
   if(parameter){
    symbol->space=ASPECT_SYMBOL_PARAMETER;
    if(p->parameters_tail)p->parameters_tail->parameter_next=symbol;else p->parameters=symbol;
    p->parameters_tail=symbol;p->parameter_bytes+=sizes[kind];
   }else{
    symbol->space=ASPECT_SYMBOL_LOCAL;symbol->index=p->size;p->size+=sizes[kind];++p->locals;
    if(end-start>1){
     if(!equal(line,start+1,"="))return fail(u,ASPECT_COMPILE_SYNTAX,line);
     init=initializer(u,line,p);
     if(!init)return fail(u,ASPECT_COMPILE_HEAP,line);
     init->first=start+2;init->last=end;init->destination=symbol;
     init->chained=kind!=3 && part+1<parts;
    }
   }
  }
  ++part;start=end+1;
 }
 return 0;
}
unsigned aspect_compiler_unit_load(aspect_compiler_unit *u,FILE *file)
{
 aspect_compiler_reader reader;aspect_compiler_line line;
 aspect_compiler_procedure *current=0,*p;aspect_compiler_symbol *symbol;
 unsigned parameter;unsigned long offset,last_line=1,last_offset=0;int kind,status,main_found=0;
 unsigned char name[254];
 if(!u||!file)return ASPECT_COMPILE_STATE;
 if(u->allocations || u->loaded || u->status)return ASPECT_COMPILE_STATE;
 aspect_compiler_reader_init(&reader,file);
 memset(&line,0,sizeof(line));line.number=1;
 while((status=aspect_compiler_next_line(&reader,&line))>0){
  last_line=line.number;last_offset=line.offset;
  if(!line.count)continue;
  if(equal(&line,0,"proc")){
   if(current || line.count!=2 || line.tokens[1].kind!=ASPECT_TOKEN_IDENTIFIER){fail(u,ASPECT_COMPILE_SYNTAX,&line);break;}
   aspect_compiler_token_copy(&line,1,name,sizeof(name));
   for(p=u->procedures;p;p=p->next)if(!strcmp(p->name,(char *)name))break;
   if(p){fail(u,ASPECT_COMPILE_SYNTAX,&line);break;}
   p=allocate(u,(unsigned)(sizeof(*p)+strlen((char *)name)));
   if(!p){fail(u,ASPECT_COMPILE_HEAP,&line);break;}
   strcpy(p->name,(char *)name);p->line=line.number;p->offset=line.offset;
   if(u->procedures_tail)u->procedures_tail->next=p;else u->procedures=p;u->procedures_tail=p;
   current=p;if(!strcmp(p->name,"main"))main_found=1;
  }else if(equal(&line,0,"endproc")){
   if(!current || line.count!=1){fail(u,ASPECT_COMPILE_SYNTAX,&line);break;}
   current=0;
  }else if((kind=type(&line,&parameter))>=0){
   /* Retain every declaration line for the validation pass, even a malformed
    * trailing part that the host's inventory pass does not materialize. */
   if(!source(u,&line,current?&current->declarations:&u->declarations,
                         current?&current->declarations_tail:&u->declarations_tail)){
    fail(u,ASPECT_COMPILE_HEAP,&line);break;
   }
   if(declaration(u,current,&line,(unsigned)kind,parameter))break;
  }else if(!current){fail(u,ASPECT_COMPILE_SYNTAX,&line);break;}
  else if(!source(u,&line,&current->body,&current->body_tail)){fail(u,ASPECT_COMPILE_HEAP,&line);break;}
 }
 if(status<0 && !u->status){
  u->status=ASPECT_COMPILE_LEXICAL;u->lexical_status=reader.status;
  u->error_line=reader.error_line;u->error_offset=reader.error_offset;
 }
 if(!u->status && (current || !main_found)){line.number=last_line;line.offset=last_offset;fail(u,ASPECT_COMPILE_SYNTAX,&line);}
 if(u->status){aspect_compiler_unit_dispose(u);return u->status;}
 for(p=u->procedures;p;p=p->next){
  offset=p->parameter_bytes+6UL;
  for(symbol=p->parameters;symbol;symbol=symbol->parameter_next){symbol->index=(unsigned)offset;offset-=sizes[symbol->kind];}
 }
 u->loaded=1;return 0;
}
