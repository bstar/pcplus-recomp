#ifndef PCPLUS_CHAT_SESSION_H
#define PCPLUS_CHAT_SESSION_H
#include "screen.h"
#define CHAT_FAILED 32
typedef struct chat_session {
    chat_owner send;
    chat_screen screen;
    chat_word rx_phase,rx_value,next_rx,fault;
#ifdef CHAT_PRESENTATION
    void CHAT_FAR *presentation;
#endif
} chat_session;
/* Single foreground owner. Callbacks must be bounded, all-or-refuse, and must
 * not reenter or mutate this context. No live parent ownership is implied. */
unsigned CHAT_CALL chat_session_open(chat_session CHAT_FAR *,chat_word CHAT_FAR *frame,
    unsigned capacity,unsigned rows,unsigned attribute,unsigned bar,unsigned clear,
    unsigned buffered,unsigned duplex,unsigned newline);
unsigned CHAT_CALL chat_session_key(chat_session CHAT_FAR *,unsigned key,unsigned transport_idle);
unsigned CHAT_CALL chat_session_receive(chat_session CHAT_FAR *,const unsigned char CHAT_FAR *table,unsigned value);
unsigned CHAT_CALL chat_session_step(chat_session CHAT_FAR *,unsigned budget,chat_sink,void CHAT_FAR *context);
void CHAT_CALL chat_session_abort(chat_session CHAT_FAR *);
#endif
