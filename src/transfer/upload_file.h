#ifndef PCPLUS_UPLOAD_FILE_H
#define PCPLUS_UPLOAD_FILE_H
/* Maintained read-only DOS source ownership. Near cdecl, DS=SS, unsigned16.
 * Fixed native tokens1(discovery)/2(binary) belong to ONE foreground owner;
 * they are not generation-tagged capabilities across successive sessions.
 */
typedef unsigned upload_file_status;
enum { UF_OK=0,UF_ARGUMENT,UF_BUSY,UF_STATE,UF_INSPECT,UF_OPEN,UF_SEEK,
 UF_READ,UF_SHRINK,UF_CLOSE,UF_INCOMPLETE,UF_RECOVERY };
enum { UF_IDLE=0,UF_READY,UF_DISCOVERY,UF_READING,UF_CLOSED,UF_COMPLETE,
 UF_ABORTED,UF_BROKEN,UF_UNCERTAIN };
typedef struct upload_file_result {
 unsigned state,first_status,dos_error,close_error;
 unsigned handle_open,handle_uncertain,discovery_open,binary_open;
 unsigned read_calls,close_calls;
 unsigned long size,consumed;
 char path[64];
} upload_file_result;
extern upload_file_result upload_source_result;
/* Call at application startup; later resets only resolved ownership. An
 * ambiguous DOS close can never be forgotten/repeated by initialize. */
upload_file_status __cdecl upload_source_initialize(void);
/* Normalized explicit ASCII DOS8.3 path<=63, no devices/directory/volume.
 * Preflight read-only open + DWORD seekEND/START. No source write/delete API. */
upload_file_status __cdecl upload_source_begin(const char *path);
/* Same normalized path; exact modes "r" ->1, "rb" ->2. Discoveryclose1 is
 * logical only; rb reuses the preflight physical handle at offset0 once. */
unsigned __cdecl upload_source_open(const char *path,const char *mode);
/* Only size1,count0..10240,token2. Near output span must not wrap or alias
 * ownership. EOF0 only at declared size; errors/earlyEOF ->ffff and latched
 * status. Positive short reads are conservatively treated as source shrink.
 * Binary bytes including1Ah are untouched; consumed is fullDWORD. */
unsigned __cdecl upload_source_read(void *data,unsigned size,unsigned count,unsigned token);
/* Checked reposition within the frozen size, including EOF. Reading binary
 * owner only; invalid range leaves the snapshot unchanged. DOS error or an
 * unexpected returned position poisons the owner; consumed advances only on
 * exact success. No reopen, reset of failure history or source mutation. */
upload_file_status __cdecl upload_source_seek(unsigned long offset);
/* Token1 logical. Token2 closes exactly once; repeats never issue another DOS
 * close. Closing before complete consumption latchesUF_INCOMPLETE. */
unsigned __cdecl upload_source_close(unsigned token);
upload_file_status __cdecl upload_source_finish(void);
upload_file_status __cdecl upload_source_abort(void);
#endif
