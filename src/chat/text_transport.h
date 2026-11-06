#ifndef PCPLUS_CHAT_TEXT_TRANSPORT_H
#define PCPLUS_CHAT_TEXT_TRANSPORT_H
#include "../terminal/chat_owner.h"
/* Optional physical TX service, not an ordinary queue-admission sink. Accepts
 * only CHAT_TX byte values after the main loop grants an empty physical slot.
 * Success consumes that grant and records the actual user byte. Rejection
 * preserves the grant, queue, progress epoch and recorder. No IO polling or
 * keyboard/receive consumption. Echo/waits are deliberately refused here. */
unsigned CHAT_FAR __cdecl terminal_chat_text_tx_sink(unsigned,unsigned,void CHAT_FAR *);
#endif
