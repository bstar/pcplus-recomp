#ifndef ASPECT_EXTERNAL_RUNTIME_H
#define ASPECT_EXTERNAL_RUNTIME_H
/* Native command frontend ABI. Guarded raw and attached experimental bindings exist;
 * these handlers remain unlinked from the shipped product's dispatch table.
 * Caller removes ten bytes; program/tail are borrowed near pointers valid
 * only during this synchronous call. Return is the raw comparison status.
 * DOS uses command_processor=1; RUN/SHELL use0. SHELL supplies a null tail,
 * wait0/save1 and the environment's COMSPEC pointer, possibly NULL.
 * Implementing this requires process/trap/UART/display/keyboard ownership,
 * not merely spawnl. The compiler may emit these currently unsupported slots.
 */
int runtime_external_execute(const char *program,const char *tail,
 unsigned command_processor,unsigned wait,unsigned save_screen);
#if defined(ASPECT_EXTERNAL_PROCESS)
unsigned runtime_external_scope(unsigned entering);
extern unsigned runtime_external_calls,runtime_external_raw_status,runtime_external_private_count;
#if defined(ASPECT_EXTERNAL_DIAGNOSTIC)
#if defined(ASPECT_PROCESS_OBSERVER_FAR)
void __far runtime_external_observe(unsigned,unsigned,unsigned,unsigned);
#else
void runtime_external_observe(unsigned,unsigned,unsigned,unsigned);
#endif
#endif
#endif
#endif
