#include "compiler_program_internal.h"
#include <string.h>
typedef struct command {const char *name,*roles;unsigned opcode,optional;} command;
static const command commands[]={
 {"comgetc","i",0xc9,0},{"comgetcd","i",0xca,0},{"message","s",0x76,0},
 {"exit","",0x33,0},{"break","",0x0d,0},{"transmit","s",0xbf,0},
 {"waitfor","s",0xd4,1},{"rstrcmp","ss",0x9a,1},{"atoi","si",6,0},
 {"atol","sl",7,0},{"itoa","wd",0x61,0},{"ltoa","qd",0x6e,0},
 {"strcat","ds",0xaa,1},{"strcmp","ss",0xab,1},{"strcpy","ds",0xac,1},
 {"strlen","si",0xae,0},{"strlwr","d",0xaf,0},{"strpeek","sni",0xb0,0},
 {"strpoke","dnn",0xb1,0},{"strset","dn",0xb2,1},{"strupdt","dsnn",0xb3,0},
 {"strupr","d",0xb4,0},{"substr","dsnn",0xb6,0},{"pause","v",0x88,0}
};
typedef struct setting {const char *name;unsigned selector,integer;} setting;
static const setting settings[]={
 {"display",0x12,0},{"findcase",0x23,0},{"switchcase",0x44,0},
 {"waitcase",0x55,0},{"whencase",0x56,0},{"keys",0x29,0},
 {"rxdata",0x3b,0},{"msg_crlf",0x2e,0},{"duplex",0x18,0},
 {"pausechar",0x30,1},{"txpace",0x4c,1},{"break",9,1}
};
static void bad(pc_compiler *c){pc_error(c,ASPECT_COMPILE_SYNTAX);}
static unsigned parse(pc_compiler *c){return aspect_compiler_parse_expression(&c->expression,7);}
static int kind(pc_compiler *c,unsigned n){return aspect_compiler_expression_kind(&c->expression,n);}
static void emit(pc_compiler *c,unsigned v){aspect_compiler_emit_byte(&c->output,v);}
static unsigned symbol(pc_compiler *c,unsigned n,const char *name)
{return n&&c->expression.nodes[n-1].value.tag==ASPECT_EXPR_SYMBOL&&pc_equal(c,c->expression.nodes[n-1].value.index,name);}
static void operand(pc_compiler *c,unsigned n,unsigned word)
{
 aspect_compiler_value value;
 if(word)aspect_compiler_word_argument(&c->expression,n,&value);
 else aspect_compiler_atomic(&c->expression,n,&value);
 aspect_compiler_emit_operand(&c->expression,&c->output,&value,1);
}
static void destination(pc_compiler *c,unsigned n,unsigned expected)
{
 unsigned k;
 if(kind(c,n)!=(int)expected){bad(c);return;}
 aspect_compiler_emit_destination(&c->expression,&c->output,n,&k);
}
void pc_filter(pc_compiler *c,unsigned first)
{
 unsigned i,n=0;c->filtered=c->line;
 for(i=first;i<c->line.count;++i)if(!pc_equal(c,i,","))c->filtered.tokens[n++]=c->line.tokens[i];
 c->filtered.count=n;
 aspect_compiler_expression_init(&c->expression,&c->filtered,&c->unit,c->current->source,0,n);
}
void pc_arguments(pc_compiler *c,unsigned first,unsigned *args,unsigned *count)
{
 *count=0;pc_filter(c,first);
 while(pc_ready(c)&&c->expression.position<c->expression.last)args[(*count)++]=parse(c);
}
static void set_fetch(pc_compiler *c,unsigned fetch)
{
 unsigned i,first,n,which=65535U;
 for(i=0;i<sizeof(settings)/sizeof(settings[0]);++i)if(pc_equal(c,1,settings[i].name)){which=i;break;}
 if(c->line.count<3||which==65535U){bad(c);return;}
 if(!fetch&&!settings[which].integer){
  const char *off=which==8?"full":"off",*on=which==8?"half":"on";
  if(c->line.count!=3||(!pc_equal(c,2,off)&&!pc_equal(c,2,on))){bad(c);return;}
  emit(c,0x9e);emit(c,settings[which].selector);emit(c,pc_equal(c,2,on));return;
 }
 first=pc_equal(c,2,",")?3:2;
 if(first==c->line.count||pc_equal(c,first,"(")){bad(c);return;}
 c->expression.position=first;n=parse(c);
 if(c->expression.position!=c->line.count){bad(c);return;}
 emit(c,fetch?0x37:0x9e);emit(c,settings[which].selector);
 if(fetch)destination(c,n,0);else operand(c,n,1);
}
static void find(pc_compiler *c)
{
 unsigned i,n;emit(c,0x3b);c->expression.position=1;
 for(i=0;i<2;++i){
  if(i&&pc_equal(c,c->expression.position,","))++c->expression.position;
  if(c->expression.position==c->expression.last||pc_equal(c,c->expression.position,"(")||pc_equal(c,c->expression.position,",")){bad(c);return;}
  n=parse(c);if(kind(c,n)!=3){bad(c);return;}operand(c,n,0);
 }
 i=c->expression.position<c->expression.last;emit(c,i);
 if(i){
  if(pc_equal(c,c->expression.position,","))++c->expression.position;
  if(c->expression.position==c->expression.last||pc_equal(c,c->expression.position,"(")||pc_equal(c,c->expression.position,",")){bad(c);return;}
  n=parse(c);destination(c,n,0);
 }
 if(c->expression.position!=c->expression.last)bad(c);
}
static void path_command(pc_compiler *c,unsigned opcode)
{
 unsigned n;c->expression.position=1;
 if(c->line.count<2||pc_equal(c,1,"(")||pc_equal(c,1,",")){bad(c);return;}
 n=parse(c);if(c->expression.position!=c->expression.last||kind(c,n)!=3){bad(c);return;}
 emit(c,opcode);operand(c,n,0);
}
static void execute(pc_compiler *c)
{
 unsigned n;c->expression.position=1;
 if(c->line.count<2||pc_equal(c,1,"(")||pc_equal(c,1,",")){bad(c);return;}
 n=parse(c);if(c->expression.position!=c->expression.last||kind(c,n)!=3){bad(c);return;}
 emit(c,0xcb);operand(c,n,0);
}
static void when(pc_compiler *c,unsigned clear)
{
 unsigned disconnected,n;pc_proc *callee;
 if(c->line.count<2||pc_equal(c,1,",")){bad(c);return;}
 pc_filter(c,1);disconnected=pc_equal(c,0,"disconnect");emit(c,clear?0x1c:0xd6);emit(c,!disconnected);
 if(disconnected)c->expression.position=1;
 else{
  if(pc_equal(c,0,"(")){bad(c);return;}n=parse(c);operand(c,n,1);
 }
 if(clear){if(c->expression.position!=c->expression.last)bad(c);return;}
 if(!disconnected){n=parse(c);if(kind(c,n)!=3){bad(c);return;}operand(c,n,0);}
 n=c->expression.position++;
 if(pc_equal(c,n,"transmit")){
  n=parse(c);if(kind(c,n)!=3){bad(c);return;}emit(c,0x32);operand(c,n,0);
 }else if(pc_equal(c,n,"call")){
  callee=pc_procedure(c,c->expression.position++);
  if(!callee||callee->source->parameters){bad(c);return;}
  emit(c,7);pc_call_patch(c,pc_jump(c,callee->source->size?0xc8:0xc7),callee);
 }else{bad(c);return;}
 if(c->expression.position!=c->expression.last)bad(c);
}
void pc_commands(pc_compiler *c)
{
 unsigned args[ASPECT_COMPILER_TOKEN_MAX],count,i,j,n,dest,expected,optional,command_index=65535U;
 char role;aspect_compiler_value value;const command *cmd;
 if(pc_equal(c,0,"chdir")){path_command(c,0x11);return;}
 if(pc_equal(c,0,"mkdir")){path_command(c,0x79);return;}
 if(pc_equal(c,0,"rmdir")){path_command(c,0x99);return;}
 if(pc_equal(c,0,"delete")){path_command(c,0x20);return;}
 if(pc_equal(c,0,"break")&&c->line.count!=1){bad(c);return;}
 if(pc_equal(c,0,"set")||pc_equal(c,0,"fetch")){set_fetch(c,pc_equal(c,0,"fetch"));return;}
 if(pc_equal(c,0,"find")){find(c);return;}
 if(pc_equal(c,0,"execute")){execute(c);return;}
 if(pc_equal(c,0,"when")||pc_equal(c,0,"cwhen")){when(c,pc_equal(c,0,"cwhen"));return;}
 dest=pc_equal(c,0,"rget");optional=pc_equal(c,0,"waitquiet");
 for(i=0;i<sizeof(commands)/sizeof(commands[0]);++i)if(pc_equal(c,0,commands[i].name)){command_index=i;break;}
 pc_arguments(c,1,args,&count);if(!pc_ready(c))return;
 if(dest||optional){
  if(count<dest||count>dest+2){bad(c);return;}emit(c,dest?0xce:0xd5);
  if(dest)destination(c,args[0],3);
  for(i=dest;i<dest+2;++i){
   if(i>=count){emit(c,0);break;}emit(c,1);
   if(optional&&i==1&&symbol(c,args[i],"forever"))emit(c,0x1a);else operand(c,args[i],1);
  }return;
 }
 if(command_index==65535U){bad(c);return;}cmd=&commands[command_index];n=strlen(cmd->roles);
 if(count<n||count>n+cmd->optional){bad(c);return;}emit(c,cmd->opcode);
 for(i=0;i<n&&pc_ready(c);++i){
  role=cmd->roles[i];j=args[i];expected=(unsigned)kind(c,j);
  if((role=='d'||role=='s')&&expected!=3){bad(c);return;}
  if(role=='d')destination(c,j,3);
  else if(role=='i'||role=='l')destination(c,j,role=='i'?0:1);
  else{
   if(strchr("nvwq",role)&&expected==3){bad(c);return;}
   if(role=='v')aspect_compiler_word_argument(&c->expression,j,&value);else aspect_compiler_atomic(&c->expression,j,&value);
   if(role=='w'||role=='q'){
    dest=role=='w'?0:1;
    if(value.tag==ASPECT_EXPR_CONSTANT&&value.kind!=2)value.kind=dest;
    else if(expected!=dest){bad(c);return;}
   }
   aspect_compiler_emit_operand(&c->expression,&c->output,&value,1);
  }
 }
 if(cmd->optional){
  emit(c,count>n);
  if(count>n){
   if(cmd->opcode==0xd4&&symbol(c,args[n],"forever"))emit(c,0x1a);
   else{if(kind(c,args[n])==3){bad(c);return;}operand(c,args[n],cmd->opcode==0xd4);}
  }
 }
}
