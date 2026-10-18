#ifndef PCPLUS_PRINTER_DEVICE_H
#define PCPLUS_PRINTER_DEVICE_H
/* Maintained fixed PRN owner, near cdecl DS=SS. No queue or formatting.
 * DOS calls themselves can block in a device driver. Snapshot is read-only.
 * API readiness is advisory; write rechecks status immediately before IO. */
enum { PD_OK=0,PD_WAIT,PD_ARGUMENT,PD_BUSY,PD_STATE,PD_OPEN,PD_IDENTITY,
 PD_MODE,PD_READY,PD_WRITE,PD_RESTORE,PD_CLOSE,PD_RECOVERY,PD_OVERFLOW };
enum { PD_IDLE=0,PD_OPENED,PD_CLOSED,PD_BROKEN,PD_UNCERTAIN };
typedef struct printer_device_snapshot {
 unsigned state,first_status,dos_error,restore_error,close_error;
 unsigned handle_open,handle_uncertain,original_mode,mode_changed;
 unsigned write_calls,close_calls,reserved;
 unsigned long accepted,ready_calls;
} printer_device_snapshot;
extern printer_device_snapshot printer_device_result;
unsigned __cdecl printer_device_initialize(void);
unsigned __cdecl printer_device_begin(void);
unsigned __cdecl printer_device_ready(void);
unsigned __cdecl printer_device_write(unsigned character);
unsigned __cdecl printer_device_close(void);
unsigned __cdecl printer_device_cleanup(void);
#endif
