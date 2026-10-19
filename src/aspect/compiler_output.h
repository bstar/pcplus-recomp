#ifndef PCPLUS_ASPECT_COMPILER_OUTPUT_H
#define PCPLUS_ASPECT_COMPILER_OUTPUT_H
#include <stdio.h>
enum { ASPECT_OUTPUT_OK=0,ASPECT_OUTPUT_IO,ASPECT_OUTPUT_RANGE,ASPECT_OUTPUT_STATE };
#define ASPECT_OUTPUT_MAX 2147483647UL
typedef struct aspect_compiler_output {FILE *file;unsigned long position;unsigned status;} aspect_compiler_output;
unsigned aspect_compiler_output_init(aspect_compiler_output *,FILE *);
unsigned aspect_compiler_output_flush(aspect_compiler_output *);
void aspect_compiler_emit_byte(aspect_compiler_output *,unsigned);
void aspect_compiler_emit_word(aspect_compiler_output *,unsigned);
void aspect_compiler_emit_dword(aspect_compiler_output *,unsigned long);
void aspect_compiler_patch_dword(aspect_compiler_output *,unsigned long,unsigned long);
#endif
