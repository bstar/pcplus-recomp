#ifndef PCPLUS_CHAT_OWNER_H
#define PCPLUS_CHAT_OWNER_H
/* Caller-owned storage: no DGROUP allocation, DOS, BIOS, UART polling or heap.
 * DS=SS. A refusing sink MUST have made no externally visible side effect. */
#ifdef __WATCOMC__
#define CHAT_FAR __far
#else
#define CHAT_FAR
#endif
#ifdef CHAT_BANK
#define CHAT_CALL CHAT_FAR __cdecl
#else
#define CHAT_CALL __cdecl
#endif
#define CHAT_TX 1
#define CHAT_LOG 2
#define CHAT_HISTORY 3
#define CHAT_ACCEPTED 1
#define CHAT_PAINT 2
#define CHAT_CLOSED 4
#define CHAT_HELP 8
#define CHAT_META 16
typedef unsigned short chat_word;
typedef struct chat_owner {
    chat_word active,buffered,duplex,newline,phase,count,at,limit,key,submit;
    unsigned char line[299];
} chat_owner;
typedef unsigned (CHAT_FAR __cdecl *chat_sink)(unsigned kind,unsigned value,void CHAT_FAR *context);
void CHAT_CALL chat_owner_open(chat_owner CHAT_FAR *,unsigned buffered,unsigned duplex,unsigned newline);
unsigned CHAT_CALL chat_owner_key(chat_owner CHAT_FAR *,unsigned key);
unsigned CHAT_CALL chat_owner_step(chat_owner CHAT_FAR *,unsigned budget,chat_sink,void CHAT_FAR *context);
void CHAT_CALL chat_owner_abort(chat_owner CHAT_FAR *);
#endif
