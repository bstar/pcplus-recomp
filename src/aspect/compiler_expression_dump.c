#include "compiler_expression_dump.h"
#include "compiler_emit.h"
#include <stdlib.h>
#include <string.h>
static void byte(FILE *f,unsigned v){fputc(v&255,f);}
static void word(FILE *f,unsigned v){byte(f,v);byte(f,v>>8);}
static void dword(FILE *f,unsigned long v){word(f,(unsigned)v);word(f,(unsigned)(v>>16));}
int aspect_compiler_expression_dump(FILE *input,FILE *output,unsigned long target,unsigned first,unsigned last,
 unsigned mode,unsigned long prefix,unsigned slot,unsigned compact)
{
 aspect_compiler_unit unit;aspect_compiler_reader reader;aspect_compiler_line line;
 aspect_compiler_procedure *proc=0,*p;aspect_compiler_expression *expr=0;
 aspect_compiler_output writer;aspect_compiler_value value;
 FILE *scratch=0;unsigned status=0,out_status=0,cursor=first,count=0,kind=65535,root=0,dest=0;
 unsigned char buffer[512];unsigned n;unsigned long size=0,i;int read_status;
 memset(&writer,0,sizeof(writer));aspect_compiler_unit_init(&unit);
 if(!input||!output)return 1;
 status=aspect_compiler_unit_load(&unit,input);if(status)goto done;
 if(fseek(input,0L,SEEK_SET)){out_status=ASPECT_OUTPUT_IO;goto done;}
 aspect_compiler_reader_init(&reader,input);
 while((read_status=aspect_compiler_next_line(&reader,&line))>0){
  if(line.count && line.tokens[0].kind==ASPECT_TOKEN_IDENTIFIER){
   for(p=unit.procedures;p;p=p->next)if(p->line==line.number){proc=p;break;}
   if(line.tokens[0].length==7){
    unsigned char name[254];aspect_compiler_token_copy(&line,0,name,sizeof(name));if(!strcmp((char *)name,"endproc"))proc=0;
   }
  }
  if(line.number==target)break;
 }
 if(read_status<=0){status=read_status<0?ASPECT_COMPILE_LEXICAL:ASPECT_COMPILE_SYNTAX;goto done;}
 if(last==65535U)last=line.count;
 expr=malloc(sizeof(*expr));if(!expr){status=ASPECT_COMPILE_HEAP;goto done;}
 aspect_compiler_expression_init(expr,&line,&unit,proc,first,last);
 if(mode>ASPECT_DIAG_CHAINED_ASSIGNMENT){status=ASPECT_COMPILE_STATE;goto done;}
 if(mode>=ASPECT_DIAG_ASSIGNMENT)aspect_compiler_parse_assignment(expr,&dest,&root);
 else{root=aspect_compiler_parse_expression(expr,1);if(expr->position!=last)aspect_compiler_expression_error(expr,ASPECT_COMPILE_SYNTAX);}
 if(expr->status)goto parsed;
 scratch=tmpfile();if(!scratch){out_status=ASPECT_OUTPUT_IO;goto parsed;}
 aspect_compiler_output_init(&writer,scratch);
 if(prefix>ASPECT_OUTPUT_MAX)writer.status=ASPECT_OUTPUT_RANGE;
 for(i=0;i<prefix&&!writer.status;++i)aspect_compiler_emit_byte(&writer,0);
 if(mode==ASPECT_DIAG_EXPRESSION){
  aspect_compiler_emit_expression(expr,&writer,root,slot,&value);aspect_compiler_emit_operand(expr,&writer,&value,compact);
  if(!expr->status)kind=(unsigned)aspect_compiler_expression_kind(expr,root);
 }else if(mode==ASPECT_DIAG_ATOMIC){
  if(!aspect_compiler_atomic(expr,root,&value)){aspect_compiler_emit_operand(expr,&writer,&value,compact);if(!expr->status)kind=(unsigned)aspect_compiler_expression_kind(expr,root);}
 }else if(mode==ASPECT_DIAG_WORD){
  if(!aspect_compiler_word_argument(expr,root,&value)){aspect_compiler_emit_operand(expr,&writer,&value,compact);if(!expr->status)kind=0;}
 }else{
  aspect_compiler_emit_assignment(expr,&writer,dest,root,mode==ASPECT_DIAG_CHAINED_ASSIGNMENT);
  if(!expr->status)kind=(unsigned)aspect_compiler_expression_kind(expr,dest);
 }
 aspect_compiler_output_flush(&writer);out_status=writer.status;
parsed:
 status=expr->status;cursor=expr->position;count=expr->count;
done:
 if(scratch&&!status&&!out_status){size=writer.position-prefix;if(fseek(scratch,(long)prefix,SEEK_SET)){out_status=ASPECT_OUTPUT_IO;size=0;}}
 if(status||out_status)kind=65535;
 fwrite("AEX1",1,4,output);byte(output,status);byte(output,out_status);word(output,cursor);word(output,count);word(output,kind);dword(output,size);
 while(size){n=size>sizeof(buffer)?sizeof(buffer):(unsigned)size;if(fread(buffer,1,n,scratch)!=n||fwrite(buffer,1,n,output)!=n){out_status=ASPECT_OUTPUT_IO;break;}size-=n;}
 if(scratch&&fclose(scratch))out_status=ASPECT_OUTPUT_IO;
 if(expr)free(expr);aspect_compiler_unit_dispose(&unit);
 if(fflush(output)||ferror(output))return 2;
 return status||out_status?1:0;
}
