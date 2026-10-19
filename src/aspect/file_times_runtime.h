#ifndef PCPLUS_ASPECT_FILE_TIMES_RUNTIME_H
#define PCPLUS_ASPECT_FILE_TIMES_RUNTIME_H
/* Separate temporary stdio owner with an eight-byte native FILE prefix.
 * Timestamp commands do not borrow numbered script slots. */
unsigned runtime_file_times_reset(void);
void runtime_file_times_finish(void);
extern unsigned runtime_file_times_live;
#endif
