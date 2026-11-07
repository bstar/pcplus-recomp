#ifndef PCPLUS_HELP_EMBEDDED_H
#define PCPLUS_HELP_EMBEDDED_H
/* Same authored-resource viewer as PCHELP, linked into a small-model caller.
 * DS=SS; saved_frame is the caller's immutable2000-word displayed VGA frame.
 * No extra DOS process, stack or screen allocation; no caller-frame writes. */
unsigned help_embedded_open(const char *,const char *,unsigned,unsigned,unsigned,unsigned,const unsigned short *);
#endif
