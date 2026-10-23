#ifndef PCPLUS_SPEAKER_H
#define PCPLUS_SPEAKER_H
#if defined(SPEAKER_BANKED)
#define SPEAKER_CODE __far
#else
#define SPEAKER_CODE
#endif
/* Maintained foreground owner, distinct from exact native blocking sound.
 * DS=SS/IF required. No callback/interrupt owns this API. */
enum {SPEAKER_OK,SPEAKER_PENDING,SPEAKER_ARGUMENT,SPEAKER_BUSY,SPEAKER_STATE,SPEAKER_BUDGET};
unsigned SPEAKER_CODE __cdecl speaker_start(unsigned frequency,unsigned ticks,unsigned long poll_limit);
unsigned SPEAKER_CODE __cdecl speaker_poll(void);
unsigned SPEAKER_CODE __cdecl speaker_stop(void);
unsigned SPEAKER_CODE __cdecl speaker_active(void);
unsigned SPEAKER_CODE __cdecl speaker_generation(void);
#endif
