/* Independent resident CRT oracle for the authored bank memory primitives. */
#include <string.h>
void __far * __far __cdecl meta_reference_copy(void __far *d,const void __far *s,unsigned n)
{return _fmemcpy(d,s,n);}
void __far * __far __cdecl meta_reference_fill(void __far *d,int c,unsigned n)
{return _fmemset(d,c,n);}
int __far __cdecl meta_reference_compare(const void __far *a,const void __far *b,unsigned n)
{return _fmemcmp(a,b,n);}
int __far __cdecl meta_reference_string(const char __far *a,const char __far *b)
{return _fstrcmp(a,b);}
