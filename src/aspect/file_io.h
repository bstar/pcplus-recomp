#ifndef PCPLUS_ASPECT_FILE_IO_H
#define PCPLUS_ASPECT_FILE_IO_H
#include <stdio.h>

/* Native small-model FILE prefix used by recovered byte/word readers.
 * The maintained bridge owns the real stdio stream and a bounded read window.
 * DOS layout is checked at compile time; DS=SS and near pointers are required. */
typedef struct aspect_file_prefix {
    unsigned char *cursor;
    int remaining;
    unsigned reserved;
    unsigned char flags,padding;
} aspect_file_prefix;

enum { ASPECT_FILE_OK=0,ASPECT_FILE_ARGUMENT,ASPECT_FILE_STATE,
       ASPECT_FILE_IO,ASPECT_FILE_RANGE,ASPECT_FILE_EOF,ASPECT_FILE_TRUNCATED };
enum { ASPECT_FILE_WINDOW=256,ASPECT_FILE_EOF_FLAG=0x10,ASPECT_FILE_ERROR_FLAG=0x20 };
typedef struct aspect_file {
    aspect_file_prefix native;
    FILE *handle;
    unsigned buffered,magic,status;
    unsigned char window[ASPECT_FILE_WINDOW];
} aspect_file;

/* Initialize before open; init on an active owner is forbidden by contract. */
unsigned aspect_file_init(aspect_file *file);
unsigned aspect_file_open(aspect_file *file,const char *path);
unsigned aspect_file_close(aspect_file *file);
/* Logical position accounts for unread native-window bytes. -1 means failure. */
long aspect_file_tell(aspect_file *file);
/* Origin0/1 (SET/CUR), signed32 offsets; validates target before repositioning.
 * Unsupported origins/ranges preserve logical position. EOF clears on success. */
int aspect_file_seek(aspect_file *file,long offset,unsigned origin);
/* fread-compatible argument order. Returns complete elements; partial bytes
 * may have been consumed/written. status distinguishes EOF/truncation/error.
 * Callers of native unchecked operand readers must abort on a short read. */
unsigned aspect_file_read(void *destination,unsigned size,unsigned count,aspect_file *file);
/* Called by native reader only after it decrements remaining from0 to-1.
 * AX return is byte0..255 or FFFF (-1). Does not itself perform nonlocal unwind. */
int aspect_file_refill(aspect_file *file);
#endif
