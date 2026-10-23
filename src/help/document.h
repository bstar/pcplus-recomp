#ifndef PCPLUS_HELP_DOCUMENT_H
#define PCPLUS_HELP_DOCUMENT_H
#include "format.h"
#ifdef __WATCOMC__
#define HELP_DOC_CODE __far
#define HELP_DOC_CALL __cdecl
#else
#define HELP_DOC_CODE
#define HELP_DOC_CALL
#endif
enum {HELP_DOC_OK,HELP_DOC_PENDING,HELP_DOC_LINE,HELP_DOC_FOUND,HELP_DOC_END,
 HELP_DOC_ARGUMENT,HELP_DOC_FORMAT,HELP_DOC_IO,HELP_DOC_RANGE};
/* Reader owns its file/storage lifetime; it must be immutable during use.
 * Each call returns0 on success and the exact byte count in got. */
typedef unsigned (HELP_DOC_CODE HELP_DOC_CALL *help_read_at)(void *,unsigned long,unsigned char *,unsigned,unsigned *);
typedef struct help_document {
 help_read_at read;void *cookie;unsigned long bytes;
 help_header header;unsigned phase,index;
 unsigned long total,minimum;
} help_document;
typedef struct help_cursor {
 help_document *document;help_record record;unsigned topic,number;
 unsigned long offset,end;
 unsigned used,available,length;
 unsigned char buffer[80];char line[82];
} help_cursor;
typedef struct help_find {
 help_document *document;help_cursor cursor;
 unsigned active,stage,topic,anchor_topic,wrapped;unsigned long anchor_line;
 unsigned length,match_topic,match_line;
 char query[32];
} help_find;
unsigned HELP_DOC_CODE HELP_DOC_CALL help_document_begin(help_document *,help_read_at,void *,unsigned long);
/* At most one38-byte index read per admission step. */
unsigned HELP_DOC_CODE HELP_DOC_CALL help_document_step(help_document *);
/* At most two index reads; text remains streamed with32-bit file positions. */
unsigned HELP_DOC_CODE HELP_DOC_CALL help_cursor_begin(help_cursor *,help_document *,unsigned);
/* At most one80-byte read; complete lines are published only with LINE.
 * Lines require LF, allow CRLF and preserve CP437 bytes. Maximum80 columns. */
unsigned HELP_DOC_CODE HELP_DOC_CALL help_cursor_step(help_cursor *);
/* position0 includes the title; position1 begins with the first body line.
 * F3 can resume at match_line+1. One wrap visits the preceding prefix too. */
unsigned HELP_DOC_CODE HELP_DOC_CALL help_find_begin(help_find *,help_document *,const char *,unsigned,unsigned long);
unsigned HELP_DOC_CODE HELP_DOC_CALL help_find_step(help_find *);
void HELP_DOC_CODE HELP_DOC_CALL help_find_cancel(help_find *);
#endif
