#ifndef PCPLUS_MOUSE_OWNER_H
#define PCPLUS_MOUSE_OWNER_H
/* Maintained near-cdecl foreground owner. DS=SS, IF1 for driver operations.
 * Native IRQ callback is assembly and supports its driver's foreign DS/SS.
 * Quarantine retains unreleased storage; repair vector/guards before retrying
 * close when driver state is still owned. A failed free after restoration
 * retries storage release only. Never terminate the callback's owning
 * allocation while driver state is held. The bank adapter copies only the
 * declared word arguments; use the compiler's caller-cleaned C ABI. */
typedef struct mouse_settings {
 unsigned scale_x,scale_y;
 unsigned char enabled[6];
} mouse_settings;
enum { MOUSE_OK=0,MOUSE_ARGUMENT,MOUSE_STATE,MOUSE_DRIVER,MOUSE_MEMORY,
 MOUSE_PENDING };
enum { MOUSE_CLOSED=0,MOUSE_READY,MOUSE_SUSPENDED,MOUSE_QUARANTINED };
/* Partial2.01 PRM decode: only04e4/04e6, UI bounds1..999. Six source defaults
 * enable the native direction/Enter/Escape mappings. No file/driver mutation;
 * reject size, wrap and overlap; destination unchanged on failure. */
unsigned __cdecl mouse_settings_decode(const unsigned char *,unsigned,mouse_settings *);
unsigned __cdecl mouse_owner_open(const mouse_settings *);
unsigned __cdecl mouse_owner_suspend(void);
unsigned __cdecl mouse_owner_resume(void);
unsigned __cdecl mouse_owner_close(void);
unsigned __cdecl mouse_owner_key(unsigned *);
unsigned __cdecl mouse_owner_phase(void);
unsigned __cdecl mouse_owner_bytes(void);
#ifdef TERMINAL_MOUSE
/* Suspended-owner settings update only. Original driver/native snapshots stay
 * unchanged; next resume installs the accepted settings. */
unsigned __cdecl mouse_owner_reconfigure(const mouse_settings *);
#endif
#endif
