#ifndef PCPLUS_ASPECT_COMPILER_LEX_DUMP_H
#define PCPLUS_ASPECT_COMPILER_LEX_DUMP_H
#include <stdio.h>
/* Diagnostic token stream only, not ASX. Neither FILE is closed. Error2 is an
 * output failure; error1 is a lexical/input failure with a terminal record. */
int aspect_compiler_lex_dump(FILE *,FILE *);
#endif
