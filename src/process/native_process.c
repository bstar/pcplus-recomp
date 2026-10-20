#include "native_process.h"
#include <dos.h>
#include <i86.h>
#include <malloc.h>
#include <stdlib.h>
#include <string.h>

extern unsigned char runtime_arena[0x3aca];
extern unsigned native_crt_error,native_dos_error;
extern unsigned native_backup_extent;
extern char **environ;
char **native_environment;
unsigned native_process_busy;
struct allocation {struct allocation *next;unsigned size;};
static struct allocation *allocations;
static unsigned owner_error;
static void __far *backup;
static unsigned backup_size;
#if defined(NATIVE_PROCESS_DIAGNOSTIC)
unsigned native_fail_near,native_fail_far,native_near_calls,native_far_calls;
unsigned native_fail_at,native_owned_count,native_owned_peak;
unsigned native_target_calls;
#endif
extern int __cdecl native_spawn_extension(unsigned,const char *,char **,char **,unsigned);
extern int __cdecl native_extension_recovered(unsigned,const char *,char **,char **,unsigned);
extern int __cdecl native_spawn_search(unsigned,const char *,char **,char **);
extern int __cdecl native_system(const char *);
extern void __interrupt __far native_child_divide(void);
static unsigned data_segment(void);
#pragma aux data_segment = "mov ax,ds" value [ax] modify [];
static unsigned stack_segment(void);
#pragma aux stack_segment = "mov ax,ss" value [ax] modify [];
static unsigned current_psp(void);
#pragma aux current_psp = "mov ah,0x62" "int 0x21" "mov ax,bx" value [ax] modify [ax bx];
static void restore_psp(unsigned);
#pragma aux restore_psp = "mov ah,0x50" "int 0x21" parm [bx] modify [ax];

/* Source-first original far-copy ABI. Both backup and restore are real copies. */
void __cdecl native_copy(unsigned ss,unsigned so,unsigned ds,unsigned dest,unsigned count)
{
 _fmemmove(MK_FP(ds,dest),MK_FP(ss,so),count);
 /* Clear only after the live arena has been backed up. The padding supplies
  * a defined DOS empty-list terminator/count, including an empty environment. */
 if(backup&&MK_FP(ds,dest)==backup&&ss==data_segment()&&so==(unsigned)runtime_arena)
  memset(runtime_arena,0,count);
}
void *__cdecl native_allocate(unsigned size)
{
 struct allocation *item;
 unsigned long total=(unsigned long)size+4+sizeof(*item);
#if defined(NATIVE_PROCESS_DIAGNOSTIC)
 ++native_near_calls;
 if(native_fail_near||(native_fail_at&&native_near_calls==native_fail_at))goto failed;
#endif
 if(total>65535UL)goto failed;
 item=_nmalloc((unsigned)total);if(!item)goto failed;
 item->next=allocations;item->size=size+4;allocations=item;
 memset(item+1,0,size+4);
#if defined(NATIVE_PROCESS_DIAGNOSTIC)
 ++native_owned_count;if(native_owned_count>native_owned_peak)native_owned_peak=native_owned_count;
#endif
 return item+1;
failed:
 native_crt_error=12;native_dos_error=8;return 0;
}
void __far *__cdecl native_backup_alloc(unsigned size)
{
#if defined(NATIVE_PROCESS_DIAGNOSTIC)
 ++native_far_calls;if(native_fail_far)return 0;
#endif
 if(size>sizeof(runtime_arena)-4)return 0;
 backup=_fmalloc(size+4);
 if(backup){backup_size=size+4;native_backup_extent=backup_size;}
 return backup;
}
void __cdecl native_backup_free(void __far *pointer)
{ if(pointer){_ffree(pointer);if(pointer==backup){backup=0;backup_size=0;}} }
static void restore_arena(void)
{
 if(backup){_fmemcpy((void __far *)runtime_arena,backup,backup_size);native_backup_free(backup);}
}
void __cdecl native_release(void *pointer)
{
 struct allocation **at,*item;
 /* Native overlong-tail failure calls near-free even after fallback. This
  * adapter must retire the saved arena; it must never free the VM arena. */
 if(pointer==runtime_arena){restore_arena();return;}
 if(!pointer)return;
 for(at=&allocations;*at;at=&(*at)->next)if((void *)(*at+1)==pointer){
  item=*at;*at=item->next;_nfree(item);
#if defined(NATIVE_PROCESS_DIAGNOSTIC)
  --native_owned_count;
#endif
  return;
 }
 owner_error=1;
}
static unsigned disjoint(const void *pointer,unsigned size)
{
 unsigned long start=(unsigned)pointer,end=start+size;
 unsigned long arena=(unsigned)runtime_arena;
 return pointer&&end<=65536UL&&(end<=arena||start>=arena+sizeof(runtime_arena));
}
static unsigned length(const char *pointer,unsigned maximum,unsigned *count)
{
 unsigned n;
 if(!pointer)return 0;
 for(n=0;n<=maximum;++n){
  if(!disjoint(pointer+n,1))return 0;
  if(!pointer[n]){*count=n;return disjoint(pointer,n+1);}
 }
 return 0;
}
static unsigned validate(const char *path,const char *tail,char **environment,unsigned kind)
{
 unsigned n,i,size;unsigned long bytes=1;char *comspec=0;
 if(kind>3)return 0;
 if(kind==3){if(path&&!length(path,125,&n))return 0;}
 else if(!length(path,127,&n)||!n||path[0]=='[')return 0;
 if(!kind&&(n<4||stricmp(path+n-4,".BAT")))return 0;
 if(tail&&!length(tail,125,&size))return 0;
 if(environment)for(i=0;;++i){
  if(i>=32767U||!disjoint(environment+i,sizeof(char *)))return 0;
  if(!environment[i])break;
  if(!length(environment[i],32766,&size))return 0;
  bytes+=size+1;if(bytes>32767UL)return 0;
  if(!comspec&&!strncmp(environment[i],"COMSPEC=",8))comspec=environment[i]+8;
 }
 /* The native batch builder subtracts the four-byte suffix and has no early
  * path-size check. Admit only bounded tails before it writes the stack. */
 if(!kind){
  if(!comspec||!length(comspec,127,&size)||!size)return 0;
  size=0;if(tail)size=strlen(tail)+1;
  if(n-4+3+size>125)return 0;
 }
 if(comspec&&!length(comspec,127,&size))return 0;
 return 1;
}
/* Every selected target passes here, including a BAT found deep in PATH.
 * The native batch prefix copy precedes its argv bound checks. Reject an
 * oversized composed batch tail before that copy can overrun its stack. */
