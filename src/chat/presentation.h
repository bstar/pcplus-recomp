#ifndef PCPLUS_CHAT_PRESENTATION_H
#define PCPLUS_CHAT_PRESENTATION_H
#include "session.h"
/* Caller-owned far context and complete backup; no heap or private frame.
 * DS=SS. A live presentation must retire before its module/storage lease. */
typedef struct chat_presentation {
    chat_word signature,rows,cells,position,shape,drawn;
    chat_word CHAT_FAR *backup;
} chat_presentation;
unsigned CHAT_CALL chat_present_open(chat_session CHAT_FAR *,chat_presentation CHAT_FAR *,
    chat_word CHAT_FAR *,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned);
unsigned CHAT_CALL chat_present_cursor(chat_session CHAT_FAR *);
unsigned CHAT_CALL chat_present_close(chat_session CHAT_FAR *);
#endif
