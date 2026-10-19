#include "compiler_output.h"
unsigned aspect_compiler_output_init(aspect_compiler_output *o,FILE *file)
{
 long p;if(!o)return ASPECT_OUTPUT_STATE;
 o->file=file;o->position=0;o->status=ASPECT_OUTPUT_STATE;
 if(!file)return o->status;
 p=ftell(file);if(p<0){o->status=ASPECT_OUTPUT_IO;return o->status;}
 o->position=(unsigned long)p;o->status=0;return 0;
}
void aspect_compiler_emit_byte(aspect_compiler_output *o,unsigned value)
{
 if(o->status)return;
 if(o->position==ASPECT_OUTPUT_MAX){o->status=ASPECT_OUTPUT_RANGE;return;}
 if(fputc(value&255,o->file)==EOF){o->status=ASPECT_OUTPUT_IO;return;}
 ++o->position;
}
void aspect_compiler_emit_word(aspect_compiler_output *o,unsigned value)
{aspect_compiler_emit_byte(o,value);aspect_compiler_emit_byte(o,value>>8);}
void aspect_compiler_emit_dword(aspect_compiler_output *o,unsigned long value)
{aspect_compiler_emit_word(o,(unsigned)value);aspect_compiler_emit_word(o,(unsigned)(value>>16));}
void aspect_compiler_patch_dword(aspect_compiler_output *o,unsigned long offset,unsigned long target)
{
 unsigned char data[4];unsigned i;
 if(o->status)return;
 if(o->position<4||offset>o->position-4||target>ASPECT_OUTPUT_MAX){o->status=ASPECT_OUTPUT_RANGE;return;}
 for(i=0;i<4;++i){data[i]=(unsigned char)target;target>>=8;}
 if(fseek(o->file,(long)offset,SEEK_SET)||fwrite(data,1,4,o->file)!=4||fseek(o->file,(long)o->position,SEEK_SET))o->status=ASPECT_OUTPUT_IO;
}

unsigned aspect_compiler_output_flush(aspect_compiler_output *o)
{if(!o->status && (fflush(o->file)||ferror(o->file)))o->status=ASPECT_OUTPUT_IO;return o->status;}
