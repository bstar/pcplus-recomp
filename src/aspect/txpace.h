#ifndef PCPLUS_ASPECT_TXPACE_H
#define PCPLUS_ASPECT_TXPACE_H
/* Maintained cooperative calibration; exact native6B72 remains its busyloop.
 * DS=SS, nearcdecl, no UART ownership or raw receive/parser calls here. */
enum { ASPECT_TXPACE_OK=0,ASPECT_TXPACE_ARGUMENT=1,ASPECT_TXPACE_STATE=2,
 ASPECT_TXPACE_IF=3,ASPECT_TXPACE_CLOCK=4,ASPECT_TXPACE_LIMIT=5,
 ASPECT_TXPACE_STEP=6,ASPECT_TXPACE_RESOLUTION=7 };
enum { ASPECT_TXPACE_ALIGN=1,ASPECT_TXPACE_BEFORE_MEASURE=2,
 ASPECT_TXPACE_AFTER_MEASURE=3,ASPECT_TXPACE_DELAY=4 };
#define ASPECT_TXPACE_CHUNK 512U
#define ASPECT_TXPACE_MAX_CHUNKS 7039U
#define ASPECT_TXPACE_ALIGN_POLLS 65535U
#define ASPECT_TXPACE_DAY 1573040UL
typedef unsigned (*aspect_txpace_step_fn)(unsigned);
void aspect_txpace_reset(void);
unsigned aspect_txpace_ready(void);
unsigned aspect_txpace_prepare(aspect_txpace_step_fn);
unsigned aspect_txpace_prepare_bounded(aspect_txpace_step_fn,unsigned);
unsigned aspect_txpace_delay(unsigned,aspect_txpace_step_fn);
extern unsigned aspect_txpace_count,aspect_txpace_step_error;
/* Backend ABI for source-owned assembly and isolated service diagnostics. */
unsigned aspect_txpace_flags(void);
void aspect_txpace_restore_if(unsigned);
unsigned long aspect_txpace_ticks(void);
void aspect_txpace_native_one(void);
#endif
