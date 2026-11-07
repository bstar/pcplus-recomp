#include "numeric_bank_runtime.h"
#include "runtime.h"
#include <malloc.h>
#include <string.h>
/* Native consumers borrow one2/4/8-byte value, never a flat bank extent.
 * Sixteen-slot groups preserve full byte-index capacity and stable per-slot
 * near addresses while ordinary expression temporaries touch few groups. */
#define GROUP_SLOTS 16U
#define GROUP_BYTES 128U
static unsigned char *groups[24];
static unsigned bank_mask;
unsigned runtime_numeric_live(void){return (bank_mask&1)+((bank_mask>>1)&1);}
void runtime_numeric_finish(void)
{
 unsigned i;for(i=0;i<24;++i)if(groups[i]){_nfree(groups[i]);groups[i]=0;}
 bank_mask=0;
}
void runtime_numeric_reset(void)
{
 unsigned i;for(i=0;i<24;++i)if(groups[i])memset(groups[i],0,GROUP_BYTES);
}
unsigned char *__cdecl runtime_numeric_address(unsigned kind,unsigned index)
{
 unsigned group;
 if(kind>1 || index>=(kind?128:256)){runtime_set_error(ASPECT_RUN_OPERAND);return 0;}
 group=(kind?16:0)+(index>>4);
 if(!groups[group]){
  groups[group]=_nmalloc(GROUP_BYTES);
  if(!groups[group]){runtime_set_error(ASPECT_RUN_HEAP);return 0;}
  memset(groups[group],0,GROUP_BYTES);bank_mask|=1U<<kind;
 }
 return groups[group]+(index&(GROUP_SLOTS-1))*8;
}
/* A later DOS far block can prevent DGROUP expansion. Materialize all groups
 * before the first far global, retaining any already-borrowed addresses. */
unsigned runtime_numeric_prepare(void)
{
 unsigned kind,index;
 for(kind=0;kind<2;++kind)for(index=0;index<(kind?128:256);index+=GROUP_SLOTS)
  if(!runtime_numeric_address(kind,index))return 0;
 return 1;
}
