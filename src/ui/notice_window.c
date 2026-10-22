#include "notice_window.h"
#include <dos.h>
#include <malloc.h>
#include <string.h>

#define BYTES 4000U
#define GUARD 16U
struct descriptor {unsigned top,left,bottom,right;unsigned *attribute;};
typedef char descriptor_size[(sizeof(struct descriptor)==10&&sizeof(unsigned)==2)?1:-1];
static struct descriptor view;
static unsigned attribute,phase,used,freed;
static unsigned char __far *block;
static unsigned char __far *payload;
extern void __cdecl window_native_initialize(unsigned);
extern void __far *__cdecl window_begin_native(const struct descriptor *);
extern void __cdecl window_end_native(const struct descriptor *,void __far *);
#if defined(NOTICE_WINDOW_DIAGNOSTIC)
unsigned notice_window_fail_alloc,notice_window_allocations,notice_window_frees;
void __cdecl notice_window_damage_guard(void){if(block)block[0]^=1;}
#endif
static unsigned data_segment(void);
#pragma aux data_segment = "mov ax,ds" value [ax] modify [];
static unsigned stack_segment(void);
#pragma aux stack_segment = "mov ax,ss" value [ax] modify [];
static unsigned interrupt_flag(void);
#pragma aux interrupt_flag = "pushf" "pop ax" "and ax,0x200" value [ax] modify [];
static unsigned mode_valid(void)
{
 union REGS in,out;
 in.h.ah=15;int86(0x10,&in,&out);
 return out.h.al==3&&out.h.ah==80&&out.h.bh==0&&
  *(unsigned char __far *)MK_FP(0x40,0x84)==24&&
  *(unsigned __far *)MK_FP(0x40,0x63)==0x3d4;
}
static unsigned guards(void)
{
 unsigned i;
 if(!block||!payload)return 0;
 for(i=0;i<GUARD;++i)if(block[i]!=0xa5||payload[BYTES+i]!=0x5a)return 0;
 return 1;
}
/* Native snapshot allocation consumes this reservation exactly once. There is
 * no fallible heap operation after the native cursor/screen mutation starts. */
void __far *__cdecl window_platform_allocate(unsigned bytes)
{
 if(phase!=1||used||bytes!=BYTES||!guards())return 0;
 used=1;return payload;
}
void __cdecl window_platform_free(void __far *pointer)
{
 if(phase!=1||!used||pointer!=payload||!guards()){phase=2;return;}
 _ffree(block);block=payload=0;freed=1;
#if defined(NOTICE_WINDOW_DIAGNOSTIC)
 ++notice_window_frees;
#endif
}
unsigned __cdecl notice_window_phase(void){return phase;}
unsigned __cdecl notice_window_open(const notice_window_rect *rect,unsigned animated)
{
 void __far *result;notice_window_rect staged;
 if(phase)return NOTICE_WINDOW_BUSY;
 if(data_segment()!=stack_segment()||!interrupt_flag())return NOTICE_WINDOW_STATE;
 if(!rect||(unsigned long)(unsigned)rect+sizeof(*rect)>65536UL||animated>1)return NOTICE_WINDOW_ARGUMENT;
 memcpy(&staged,rect,sizeof(staged));rect=&staged;
 if(rect->attribute>255||rect->top>rect->bottom||
    rect->left>rect->right||rect->bottom>=25||rect->right>=80||
    rect->bottom-rect->top<2||rect->right-rect->left<3)return NOTICE_WINDOW_ARGUMENT;
 if(!mode_valid())return NOTICE_WINDOW_STATE;
#if defined(NOTICE_WINDOW_DIAGNOSTIC)
 if(notice_window_fail_alloc)return NOTICE_WINDOW_MEMORY;
#endif
 block=_fmalloc(BYTES+GUARD*2);if(!block)return NOTICE_WINDOW_MEMORY;
 if((unsigned long)FP_OFF(block)+BYTES+GUARD*2>65536UL){_ffree(block);block=0;return NOTICE_WINDOW_MEMORY;}
 payload=block+GUARD;
 _fmemset(block,0xa5,GUARD);_fmemset(payload+BYTES,0x5a,GUARD);
#if defined(NOTICE_WINDOW_DIAGNOSTIC)
 ++notice_window_allocations;
#endif
 attribute=rect->attribute;view.top=rect->top;view.left=rect->left;
 view.bottom=rect->bottom;view.right=rect->right;view.attribute=&attribute;
 used=freed=0;phase=1;window_native_initialize(animated);
 result=window_begin_native(&view);
 if(result!=payload||!used||!guards()){phase=2;return NOTICE_WINDOW_GUARD;}
 return NOTICE_WINDOW_OK;
}
unsigned __cdecl notice_window_close(void)
{
 if(!phase)return NOTICE_WINDOW_OK;
 if(data_segment()!=stack_segment()||!interrupt_flag()||!mode_valid())return NOTICE_WINDOW_STATE;
 if(!guards()){phase=2;return NOTICE_WINDOW_GUARD;}
 phase=1;window_end_native(&view,payload);
 if(!freed||block){phase=2;return NOTICE_WINDOW_GUARD;}
 phase=used=0;return NOTICE_WINDOW_OK;
}
