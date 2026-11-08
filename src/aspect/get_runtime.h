#ifndef PCPLUS_ASPECT_GET_RUNTIME_H
#define PCPLUS_ASPECT_GET_RUNTIME_H
#include "get_field.h"
/* Attached-terminal editor owner, called within an admitted native GET
 * checkpoint. No source/output pointer survives a call. Width1..80; source
 * and commit target are82-byte far spans. Normal end follows ACCEPT/CANCEL;
 * commit is allowed only after successful ACCEPT retirement in the same native
 * generation. Error end discards output. Recovery after a matching caught abort
 * retires display before discarding abandoned WHEN bookkeeping. Failed cleanup
 * retains ownership for retry and blocks reuse; it never clears another owner. */
unsigned runtime_get_field_begin(unsigned,unsigned,unsigned,unsigned,unsigned,const unsigned char __far *);
unsigned runtime_get_field_poll(void);
unsigned runtime_get_field_phase(void);
/* Native field result after ACCEPT/CANCEL, before ending a canceled field. */
unsigned runtime_get_field_result(void);
unsigned runtime_get_field_end(unsigned);
/* Last presented physical cursor, cached before normal display retirement. */
unsigned runtime_get_field_position(void);
unsigned runtime_get_field_commit(unsigned char __far *);
unsigned runtime_get_field_recover(void);
unsigned runtime_get_field_active(void);
unsigned runtime_get_field_discard(void);
#endif
