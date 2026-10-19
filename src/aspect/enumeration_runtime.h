#ifndef PCPLUS_ASPECT_ENUMERATION_RUNTIME_H
#define PCPLUS_ASPECT_ENUMERATION_RUNTIME_H
/* One DOS enumeration context, independent of numbered streams. State survives
 * EXECUTE. Kernel DTA selection is bracketed on EVERY search and next call. */
void runtime_enumeration_reset(void);
#endif
