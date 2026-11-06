#ifndef PCPLUS_CHAT_TIMING_H
#define PCPLUS_CHAT_TIMING_H
#include "text.h"
/* Caller-owned far storage, DS=SS. No DOS/heap/private data/UART/key reads.
 * Preparation measures native busy-loop chunks across one BIOS tick interval;
 * alignment yields. A measurement is bounded by7039 chunks (ASPECT's limit).
 * Each nonzero pacing effect executes at most one calibrated unit per call.
 * BIOS waits use elapsed full-day ticks; missed observations do not add waits.
 * Only foreground use with IRQs enabled. Reset retires pending work. */
typedef struct chat_timing {
    chat_word phase,error,count,chunks;
    unsigned long stamp;
    chat_word kind,value,remaining;
} chat_timing;
#define CHAT_TIMING_DAY 1573040UL
#define CHAT_TIMING_READY 3
#define CHAT_TIMING_FAULT 4
enum {CHAT_TIMING_IF=1,CHAT_TIMING_CLOCK,CHAT_TIMING_LIMIT,CHAT_TIMING_RESOLUTION};
void CHAT_CALL chat_timing_reset(chat_timing CHAT_FAR *);
unsigned CHAT_CALL chat_timing_prepare(chat_timing CHAT_FAR *);
unsigned CHAT_CALL chat_timing_effect(chat_timing CHAT_FAR *,unsigned,unsigned);
/* Mechanical platform ABI, also exercised independently. */
unsigned CHAT_FAR __cdecl chat_timing_flags(void);
unsigned long CHAT_FAR __cdecl chat_timing_ticks(void);
void CHAT_FAR __cdecl chat_timing_one(unsigned);
#endif
