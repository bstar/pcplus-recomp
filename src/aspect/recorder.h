#ifndef PCPLUS_ASPECT_RECORDER_H
#define PCPLUS_ASPECT_RECORDER_H
/* Source-owned recorder. Initialize the session to zero before first start.
 * Callback code may live in a DOS far code bank; arguments remain near DS=SS.
 * Output is unpublished ASP scratch storage. The caller publishes it only
 * after stop returns OK; failed/cancelled output must be discarded.
 * A successful start admission transfers one close obligation, even if its
 * initial write fails. stop/cancel closes exactly once. close consumes the
 * stream even on error. This component neither opens nor publishes a path.
 */
#ifdef __WATCOMC__
#define AR_FAR __far
#define AR_CALL __cdecl
#else
#define AR_FAR
#define AR_CALL
#endif
enum {AR_OK=0,AR_ARGUMENT,AR_STATE,AR_WRITE,AR_CLOSE,AR_CANCELLED};
typedef struct aspect_recorder_ops {
 unsigned (AR_FAR AR_CALL *write)(void *,const void *,unsigned,unsigned *);
 unsigned (AR_FAR AR_CALL *close)(void *);
} aspect_recorder_ops;
typedef struct aspect_recorder {
 aspect_recorder_ops ops;
 void *context;
 unsigned started,active,owned,busy,status,write_error,close_error;
 unsigned tx_count,rx_count,timeout;
 unsigned char tx[40],rx[16];
 unsigned long transmitted_bytes,received_bytes,source_bytes;
} aspect_recorder;
unsigned AR_FAR AR_CALL aspect_recorder_start(aspect_recorder *,const aspect_recorder_ops *,void *,unsigned timeout);
/* Explicit successfully transmitted bytes, including expanded bindings. Keys
 * do not erase already transmitted data: wire backspace is recorded literally.
 * Feed <=40 TX or <=16 RX bytes per call, chunking larger observed spans.
 * Prompts retain the last16 RX bytes and native leading-control/NUL filtering.
 */
unsigned AR_FAR AR_CALL aspect_recorder_transmit(aspect_recorder *,const void *,unsigned);
unsigned AR_FAR AR_CALL aspect_recorder_receive(aspect_recorder *,const void *,unsigned);
unsigned AR_FAR AR_CALL aspect_recorder_flush(aspect_recorder *);
unsigned AR_FAR AR_CALL aspect_recorder_stop(aspect_recorder *);
unsigned AR_FAR AR_CALL aspect_recorder_cancel(aspect_recorder *);
#endif
