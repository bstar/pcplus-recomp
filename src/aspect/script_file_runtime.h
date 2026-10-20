#ifndef PCPLUS_ASPECT_SCRIPT_FILE_RUNTIME_H
#define PCPLUS_ASPECT_SCRIPT_FILE_RUNTIME_H
/* Near native FILE prefix. Only this adapter owns the real CRT FILE pointer. */
typedef struct aspect_script_file_prefix {
 unsigned char *cursor;
 int remaining;
 unsigned char *base;
 unsigned char flags,descriptor;
} aspect_script_file_prefix;
enum { ASPECT_SCRIPT_FILE_SLOTS=6, ASPECT_SCRIPT_FILE_EOF=16,
       ASPECT_SCRIPT_FILE_ERROR=32, ASPECT_SCRIPT_FILE_TEXT=128 };
extern aspect_script_file_prefix *runtime_script_file_slots[ASPECT_SCRIPT_FILE_SLOTS];
extern aspect_script_file_prefix runtime_script_file_fallback;
extern unsigned runtime_script_file_last,runtime_script_file_keep_crlf;
extern unsigned char runtime_script_file_mode_flags[256];
extern char *runtime_script_file_mode_pointer;
extern unsigned runtime_script_file_live,runtime_script_file_peak;
extern unsigned runtime_script_file_open_calls,runtime_script_file_close_calls;
extern unsigned runtime_script_file_cleanup_errors;
unsigned runtime_script_files_reset(void);
void runtime_script_files_finish(void);
aspect_script_file_prefix *runtime_script_file_open(const char *,const char *);
int runtime_script_file_close(aspect_script_file_prefix *);
int runtime_script_file_flush(aspect_script_file_prefix *);
int runtime_script_file_getc(aspect_script_file_prefix *);
char *runtime_script_file_gets(char *,int,aspect_script_file_prefix *);
int runtime_script_file_putc(int,aspect_script_file_prefix *);
int runtime_script_file_puts(const char *,aspect_script_file_prefix *);
unsigned runtime_script_file_read(void *,unsigned,unsigned,aspect_script_file_prefix *);
unsigned runtime_script_file_write(const void *,unsigned,unsigned,aspect_script_file_prefix *);
int runtime_script_file_seek(aspect_script_file_prefix *,long,int);
long runtime_script_file_tell(aspect_script_file_prefix *);
#if defined(ASPECT_EXTERNAL_PROCESS)
/* Flush pending output, retain real CRT owners/prefixes/positions and list
 * private descriptors for the DOS inheritance bracket. No stream is closed. */
unsigned runtime_script_files_external_begin(unsigned *,unsigned *);
unsigned runtime_script_files_external_end(void);
#endif
#endif
