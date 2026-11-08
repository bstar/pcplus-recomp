#ifndef PCPLUS_ASPECT_GET_COMMAND_H
#define PCPLUS_ASPECT_GET_COMMAND_H
/* Ordinary VM DS=SS/IF1/DF0 only. Caller supplies checked wrap policy. Run returns sticky typed error; recover
 * retries only matching restored GET ownership. Ready authorizes final native
 * abort propagation, never freeing/reusing a retained editor/modal owner.
 * Execute invokes recovered abort/longjmp only when cleanup is complete; its
 * caller must have a native dispatcher context. Quarantine returns normally.
 * Direct dispatcher longjmp bypassing the GET checkpoint is not recovered. */
unsigned __cdecl runtime_get_command_run(unsigned);
unsigned __cdecl runtime_get_command_recover(void);
unsigned __cdecl runtime_get_command_ready(void);
/* GET-specific lifetime only: unrelated WINDOW/PROGRAM/WHEN confirmation
 * owners must still reach their existing recovery paths. */
unsigned __cdecl runtime_get_command_retained(void);
unsigned __cdecl runtime_get_command_execute(unsigned);
#endif
