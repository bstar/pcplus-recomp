#ifndef PCPLUS_ASPECT_RESIDENT_RENDER_H
#define PCPLUS_ASPECT_RESIDENT_RENDER_H
/* Maintained application RPC contract, not an original PCPlus structure.
 * ASIOv4 appends four words to the v3 descriptor: parent far entry offset,
 * segment, nonzero lease token, capability version. All four bind the guard.
 * Capability2 adds STATUS; capability1 descriptors are rejected explicitly.
 * Far request AX=operation/BX=value, AX=result, all other registers/FLAGS
 * preserved. Each context runs DS=SS on its own checked stack slice. */
#define ASIO_VERSION_RENDER 4U
#define ASIO_V4_SIZE 48U
#define ASPECT_RENDER_CAP_VERSION 2U
#define ASPECT_RENDER_CLIENT_MAGIC 0x5243U
#define ASPECT_RENDER_CLIENT_SIZE 10U
enum { ASPECT_RENDER_BEGIN=0, ASPECT_RENDER_EMIT=1, ASPECT_RENDER_END=2,
 ASPECT_RENDER_STATUS=3 };
enum { ASPECT_RENDER_RAW_WAIT=0, ASPECT_RENDER_UNREAD=1,
 ASPECT_RENDER_SEND=2, ASPECT_RENDER_POLL=3, ASPECT_RENDER_ERROR=4,
 ASPECT_RENDER_RAW_NOW=5 };
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
unsigned __cdecl aspect_render_finish(void);
#endif
