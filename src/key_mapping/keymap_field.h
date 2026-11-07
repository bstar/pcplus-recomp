#ifndef PCPLUS_KEYMAP_FIELD_H
#define PCPLUS_KEYMAP_FIELD_H
#define KEYMAP_FIELD_WIDTH 10
enum {KEYMAP_FIELD_ACTIVE=0,KEYMAP_FIELD_ACCEPT,KEYMAP_FIELD_CANCEL,KEYMAP_FIELD_ARGUMENT,KEYMAP_FIELD_BELL};
typedef struct keymap_field_state {
 unsigned cookie,phase,cursor,insert,saved_start,saved_end;
 unsigned char field[KEYMAP_FIELD_WIDTH];
} keymap_field_state;
/* Memory-only small-model DOS API: DS=SS, separate state/input/output buffers.
 * Initial input is notation, not wire/storage data. Oversized input is refused.
 * End/three-byte marker can put the cursor at width, as in the original.
 * Mutations there are bounded; malformed notation is refused on binding commit.
 */
unsigned keymap_field_begin(keymap_field_state *,const unsigned char *,unsigned,unsigned,unsigned);
unsigned keymap_field_key(keymap_field_state *,unsigned);
int keymap_field_commit(const keymap_field_state *,unsigned char *,unsigned);
unsigned keymap_field_shape(const keymap_field_state *);
#endif
