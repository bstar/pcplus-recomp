#include "process_handles.h"
#include <dos.h>
#if defined(ASPECT_EXTERNAL_UNWIND)
#include "../aspect/external_unwind.h"
#else
#define external_phase(value) ((void)0)
#endif
static unsigned saved_psp,saved_count,held_count,indices[7];
static unsigned char entries[7];
static unsigned char __far *table;
unsigned process_handles_active;
static unsigned psp(void);
#pragma aux psp = "mov ah,0x62" "int 0x21" "mov ax,bx" value [ax] modify [ax bx];
static unsigned char __far *current_table(unsigned owner)
{return *(unsigned char __far * __far *)MK_FP(owner,0x34);}
unsigned __cdecl process_handles_begin(const unsigned *descriptors,unsigned count)
{
 unsigned owner,capacity,i,j;unsigned char __far *candidate;unsigned long address;
 if(process_handles_active||!descriptors||!count||count>7)return 1;
 owner=psp();if(!owner||*(unsigned __far *)MK_FP(owner,0)!=0x20cd)return 1;
 capacity=*(unsigned __far *)MK_FP(owner,0x32);candidate=current_table(owner);
 address=(unsigned long)FP_SEG(candidate)*16UL+FP_OFF(candidate);
 if(!capacity||capacity>255||(unsigned long)FP_OFF(candidate)+capacity>65536UL||address+capacity>1048576UL)return 1;
 for(i=0;i<count;++i){
  if(descriptors[i]>=capacity||candidate[descriptors[i]]==255)return 1;
  for(j=0;j<i;++j)if(descriptors[i]==descriptors[j])return 1;
 }
 saved_psp=owner;saved_count=capacity;table=candidate;held_count=count;
 for(i=0;i<count;++i){indices[i]=descriptors[i];entries[i]=table[indices[i]];}
 /* No DOS calls/CRT operations after the first entry changes. UART/BIOS ISRs
  * do not use this private foreground table, so no long CLI bracket is needed. */
 process_handles_active=1;
 for(i=0;i<count;++i){table[indices[i]]=255;if(!i)external_phase(EXTERNAL_HANDLE_MASK);}
 return 0;
}
unsigned __cdecl process_handles_end(void)
{
 unsigned i,bad;
 if(!process_handles_active)return 1;
 bad=psp()!=saved_psp||current_table(saved_psp)!=table||
     *(unsigned __far *)MK_FP(saved_psp,0x32)!=saved_count;
 for(i=0;i<held_count;++i){if(table[indices[i]]!=255)bad=1;table[indices[i]]=entries[i];if(!i)external_phase(EXTERNAL_HANDLE_UNMASK);}
 process_handles_active=0;held_count=0;table=0;return bad;
}
#if defined(ASPECT_EXTERNAL_UNWIND)
unsigned __cdecl process_handles_recover(void)
{
 unsigned i,bad;
 if(!process_handles_active)return 0;
 bad=psp()!=saved_psp||current_table(saved_psp)!=table||
     *(unsigned __far *)MK_FP(saved_psp,0x32)!=saved_count;
 /* BEGIN or END may have stopped between selected entries. Both our mask
  * and the saved byte are legitimate; a third value remains a foreign edit. */
 for(i=0;i<held_count;++i){
  if(table[indices[i]]!=255&&table[indices[i]]!=entries[i])bad=1;
  table[indices[i]]=entries[i];
 }
 process_handles_active=0;held_count=0;table=0;return bad;
}
#endif
