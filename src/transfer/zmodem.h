#ifndef PCPLUS_ZMODEM_H
#define PCPLUS_ZMODEM_H
#include "zmodem_wire.h"
#include "batch_header.h"
#include "zmodem_name.h"
#ifdef __WATCOMC__
#define ZM_FAR __far
#else
#define ZM_FAR
#endif
/* Explicit foreground owner. Callbacks service transport/cancel during waits
 * and writes. read returns byte or one of the three sentinel values below.
 * A zero-second read must poll without waiting and preserve unread bytes.
 * Other callbacks return zero on success, nonzero on failure; next returns
 * ZM_DONE only when enumeration is complete. Seek accepts offsets including EOF.
 * Received metadata size is advisory. commit must check close and installation
 * before returning success. abort/close must retain ambiguous ownership outside
 * this workspace and must never retry an uncertain physical close.
 */
enum { ZM_OK=0,ZM_DONE=1,ZM_ARGUMENT=2,ZM_IO,ZM_TIMEOUT,ZM_CANCEL,
 ZM_PROTOCOL,ZM_FILE,ZM_END_UNCONFIRMED };
#define ZM_WAIT 0xffffU
#define ZM_BROKEN 0xfffeU
#define ZM_ABORT 0xfffdU
typedef struct zm_ops {
 unsigned (ZM_FAR __cdecl *read_byte)(void *,unsigned seconds);
 unsigned (ZM_FAR __cdecl *write_wire)(void *,const void *,unsigned);
 unsigned (ZM_FAR __cdecl *next)(void *,char *,zw_u32 *);
 unsigned (ZM_FAR __cdecl *seek)(void *,zw_u32);
 unsigned (ZM_FAR __cdecl *read_file)(void *,void *,unsigned,unsigned *);
 unsigned (ZM_FAR __cdecl *close_source)(void *,unsigned complete);
 unsigned (ZM_FAR __cdecl *open_received)(void *,const batch_header_result *);
 unsigned (ZM_FAR __cdecl *write_received)(void *,const void *,unsigned);
 unsigned (ZM_FAR __cdecl *commit_received)(void *);
 unsigned (ZM_FAR __cdecl *abort_received)(void *);
} zm_ops;
/* Optional checked active-stage readback. Compare exactly count bytes at the
 * supplied offset without changing the append cursor. Return0 only for an
 * exact match, ZM_PROTOCOL for a mismatch, ZM_ABORT for cancellation,
 * ZM_BROKEN for transport failure, otherwise a storage failure. The
 * callback must service cancellation/transport and retain checked file owner
 * state on every exit. It is never called for unverified packet data. */
typedef unsigned (ZM_FAR __cdecl *zm_verify_received)(void *,zw_u32,const void *,unsigned);
typedef struct zm_session {
 const zm_ops *ops;void *context;
 /* owned: 0 resolved, 1 active, 2 source close failed (never called again). */
 unsigned status,cleanup_status,sending,owned,format,control,block,retries;
 unsigned phase,skipped,window,capacity,response_bps;
 zw_u32 position,size,files,bytes;
 /* Full bounded remote identity on receive; next() still supplies DOS83 on send. */
 char name[ZM_WIRE_NAME_MAX+1];
 zw_decoder decoder;
 unsigned char data[1024];
 /* Only consumed/CRC-accepted receive data can be acknowledged. Once handed
  * to the checked writer, its buffer may encode a response. A sender never
  * decodes payload packets, so its encoded output can use the same region.
  * 8KiB ZedZap RX plus standard 1KiB TX fits the existing exclusive arena. */
 union {unsigned char rx[ZW_RECEIVE_MAX],wire[ZW_RECEIVE_MAX];} io;
 zm_verify_received verify_received;
 /* Recovery frontier bounds repeated old packets without confusing verified
  * forward readback progress with newly accepted file bytes. */
 zw_u32 replay_verified;
} zm_session;
/* Caller provides the workspace, disjoint ops and durable callback context.
 * No static state or allocation. DOS near arguments, DS=SS; callbacks are far
 * so the engine/codec may later occupy a separate code segment. A session is
 * synchronous and non-reentrant. Receiver starts at offset zero in a new owned
 * stage; retransmission resumes that stage's verified offset. Existing files
 * may be skipped by open_received returning ZM_DONE, never overwritten here.
 * Sender uses bounded asynchronous windows only with CANFDX/CANOVIO; otherwise
 * ZCRCW packets. Receiver accepts all four endings.
 */
unsigned __cdecl zm_run(zm_session *,const zm_ops *,void *,unsigned sending);
/* Optional minimum carrier rate for a buffered serial modem, independently of
 * DTE speed. Zero preserves ordinary three-second protocol reads; a nonzero
 * floor must be at least300bps. Sender reply reads include worst-case quoted
 * outstanding bytes and frame/control overhead. The adapter must honor waits
 * beyond30 seconds while continuing cancellation and its verified-progress
 * watchdog. This does not change receive timing or confirm attempted output. */
unsigned __cdecl zm_run_link(zm_session *,const zm_ops *,void *,unsigned sending,unsigned response_bps);
/* Explicit receive credit1..8192; zero retains the historical8192 offer.
 * Sending requires zero credit and keeps peer negotiation unchanged. This
 * requests a sender checkpoint policy, not a smaller decoder workspace: peers
 * ignoring the offer may still send valid packets up to8192 bytes. Invalid
 * policy returns ZM_ARGUMENT before touching the session or callbacks. */
unsigned __cdecl zm_run_profile(zm_session *,const zm_ops *,void *,unsigned sending,
 unsigned response_bps,unsigned receive_credit);
/* Explicit opt-in for checked stale/overlapping active-file data. Legacy APIs
 * retain their existing mismatch recovery. Sending requires a null verifier.
 * Old data never advances accepted progress; only a matching stored prefix
 * followed by checked appended bytes can extend the verified position. */
unsigned __cdecl zm_run_checked_profile(zm_session *,const zm_ops *,void *,unsigned sending,
 unsigned response_bps,unsigned receive_credit,zm_verify_received);
#endif
