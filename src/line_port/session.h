#ifndef LOC_LINE_PORT_SESSION_H
#define LOC_LINE_PORT_SESSION_H
#include "view.h"
/* Caller owns this near allocation and admits one foreground transaction.
 * Native selection uses a serial adapter singleton, so calls must not nest.
 * No hardware or file operations occur in this module. */
typedef struct line_port_session {
 line_port_values selected,initial;
 unsigned phase,save,notice,quiesce_requests;
} line_port_session;
enum { LINE_PORT_EDIT=1,LINE_PORT_REQUEST,LINE_PORT_SAVED,LINE_PORT_DONE };
enum { LINE_PORT_CHANGED=0,LINE_PORT_ARGUMENT,LINE_PORT_UNSUPPORTED,
 LINE_PORT_APPLY_FAILED,LINE_PORT_SAVE_FAILED,LINE_PORT_LOCKED };
/* Begin a zeroed or completed owner with the actual transport in native indices.
 * An uncertain-save lock cannot be cleared by begin(). COM1..4 are
 * currently supported. Unsupported values reject without changing the owner. */
unsigned __far __cdecl line_port_session_begin(line_port_session *,const line_port_values *);
/* Key input while editing. Escape requests session application; Alt-S requests
 * save then apply. Native invalid-key bell is returned in bit0; port quiesce
 * requests in bit1. Hardware quiescing belongs to the later foreground commit. */
unsigned __far __cdecl line_port_session_key(line_port_session *,unsigned key,unsigned *events);
/* Publish a persistence result only after an Alt-S request. Success means the
 * exact staged prefix is saved; a subsequent apply failure must not be shown
 * as an unsaved edit. Uncertain IO locks the owner for explicit recovery. */
unsigned __far __cdecl line_port_session_saved(line_port_session *,unsigned error,unsigned uncertain);
/* Publish a drained handoff result. Failure keeps the staged selection for
 * retry. A saved selection retries apply without silently repeating disk IO. */
unsigned __far __cdecl line_port_session_applied(line_port_session *,unsigned error);
/* Snapshot a request. Outputs are committed only for a valid ready request;
 * save0 means session only or already saved. Caller supplies distinct storage. */
unsigned __far __cdecl line_port_session_request(const line_port_session *,line_port_values *,unsigned *save);
#endif
