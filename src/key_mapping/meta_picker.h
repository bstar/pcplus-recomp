#ifndef PCPLUS_META_PICKER_H
#define PCPLUS_META_PICKER_H
#define META_PICKER_CAPACITY 1001
#define META_PICKER_BYTES (META_PICKER_CAPACITY*9)
enum {META_PICKER_COLLECT=0,META_PICKER_SORT,META_PICKER_ACTIVE,META_PICKER_ACCEPT,META_PICKER_CANCEL,META_PICKER_EMPTY};
enum {META_PICKER_OK=0,META_PICKER_ARGUMENT,META_PICKER_BUSY,META_PICKER_LIMIT,META_PICKER_BELL};
typedef struct meta_picker_state {
 unsigned cookie,phase,count,top,row,index,limit,changed;
 unsigned char __far *names;
} meta_picker_state;
/* Caller owns explicit disjoint far state20/table9009. No DOS, allocation,
 * blocking input or UART. Add terminated stems of1..8 bytes in enumeration
 * order, then seal; bounded sort_step uses at most64 adjacent comparisons.
 * Stable ASCII case-insensitive sort. Original navigation/15-row viewport,
 * including End selecting FIRST row of last page, not the last entry.
 * Caller owns enumeration/resource lifetime and must validate resolved paths.
 */
unsigned __far __cdecl meta_picker_begin(meta_picker_state __far *,unsigned char __far *);
unsigned __far __cdecl meta_picker_add(meta_picker_state __far *,const char __far *);
unsigned __far __cdecl meta_picker_seal(meta_picker_state __far *);
unsigned __far __cdecl meta_picker_sort_step(meta_picker_state __far *,unsigned);
unsigned __far __cdecl meta_picker_key(meta_picker_state __far *,unsigned);
unsigned __far __cdecl meta_picker_selected(const meta_picker_state __far *,char __far *);
/* Bounded supplied80x25 frame view: native list rows5..19/col35, authored border.
 * No actual VGA/BIOS ownership or automatic previous-frame restoration. */
unsigned __far __cdecl meta_picker_draw(const meta_picker_state __far *,unsigned __far *,unsigned);
#endif
