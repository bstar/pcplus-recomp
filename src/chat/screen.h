#ifndef PCPLUS_CHAT_SCREEN_H
#define PCPLUS_CHAT_SCREEN_H
#include "../terminal/chat_owner.h"
typedef struct chat_pane {chat_word first,last,row,column;} chat_pane;
typedef struct chat_screen {
    chat_word active,rows,cells,attribute,bar;
    chat_word CHAT_FAR *frame;
    chat_pane pane[2];
} chat_screen;
/* Narrow80-column single-width Chat contract; no BIOS/global cursor mutation. */
unsigned CHAT_CALL chat_screen_open(chat_screen CHAT_FAR *,chat_word CHAT_FAR *frame,
    unsigned capacity,unsigned rows,unsigned attribute,unsigned bar,unsigned clear);
unsigned CHAT_CALL chat_screen_put(chat_screen CHAT_FAR *,unsigned pane,unsigned value);
unsigned CHAT_CALL chat_screen_receive(chat_screen CHAT_FAR *,const unsigned char CHAT_FAR *table,unsigned value);
#endif
