#ifndef PCPLUS_CAPTURE_SESSION_H
#define PCPLUS_CAPTURE_SESSION_H
#include "capture_file.h"
/* Maintained processed-text owner, using native09b6 filtering before put().
 * No native CRT FILE pointer is accepted or dereferenced. Foreground only. */
enum { CS_OPEN=1,CS_HOLD,CS_CLOSED,CS_ERROR,CS_DENIED };
extern unsigned capture_session_notice,capture_session_failed;
extern unsigned capture_session_buffered;
unsigned __cdecl capture_session_initialize(void);
unsigned __cdecl capture_session_begin(const char *path,unsigned long ticks);
unsigned __cdecl capture_session_put(unsigned character,unsigned unused_handle);
unsigned __cdecl capture_session_flush(void);
unsigned __cdecl capture_session_stop(void);
unsigned __cdecl capture_session_pause(void);
void __cdecl capture_session_poll(unsigned long ticks);
unsigned __cdecl capture_session_shutdown(void);
#endif
