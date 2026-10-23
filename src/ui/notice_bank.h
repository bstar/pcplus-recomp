/* Far bridges run in the near CRT/callback code segment. Pointers still belong
 * to the shared DGROUP; stack pointers require DS=SS. Callback types stay near
 * and must refer to that CRT segment, not the notice bank. */
#ifndef PCPLUS_NOTICE_BANK_H
#define PCPLUS_NOTICE_BANK_H
#include "notice.h"
#include <dos.h>
int __far __cdecl notice_bank_int86(int,union REGS *,union REGS *);
void * __far __cdecl notice_bank_memcpy(void *,const void *,unsigned);
void * __far __cdecl notice_bank_memset(void *,int,unsigned);
void __far * __far __cdecl notice_bank_fmalloc(unsigned);
void __far __cdecl notice_bank_ffree(void __far *);
void __far * __far __cdecl notice_bank_fmemset(void __far *,int,unsigned);
unsigned __far __cdecl notice_bank_service(notice_service);
unsigned __far __cdecl notice_bank_sound(notice_sound,unsigned);
#ifndef NOTICE_BANK_IMPLEMENTATION
#define int86 notice_bank_int86
#define memcpy notice_bank_memcpy
#define memset notice_bank_memset
#define _fmalloc notice_bank_fmalloc
#define _ffree notice_bank_ffree
#define _fmemset notice_bank_fmemset
#define NOTICE_SERVICE_CALL(callback) notice_bank_service(callback)
#define NOTICE_SOUND_CALL(callback,kind) notice_bank_sound(callback,kind)
#endif
#endif
