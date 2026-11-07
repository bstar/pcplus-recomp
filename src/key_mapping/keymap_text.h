#ifndef PCPLUS_KEYMAP_TEXT_H
#define PCPLUS_KEYMAP_TEXT_H
/* PCKEYMAP 2.01 notation; separate source/target buffers, explicit lengths.
 * Returns content length or -1. Failure leaves target untouched.
 * No truncation to the original editor's ten visible columns.
 */
#define KEYMAP_STORAGE_MAX 11
#define KEYMAP_NOTATION_MAX 33
int keymap_text_encode(const unsigned char *source, unsigned length,
                       unsigned char *target, unsigned capacity);
int keymap_text_decode(const unsigned char *source, unsigned length,
                       unsigned char *target, unsigned capacity);
#endif
