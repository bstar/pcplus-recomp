#ifndef PCPLUS_ASPECT_COMPILER_LEXER_H
#define PCPLUS_ASPECT_COMPILER_LEXER_H
#include <stdio.h>
#define ASPECT_COMPILER_LINE_MAX 253U
#define ASPECT_COMPILER_TOKEN_MAX 253U
enum { ASPECT_LEX_OK=0,ASPECT_LEX_IO,ASPECT_LEX_LINE_SIZE,
       ASPECT_LEX_CHARACTER,ASPECT_LEX_POSITION,ASPECT_LEX_ARGUMENT };
enum { ASPECT_TOKEN_IDENTIFIER=1,ASPECT_TOKEN_NUMBER,ASPECT_TOKEN_STRING,
       ASPECT_TOKEN_OPERATOR };
typedef struct aspect_compiler_token {
    unsigned kind,start,length;
} aspect_compiler_token;
typedef struct aspect_compiler_line {
    unsigned long number,offset;
    unsigned length,count;
    unsigned char bytes[ASPECT_COMPILER_LINE_MAX+1];
    aspect_compiler_token tokens[ASPECT_COMPILER_TOKEN_MAX];
} aspect_compiler_line;
typedef struct aspect_compiler_reader {
    FILE *file;
    unsigned long number,offset,error_line,error_offset;
    unsigned status,error_column,finished;
    int pending;
} aspect_compiler_reader;
/* Binary input, borrowed FILE ownership. No rewind, write, close or heap use.
 * Each next call returns1(line),0(EOF),-1(sticky error). Lines and tokens borrow
 * caller storage until the next call. Positions count original source bytes,
 * relative to init, not translated C text offsets. CRLF counts as one physical line boundary.
 * Other splitlines boundaries match the existing CP437 host frontend. */
unsigned aspect_compiler_reader_init(aspect_compiler_reader *,FILE *);
int aspect_compiler_next_line(aspect_compiler_reader *,aspect_compiler_line *);
/* Copy the normalized token, append NUL and return its explicit byte length.
 * Destination must be disjoint from line storage. String tokens retain quoted
 * CP437 bytes, including embedded NUL. Other
 * tokens ASCII-fold to lowercase. Invalid input preserves destination. */
int aspect_compiler_token_copy(const aspect_compiler_line *,unsigned,
                               unsigned char *,unsigned);
#endif
