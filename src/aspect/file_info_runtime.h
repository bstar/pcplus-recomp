#ifndef PCPLUS_ASPECT_FILE_INFO_RUNTIME_H
#define PCPLUS_ASPECT_FILE_INFO_RUNTIME_H
/* Separate temporary FILE ownership for ISFILE/GETFSIZE. Never consumes one
 * of the six numbered script streams. Final unwind closes an open temporary
 * if destination decoding aborts between native fopen and fclose. */
unsigned runtime_file_info_reset(void);
void runtime_file_info_finish(void);
extern unsigned runtime_file_info_live,runtime_file_info_segment;
#endif
