/* Diagnostic only; product runtime is compared with actual resident Watcom
 * CRT routines, separately compiled without the bank's aliases. */
#include <string.h>
void __far * __far __cdecl meta_reference_copy(void __far *,const void __far *,unsigned);
void __far * __far __cdecl meta_reference_fill(void __far *,int,unsigned);
int __far __cdecl meta_reference_compare(const void __far *,const void __far *,unsigned);
int __far __cdecl meta_reference_string(const char __far *,const char __far *);
static int sign(int v){return (v>0)-(v<0);}
#define CHECK(x) do {++checks;if(!(x))return __LINE__;}while(0)
unsigned __far __cdecl meta_bank_memory_probe(unsigned __far *total)
{
 static const unsigned lengths[]={0,1,2,3,7,16,128,255};
 static const unsigned char fills[]={0,128,255};
 static const unsigned char values[]={0,1,65,127,128,224,255};
 unsigned checks=0,i,j,n,off,k,a,b;unsigned char src[260],actual[260],expected[260];
 for(i=0;i<260;++i)src[i]=(unsigned char)(i*71+9);
 for(off=0;off<4;++off)for(k=0;k<8;++k){
  n=lengths[k];memset(actual,0x5a,260);memset(expected,0x5a,260);
  CHECK(_fmemcpy(actual+off,src+off,n)==actual+off);
  CHECK(meta_reference_copy(expected+off,src+off,n)==expected+off);
  for(i=0;i<260;++i)CHECK(actual[i]==expected[i]);
  for(j=0;j<3;++j){
   CHECK(_fmemset(actual+off,fills[j],n)==actual+off);
   CHECK(meta_reference_fill(expected+off,fills[j],n)==expected+off);
   for(i=0;i<260;++i)CHECK(actual[i]==expected[i]);
  }
  CHECK(sign(_fmemcmp(src+off,src+off,n))==sign(meta_reference_compare(src+off,src+off,n)));
  for(a=0;a<7;++a)for(b=0;b<7;++b){
   memset(actual,0x5a,260);memset(expected,0x5a,260);
   if(n){actual[off+n-1]=values[a];expected[off+n-1]=values[b];}
   CHECK(sign(_fmemcmp(actual+off,expected+off,n))==sign(meta_reference_compare(actual+off,expected+off,n)));
  }
 }
 for(off=0;off<4;++off)for(a=0;a<7;++a)for(b=0;b<7;++b){
  actual[off]=values[a];expected[off]=values[b];actual[off+1]=expected[off+1]=0;
  CHECK(sign(_fstrcmp(actual+off,expected+off))==sign(meta_reference_string(actual+off,expected+off)));
 }
 *total=checks;return 0;
}
