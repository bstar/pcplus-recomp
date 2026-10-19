/* Streaming DOS frontend for the maintained ASPECT compiler. Grammar and ASX
 * emission are separate phases; this is not a claim of a finished compiler. */
#include "compiler_lexer.h"
#include <limits.h>
#include <string.h>
static unsigned digit(unsigned char c){return c>='0' && c<='9';}
static unsigned hex(unsigned char c)
{return digit(c)||(c>='a'&&c<='f')||(c>='A'&&c<='F');}
static unsigned first(unsigned char c)
{return (c>='a'&&c<='z')||(c>='A'&&c<='Z')||c=='_'||c=='$';}
static unsigned continuation(unsigned char c){return first(c)||digit(c);}
static unsigned boundary(unsigned char c)
{return c==10||c==11||c==12||c==13||c==28||c==29||c==30;}
static unsigned space(unsigned char c)
{return c==9||c==32||c==31||c==255;}
static unsigned single(unsigned char c)
{return c && strchr("(),=+*/%<>-",c)!=0;}
static unsigned pair(unsigned char a,unsigned char b)
{
 return (a=='+'&&b=='+')||(a=='-'&&b=='-')||(a=='&'&&b=='&')||
        (a=='|'&&b=='|')||((a=='='||a=='!'||a=='<'||a=='>')&&b=='=')||
        ((a=='+'||a=='-'||a=='*'||a=='/'||a=='%')&&b=='=');
}
static int fail(aspect_compiler_reader *r,unsigned status,unsigned column,
                unsigned long offset)
{
 r->status=status;r->error_line=r->number;
 r->error_column=column;r->error_offset=offset;return -1;
}
unsigned aspect_compiler_reader_init(aspect_compiler_reader *r,FILE *file)
{
 if(!r||!file)return ASPECT_LEX_ARGUMENT;
 memset(r,0,sizeof(*r));r->file=file;r->number=1;r->pending=EOF;
 return ASPECT_LEX_OK;
}
static int take(aspect_compiler_reader *r)
{
 int value;
 if(r->pending!=EOF){value=r->pending;r->pending=EOF;}
 else value=fgetc(r->file);
 if(value!=EOF){
  if(r->offset==ULONG_MAX){r->status=ASPECT_LEX_POSITION;return EOF;}
  ++r->offset;
 }
 return value;
}
static int scan(aspect_compiler_reader *r,aspect_compiler_line *line)
{
 unsigned p=0,start,kind,q;
 while(p<line->length){
  if(space(line->bytes[p])){++p;continue;}
  if(line->bytes[p]==';')break;
  start=p;
  if(line->bytes[p]=='"'){
   ++p;while(p<line->length && line->bytes[p]!='"')++p;
   if(p==line->length)return fail(r,ASPECT_LEX_CHARACTER,start,line->offset+start);
   ++p;kind=ASPECT_TOKEN_STRING;
  }else if(first(line->bytes[p])){
   do{++p;}while(p<line->length && continuation(line->bytes[p]));
   kind=ASPECT_TOKEN_IDENTIFIER;
  }else if(digit(line->bytes[p])){
   if(p+2<line->length && line->bytes[p]=='0' &&
       (line->bytes[p+1]=='x'||line->bytes[p+1]=='X') && hex(line->bytes[p+2])){
    p+=3;while(p<line->length && hex(line->bytes[p]))++p;
   }else{
    do{++p;}while(p<line->length && digit(line->bytes[p]));
    if(p+1<line->length && line->bytes[p]=='.' && digit(line->bytes[p+1])){
     p+=2;while(p<line->length && digit(line->bytes[p]))++p;
    }
    if(p<line->length && (line->bytes[p]=='e'||line->bytes[p]=='E')){
     q=p+1;
     if(q<line->length && (line->bytes[q]=='+'||line->bytes[q]=='-'))++q;
     if(q<line->length && digit(line->bytes[q])){
      p=q+1;while(p<line->length && digit(line->bytes[p]))++p;
     }
    }
   }
   if(p<line->length && (line->bytes[p]=='l'||line->bytes[p]=='L'))++p;
   kind=ASPECT_TOKEN_NUMBER;
  }else if(p+1<line->length && pair(line->bytes[p],line->bytes[p+1])){
   p+=2;kind=ASPECT_TOKEN_OPERATOR;
  }else if(single(line->bytes[p])){++p;kind=ASPECT_TOKEN_OPERATOR;}
  else return fail(r,ASPECT_LEX_CHARACTER,p,line->offset+p);
  if(line->count>=ASPECT_COMPILER_TOKEN_MAX)return fail(r,ASPECT_LEX_LINE_SIZE,start,line->offset+start);
  line->tokens[line->count].kind=kind;
  line->tokens[line->count].start=start;
  line->tokens[line->count++].length=p-start;
 }
 return 1;
}
int aspect_compiler_next_line(aspect_compiler_reader *r,aspect_compiler_line *line)
{
 int value,following;
 if(!r||!line||!r->file)return -1;
 if(r->status)return -1;
 if(r->finished)return 0;
 line->number=r->number;line->offset=r->offset;line->length=line->count=0;
 for(;;){
  value=take(r);
  if(value==EOF){
   if(r->status)return fail(r,r->status,line->length,r->offset);
   if(ferror(r->file))return fail(r,ASPECT_LEX_IO,line->length,r->offset);
   r->finished=1;
   if(!line->length)return 0;
   break;
  }
  if(boundary((unsigned char)value)){
   if(value==13){
    following=fgetc(r->file);
    if(following==10){
     if(r->offset==ULONG_MAX)return fail(r,ASPECT_LEX_POSITION,line->length,r->offset);
     ++r->offset;
    }else if(following!=EOF)r->pending=following;
    else if(ferror(r->file))return fail(r,ASPECT_LEX_IO,line->length,r->offset);
   }
   break;
  }
  if(line->length==ASPECT_COMPILER_LINE_MAX)
   return fail(r,ASPECT_LEX_LINE_SIZE,line->length,r->offset-1);
  line->bytes[line->length++]=(unsigned char)value;
 }
 line->bytes[line->length]=0;
 if(scan(r,line)<0)return -1;
 if(r->number==ULONG_MAX)return fail(r,ASPECT_LEX_POSITION,line->length,r->offset);
 ++r->number;
 return 1;
}
int aspect_compiler_token_copy(const aspect_compiler_line *line,unsigned index,
                               unsigned char *output,unsigned capacity)
{
 unsigned i;aspect_compiler_token token;
 if(!line||!output||index>=line->count)return -1;
 token=line->tokens[index];
 if(token.start>line->length || token.length>line->length-token.start ||
    token.length>=capacity || token.kind<ASPECT_TOKEN_IDENTIFIER ||
    token.kind>ASPECT_TOKEN_OPERATOR)return -1;
 /* Read-only source and disjoint caller output are the token-copy contract. */
 for(i=0;i<token.length;++i){
  unsigned char c=line->bytes[token.start+i];
  if(token.kind!=ASPECT_TOKEN_STRING && c>='A'&&c<='Z')c+='a'-'A';
  output[i]=c;
 }
 output[token.length]=0;return (int)token.length;
}
