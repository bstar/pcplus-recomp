#include "compiler_lexer.h"
#include "compiler_lex_dump.h"
static void byte(FILE *f,unsigned value){fputc(value&255,f);}
static void word(FILE *f,unsigned value){byte(f,value);byte(f,value>>8);}
static void dword(FILE *f,unsigned long value)
{word(f,(unsigned)value);word(f,(unsigned)(value>>16));}
int aspect_compiler_lex_dump(FILE *input,FILE *output)
{
 aspect_compiler_reader reader;aspect_compiler_line line;
 unsigned i;int status;unsigned char text[ASPECT_COMPILER_LINE_MAX+1];
 if(!input||!output)return 1;
 if(aspect_compiler_reader_init(&reader,input))return 1;
 if(fwrite("ALX1",1,4,output)!=4)return 2;
 while((status=aspect_compiler_next_line(&reader,&line))>0){
  byte(output,1);dword(output,line.number);dword(output,line.offset);
  word(output,line.length);word(output,line.count);
  if(fwrite(line.bytes,1,line.length,output)!=line.length)return 2;
  for(i=0;i<line.count;++i){
   aspect_compiler_token token=line.tokens[i];
   if(aspect_compiler_token_copy(&line,i,text,sizeof(text))<0)return 2;
   byte(output,token.kind);word(output,token.start);word(output,token.length);
   if(fwrite(text,1,token.length,output)!=token.length)return 2;
  }
  if(ferror(output))return 2;
 }
 if(status<0){
  byte(output,255);byte(output,reader.status);
  dword(output,reader.error_line);dword(output,reader.error_offset);
  word(output,reader.error_column);
 }else{byte(output,0);dword(output,reader.number);dword(output,reader.offset);}
 if(fflush(output) || ferror(output))return 2;
 return status<0?1:0;
}
