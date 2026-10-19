#ifndef PCPLUS_ASPECT_SOURCE_COMPILE_H
#define PCPLUS_ASPECT_SOURCE_COMPILE_H
#include "file_io.h"
/* Open normalized ASX, or explicitly compile ASP / a missing ASX's ASP sibling.
 * Path82 is updated to the accepted compiled name only on success. The compiler
 * is a sibling of this running interpreter, never a PATH/CWD command search. */
unsigned runtime_source_open(aspect_file *,char *path,unsigned source);
unsigned runtime_compiler_scope(unsigned entering);
extern unsigned runtime_compiler_calls,runtime_compiler_exit,runtime_compiler_dos_error;
#endif
