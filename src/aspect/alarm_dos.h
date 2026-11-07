#ifndef PCPLUS_ALARM_DOS_H
#define PCPLUS_ALARM_DOS_H
#include "alarm_cooperative.h"
/* Real BIOS/DOS/speaker platform. Caller selects runtime_keyboard_mode before
 * running; this adapter preserves it. The bounded foreground service must
 * leave keys alone and cannot use a competing speaker owner. Borrowed service
 * context remains live until alarm_dos_active becomes zero, including recovery.
 * This is not yet the VM/parent PRM or WHEN/RX-renderer binding. */
unsigned ALARM_CALL alarm_dos_run(unsigned seconds,unsigned enabled,
 unsigned long polls,unsigned (ALARM_CALL *service)(void *),void *cookie);
unsigned ALARM_CALL alarm_dos_recover(void);
unsigned ALARM_CALL alarm_dos_active(void);
unsigned ALARM_CALL alarm_dos_service_status(void);
#endif
