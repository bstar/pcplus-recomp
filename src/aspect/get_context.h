#ifndef PCPLUS_ASPECT_GET_CONTEXT_H
#define PCPLUS_ASPECT_GET_CONTEXT_H
/* Near scalar aliases required by the recovered owner. WRAP is supplied by
 * the caller's checked policy, never inferred from screen geometry. Entry is
 * inside the native checkpoint and precedes operand reads. Shared scratch is
 * the existing script-file-mode pointer (both original roles use4B06). */
extern unsigned runtime_get_row,runtime_get_column,runtime_get_attribute;
extern unsigned runtime_get_columns,runtime_get_rows,runtime_get_origin;
/* Required before each invocation, outside native/field ownership. */
unsigned runtime_get_context_policy(unsigned);
unsigned __cdecl runtime_get_context_enter(void);
unsigned __cdecl runtime_get_context_leave(void);
#endif
