#ifndef PCPLUS_CHAT_TEXT_H
#define PCPLUS_CHAT_TEXT_H
#include "../terminal/chat_owner.h"
/* Additional sink boundaries of native48CC. Transmit acceptance represents
 * completion at the native UART boundary, not merely queue admission. A delay
 * sink accepts only after its requested wait. Refusal makes no external effect.
 * One foreground owner; callbacks must not mutate/reenter this state. */
#define CHAT_TEXT_ECHO 4
#define CHAT_TEXT_BIOS_WAIT 5
#define CHAT_TEXT_PACE 6
typedef struct chat_text {
    chat_word active,count,at,phase,character,pause,echo,pacing;
    unsigned char bytes[52];
} chat_text;
/* Fixed KEY text field, not its preceding kind word. Capacity1..52 includes
 * NUL. Source and state must be disjoint conventional far storage. Invalid
 * input/busy refusal preserves state and emits nothing. DS=SS, DF clear. */
unsigned CHAT_CALL chat_text_open(chat_text CHAT_FAR *,const unsigned char CHAT_FAR *,
    unsigned capacity,unsigned pause,unsigned echo,unsigned pacing);
unsigned CHAT_CALL chat_text_step(chat_text CHAT_FAR *,unsigned budget,chat_sink,void CHAT_FAR *);
void CHAT_CALL chat_text_abort(chat_text CHAT_FAR *);
#endif
