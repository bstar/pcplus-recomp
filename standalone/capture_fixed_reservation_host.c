/* Actual DOS fixed log identity + dynamic recorder reservations. Synthetic
 * paths only; the optional close-fault backend is explicit test code. */
#include "../src/capture/capture_reservation.h"
#include "../src/capture/capture_fs.h"
#include <dos.h>
#include <stdio.h>
#include <string.h>
static unsigned checks,failed,reenter,probes;
static int log_owner,other_owner,rec_owner;
static char recorder[64]="C:\\REC.ASP",scratch[64]="C:\\R000.TMP";
#define CHECK(c) do{++checks;if(!(c)){++failed;printf("FAIL line%u\n",__LINE__);}}while(0)
static unsigned __far __cdecl probe(const char *identity,void *context)
{
 ++probes;CHECK(context==&rec_owner);
 if(reenter){
  CHECK(capture_file_claim("C:\\REENTER.FON",&other_owner)==CF_BUSY);
  CHECK(capture_file_unclaim(&log_owner)==CF_BUSY);
  CHECK(capture_file_reserve(probe,&rec_owner)==CF_BUSY);
  CHECK(capture_file_release(probe,&rec_owner)==CF_BUSY);
  CHECK(capture_file_initialize()==CF_BUSY);
  CHECK(capture_file_begin("REENTER.BIN",CF_NEW)==CF_BUSY);
  CHECK(capture_file_close()==CF_BUSY);
 }
 return !strcmp(identity,recorder)||!strcmp(identity,scratch);
}
#ifdef FIXED_FAULT
static unsigned closes,creates,writes;
unsigned capture_fs_canonical(const char *path,char *out)
{strcpy(out,"C:\\");strcat(out,path);return 0;}
unsigned capture_fs_attributes(const char *path,unsigned *attr)
{(void)path;*attr=0;return 2;}
unsigned capture_fs_create(const char *path,int *handle)
{(void)path;*handle=7+(int)creates++;return 0;}
unsigned capture_fs_create_replace(const char *path,int *handle)
{return capture_fs_create(path,handle);}
unsigned capture_fs_open_append(const char *path,int *handle)
{return capture_fs_create(path,handle);}
unsigned capture_fs_seek_end(int handle,unsigned long *position)
{(void)handle;*position=0;return 0;}
unsigned capture_fs_write(int handle,const void *data,unsigned count,unsigned *actual)
{(void)handle;(void)data;++writes;*actual=count;return 0;}
unsigned capture_fs_close(int handle)
{(void)handle;++closes;return 6;}
#endif
static void sinks(capture_file_snapshot *out)
{out[0]=capture_file_result;out[1]=snapshot_file_result;out[2]=monitor_file_result;out[3]=history_file_result;}
int main(void)
{
 capture_reservation_state saved;
 capture_file_snapshot snapshots[4],after[4];
#ifndef FIXED_FAULT
 unsigned i;unsigned char handles[20],__far *jft;union REGS regs;FILE *file;
 const char *aliases[]={"CALLS.FON","calls.fon","C:calls.fon","\\CALLS.FON","C:/CALLS.FON"};
 regs.h.ah=0x62;intdos(&regs,&regs);jft=(unsigned char __far *)MK_FP(regs.x.bx,0x18);
 for(i=0;i<20;++i)handles[i]=jft[i];
#endif
 CHECK(capture_file_initialize()==CF_OK&&snapshot_file_initialize()==CF_OK&&monitor_file_initialize()==CF_OK);
 CHECK(history_file_event(HISTORY_CLOSE,0,0)==CF_OK);
 CHECK(capture_file_unclaim(0)==CF_ARGUMENT&&capture_file_unclaim(&log_owner)==CF_STATE);
 saved=capture_reservation;
 CHECK(capture_file_claim("CALLS.FON",&log_owner)==CF_ARGUMENT);
 CHECK(capture_file_claim("C:\\CALLS.FON",0)==CF_ARGUMENT);
 CHECK(capture_file_claim((const char *)0xfffe,&log_owner)==CF_ARGUMENT);
 CHECK(capture_file_claim((const char *)&capture_reservation,&log_owner)==CF_ARGUMENT);
 CHECK(capture_file_claim("C:\\NUL",&log_owner)==CF_ARGUMENT);
 CHECK(capture_file_claim("C:\\..\\CALLS.FON",&log_owner)==CF_ARGUMENT);
 CHECK(!memcmp(&saved,&capture_reservation,sizeof(saved)));
#ifdef FIXED_FAULT
 CHECK(capture_file_begin("CALLS.FON",CF_NEW)==CF_OK);
 CHECK(capture_file_close()==CF_CLOSE);sinks(snapshots);
 CHECK(capture_file_claim("C:\\CALLS.FON",&log_owner)==CF_BUSY);
 sinks(after);CHECK(!memcmp(snapshots,after,sizeof(after)));
 CHECK(capture_file_claim("C:\\OTHER.FON",&log_owner)==CF_OK);
 CHECK(capture_file_reserve(probe,&rec_owner)==CF_OK);
 reenter=1;CHECK(capture_file_reserve(probe,&rec_owner)==CF_OK);reenter=0;
 CHECK(capture_file_unclaim(&other_owner)==CF_STATE);
 CHECK(capture_file_unclaim(&log_owner)==CF_OK);
 CHECK(capture_file_release(probe,&rec_owner)==CF_OK);
 CHECK(capture_file_initialize()==CF_RECOVERY&&closes==1&&creates==1&&writes==0);
#else
 file=fopen("CALLS.FON","wb");CHECK(file!=0);if(!file)return 2;
 CHECK(fwrite("KEEP",1,4,file)==4&&fclose(file)==0);
 CHECK(capture_file_claim("c:/calls.fon",&log_owner)==CF_OK);
 CHECK(!strcmp(capture_reservation.fixed_identity,"C:\\CALLS.FON"));
 CHECK(capture_file_reserve(probe,&rec_owner)==CF_OK);
 CHECK(capture_file_claim("C:\\ALT.FON",&log_owner)==CF_OK);
 CHECK(!capture_file_reserved("C:\\CALLS.FON")&&capture_file_reserved("C:\\ALT.FON"));
 CHECK(capture_file_claim("C:\\CALLS.FON",&log_owner)==CF_OK);
 saved=capture_reservation;sinks(snapshots);
 CHECK(capture_file_claim("C:\\OTHER.FON",&other_owner)==CF_BUSY);
 CHECK(capture_file_unclaim(&other_owner)==CF_STATE);
 CHECK(capture_file_claim("C:\\REC.ASP",&log_owner)==CF_BUSY);
 CHECK(!memcmp(&saved,&capture_reservation,sizeof(saved)));
 for(i=0;i<sizeof(aliases)/sizeof(aliases[0]);++i){
  CHECK(capture_file_begin(aliases[i],CF_APPEND)==CF_BUSY);
  CHECK(snapshot_file_begin(aliases[i],CF_NEW)==CF_BUSY);
  CHECK(monitor_file_begin(aliases[i],CF_REPLACE)==CF_BUSY);
  CHECK(history_file_event(HISTORY_BEGIN,aliases[i],0)==CF_BUSY);
  sinks(after);CHECK(!memcmp(snapshots,after,sizeof(after)));
 }
 strcpy(recorder,"C:\\CALLS.FON");
 CHECK(capture_file_reserve(probe,&rec_owner)==CF_BUSY);
 strcpy(recorder,"C:\\REC.ASP");
 reenter=1;CHECK(capture_file_claim("C:\\CALLS.FON",&log_owner)==CF_OK);
 CHECK(capture_file_reserve(probe,&rec_owner)==CF_OK);
 CHECK(capture_file_begin("OTHER.LOG",CF_NEW)==CF_OK);reenter=0;
 CHECK(capture_file_append("OTHER",5)==CF_OK&&capture_file_close()==CF_OK);
 CHECK(capture_file_release(probe,&rec_owner)==CF_OK);
 CHECK(capture_file_reserved("C:\\CALLS.FON")!=0);
 CHECK(capture_file_unclaim(&log_owner)==CF_OK);
 CHECK(capture_reservation.fixed_owner==0);
 for(i=0;i<64;++i)CHECK(capture_reservation.fixed_identity[i]==0);
 CHECK(capture_file_begin("CALLS.FON",CF_APPEND)==CF_OK);
 sinks(snapshots);saved=capture_reservation;
 CHECK(capture_file_claim("C:\\CALLS.FON",&log_owner)==CF_BUSY);
 sinks(after);CHECK(!memcmp(snapshots,after,sizeof(after))&&!memcmp(&saved,&capture_reservation,sizeof(saved)));
 CHECK(capture_file_append("A",1)==CF_OK&&capture_file_close()==CF_OK);
 CHECK(capture_file_reserve(probe,&rec_owner)==CF_OK);
 CHECK(capture_file_claim("C:\\REC.ASP",&log_owner)==CF_BUSY);
 CHECK(capture_file_claim("C:\\CALLS.FON",&log_owner)==CF_OK);
 CHECK(capture_file_release(probe,&rec_owner)==CF_OK);
 CHECK(capture_file_reserved("C:\\CALLS.FON")!=0);
 CHECK(capture_file_unclaim(&log_owner)==CF_OK);
 for(i=0;i<20;++i)CHECK(handles[i]==jft[i]);
#endif
 CHECK(probes>0);
 printf("FIXED %u checks %u failures\n",checks,failed);return failed?1:0;
}
