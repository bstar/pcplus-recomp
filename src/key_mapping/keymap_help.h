#ifndef PCPLUS_KEYMAP_HELP_H
#define PCPLUS_KEYMAP_HELP_H
/* Synchronous small-model DS=SS full Help viewer; context17, sibling HLP only.
 * Existing bindings/baseline stay allocated. No serial or KBD-file operation.
 * Reuses the caller's immutable displayed2000-word frame for restoration. */
unsigned keymap_help_open(const unsigned short *);
#endif
