#ifndef PCPLUS_CHAT_REDISPLAY_LEASE_H
#define PCPLUS_CHAT_REDISPLAY_LEASE_H
#include "module.h"
#define CHAT_VIEW_BEGIN 1
#define CHAT_VIEW_RESUME 2
#define CHAT_VIEW_CLOSE 3
/* Immutable parent CODE descriptor. Both banks retain the parent's DS=SS;
 * these three near words belong to that DS, never to the module's CS. */
typedef struct chat_view_binding {
    unsigned __near *active,*owner,*snapshot_segment;
    const unsigned __near *tx_count,*connection;
    chat_word CHAT_FAR *underlay;
    void CHAT_FAR *scratch;
    unsigned (CHAT_FAR __cdecl *enter)(void);
    void (CHAT_FAR __cdecl *leave)(void);
    const unsigned __near *rows,*attribute,*duplex,*newline,*translate;
    const unsigned char __near *input_table;
    void CHAT_FAR *presentation;
    unsigned char CHAT_FAR *rx_table;
    chat_sink sink;
} chat_view_binding;
unsigned CHAT_CALL chat_view_dispatch(chat_module_request CHAT_FAR *);
unsigned CHAT_CALL chat_view_service(chat_module_request CHAT_FAR *);
unsigned CHAT_CALL chat_view_front_open(chat_module_request CHAT_FAR *);
#endif
