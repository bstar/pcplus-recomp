#ifndef PCPLUS_VIEWER_SESSION_H
#define PCPLUS_VIEWER_SESSION_H
/* Foreground DS=SS, one banked internal viewer. Caller owns a stable disjoint
 * far character page and near token until stop resolves. Geometry1..132 by
 *1..49. Input path is a readable64-byte near DOS83 span. No UI/video calls.
 * Start opens/claims once. Each loading step performs at most one read256 or
 * seek; decoding is a separate bounded step. No hidden read/seek loops.
 * Read-ahead is retained across forward pages. Backward/Home seeks discard it.
 *64 cached offsets accelerate navigation; older pages rescan incrementally
 * from offset0. No silent100-page cap. Page numbers are zero-based32-bit.
 * Argument/busy/top/end refusals preserve state/page. Stop cancels any phase;
 * close/release uncertainty retains ownership and forbids reset/retry.
 * Caller page must not alias any other application's owner/storage allocation.
 * Session errors retain underlying file/decode status; inspect file owner for
 * primary DOS and secondary cleanup errors. No child/exit policy is implied.
 */
enum { VS_OK=0,VS_ARGUMENT,VS_BUSY,VS_STATE,VS_TOP,VS_END,VS_IO,
 VS_DECODE,VS_RECOVERY,VS_INVARIANT };
enum { VS_IDLE=0,VS_LOADING,VS_READY,VS_FAILED,VS_UNCERTAIN,VS_CLOSED };
enum { VS_HOME=0,VS_PREVIOUS,VS_NEXT };
typedef struct viewer_session_snapshot {
 unsigned phase,error,file_status,decode_status,owned,pending_seek;
 unsigned buffered,consumed,eof,width,rows;
 unsigned long page,target,start,next,read_position,cache_first,cache_last;
} viewer_session_snapshot;
unsigned __far __cdecl viewer_session_begin(const char *,void *,
 unsigned char __far *,unsigned,unsigned,unsigned);
unsigned __far __cdecl viewer_session_step(void);
unsigned __far __cdecl viewer_session_move(unsigned);
unsigned __far __cdecl viewer_session_stop(void);
unsigned __far __cdecl viewer_session_inspect(viewer_session_snapshot *);
#endif
