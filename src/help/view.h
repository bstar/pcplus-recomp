#ifndef PCPLUS_HELP_VIEW_H
#define PCPLUS_HELP_VIEW_H
#define HELP_VIEW_OK 0
#define HELP_VIEW_ARGUMENT 1
#define HELP_VIEW_STATE 2
#define HELP_VIEW_MEMORY 3
#define HELP_VIEW_GUARD 4
/* Source-owned fixed80x25/page0 foreground view. Content is caller-owned near
 * DS=SS storage that must remain immutable until successful close. */
typedef struct help_page {const char *title;const char *lines[17];} help_page;
unsigned __far __cdecl help_view_open(const help_page *,unsigned,unsigned);
unsigned __far __cdecl help_view_key(unsigned);
unsigned __far __cdecl help_view_close(void);
/* Internal enclosing-owner recovery: caller proved its original view retired
 * and no replacement owner remains. Release storage without replaying a stale
 * screen/cursor. Failed release retains a discard-only retry. */
unsigned __far __cdecl help_view_discard(void);
unsigned __far __cdecl help_view_active(void);
unsigned __far __cdecl help_view_topic(void);
#ifdef HELP_VIEW_DIAGNOSTIC
extern unsigned help_view_fail_allocate,help_view_fail_release;
void __far __cdecl help_view_damage_guard(void);
#endif
#endif
