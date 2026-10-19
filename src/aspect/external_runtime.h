#ifndef ASPECT_EXTERNAL_RUNTIME_H
#define ASPECT_EXTERNAL_RUNTIME_H
/* Native command frontend ABI. Not yet implemented/linked in the product.
 * Caller removes ten bytes; program/tail are borrowed near pointers valid
 * only during this synchronous call. Return is the raw comparison status.
 * DOS uses command_processor=1; RUN/SHELL use0. SHELL supplies a null tail,
 * wait0/save1 and the environment's COMSPEC pointer, possibly NULL.
 * Implementing this requires process/trap/UART/display/keyboard ownership,
 * not merely spawnl. The compiler may emit these currently unsupported slots.
 */
int runtime_external_execute(const char *program,const char *tail,
 unsigned command_processor,unsigned wait,unsigned save_screen);
#endif
