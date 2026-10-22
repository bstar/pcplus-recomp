#ifndef PCPLUS_RECORDING_FILE_H
#define PCPLUS_RECORDING_FILE_H
#include "../aspect/recorder.h"
enum { RF_OK=0,RF_ARGUMENT,RF_BUSY,RF_STATE,RF_CANONICAL,RF_INSPECT,RF_CONFLICT,
 RF_CREATE,RF_WRITE,RF_CLOSE,RF_PUBLISH,RF_CLEANUP,RF_RELEASE,RF_RECOVERY,RF_CANCELLED,RF_OVERFLOW };
enum { RF_IDLE=0,RF_RECORDING,RF_SAVED,RF_CANCELLED_STATE,RF_FAILED,RF_RECOVERY_STATE };
enum { RF_NEW=1,RF_REPLACE=2 };
struct recording_file;
/* DOS error conventions:0 success,2 missing,80 exclusive-create collision.
 * Create/rename must refuse existing destinations. Close error is ambiguous;
 * the library never retries it. Callbacks are far, arguments near DS=SS.
 * Reserve/release bind this stable owner to the shared canonical sink checks.
 */
typedef struct recording_file_ops {
 unsigned (AR_FAR AR_CALL *canonical)(void *,const char *,char *);
 unsigned (AR_FAR AR_CALL *attributes)(void *,const char *,unsigned *);
 unsigned (AR_FAR AR_CALL *create)(void *,const char *,int *);
 unsigned (AR_FAR AR_CALL *write)(void *,int,const void *,unsigned,unsigned *);
 unsigned (AR_FAR AR_CALL *close)(void *,int);
 unsigned (AR_FAR AR_CALL *rename)(void *,const char *,const char *);
 unsigned (AR_FAR AR_CALL *remove)(void *,const char *);
 unsigned (AR_FAR AR_CALL *reserve)(void *,struct recording_file *);
 unsigned (AR_FAR AR_CALL *release)(void *,struct recording_file *);
} recording_file_ops;
/* Initialize to zero once. Thereafter callers may inspect but not mutate it.
 * As with the recorder core, callers supply valid argument strings/spans;
 * input data must not alias the mutable ownership/recorder state.
 * Leaf names are siblings of the fixed canonical target; no CWD dependence.
 * A recovery state may retain a complete stage or original backup. Never
 * discard an original backup after failed restoration. No power-loss,
 * external-process lock or concurrent namespace-remapping guarantee.
 */
typedef struct recording_file {
 recording_file_ops ops;
 void *context;
 aspect_recorder recorder;
 unsigned state,status,dos_error,close_error,cleanup_error,publish_error,restore_error,reservation_error;
 unsigned mode,busy,claimed,stage_owned,backup_owned,published,handle_state,sequence,directory_length;
 int handle;
 char target[128],stage[13],backup[13];
} recording_file;
unsigned AR_FAR AR_CALL recording_file_begin(recording_file *,const recording_file_ops *,void *,const char *,unsigned mode,unsigned timeout);
unsigned AR_FAR AR_CALL recording_file_transmit(recording_file *,const void *,unsigned);
unsigned AR_FAR AR_CALL recording_file_receive(recording_file *,const void *,unsigned);
unsigned AR_FAR AR_CALL recording_file_flush(recording_file *);
unsigned AR_FAR AR_CALL recording_file_stop(recording_file *);
unsigned AR_FAR AR_CALL recording_file_cancel(recording_file *);
/* Explicitly discard a certain owned stage / clean a published backup. Never
 * retries an uncertain close or removes a backup after failed restoration.
 * First and secondary errors remain observable even after cleanup succeeds.
 */
unsigned AR_FAR AR_CALL recording_file_cleanup(recording_file *);
/* Pure canonical probe for capture_file_reserve. Valid while owner is claimed,
 * including during create/publication; it does not enter any filesystem API. */
unsigned AR_FAR AR_CALL recording_file_conflict(const recording_file *,const char *);
#endif
