#ifndef PCPLUS_DISPLAY_PREFERENCES_H
#define PCPLUS_DISPLAY_PREFERENCES_H
/* Raw saved words, not accepted hardware geometry or a live selector.
 * Populated only by a successful startup preferences transaction. No defaults,
 * normalization, BIOS mutation or PRM write. See DISPLAY_CONFIGURATION.md. */
typedef struct display_preferences {
 unsigned status_hidden,selector,rows,video_mode;
} display_preferences;
extern display_preferences terminal_display_preferences;
extern unsigned terminal_display_preferences_ready;
#endif
