/* This translation unit must remain in _TEXT with the near CRT and callbacks. */
#include <dos.h>
#include <malloc.h>
#include <string.h>
#define NOTICE_BANK_IMPLEMENTATION
#include "notice_bank.h"
int __far __cdecl notice_bank_int86(int number,union REGS *in,union REGS *out)
{return int86(number,in,out);}
void * __far __cdecl notice_bank_memcpy(void *to,const void *from,unsigned count)
{return memcpy(to,from,count);}
void * __far __cdecl notice_bank_memset(void *to,int byte,unsigned count)
{return memset(to,byte,count);}
void __far * __far __cdecl notice_bank_fmalloc(unsigned count)
{return _fmalloc(count);}
void __far __cdecl notice_bank_ffree(void __far *pointer)
{_ffree(pointer);}
void __far * __far __cdecl notice_bank_fmemset(void __far *to,int byte,unsigned count)
{return _fmemset(to,byte,count);}
unsigned __far __cdecl notice_bank_service(notice_service callback)
{return callback();}
unsigned __far __cdecl notice_bank_sound(notice_sound callback,unsigned kind)
{return callback(kind);}
