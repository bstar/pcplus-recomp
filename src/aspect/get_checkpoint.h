#ifndef PCPLUS_ASPECT_GET_CHECKPOINT_H
#define PCPLUS_ASPECT_GET_CHECKPOINT_H
/* Ordinary VM DS=SS stack only; IF must be enabled and DF clear. The recovered GET owner
 * runs synchronously. An intercepted native abort restores this caller before
 * returning ABORTED, without resuming the abandoned operand/editor/writeback.
 * The caller must retire field/display/WHEN leases before propagating abort.
 * No destination/stack pointer is retained after return. Nested entry refuses.
 * Does not catch direct dispatcher longjmp, CPU faults or foreign SS. */
enum {GET_NATIVE_OK,GET_NATIVE_ABORTED,GET_NATIVE_BUSY,GET_NATIVE_CONTEXT};
unsigned __cdecl runtime_get_native(void);
unsigned __cdecl runtime_get_native_active(void);
/* Nonzero generation advances only on admitted entry; rejected nesting retains it. */
unsigned __cdecl runtime_get_native_generation(void);
unsigned __cdecl runtime_get_native_aborted(void);
#endif
