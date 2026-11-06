#ifndef PCPLUS_CHAT_MODULE_H
#define PCPLUS_CHAT_MODULE_H
#include "session.h"
#if defined(CHAT_FOREGROUND_TEXT) && !defined(CHAT_TIMING)
#error CHAT_FOREGROUND_TEXT requires CHAT_TIMING
#endif
#if defined(CHAT_TIMING) && !defined(CHAT_TEXT)
#error CHAT_TIMING requires CHAT_TEXT
#endif
#ifdef CHAT_TEXT
#ifndef CHAT_PRESENTATION
#error CHAT_TEXT requires CHAT_PRESENTATION
#endif
#ifdef CHAT_TIMING
#ifdef CHAT_FOREGROUND_TEXT
#ifdef CHAT_REDISPLAY
#define CHAT_MODULE_API 0x0105
#define CHAT_MODULE_STATE_BYTES 480
#else
#define CHAT_MODULE_API 0x0104
#define CHAT_MODULE_STATE_BYTES 476
#endif
#else
#define CHAT_MODULE_API 0x0103
#define CHAT_MODULE_STATE_BYTES 448
#endif
#else
#define CHAT_MODULE_API 0x0102
#define CHAT_MODULE_STATE_BYTES 430
#endif
#ifdef CHAT_FOREGROUND_TEXT
#ifdef CHAT_REDISPLAY
#define CHAT_MODULE_MAX_OPERATION 15
#define CHAT_MODULE_FRONT_OPEN 15
#define CHAT_MODULE_KEY_HOLD 12
#define CHAT_MODULE_RX_HOLD 13
#define CHAT_MODULE_FOREGROUND_STEP 14
#define CHAT_MODULE_REDISPLAY 11
#else
#define CHAT_MODULE_MAX_OPERATION 10
#endif
#define CHAT_MODULE_BIND_TEXT 10
#else
#define CHAT_MODULE_MAX_OPERATION 9
#endif
#define CHAT_MODULE_TEXT_OPEN 8
#define CHAT_MODULE_TEXT_STEP 9
#elif defined(CHAT_PRESENTATION)
#define CHAT_MODULE_API 0x0101
#define CHAT_MODULE_STATE_BYTES 362
#define CHAT_MODULE_MAX_OPERATION 7
#endif
#ifdef CHAT_PRESENTATION
#define CHAT_MODULE_PRESENT_OPEN 6
#define CHAT_MODULE_PRESENT_CURSOR 7
#endif
#ifndef CHAT_PRESENTATION
#define CHAT_MODULE_API 0x0100
#define CHAT_MODULE_STATE_BYTES 358
#define CHAT_MODULE_MAX_OPERATION 5
#endif
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
