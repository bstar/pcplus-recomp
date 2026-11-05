#include "process_handles.h"
#include <dos.h>
#if defined(ASPECT_EXTERNAL_UNWIND)
#include "../aspect/external_unwind.h"
#else
#define external_phase(value) ((void)0)
#endif
#if defined(PROCESS_HANDLES_BANKED)
typedef struct handles_state {
 unsigned cookie,owner,capacity,count,slots[7];
 unsigned char values[7];
 unsigned char __far *jft;
 unsigned active;
} handles_state;
handles_state __based(__segname("_CODE")) process_handles_storage={0x484a};
typedef char handles_layout[sizeof(handles_state)==36?1:-1];
#define H process_handles_storage
#define saved_psp H.owner
#define saved_count H.capacity
#define held_count H.count
#define indices H.slots
#define entries H.values
#define table H.jft
#define process_handles_active H.active
static unsigned context(void)
{
 unsigned d=0,s=0,f=0;
 __asm {
  mov d,ds
  mov s,ss
  pushf
  pop ax
  mov f,ax
 }
 return d==s && (f&0x600)==0x200;
}
static unsigned saved_valid(void)
{
 unsigned i,j;unsigned long address;
 if(H.cookie!=0x484a || !saved_psp || saved_psp>0xfffc || !saved_count || saved_count>255 || !held_count || held_count>7 || !table)return 0;
 address=(unsigned long)FP_SEG(table)*16UL+FP_OFF(table);
 if((unsigned long)FP_OFF(table)+saved_count>65536UL || address+saved_count>1048576UL)return 0;
 for(i=0;i<held_count;++i){if(indices[i]>=saved_count || entries[i]==255)return 0;for(j=0;j<i;++j)if(indices[i]==indices[j])return 0;}
 return 1;
}
unsigned __far __cdecl process_handles_active_query(void)
{return H.cookie!=0x484a || process_handles_active!=0;}
#else
static unsigned saved_psp,saved_count,held_count,indices[7];
static unsigned char entries[7];
static unsigned char __far *table;
unsigned process_handles_active;
#endif
static unsigned psp(void);
#pragma aux psp = "mov ah,0x62" "int 0x21" "mov ax,bx" value [ax] modify [ax bx];
static unsigned char __far *current_table(unsigned owner)
{return *(unsigned char __far * __far *)MK_FP(owner,0x34);}
unsigned PROCESS_HANDLES_FAR __cdecl process_handles_begin(const unsigned *descriptors,unsigned count)
{
 unsigned owner,capacity,i,j;unsigned char __far *candidate;unsigned long address;
#if defined(PROCESS_HANDLES_BANKED)
 unsigned long storage;
 if(!context() || H.cookie!=0x484a || (unsigned long)(unsigned)descriptors+count*2UL>65536UL)return 1;
#endif
 if(process_handles_active||!descriptors||!count||count>7)return 1;
 owner=psp();
#if defined(PROCESS_HANDLES_BANKED)
 if(owner>0xfffc)return 1;
#endif
 if(!owner||*(unsigned __far *)MK_FP(owner,0)!=0x20cd)return 1;
 capacity=*(unsigned __far *)MK_FP(owner,0x32);candidate=current_table(owner);
 address=(unsigned long)FP_SEG(candidate)*16UL+FP_OFF(candidate);
 if(!capacity||capacity>255||(unsigned long)FP_OFF(candidate)+capacity>65536UL||address+capacity>1048576UL)return 1;
#if defined(PROCESS_HANDLES_BANKED)
 storage=(unsigned long)FP_SEG((void __far *)&H)*16UL+FP_OFF((void __far *)&H);
 if(!candidate || !(address+capacity<=storage || storage+sizeof(H)<=address))return 1;
#endif
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
unsigned PROCESS_HANDLES_FAR __cdecl process_handles_end(void)
{
 unsigned i,bad;
#if defined(PROCESS_HANDLES_BANKED)
 if(!context() || H.cookie!=0x484a || (process_handles_active && !saved_valid()))return 1;
#endif
 if(!process_handles_active)return 1;
 bad=psp()!=saved_psp||current_table(saved_psp)!=table||
     *(unsigned __far *)MK_FP(saved_psp,0x32)!=saved_count;
 for(i=0;i<held_count;++i){if(table[indices[i]]!=255)bad=1;table[indices[i]]=entries[i];if(!i)external_phase(EXTERNAL_HANDLE_UNMASK);}
 process_handles_active=0;held_count=0;table=0;return bad;
}
#if defined(ASPECT_EXTERNAL_UNWIND) || defined(PROCESS_HANDLES_BANKED)
unsigned PROCESS_HANDLES_FAR __cdecl process_handles_recover(void)
{
 unsigned i,bad;
#if defined(PROCESS_HANDLES_BANKED)
 if(!context() || H.cookie!=0x484a || (process_handles_active && !saved_valid()))return 1;
#endif
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
