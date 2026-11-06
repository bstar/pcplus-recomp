#ifndef PCPLUS_CHAT_LIVE_H
#define PCPLUS_CHAT_LIVE_H
#include "../terminal/chat_owner.h"
typedef unsigned (CHAT_FAR __cdecl *chat_echo_error)(void);
/* Immutable parent descriptor, copied into caller-owned session storage.
 * Read-only KEY/config pointers are explicitly relative to the parent DS=SS;
 * callbacks/cursor remain far. A selected field is copied by text_open.
 * Callback code/lifetime belongs to the trusted parent, never private DGROUP. */
typedef struct chat_live_binding {
    const unsigned char __near *keys;
    const unsigned char __near *pause;
    const chat_word __near *pacing;
    const chat_word __near *duplex;
    chat_sink transmit,echo;
    chat_echo_error error;
    chat_word CHAT_FAR *cursor;
#ifdef CHAT_REDISPLAY
    const void CHAT_FAR *view;
#endif
} chat_live_binding;
#ifdef CHAT_REDISPLAY
typedef char chat_live_binding_must_be_28[(sizeof(chat_live_binding)==28)?1:-1];
#else
typedef char chat_live_binding_must_be_24[(sizeof(chat_live_binding)==24)?1:-1];
#endif
struct chat_session;
struct chat_module_request;
unsigned CHAT_CALL chat_live_bind(struct chat_session CHAT_FAR *,const chat_live_binding CHAT_FAR *);
unsigned CHAT_CALL chat_live_key(struct chat_module_request CHAT_FAR *);
unsigned CHAT_CALL chat_live_step(struct chat_module_request CHAT_FAR *);
#endif
