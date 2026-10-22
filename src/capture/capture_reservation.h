#ifndef PCPLUS_CAPTURE_RESERVATION_H
#define PCPLUS_CAPTURE_RESERVATION_H
#include "capture_file.h"
/* Private shared guard. Kept near DS while its operations may occupy a far
 * code bank. Only these implementations may mutate it. */
typedef struct capture_reservation_state {
 capture_file_probe probe;
 void *context;
 unsigned busy;
} capture_reservation_state;
extern capture_reservation_state capture_reservation;
unsigned __far __cdecl capture_file_reserved(const char *identity);
/* Resident backend called only inside a guarded registration. Invokes the
 * candidate callback for each current open/uncertain binary-sink identity. */
unsigned __far __cdecl capture_file_probe_owners(capture_file_probe,void *);
#endif
