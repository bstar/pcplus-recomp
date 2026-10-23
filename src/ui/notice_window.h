#ifndef PCPLUS_NOTICE_WINDOW_H
#define PCPLUS_NOTICE_WINDOW_H
/* Component owner: one mode3/page0/80x25 window. Native algorithms are unchanged. */
enum {NOTICE_WINDOW_OK,NOTICE_WINDOW_ARGUMENT,NOTICE_WINDOW_BUSY,NOTICE_WINDOW_MEMORY,NOTICE_WINDOW_STATE,NOTICE_WINDOW_GUARD};
typedef struct notice_window_rect {unsigned top,left,bottom,right,attribute;} notice_window_rect;
unsigned __cdecl notice_window_open(const notice_window_rect *,unsigned animated);
unsigned __cdecl notice_window_close(void);
unsigned __cdecl notice_window_phase(void);
/* Internal identity token; compare only, never dereference or free it. */
void __far * __cdecl notice_window_identity(void);
unsigned __cdecl notice_window_generation(void);
#if defined(NOTICE_WINDOW_DIAGNOSTIC)
extern unsigned notice_window_fail_alloc,notice_window_allocations,notice_window_frees;
void __cdecl notice_window_damage_guard(void);
#endif
#endif
