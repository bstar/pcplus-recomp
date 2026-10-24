/* Actual DOS reset/geometry/storage and typed-failure observer. */
#include "shadow_owner.h"
#include <dos.h>
#include <stdio.h>
#include <string.h>
extern void __cdecl shadow_native_initialize(void);
extern unsigned __cdecl shadow_entry_flags(void);
extern void __cdecl shadow_boot_write(void);
extern unsigned __cdecl shadow_request_if_off(void),shadow_request_df(void);
extern unsigned shadow_offset,shadow_segment,shadow_bytes,shadow_configured_wide;
extern unsigned shadow_rows,shadow_columns,shadow_cga_port,shadow_flags_pointer;
extern unsigned char shadow_image[];
typedef struct { unsigned cursor,shape,segment,offset,bytes; } stamp;
static unsigned reference[2],trace_open;static int trace_handle;
static unsigned free_paragraphs(void)
{
 union REGS in,out;in.h.ah=0x48;in.x.bx=0xffff;intdos(&in,&out);
 if(!out.x.cflag){_dos_freemem(out.x.ax);return 0;}return out.x.bx;
}
static unsigned pressure(unsigned keep)
{
 unsigned available=free_paragraphs(),segment;
 if(available<=keep+1||_dos_allocmem(available-keep,&segment))return 0;
 return segment;
}
static void capture(stamp *s,unsigned slot)
{
 union REGS in,out;unsigned char __far *p=MK_FP(reference[slot],0);
 memset(s,0,sizeof(*s));_fmemcpy(p,(void __far *)shadow_image,0xd600);
 _fmemcpy(p+0xd600,MK_FP(0xb800,0),4000);
 if(shadow_segment)_fmemcpy(p+0xd600+4000,MK_FP(shadow_segment,shadow_offset),shadow_bytes);
 s->segment=shadow_segment;s->offset=shadow_offset;s->bytes=shadow_bytes;
 in.h.ah=3;in.h.bh=0;int86(0x10,&in,&out);s->cursor=out.x.dx;s->shape=out.x.cx;
}
static unsigned unchanged(const stamp *a,const stamp *b)
{return !memcmp(a,b,sizeof(*a))&&!_fmemcmp(MK_FP(reference[0],0),MK_FP(reference[1],0),0xd600+4000+(a->segment?a->bytes:0));}
static void paint(void)
{
 unsigned i;unsigned char __far *p=MK_FP(0xb800,0);union REGS in,out;
 for(i=0;i<4000;++i)p[i]=(unsigned char)(i*17U+31U);
 if(shadow_segment){p=MK_FP(shadow_segment,shadow_offset);for(i=0;i<shadow_bytes;++i)p[i]=(unsigned char)(i*23U+71U);}
 in.h.ah=2;in.h.bh=0;in.x.dx=0x050b;int86(0x10,&in,&out);
}
static unsigned checks;
static unsigned verify(unsigned value,const char *name)
{unsigned written;++checks;if(trace_open){_dos_write(trace_handle,name,strlen(name),&written);_dos_write(trace_handle,"\r\n",2,&written);_dos_commit(trace_handle);}if(!value){printf("FAIL %u %s\n",checks,name);return 0;}return 1;}
#define CHECK(x,n) do{if(!verify((x),(n)))return 1;}while(0)
int main(void)
{
 unsigned status,segment,offset,iteration,saved,allocations,entry_flags,free_before;stamp before,after;
 entry_flags=shadow_entry_flags();shadow_native_initialize();shadow_boot_write();
 trace_open=!_dos_creat("D:\\TRACE.TXT",0,&trace_handle);CHECK(trace_open,"phase log open");
 free_before=free_paragraphs();CHECK(free_before!=0,"independent DOS free-memory baseline");
 CHECK(!_dos_allocmem((65120U+15U)>>4,&reference[0]),"independent before-state buffer");
 CHECK(!_dos_allocmem((65120U+15U)>>4,&reference[1]),"independent after-state buffer");
 CHECK(shadow_request(1)==SHADOW_OK,"first wide reset");
 CHECK(shadow_segment&&shadow_offset==16&&shadow_bytes==6336,"real owned shadow");
 CHECK(shadow_owned_blocks()==1,"only committed block");
 CHECK(shadow_configured_wide==0,"temporary setting restored");
 segment=shadow_segment;offset=shadow_offset;
 CHECK(shadow_request(1)==SHADOW_OK,"reuse wide reset");
 CHECK(shadow_segment==segment&&shadow_offset==offset&&shadow_owned_blocks()==1,"same block retained");
 CHECK(shadow_request(0)==SHADOW_OK,"narrow reset");
 CHECK(!shadow_segment&&!shadow_offset&&!shadow_owned_blocks(),"released at narrow commit");
 for(iteration=0;iteration<8;++iteration){
  CHECK(shadow_request(1)==SHADOW_OK,"repeated wide");
  CHECK(shadow_request(0)==SHADOW_OK,"repeated narrow");
 }
 segment=pressure(1000);CHECK(segment!=0,"real DOS pressure reservation");
 paint();capture(&before,0);
 CHECK(shadow_request(1)==SHADOW_MEMORY,"actual DOS snapshot allocation failure");
 capture(&after,1);CHECK(unchanged(&before,&after),"real snapshot exhaustion leaves all state unchanged");
 CHECK(!_dos_freemem(segment),"first pressure reservation released");
 saved=shadow_native_errors;segment=pressure((0xd600U+4000U+32U+15U)/16U+32U);
 CHECK(segment!=0,"real native-allocation pressure reservation");
 paint();capture(&before,0);
 CHECK(shadow_request(1)==SHADOW_MEMORY,"actual DOS native shadow allocation failure");
 capture(&after,1);CHECK(unchanged(&before,&after),"real native exhaustion rolls back all state");
 CHECK(shadow_native_errors==saved+1,"actual native failure callback under DOS exhaustion");
 CHECK(!_dos_freemem(segment),"second pressure reservation released");
 shadow_fail_allocation=1;
 paint();capture(&before,0);
 CHECK(shadow_request(1)==SHADOW_MEMORY,"snapshot allocation refusal");
 capture(&after,1);CHECK(unchanged(&before,&after),"snapshot refusal preserves complete state");
 CHECK(!shadow_segment&&!shadow_owned_blocks(),"preflight unchanged");
 shadow_fail_allocation=2;
 saved=shadow_native_errors;
 paint();capture(&before,0);
 CHECK(shadow_request(1)==SHADOW_MEMORY,"native shadow allocation failure");
 capture(&after,1);CHECK(unchanged(&before,&after),"native allocation restores complete state");
 CHECK(shadow_native_errors==saved+1,"actual native allocation-error callback");
 CHECK(!shadow_segment&&!shadow_offset&&!shadow_owned_blocks(),"failed allocation rollback");
 CHECK(shadow_configured_wide==0,"failed reset restores temporary setting");
 shadow_abort_after_allocation=1;
 paint();capture(&before,0);
 CHECK(shadow_request(1)==SHADOW_NATIVE,"typed abort with new block");
 capture(&after,1);CHECK(unchanged(&before,&after),"post-allocation abort restores complete state");
 CHECK(!shadow_segment&&!shadow_owned_blocks(),"new block released on abort");
 CHECK(shadow_request(1)==SHADOW_OK,"retry after abort");
 paint();capture(&before,0);shadow_abort_after_reset=1;
 CHECK(shadow_request(1)==SHADOW_NATIVE,"abort after clearing reused shadow");
 capture(&after,1);CHECK(unchanged(&before,&after),"reused shadow bytes restore exactly");
 shadow_abort_after_reset=1;
 CHECK(shadow_request(0)==SHADOW_NATIVE,"abort after deferred old-shadow free");
 capture(&after,1);CHECK(unchanged(&before,&after),"old allocation and all state survive rollback");
 CHECK(shadow_request(0)==SHADOW_OK,"narrow retry after rollback");
 paint();capture(&before,0);shadow_foreign_release=1;
 CHECK(shadow_request(1)==SHADOW_STATE,"foreign release is rejected");
 capture(&after,1);CHECK(unchanged(&before,&after),"foreign release leaves state unchanged");
 CHECK(!shadow_owned_blocks(),"foreign release frees only pending/snapshot ownership");
 shadow_reenter=1;CHECK(shadow_request(1)==SHADOW_OK,"outer transaction survives reentry refusal");
 CHECK(shadow_reenter_result==SHADOW_STATE&&shadow_owned_blocks()==1,"nested request rejected before allocation");
 allocations=shadow_allocations;saved=shadow_rows;shadow_rows=0;
 CHECK(shadow_request(0)==SHADOW_STATE&&shadow_allocations==allocations,"zero rows preflight");shadow_rows=saved;
 shadow_rows=25;CHECK(shadow_request(0)==SHADOW_STATE,"oversized attribute geometry preflight");shadow_rows=saved;
 saved=shadow_flags_pointer;shadow_flags_pointer=1;
 CHECK(shadow_request(0)==SHADOW_STATE,"foreign near plane rejected");shadow_flags_pointer=saved;
 shadow_cga_port=0x3da;CHECK(shadow_request(0)==SHADOW_STATE,"unadmitted CGA preflight");shadow_cga_port=0;
 CHECK(shadow_request(2)==SHADOW_STATE,"nonboolean width preflight");
 CHECK(shadow_allocations==allocations,"refused admissions do not allocate");
 CHECK(shadow_request_if_off()==SHADOW_STATE,"IF-disabled admission refused");
 CHECK(shadow_request_df()==SHADOW_STATE,"DF-set admission refused");
 CHECK(shadow_allocations==allocations,"flag refusals do not allocate");
 shadow_fail_release=1;
 status=shadow_close();
 CHECK(status==SHADOW_RELEASE&&shadow_owned_blocks()==1,"failed release retains ownership");
 CHECK(shadow_close()==SHADOW_OK&&!shadow_owned_blocks(),"retained release retries");
 CHECK(shadow_request(1)==SHADOW_STATE,"closed wide view rejects reuse before reinitialization");
 shadow_native_initialize();
 CHECK(shadow_request(1)==SHADOW_OK,"fresh reset after close");
 *(unsigned char __far *)MK_FP(shadow_segment,0)=0;
 CHECK(shadow_close()==SHADOW_GUARD&&shadow_owned_blocks()==1,"canary failure retains allocation");
 *(unsigned char __far *)MK_FP(shadow_segment,0)=0xa5;
 CHECK(shadow_close()==SHADOW_OK&&!shadow_owned_blocks(),"known injected canary repair permits release");
 CHECK(shadow_allocations==shadow_releases,"all DOS allocations balanced");
 CHECK(!_dos_freemem(reference[0])&&!_dos_freemem(reference[1]),"independent comparison buffers released");
 CHECK(free_paragraphs()==free_before,"DOS largest free block restored exactly");
 _dos_close(trace_handle);trace_open=0;
 printf("PASS %u checks allocations=%u releases=%u entry_flags=%04x\n",checks,shadow_allocations,shadow_releases,entry_flags);
 return 0;
}
