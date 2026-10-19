#ifndef PCPLUS_ASPECT_LITERAL_H
#define PCPLUS_ASPECT_LITERAL_H
#if defined(__WATCOMC__)
typedef unsigned long aspect_u32;
#else
#include <stdint.h>
typedef uint32_t aspect_u32;
#endif

enum { ASPECT_LITERAL_OK=0, ASPECT_LITERAL_ARGUMENT,
       ASPECT_LITERAL_RANGE, ASPECT_LITERAL_TRUNCATED, ASPECT_LITERAL_FORMAT };
enum { ASPECT_LITERAL_MAX=80 };
typedef struct aspect_literal_result {
    unsigned text_length,wire_length,stride;
} aspect_literal_result;

/* Nonempty ASPECT 1.01 literal payload, after token AA. Position is the
 * absolute byte offset of the payload's length byte, not the token offset.
 * Source line is the compiler's current 32-bit fgets chunk counter.
 * Input bytes are literal CP437/source bytes; caret expansion is not performed.
 * Outputs and result must be disjoint from inputs and each other. Failure
 * leaves both output objects intact. Near ranges cannot wrap in DOS. */
unsigned aspect_literal_encode(const unsigned char *text,unsigned length,
    aspect_u32 position,aspect_u32 source_line,unsigned char *wire,
    unsigned capacity,aspect_literal_result *result);

/* Decode one payload from a possibly longer bytecode stream. No source line
 * is required: stride is carried by the payload. Length/stride/parity and
 * decoded non-NUL bytes are checked; this is not an integrity checksum.
 * Returns raw length-delimited bytes without a terminating NUL. Empty literal
 * token 6E 13, expressions and whole-ASX parsing are separate contracts. */
unsigned aspect_literal_decode(const unsigned char *wire,unsigned available,
    aspect_u32 position,unsigned char *text,unsigned capacity,
    aspect_literal_result *result);
#endif
