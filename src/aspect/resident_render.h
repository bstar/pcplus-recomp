#ifndef PCPLUS_ASPECT_RESIDENT_RENDER_H
#define PCPLUS_ASPECT_RESIDENT_RENDER_H
/* Maintained application RPC contract, not an original PCPlus structure.
 * ASIOv4 appends four words to the v3 descriptor: parent far entry offset,
 * segment, nonzero lease token, capability version. All four bind the guard.
 * Capability6 adds shared profile key output; capability5 added BIOS inheritance.
 * Older capability versions are rejected explicitly.
 * Far request AX=operation/BX=value, AX=result, all other registers/FLAGS
 * preserved. Each context runs DS=SS on its own checked stack slice. */
#define ASIO_VERSION_RENDER 4U
#define ASIO_V4_SIZE 48U
#if defined(ASPECT_EXTERNAL_RENDER)
#define ASPECT_RENDER_CAP_VERSION 7U
#else
#define ASPECT_RENDER_CAP_VERSION 6U
#endif
#define ASPECT_RENDER_CLIENT_MAGIC 0x5243U
#define ASPECT_RENDER_CLIENT_SIZE 10U
enum { ASPECT_RENDER_BEGIN=0, ASPECT_RENDER_EMIT=1, ASPECT_RENDER_END=2,
 ASPECT_RENDER_STATUS=3, ASPECT_RENDER_BREAK_POLICY=4,
 ASPECT_RENDER_BREAK_NOTICE=5, ASPECT_RENDER_SCRIPT_LABEL=6,
 ASPECT_RENDER_KEYBOARD_POLICY=7, ASPECT_RENDER_KEY=8,
 ASPECT_RENDER_PROGRAM_BEGIN=9, ASPECT_RENDER_PROGRAM_END=10 };
enum { ASPECT_RENDER_RAW_WAIT=0, ASPECT_RENDER_UNREAD=1,
 ASPECT_RENDER_SEND=2, ASPECT_RENDER_POLL=3, ASPECT_RENDER_ERROR=4,
 ASPECT_RENDER_RAW_NOW=5, ASPECT_RENDER_BREAK_VALUE=6,
 ASPECT_RENDER_LABEL_BYTE=7, ASPECT_RENDER_KEYBOARD_MODE=8,
 ASPECT_RENDER_KEY_DUPLEX=9 };
typedef struct aspect_render_client {
 unsigned magic,version,token,callback_offset,callback_segment;
} aspect_render_client;
typedef char aspect_render_client_size_check[sizeof(aspect_render_client)==ASPECT_RENDER_CLIENT_SIZE?1:-1];
/* Validate the parent's capability before UART I/O; attach only after the
 * actual child UART is ready. BEGIN receives a near client-record offset.
 * Parent derives its segment from the saved child SS=DS and validates the
 * current child PSP/MCB and callback extents. EMIT receives one mapped byte.
 * Parser continuations call RAW callbacks, never re-enter translation/matching.
 * Parent return codes0..14 are ASPECT runtime results; bridge-reserved codes
 * FFFB..FFFE map to invalid-state. Callback unread/send/poll return typed errors;
 * raw reads return byte/FFFF and ERROR reports any accompanying runtime error.
 * END retires callbacks; parent view adoption persists until ordinary return. */
unsigned __cdecl aspect_render_active(void);
unsigned __cdecl aspect_render_emit(unsigned byte);
/* FFFF selects the parent's current duplex;0..255 selects a rendering
 * snapshot override. No setting is committed by drawing the status row. */
unsigned __cdecl aspect_render_status(unsigned duplex);
/* One inherited raw duration per interpreter invocation; callback6 is admitted
 * only during this synchronous request, once, with the live UART lease. */
void __cdecl aspect_render_policy_reset(void);
unsigned __cdecl aspect_render_policy_inherit(void);
unsigned __cdecl aspect_render_keyboard_inherit(void);
unsigned __cdecl aspect_render_key(unsigned key);
/*0 begins a single owned cursor/notice bracket,1 ends it idempotently.
 * STATUS remains a separate operation; no child pointer crosses this API. */
unsigned __cdecl aspect_render_break_notice(unsigned end);
/* Synchronous scalar-byte pull; label is never a parent-dereferenced pointer. */
unsigned __cdecl aspect_render_script_label(const char *,unsigned duplex);
unsigned __cdecl aspect_render_finish(void);
#if defined(ASPECT_EXTERNAL_RENDER)
/* Capability7 only. The parent rejects rendering/callback requests until END.
 * END rechecks the real view and retires the lease even on a failed probe. */
unsigned __cdecl aspect_render_program_begin(unsigned save_screen);
unsigned __cdecl aspect_render_program_end(unsigned view_reset);
#if defined(ASPECT_EXTERNAL_UNWIND)
unsigned __cdecl aspect_render_program_active(void);
#endif
#endif
#endif
