#ifndef PCPLUS_META_FRONT_H
#define PCPLUS_META_FRONT_H
#define META_KEYS_ACTION 126U
unsigned __far __cdecl meta_front_event(unsigned,unsigned,unsigned short __far *);
unsigned __far __cdecl meta_front_cursor(void);
unsigned __far __cdecl meta_front_shape(void);
unsigned __far __cdecl meta_front_owned(void);
unsigned __far __cdecl meta_front_pending(void);
unsigned __far __cdecl meta_front_exec_allowed(void);
#endif
