#ifndef PCPLUS_ASPECT_RUNTIME_H
#define PCPLUS_ASPECT_RUNTIME_H
/* Incremental native ASPECT composition for authored test fixtures. This is
 * not a complete or validated arbitrary-bytecode interpreter. The native
 * handlers retain unchecked indexing/frame arithmetic. Unsupported services
 * abort explicitly. Terminal scheduling and full command coverage remain open. */
enum { ASPECT_RUN_OK=0,ASPECT_RUN_OPEN,ASPECT_RUN_HEADER,ASPECT_RUN_UNSUPPORTED,
       ASPECT_RUN_FLOAT,ASPECT_RUN_IO,ASPECT_RUN_BUDGET,ASPECT_RUN_OPERAND,
       ASPECT_RUN_HEAP,ASPECT_RUN_STACK,ASPECT_RUN_STATE,ASPECT_RUN_DIVIDE_ZERO,ASPECT_RUN_ARITHMETIC_FAULT };
unsigned aspect_runtime_run(const char *path,unsigned step_limit);
extern unsigned runtime_integer_a[10],runtime_integer_b[128];
extern unsigned long runtime_longs[128];
extern unsigned runtime_steps,runtime_last_opcode,runtime_peak_live;
extern unsigned runtime_native_error_code,runtime_string_compare_result;
extern unsigned runtime_live,runtime_cleanup_count,runtime_close_count,runtime_abi_bad;
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
extern unsigned runtime_fail_after;
extern unsigned char runtime_string_snapshot[128][81];
#endif
#endif
