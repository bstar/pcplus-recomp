#ifndef PCPLUS_META_TEXT_H
#define PCPLUS_META_TEXT_H
#define META_TEXT_WIDTH 50
#define META_TEXT_RECORD_BYTES 52
enum {META_TEXT_ACTIVE=0,META_TEXT_ACCEPT,META_TEXT_CANCEL,META_TEXT_ARGUMENT,META_TEXT_BELL};
typedef struct meta_text_state {
 unsigned cookie,phase,cursor,insert,full,saved_shape,result;
 unsigned char field[META_TEXT_WIDTH];
} meta_text_state;
/* Serviced, memory-only Meta Keys field. DS=SS; explicit far, nonwrapping,
 * disjoint state/source or state/target spans. No keyboard, BIOS, DOS or UART.
 * Source is a52-byte record with a NUL; first50 bytes form the working field.
 * Escape never writes the record. Only commit after ACCEPT writes through NUL,
 * preserving opaque suffix bytes. Native input keys are already canonicalized.
 * KEY51-byte legacy text is retained on cancel and limited to50 on acceptance.
 */
unsigned __far __cdecl meta_text_begin(meta_text_state __far *,const unsigned char __far *,unsigned);
unsigned __far __cdecl meta_text_key(meta_text_state __far *,unsigned);
unsigned __far __cdecl meta_text_commit(const meta_text_state __far *,unsigned char __far *);
unsigned __far __cdecl meta_text_shape(const meta_text_state __far *);
#endif
