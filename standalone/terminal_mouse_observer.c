/* Independent DOS parent: driver snapshots, real menus/EXEC and TSR cleanup. */
#include <dos.h>
#include <malloc.h>
#include <process.h>
#include <stdio.h>
#include <string.h>
typedef void (__interrupt __far *vector_type)(void);
typedef void (__far *callback_type)(void);
extern void __far mouse_observer_prior(void),mouse_observer_driver(void);
extern void __cdecl mouse_observer_begin(unsigned),mouse_observer_end(void);
extern unsigned __cdecl mouse_observer_stage(void),mouse_observer_invoke(callback_type);
extern unsigned __cdecl mouse_observer_registrations(void);
static unsigned checks,failures;
static unsigned observer_psp;
static void check(unsigned pass,unsigned line)
{++checks;if(!pass){++failures;printf("MOUSE FAIL %u\n",line);}}
#define CHECK(x) check((x)!=0,__LINE__)
static unsigned state_bytes(void)
{union REGS in,out;in.x.ax=0x15;in.x.bx=0;int86(0x33,&in,&out);return out.x.bx;}
static void state_io(unsigned fn,void __far *buffer)
{union REGS in,out;struct SREGS s;segread(&s);s.es=FP_SEG(buffer);in.x.ax=fn;in.x.dx=FP_OFF(buffer);int86x(0x33,&in,&out,&s);}
static callback_type exchange(callback_type callback,unsigned mask,unsigned *previous_mask)
{
 union REGS in,out;struct SREGS s;segread(&s);s.es=FP_SEG(callback);
 in.x.ax=0x14;in.x.cx=mask;in.x.dx=FP_OFF(callback);int86x(0x33,&in,&out,&s);
 *previous_mask=out.x.cx;return (callback_type)MK_FP(s.es,out.x.dx);
}
static unsigned owners(unsigned *list)
{
 unsigned segment=observer_psp-1,count=0,steps=0,i,owner;
 for(;;){
  unsigned char __far *m=(unsigned char __far *)MK_FP(segment,0);
  unsigned size=*(unsigned __far *)(m+3);
  if((m[0]!='M'&&m[0]!='Z')||++steps>1024)return 0xffff;
  owner=*(unsigned __far *)(m+1);
  if(owner){for(i=0;i<count&&list[i]!=owner;++i);if(i==count){if(count==128)return 0xffff;list[count++]=owner;}}
  if(m[0]=='Z')return count;
  if(size==65535U||(unsigned long)segment+size+1>65535UL)return 0xffff;
  segment+=size+1;
 }
}
static unsigned contains(const unsigned *list,unsigned count,unsigned value)
{unsigned i;for(i=0;i<count;++i)if(list[i]==value)return 1;return 0;}
static unsigned release_owner(unsigned owner)
{
 unsigned segment,steps=0;
restart:
 segment=observer_psp-1;
 for(;;){
  unsigned char __far *m=(unsigned char __far *)MK_FP(segment,0);
  unsigned size=*(unsigned __far *)(m+3);
  if((m[0]!='M'&&m[0]!='Z')||++steps>4096)return 0;
  if(*(unsigned __far *)(m+1)==owner){if(_dos_freemem(segment+1))return 0;goto restart;}
  if(m[0]=='Z')return 1;
  if(size==65535U||(unsigned long)segment+size+1>65535UL)return 0;
  segment+=size+1;
 }
}
int main(int argc,char **argv)
{
 unsigned bytes,mask,mode,before_count,after_count,retained=0,owner=0,i,stage,callback_seen=0,registrations;
 unsigned before_owners[128],after_owners[128];int child;
 unsigned char __far *original;unsigned char __far *before;unsigned char __far *after;
 vector_type original_vector;callback_type callback;FILE *report;
 union REGS psp_in,psp_out;
 if(argc<3)return 90;mode=(unsigned char)argv[1][0];
 psp_in.x.ax=0x6200;int86(0x21,&psp_in,&psp_out);observer_psp=psp_out.x.bx;
 bytes=state_bytes();if(!bytes||bytes>=65504U)return 91;
 original=_fmalloc(bytes);before=_fmalloc(bytes);after=_fmalloc(bytes);if(!original||!before||!after)return 92;
 original_vector=_dos_getvect(0x33);state_io(0x16,original);
 exchange(mouse_observer_prior,0x0b,&mask);state_io(0x16,before);
 before_count=owners(before_owners);CHECK(before_count!=0xffff);
 mouse_observer_begin(mode);
 if(mode=='B')_dos_setvect(0x33,0);
 ++argv;argv[0]="TERMINAL.EXE";
 child=spawnv(P_WAIT,"C:\\TERMINAL.EXE",(const char * const *)argv);
 stage=mouse_observer_stage();
 registrations=mouse_observer_registrations();
 CHECK(child==(mode=='Q'?0x030e:mode=='R'?7:0));
 if(mode=='Q'||mode=='B')CHECK(_dos_getvect(0x33)==0);
 else CHECK(_dos_getvect(0x33)==(vector_type)mouse_observer_driver);
 mouse_observer_end();CHECK(_dos_getvect(0x33)==original_vector);
 after_count=owners(after_owners);CHECK(after_count!=0xffff);
 for(i=0;i<after_count&&after_count!=0xffff;++i)if(!contains(before_owners,before_count,after_owners[i])){++retained;owner=after_owners[i];}
 if(mode=='Q'){
  CHECK(stage==1&&retained==1&&owner!=observer_psp);
  callback=exchange(0,0,&mask);callback_seen=callback!=0;
  CHECK(callback!=0&&callback!=mouse_observer_prior&&mask==0x0b);
  if(retained==1){
   unsigned keep=*(unsigned __far *)MK_FP(owner-1,3);
   CHECK(keep==EXPECTED_KEEP&&FP_SEG(callback)>=owner+16&&FP_SEG(callback)<owner+keep);
   CHECK(mouse_observer_invoke(callback)==1);
  }
  /* Controlled repair: retire the retained callback before reclaiming blocks. */
  state_io(0x17,original);
  CHECK(retained==1&&release_owner(owner));
  after_count=owners(after_owners);CHECK(after_count==before_count);
 }else{
  CHECK(retained==0);
  state_io(0x16,after);CHECK(!_fmemcmp(before,after,bytes));
  callback=exchange(0,0,&mask);CHECK(callback==mouse_observer_prior&&mask==0x0b);
  if(mode=='S'||mode=='L')CHECK(stage==2);
  if(mode=='B'||mode=='U')CHECK(registrations==0);
  state_io(0x17,original);
 }
 state_io(0x16,after);CHECK(!_fmemcmp(original,after,bytes));
 _ffree(original);_ffree(before);_ffree(after);
 report=fopen("MOUSE.OUT","w");if(!report)return 93;
 fprintf(report,"MOUSEOBS checks=%u failures=%u child=%u retained=%u driver_bytes=%u stage=%u callback=%u registrations=%u\n",checks,failures,(unsigned)child,retained,bytes,stage,callback_seen,registrations);
 if(fclose(report))return 94;
 return failures?1:0;
}
