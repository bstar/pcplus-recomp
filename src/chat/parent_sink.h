#ifndef PCPLUS_CHAT_PARENT_SINK_H
#define PCPLUS_CHAT_PARENT_SINK_H
#include "../terminal/chat_owner.h"
/* Parent DS=SS, exclusive Chat storage owner2, foreground only. user is unused.
 * TX is user-origin queue admission; accepted LOG/HISTORY use native services.
 * Printer/TX backpressure refuses before side effects. No polling or reentry. */
unsigned CHAT_FAR __cdecl terminal_chat_sink(unsigned,unsigned,void CHAT_FAR *);
#endif
