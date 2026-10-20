#ifndef ASPECT_PROCESS_SERIAL_H
#define ASPECT_PROCESS_SERIAL_H
#include "serial.h"
/* Component gate: all linked serial objects must use ASPECT_EXTERNAL_PROCESS.
 * pause requires IF1 and first drains introduced flow/TEMT with the existing
 * live IRQ bracket. Success makes active=2 until resume. During suspension,
 * byte/close/reopen APIs cannot touch the port or retire the unread token.
 * resume restores the driver even on line/overrun/TEMT timeout errors.
 * No screen or interpreter command dispatcher is integrated here. */
unsigned __cdecl aspect_process_serial_pause(void);
unsigned __cdecl aspect_process_serial_resume(void);
extern unsigned aspect_process_serial_detached;
#endif
