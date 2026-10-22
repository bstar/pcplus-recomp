#include "compiler_unit.h"
#include "compiler_unit_dump.h"
#include <string.h>
static void byte(FILE *f,unsigned value){fputc(value&255,f);}
static void word(FILE *f,unsigned value){byte(f,value);byte(f,value>>8);}
static void dword(FILE *f,unsigned long value){word(f,(unsigned)value);word(f,(unsigned)(value>>16));}
static void name(FILE *f,const char *value)
{unsigned n=strlen(value);word(f,n);fwrite(value,1,n,f);}
static void symbols(FILE *f,aspect_compiler_symbol *s)
{
 for(;s;s=s->next){byte(f,1);byte(f,s->kind);byte(f,s->space);word(f,s->index);name(f,s->name);}
 byte(f,0);
}
static void ranges(FILE *f,aspect_compiler_source *s)
{for(;s;s=s->next){byte(f,1);dword(f,s->line);dword(f,s->offset);}byte(f,0);}
int aspect_compiler_unit_dump(FILE *input,FILE *output)
{
 aspect_compiler_unit unit;aspect_compiler_procedure *p;aspect_compiler_source *s;aspect_compiler_initializer *init;
 unsigned status,i;
 if(!input||!output)return 1;
 aspect_compiler_unit_init(&unit);status=aspect_compiler_unit_load(&unit,input);
 fwrite("AUN1",1,4,output);byte(output,status);byte(output,unit.lexical_status);
 dword(output,unit.error_line);dword(output,unit.error_offset);
 if(!status){
  for(i=0;i<4;++i)word(output,unit.counts[i]);
  symbols(output,unit.globals);ranges(output,unit.declarations);
  for(p=unit.procedures;p;p=p->next){
   byte(output,1);name(output,p->name);word(output,p->size);dword(output,p->parameter_bytes);
   dword(output,p->line);dword(output,p->offset);symbols(output,p->symbols);ranges(output,p->declarations);
   for(init=p->initializers;init;init=init->next){
    byte(output,1);dword(output,init->line);dword(output,init->offset);word(output,init->first);word(output,init->last);
    byte(output,init->chained);name(output,init->destination->name);
   }
   byte(output,0);
   for(s=p->body;s;s=s->next){byte(output,1);dword(output,s->line);dword(output,s->offset);}
   byte(output,0);
  }
  byte(output,0);
 }
 aspect_compiler_unit_dispose(&unit);
 if(fflush(output)||ferror(output))return 2;
 return status?1:0;
}
