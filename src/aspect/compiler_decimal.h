#ifndef PCPLUS_ASPECT_COMPILER_DECIMAL_H
#define PCPLUS_ASPECT_COMPILER_DECIMAL_H
/* Nonnegative, lexer-validated decimal token without L suffix. Correctly
 * rounded IEEE754 binary64, ties to even; no hardware or CRT floating point.
 * Returns zero on success. Token length is bounded by253 source bytes. */
unsigned aspect_compiler_decimal(const unsigned char *,unsigned,unsigned char [8]);
#endif
