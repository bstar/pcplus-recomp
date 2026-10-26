#ifndef PCPLUS_DIRECTORY_READER_H
#define PCPLUS_DIRECTORY_READER_H
#include "directory_dos.h"
/* Incremental foreground-only read owner. DOS16 near cdecl, DS=SS. Callers
 * service serial/keyboard between steps; the reader never polls either.
 * The separate staging/destination pages are far, scratch is near512 bytes.
 * One step issues at most one DOS operation and copies at most1394 bytes.
 * This does not establish a bound on a DOS driver call's execution time. */
#define DIRECTORY_READER_CHUNK 512U
#define DIRECTORY_READER_PENDING 256U
#define DIRECTORY_READER_CANCELLED 6U
#define DIRECTORY_READER_BUSY 7U
#define DIRECTORY_READER_MAGIC 0x4452U
#ifdef DIRECTORY_READER_FAR
#define DIRECTORY_READER_CALL __far __cdecl
#else
#define DIRECTORY_READER_CALL __cdecl
#endif
enum { DIRECTORY_READER_IDLE=0, DIRECTORY_READER_READ,
 DIRECTORY_READER_PROBE, DIRECTORY_READER_CLOSE, DIRECTORY_READER_DONE,
 DIRECTORY_READER_RECOVERY };
typedef struct directory_reader {
 unsigned magic,phase,status,dos_error,close_error,bytes_processed;
 unsigned first_entry,count,handle_open;
 int handle;
 directory_dos_page_data __far *stage;
 directory_dos_page_data __far *destination;
 unsigned char *scratch;
} directory_reader;
/* First initialization requires zeroed caller storage. Reinitialization of an
 * active or uncertain-close owner refuses without losing its handle/state. */
unsigned DIRECTORY_READER_CALL directory_reader_initialize(directory_reader *);
/* Explicit original-format path, entry1..200. Opens read-only immediately;
 * no path is retained or resolved again. All state/page/scratch/path extents
 * must be disjoint and nonwrapping, including physical far-pointer aliases.
 * Pages must fit a segment and the8086 address space. Destination stays exact
 * until full23050-byte read, suffix probe and successful close. Failure or
 * cancellation never publishes stage bytes. External concurrent file changes
 * are not excluded; an open handle is not an atomic file snapshot. */
unsigned DIRECTORY_READER_CALL directory_reader_begin(directory_reader *,const char *,unsigned,
 directory_dos_page_data __far *,directory_dos_page_data __far *,unsigned char *);
/* PENDING means call again after servicing the terminal. Terminal states are
 * idempotent. Short successful reads are retained. Failed close enters RECOVERY
 * and is never blindly retried: the DOS handle may already have been released.
 * Caller retains ownership information for explicit session-level recovery. */
unsigned DIRECTORY_READER_CALL directory_reader_step(directory_reader *);
/* Mark canceled; the next step closes. Repeated cancel never hides an earlier
 * IO error, reopens, retries a close, or publishes a page. */
unsigned DIRECTORY_READER_CALL directory_reader_cancel(directory_reader *);
#endif
