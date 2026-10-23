/* Source-owned PCHELP handoff and HLP index decoder. No original resources. */
#ifndef PCPLUS_HELP_FORMAT_H
#define PCPLUS_HELP_FORMAT_H
#define HELP_OK 0
#define HELP_ARGUMENT 1
#define HELP_FORMAT 2
#define HELP_RANGE 3
#define HELP_HEADER_BYTES 3
#define HELP_RECORD_BYTES 38
#define HELP_CONTEXT_BYTES 18
typedef struct { unsigned topics,lines; unsigned long text_start; } help_header;
typedef struct { char title[33];unsigned lines;unsigned long offset; } help_record;
/* The two offsets are in the parent's segment from the decimal far pointer.
 * ui_words preserves six native words without assigning unproved meanings. */
typedef struct { unsigned path_offset,title_offset,topic,ui_words[6]; } help_context;
unsigned help_pointer_parse(const char *,unsigned long *);
unsigned help_context_decode(const unsigned char *,unsigned,help_context *);
unsigned help_header_decode(const unsigned char *,unsigned,unsigned long,help_header *);
unsigned help_record_decode(const unsigned char *,unsigned,const help_header *,unsigned long,help_record *);
unsigned help_index_validate(const unsigned char *,unsigned,unsigned long);
unsigned help_topic_select(unsigned,unsigned);
#endif
