#ifndef PCPLUS_CLIPBOARD_H
#define PCPLUS_CLIPBOARD_H
/* Maintained filename-list semantics recovered from PCPlus2.01.
 * Pure near-cdecl DOS16, DS=SS: no heap, filesystem, video or UART ownership.
 * The caller owns this fixed214-byte state and initializes it before use.
 * count records allocated entries: editing an entry to empty leaves a hole.
 */
#define CLIPBOARD_SLOTS 15
#define CLIPBOARD_NAME 13
#define CLIPBOARD_PACKET 196
typedef struct clipboard_state {
 unsigned count,separator;
 char names[CLIPBOARD_SLOTS][CLIPBOARD_NAME];
 unsigned char tags[CLIPBOARD_SLOTS];
} clipboard_state;
enum { CLIP_OK=0,CLIP_ARGUMENT,CLIP_STATE,CLIP_FULL,CLIP_DUPLICATE,
 CLIP_EMPTY,CLIP_CAPACITY,CLIP_NO_FILENAME };
enum { CLIP_ADD=0,CLIP_EDIT,CLIP_DELETE,CLIP_PURGE,CLIP_TAG,CLIP_SEPARATOR };
enum { CLIP_SINGLE=0,CLIP_ALL,CLIP_TAGGED };
unsigned __cdecl clip_initialize(clipboard_state *state);
/* Raw field contents1..12 bytes for add; edit also permits empty. Trailing
 * spaces are trimmed. Add uppercases ASCII and compares all15 slots exactly;
 * edit preserves case, duplicates and allocated count. Text may alias state:
 * it is fully staged before mutation. Keyboard/field policy belongs to the UI.
 * DELETE compacts names/tags; PURGE retains the configured separator.
 * TAG stores16 or0, matching the original selected bit. SEPARATOR accepts0..255.
 * Rejected operations leave state unchanged. Every slot must be NUL-terminated.
 */
unsigned __cdecl clip_change(clipboard_state *state,unsigned operation,
 unsigned index,const char *text);
/* Exact original screen-byte predicate: ASCII21..7E minus ."/\[]:|<>+=;,
 * Width1..132. A filename has1..8 allowed basename bytes before dot and at
 * least one extension byte; extension is copied at most3 bytes. Row edges are
 * bounded delimiters rather than the original's unchecked neighboring reads.
 * out13,first2,past2 must be valid/disjoint from row and each other. All outputs
 * remain untouched on no-match or rejection; past excludes the final NUL.
 */
unsigned __cdecl clip_valid_byte(unsigned value);
unsigned __cdecl clip_extract(const unsigned char *row,unsigned width,
 unsigned dot,char *out,unsigned *first,unsigned *past);
/* Prepare bounded raw bytes without mutating state or performing output.
 * SINGLE: first allocated entry+CR, including an edited empty entry.
 * ALL/TAGGED: allocated entries, including edited empty names; separator
 * AFTER EACH selected entry, then final CR.
 * No selected names produces0 bytes. State count0 produces0 bytes.
 * out and size must be disjoint from state/each other. On rejection outputs
 * are unchanged. A transport must commit SINGLE removal only after delivery;
 * call DELETE index0 after acceptance/completion, not during preparation.
 */
unsigned __cdecl clip_prepare(const clipboard_state *state,unsigned mode,
 unsigned char *out,unsigned capacity,unsigned *size);
#endif
