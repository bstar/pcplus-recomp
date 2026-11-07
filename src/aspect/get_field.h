#ifndef PCPLUS_ASPECT_GET_FIELD_H
#define PCPLUS_ASPECT_GET_FIELD_H
#define GET_FIELD_MAX 81
#define GET_FIELD_BUFFER 82
enum {GET_FIELD_ACTIVE=0,GET_FIELD_ACCEPT,GET_FIELD_CANCEL,GET_FIELD_ARGUMENT,GET_FIELD_BELL};
typedef struct get_field_state {
 unsigned cookie,phase,cursor,insert,full,saved_shape,result,width,numeric,masked,visible;
 unsigned char field[GET_FIELD_MAX];
} get_field_state;
/* Serviced model of original79D4 with GET's string/numeric callbacks.
 * No blocking keyboard/BIOS/DOS/UART services; DS=SS, far spans nonwrapping.
 * Width1..81 and initial length<=width are maintained safety guards, not native
 * validation. NULL initial means blank; otherwise supply an82-byte buffer.
 * Commit/render targets must be82-byte buffers disjoint from state. Cancel
 * never commits. The future owner must restore cursor visibility to visible.
 */
unsigned __far __cdecl get_field_begin(get_field_state __far *,const unsigned char __far *,unsigned,unsigned,unsigned,unsigned,unsigned);
unsigned __far __cdecl get_field_key(get_field_state __far *,unsigned);
unsigned __far __cdecl get_field_commit(const get_field_state __far *,unsigned char __far *);
unsigned __far __cdecl get_field_render(const get_field_state __far *,unsigned char __far *);
unsigned __far __cdecl get_field_shape(const get_field_state __far *);
unsigned __far __cdecl get_field_visible(const get_field_state __far *);
#endif
