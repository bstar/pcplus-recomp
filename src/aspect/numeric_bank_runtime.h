#ifndef PCPLUS_NUMERIC_BANK_RUNTIME_H
#define PCPLUS_NUMERIC_BANK_RUNTIME_H
/* Stable near banks, full native byte-index/system and128-float capacities.
 * Borrowed addresses survive EXECUTE and ordinary string/global cleanup.
 * Reset only at invocation initialization; finish only after VM frames retire. */
unsigned char *__cdecl runtime_numeric_address(unsigned kind,unsigned index);
unsigned runtime_numeric_prepare(void);
void runtime_numeric_reset(void);
void runtime_numeric_finish(void);
unsigned runtime_numeric_live(void);
#endif
