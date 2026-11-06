#ifndef PCPLUS_CHAT_MODULE_H
#define PCPLUS_CHAT_MODULE_H
#include "session.h"
#define CHAT_MODULE_API 0x0100
#define CHAT_MODULE_QUERY 0
#define CHAT_MODULE_OPEN 1
#define CHAT_MODULE_KEY 2
#define CHAT_MODULE_RECEIVE 3
#define CHAT_MODULE_STEP 4
#define CHAT_MODULE_ABORT 5
#define CHAT_MODULE_BAD 0xffff
typedef struct chat_module_request {
    chat_word api,operation,result;
    chat_session CHAT_FAR *state;
    chat_word CHAT_FAR *frame;
    const unsigned char CHAT_FAR *table;
    chat_sink sink;
    void CHAT_FAR *user;
    chat_word capacity,rows,attribute,bar,clear,buffered,duplex,newline;
    chat_word key,transport_idle,budget,value;
} chat_module_request;
typedef unsigned (CHAT_FAR __cdecl *chat_module_entry)(chat_module_request CHAT_FAR *);
unsigned CHAT_FAR __cdecl chat_module_dispatch(chat_module_request CHAT_FAR *);
#endif
