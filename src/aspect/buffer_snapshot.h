#ifndef PCPLUS_BUFFER_SNAPSHOT_H
#define PCPLUS_BUFFER_SNAPSHOT_H
/* Exact512-byte snapshots; no open backup descriptor crosses PROGRAM EXEC. */
unsigned aspect_buffer_snapshot_begin(unsigned);
unsigned aspect_buffer_snapshot_save(unsigned,const unsigned char *);
unsigned aspect_buffer_snapshot_seal(void);
unsigned aspect_buffer_snapshot_compare(unsigned,const unsigned char *);
unsigned aspect_buffer_snapshot_finish(void);
unsigned aspect_buffer_snapshot_discard(void);
unsigned aspect_buffer_snapshot_active(void);
const char *aspect_buffer_snapshot_path(void);
#endif
