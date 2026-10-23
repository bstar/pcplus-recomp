#ifndef PCPLUS_HOOK_EXCHANGE_H
#define PCPLUS_HOOK_EXCHANGE_H
#ifdef __WATCOMC__
#define HOOK_CODE __far
#define HOOK_CALL __cdecl
#else
#define HOOK_CODE
#define HOOK_CALL
#endif
#define HOOK_INTEGER_BYTES 20U
#define HOOK_STRING_COUNT 10U
#define HOOK_STRING_BYTES 810U
#define HOOK_PRM_BYTES 1264U
#define HOOK_EXCHANGE_BYTES 2094U
#define HOOK_KEY_TAIL_CAPACITY 48U
/* Packed segment:offset values, not linear addresses. Context is signed16.
 * Host unsigned long may be wider; values above32 bits are rejected. */
typedef struct hook_key_command {
 unsigned long integers,strings,prm;
 long context;
} hook_key_command;
enum {HOOK_OK,HOOK_ARGUMENT,HOOK_RANGE,HOOK_FORMAT,HOOK_STRING};
/* Pure bounded codec for original KEY-kind2 argument order. No dereferencing,
 * allocation, DOS EXEC, shell expansion or original helper admission. Failed
 * calls leave output unchanged. Output must be disjoint from input storage. */
unsigned HOOK_CODE HOOK_CALL hook_key_format(const hook_key_command *,char *,unsigned);
unsigned HOOK_CODE HOOK_CALL hook_key_parse(const char *,unsigned,hook_key_command *);
/* Validate segment/offset and20-bit spans and mutual non-aliasing of the three
 * typed banks. This does not prove PSP ownership or trust foreign memory. */
unsigned HOOK_CODE HOOK_CALL hook_key_spans(const hook_key_command *);
/* Maintained contiguous staging layout:20 raw integer bytes, ten81-byte string
 * slots,1264 opaque PRM bytes. It is not an original file/header format. Each
 * string slot must contain NUL; opaque tails and all other bits are preserved.
 * No PRM semantic validation or active settings application is performed.
 * Sources and destinations must be valid, mutually disjoint near extents. */
unsigned HOOK_CODE HOOK_CALL hook_exchange_pack(unsigned char *,unsigned,const unsigned char *,const unsigned char *,const unsigned char *);
unsigned HOOK_CODE HOOK_CALL hook_exchange_unpack(const unsigned char *,unsigned,unsigned char *,unsigned char *,unsigned char *);
#endif
