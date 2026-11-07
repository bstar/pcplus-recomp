#include "numeric_bank_runtime.h"
#include "runtime.h"
#include <malloc.h>
#include <string.h>
static unsigned char *banks[2];
unsigned runtime_numeric_live(void){return (banks[0]!=0)+(banks[1]!=0);}
void runtime_numeric_finish(void)
{
 unsigned i;for(i=0;i<2;++i)if(banks[i]){_nfree(banks[i]);banks[i]=0;}
}
void runtime_numeric_reset(void)
{
 unsigned i;for(i=0;i<2;++i)if(banks[i])memset(banks[i],0,i?1024:2048);
}
unsigned char *__cdecl runtime_numeric_address(unsigned kind,unsigned index)
{
 unsigned size;
 if(kind>1 || index>=(kind?128:256)){runtime_set_error(ASPECT_RUN_OPERAND);return 0;}
 if(!banks[kind]){
  size=kind?1024:2048;banks[kind]=_nmalloc(size);
  if(!banks[kind]){runtime_set_error(ASPECT_RUN_HEAP);return 0;}
  memset(banks[kind],0,size);
 }
 return banks[kind]+index*8;
}

/* Far globals can occupy the DOS block immediately after DGROUP, preventing
 * later near expansion. Reserve both full banks before the first far global.
 * Scripts without far globals still materialize only the banks they touch. */
unsigned runtime_numeric_prepare(void)
{
 return runtime_numeric_address(0,0)!=0 && runtime_numeric_address(1,0)!=0;
}
