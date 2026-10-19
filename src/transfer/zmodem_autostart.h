#ifndef PCPLUS_ZMODEM_AUTOSTART_H
#define PCPLUS_ZMODEM_AUTOSTART_H
#ifndef __WATCOMC__
#ifndef __cdecl
#define __cdecl
#endif
#endif
/* Maintained terminal invitation recognizer, not a transfer owner. Near cdecl,
 * DS=SS; no allocation, UART, screen or filesystem access. Recognizes only the
 * canonical hex ZRQINIT invitation (** ZDLE B, seven hex bytes, CR LF).
 * ZF0 must be zero (data transfer). Uppercase hex and parity-marked LF are accepted. Binary
 * headers and embedded flow-control bytes remain ordinary terminal input.
 * A caller must explicitly enable detection and enforce ownership boundaries.
 */
#define ZA_HELD_MAX 20
enum { ZA_MORE=0, ZA_START=1, ZA_ARGUMENT=2 };
typedef struct za_state {
 unsigned count;
 unsigned char held[ZA_HELD_MAX];
} za_state;
/* All arguments must be valid, disjoint near objects. Output has at least
 * ZA_HELD_MAX bytes. Every consumed byte is either released in original order,
 * retained as a possible invitation, or consumed by a validated ZA_START.
 * released may be nonzero together with ZA_START. Nothing after the invitation
 * is consumed, including its optional XON. No implicit idle timeout: flush on
 * the caller's bounded deadline, disable, ownership change or shutdown, then
 * deliver those bytes through the same terminal path as ordinary input.
 */
void __cdecl za_reset(za_state *);
unsigned __cdecl za_feed(za_state *,unsigned byte_value,
 unsigned char *output,unsigned *released);
unsigned __cdecl za_flush(za_state *,unsigned char *output);
#endif
