#ifndef PCPLUS_ASPECT_RUNNER_ERROR_H
#define PCPLUS_ASPECT_RUNNER_ERROR_H
/* Fixed diagnostic vocabulary: keep the general printf engine out of the
 * resident interpreter. Return the full length, with bounded NUL termination,
 * so both attached video and stderr can use exactly the same message. */
typedef struct aspect_error_writer {char *text;unsigned capacity,length;} aspect_error_writer;
static void aspect_error_char(aspect_error_writer *w,char ch)
{if(w->capacity&&w->length<w->capacity-1)w->text[w->length]=ch;++w->length;}
static void aspect_error_text(aspect_error_writer *w,const char *text)
{while(*text)aspect_error_char(w,*text++);}
static void aspect_error_number(aspect_error_writer *w,unsigned value,unsigned radix,unsigned width)
{
 char digits[5];unsigned n=0;
 do{digits[n++]="0123456789ABCDEF"[value%radix];value/=radix;}while(value);
 while(n<width)digits[n++]='0';
 while(n)aspect_error_char(w,digits[--n]);
}
static unsigned aspect_runner_error(char *text,unsigned capacity,unsigned result,
 unsigned opcode,unsigned steps,unsigned native,unsigned serial,unsigned pacing)
{
 static const char *errors[]={"success","cannot open script","invalid script header",
  "unsupported command or service","floating-point service unavailable","file or output error",
  "instruction budget exhausted","invalid operand","out of memory","script stack overflow",
  "invalid runtime state","division by zero","CPU arithmetic fault","cancelled","serial service error"};
 aspect_error_writer w;
 if(capacity&&!text)return 0;
 w.text=text;w.capacity=capacity;w.length=0;
 aspect_error_text(&w,"ASPECT: ");
 aspect_error_text(&w,result<sizeof(errors)/sizeof(errors[0])?errors[result]:"runtime error");
 aspect_error_text(&w," (error ");aspect_error_number(&w,result,10,0);
 aspect_error_text(&w,", opcode ");aspect_error_number(&w,opcode,16,2);
 aspect_error_text(&w,", step ");aspect_error_number(&w,steps,10,0);
 if(native){aspect_error_text(&w,", native ");aspect_error_number(&w,native,10,0);}
 if(serial){aspect_error_text(&w,", serial ");aspect_error_number(&w,serial,10,0);}
 if(pacing){aspect_error_text(&w,", pacing ");aspect_error_number(&w,pacing,10,0);}
 aspect_error_char(&w,')');
 if(capacity)text[w.length<capacity?w.length:capacity-1]=0;
 return w.length;
}
#endif
