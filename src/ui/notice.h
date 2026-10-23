#ifndef PCPLUS_NOTICE_H
#define PCPLUS_NOTICE_H
/* Near DS=SS/cdecl. Service must poll transport/flow without consuming display
 * bytes or local keys, and return in bounded time. All callbacks run in the
 * foreground, never an ISR. */
enum {NOTICE_OK,NOTICE_KEY,NOTICE_CANCELLED,NOTICE_ARGUMENT,NOTICE_BUSY,
 NOTICE_WINDOW,NOTICE_SERVICE,NOTICE_TIMEOUT,NOTICE_BUDGET,NOTICE_STATE,NOTICE_CLEANUP};
typedef unsigned (__cdecl *notice_service)(void);
typedef unsigned (__cdecl *notice_sound)(unsigned kind);
typedef struct notice_options {
 unsigned attribute,animated,timeout_ticks;
 unsigned long poll_limit;
 notice_service service;
 notice_sound sound;
} notice_options;
typedef struct notice_result {
 unsigned status,cause,key,service_status,window_status;
 unsigned long polls,elapsed_ticks;
} notice_result;
/* kind0 selects the native message/tone route; kind1 the BX error/bell route.
 * NULL options select quiet 70h, no animation,74 BIOS ticks,1,000,000 polls.
 * A NULL sound callback deliberately selects quiet operation. Original native
 * sound configuration remains the eventual application platform's responsibility. */
unsigned __cdecl notice_show(const char *,unsigned kind,const notice_options *,notice_result *);
/* Retry retained cleanup after repairing geometry/guards; returns the original
 * cause once cleanup succeeds. Never closes a window
 * with a different generation, even if the far allocation address was reused. */
unsigned __cdecl notice_recover(notice_result *);
unsigned __cdecl notice_active(void);
#endif
