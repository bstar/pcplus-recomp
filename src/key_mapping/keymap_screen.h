#ifndef PCPLUS_KEYMAP_SCREEN_H
#define PCPLUS_KEYMAP_SCREEN_H
#define KEYMAP_SCREEN_WORDS 2000
#define KEYMAP_PROFILE_BYTES 948
/* Dispatch 0..78 selects a slot. Other actions leave the slot unchanged. */
enum {KEYMAP_NEXT=79,KEYMAP_PREVIOUS,KEYMAP_OPEN,KEYMAP_SAVE,KEYMAP_EXIT,KEYMAP_ABOUT,KEYMAP_RESERVED,KEYMAP_INVALID};
unsigned keymap_screen_key(unsigned key);
unsigned keymap_screen_position(unsigned slot);
const char *keymap_screen_label(unsigned slot);
const char *keymap_screen_profile(unsigned profile);
/* Caller owns a full 2000-word frame and disjoint 948-byte profile image.
 * Rendering never modifies bindings. Long/ambiguous bindings are marked.
 * leaf is an at-most-12-character DOS leaf, not a path or private record.
 */
unsigned keymap_screen_render(unsigned short *frame,unsigned profile,const unsigned char *bindings,const char *leaf);
#endif