int __cdecl native_extension_checked(unsigned mode,const char *path,char **argv,
 char **environment,unsigned kind)
{
 unsigned n,i,size;unsigned long total;
#if defined(NATIVE_PROCESS_DIAGNOSTIC)
 ++native_target_calls;
#endif
 if(mode||!length(path,259,&n)||!n)goto bad;
 if(!kind){
  if(n<4||stricmp(path+n-4,".BAT"))goto bad;
  total=n-1;
  if(argv&&argv[0])for(i=1;argv[i];++i){
   if(!length(argv[i],125,&size))goto large;
   total+=size+1;if(total>125)goto large;
  }
  if(total>125)goto large;
 }
 return native_extension_recovered(mode,path,argv,environment,kind);
large:
 native_crt_error=7;native_dos_error=10;return -1;
bad:
 native_crt_error=22;native_dos_error=12;return -1;
}
static unsigned run(const char *path,const char *tail,
 char **environment,unsigned kind,native_process_result *result)
{
 native_process_result local;char *arguments[3];unsigned psp,status,child;
 void (__interrupt __far *zero)(void),(__interrupt __far *brk)(void),(__interrupt __far *critical)(void);
 if(native_process_busy)return NATIVE_PROCESS_BUSY;
 if(data_segment()!=stack_segment()||!disjoint(result,sizeof(*result)))return NATIVE_PROCESS_ARGUMENT;
 memset(&local,0,sizeof(local));local.child_status=65535U;
 if(!environment)environment=environ;
 if(!validate(path,tail,environment,kind)){local.status=NATIVE_PROCESS_ARGUMENT;*result=local;return local.status;}
 native_process_busy=1;native_environment=environment;
 allocations=0;owner_error=0;backup=0;backup_size=0;
 arguments[0]=(char *)path;arguments[1]=(char *)tail;arguments[2]=0;
 psp=current_psp();zero=_dos_getvect(0);brk=_dos_getvect(0x23);critical=_dos_getvect(0x24);
 _dos_setvect(0,native_child_divide);
 /* Startup already releases maxalloc slack. Keep the near heap's capacity:
  * shrinking it can leave a sub-growth-quantum gap before a live far block,
  * making later fopen/malloc fail although all held owners remain valid.
  * Release only unused far heap storage; never guess PSP allocation bounds. */
 _fheapshrink();status=NATIVE_PROCESS_OK;
 if(!status){
  if(kind==3)child=(unsigned)native_system(path);
  else if(kind==2)child=(unsigned)native_spawn_search(0,path,arguments,environment);
  else child=(unsigned)native_spawn_extension(0,path,arguments,environment,kind);
  local.child_status=child;
  if(child==65535U)status=native_crt_error==12?NATIVE_PROCESS_MEMORY:NATIVE_PROCESS_EXEC;
 }
 local.crt_error=native_crt_error;local.dos_error=native_dos_error;
 local.changed_vectors=(_dos_getvect(0)!=native_child_divide?1:0)|
     (_dos_getvect(0x23)!=brk?2:0)|(_dos_getvect(0x24)!=critical?4:0);
 if(current_psp()!=psp)restore_psp(psp);
 _dos_setvect(0,zero);_dos_setvect(0x23,brk);_dos_setvect(0x24,critical);
 restore_arena();
 /* Native routines should have retired every nested name/PATH/environment
  * allocation themselves. Drain any remaining owner and report the fault. */
 if(allocations){owner_error=1;while(allocations)native_release(allocations+1);}
 if(owner_error)status=NATIVE_PROCESS_STATE;
 native_environment=0;native_process_busy=0;
 local.status=status;*result=local;return status;
}
unsigned __cdecl native_process_run(const char *path,const char *tail,
 char **environment,unsigned kind,native_process_result *result)
{
 return run(path,tail,environment,kind>1?4:kind,result);
}
unsigned __cdecl native_process_search(const char *path,const char *tail,
 char **environment,native_process_result *result)
{return run(path,tail,environment,2,result);}
unsigned __cdecl native_process_system(const char *command,char **environment,
 native_process_result *result)
{return run(command,0,environment,3,result);}
