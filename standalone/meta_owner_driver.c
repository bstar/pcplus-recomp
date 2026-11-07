#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dos.h>
#include "meta_key_owner.h"
#include "../src/capture/capture_file.h"
#include "key_editor_faults.h"
extern meta_key_owner __far owner;
extern meta_key_owner __far other_owner;
extern unsigned char __far live[540];
extern unsigned char __far changed[540];
extern unsigned __far __cdecl meta_release_real(capture_file_probe,void *);
static unsigned release_fault,checks,foreign;
static char path[64]="C:\\LAB\\TEST.KEY",stage[64]="C:\\LAB\\KEYSTG.$$$",backup[64]="C:\\LAB\\KEYBAK.$$$",next_path[64]="C:\\LAB\\NEW.KEY";
static unsigned char original[540],saved_live[540],competitor[540];
#define CHECK(x) do {++checks;if(!(x)){printf("FAIL line %u check %u phase %u status %u io %u calls %u\r\n",__LINE__,checks,owner.phase,owner.status,owner.io_status,key_calls);exit(1);}}while(0)
unsigned __far __cdecl capture_file_release(capture_file_probe p,void *c)
{if(release_fault)return CF_BUSY;return meta_release_real(p,c);}
static unsigned __far __cdecl foreign_probe(const char *p,void *c){(void)p;(void)c;return 0;}
static unsigned ds(void);
#pragma aux ds = "mov ax,ds" value [ax] modify [];
static unsigned ss(void);
#pragma aux ss = "mov ax,ss" value [ax] modify [];
static int put(const char *p,const unsigned char __far *v,unsigned n)
{unsigned i;FILE *f=fopen(p,"wb");if(!f)return 0;for(i=0;i<n;++i)if(fputc(v[i],f)==EOF){fclose(f);return 0;}return !fclose(f);}
static int matches(const char *p,const unsigned char __far *v,unsigned n)
{unsigned i;int good=1;FILE *f=fopen(p,"rb");if(!f)return 0;for(i=0;i<n;++i)if(fgetc(f)!=v[i])good=0;if(fgetc(f)!=EOF)good=0;if(fclose(f))good=0;return good;}
static unsigned exists(const char *p){unsigned a;return !_dos_getfileattr(p,&a);}
static void claim_checks(void)
{
 unsigned calls=key_calls;
 CHECK(capture_file_begin(path,CF_NEW)==CF_BUSY);CHECK(snapshot_file_begin(stage,CF_NEW)==CF_BUSY);CHECK(monitor_file_begin(backup,CF_NEW)==CF_BUSY);CHECK(capture_file_claim(path,&foreign)==CF_BUSY);CHECK(history_file_event(HISTORY_BEGIN,path,0)==CF_BUSY);CHECK(key_calls==calls && !meta_key_owner_exec_allowed());
}
int main(int argc,char **argv)
{
 unsigned i,r,mode=argc>1?atoi(argv[1]):0,status,calls,want_held;
 CHECK(ds()==ss() && FP_SEG(&owner)!=ds() && sizeof(owner)==1518);
 for(i=0;i<540;++i)original[i]=(unsigned char)(i%200+32);
 for(r=0;r<10;++r){original[r*54]=r%4;original[r*54+1]=0;original[r*54+2]='A'+r;original[r*54+3]=0;}
 _fmemcpy(live,original,540);_fmemcpy(changed,original,540);changed[2]='!';
 _dos_setfileattr(path,0);remove(path);remove(stage);remove(backup);remove(next_path);CHECK(put(path,original,540));
 CHECK(!capture_file_initialize());CHECK(!snapshot_file_initialize());CHECK(!monitor_file_initialize());
 key_fault_reset(0);CHECK(meta_key_owner_exec_allowed());CHECK(meta_key_owner_begin((meta_key_owner __far *)MK_FP(ds(),0xfff0))==META_OWNER_ARGUMENT && !key_calls);
 if(!mode){
  CHECK(!capture_file_reserve(foreign_probe,&foreign));CHECK(meta_key_owner_begin(&owner)==META_OWNER_CLAIM && meta_key_owner_exec_allowed());CHECK(!capture_file_release(foreign_probe,&foreign));
  CHECK(!meta_key_owner_begin(&owner));CHECK(meta_key_owner_begin(&other_owner)==META_OWNER_BUSY && !key_calls);
  CHECK(!capture_file_begin(path,CF_APPEND));CHECK(meta_key_owner_load(&owner,path,live,live)==META_OWNER_CLAIM && !key_calls && !_fmemcmp(live,original,540));CHECK(!capture_file_close());
  CHECK(!capture_file_claim(stage,&foreign));CHECK(meta_key_owner_load(&owner,path,live,live)==META_OWNER_CLAIM && !key_calls);CHECK(!capture_file_unclaim(&foreign));
  live[2]='?';CHECK(!meta_key_owner_bind(&owner,path) && owner.baseline_exists && live[2]=='?' && !_fmemcmp(owner.baseline,original,540));live[2]=original[2];
  key_fault_reset(0);CHECK(meta_key_owner_load(&owner,path,owner.baseline,live)==META_OWNER_ARGUMENT && !key_calls);CHECK(meta_key_owner_save(&owner,owner.baseline)==META_OWNER_ARGUMENT && !key_calls);changed[1]=1;CHECK(meta_key_owner_save(&owner,changed)==META_OWNER_ARGUMENT && !key_calls);changed[1]=0;CHECK(meta_key_owner_begin(&owner)==META_OWNER_BUSY && !key_calls);
  CHECK(!meta_key_owner_load(&owner,path,live,live) && owner.has_current && !owner.created && !_fmemcmp(owner.baseline,original,540));claim_checks();
  CHECK(!meta_key_owner_save(&owner,changed));CHECK(matches(path,changed,540) && !_fmemcmp(owner.baseline,changed,540));
  CHECK(put(next_path,original,539));_fmemcpy(saved_live,live,540);CHECK(meta_key_owner_load(&owner,next_path,live,live)==META_OWNER_LOAD && !_fmemcmp(live,saved_live,540) && !_fstrcmp(owner.paths[0][0],path));claim_checks();CHECK(capture_file_begin(next_path,CF_APPEND)==0);CHECK(!capture_file_close());remove(next_path);
  CHECK(!meta_key_owner_load(&owner,next_path,live,live) && owner.created && owner.has_current && matches(next_path,live,540));
  for(r=0;r<10;++r)for(i=0;i<54;++i)CHECK(live[r*54+i]==(i<3?(i==0?3:0):original[r*54+i]));
  CHECK(!_fmemcmp(owner.baseline,live,540));CHECK(capture_file_begin(next_path,CF_NEW)==CF_BUSY);CHECK(!capture_file_begin(path,CF_APPEND));CHECK(!capture_file_close());
  CHECK(!meta_key_owner_end(&owner) && meta_key_owner_exec_allowed());CHECK(!snapshot_file_begin(stage,CF_NEW));CHECK(!snapshot_file_close());remove(stage);
  CHECK(!meta_key_owner_begin(&owner));_fmemcpy(saved_live,live,540);CHECK(meta_key_owner_load(&owner,"C:\\NONE\\NO.KEY",live,live)==META_OWNER_LOAD && !owner.has_current && !_fmemcmp(live,saved_live,540));CHECK(!meta_key_owner_end(&owner));
  remove(next_path);CHECK(!meta_key_owner_begin(&owner));CHECK(!meta_key_owner_bind(&owner,next_path) && !owner.baseline_exists && !exists(next_path));CHECK(!meta_key_owner_save(&owner,changed) && owner.baseline_exists && matches(next_path,changed,540));CHECK(!meta_key_owner_end(&owner));
  printf("PASS %u checks;claims/load/save/default-create/opaque tails/switch/failure/release\r\n",checks);return 0;
 }
 CHECK(!meta_key_owner_begin(&owner));CHECK(!meta_key_owner_load(&owner,path,live,live));_fmemcpy(saved_live,live,540);
 /* Positive fault modes use the existing actual-DOS boundary injector. Mode99
  * injects a failed lease release, without releasing it underneath the owner. */
 if(mode==96){char alt[64]="C:\\ALT\\NEXT.KEY";CHECK(put(alt,original,540));key_fault_reset(KF_CLOSE_FIRST);status=meta_key_owner_load(&owner,alt,live,live);want_held=1;}
 else if(mode==97){remove(path);key_fault_reset(KF_CREATE_RACE);status=meta_key_owner_load(&owner,path,live,live);want_held=0;}
 else if(mode==99){release_fault=1;status=meta_key_owner_end(&owner);want_held=1;}
 else if(mode==98){key_fault_reset(KF_CLOSE_FIRST);status=meta_key_owner_load(&owner,path,live,live);want_held=1;}
 else{key_fault_reset(mode);status=meta_key_owner_save(&owner,changed);want_held=mode==KF_CLOSE_FIRST || mode==KF_CLOSE_STAGE || mode==KF_CLOSE_RECHECK || mode==KF_CLOSE_BEFORE || mode==KF_ROLLBACK || mode==KF_DELETE_BACKUP || mode==KF_DELETE_STAGE;}
 if(want_held){
  CHECK(status==META_OWNER_RECOVERY && owner.phase==META_OWNER_HELD && owner.claimed);claim_checks();if(mode==96){CHECK(capture_file_begin("C:\\ALT\\NEXT.KEY",CF_NEW)==CF_BUSY);CHECK(snapshot_file_begin("C:\\ALT\\KEYSTG.$$$",CF_NEW)==CF_BUSY);CHECK(monitor_file_begin("C:\\ALT\\KEYBAK.$$$",CF_NEW)==CF_BUSY);}calls=key_calls;
  CHECK(meta_key_owner_bind(&owner,path)==META_OWNER_RECOVERY);CHECK(meta_key_owner_load(&owner,path,live,live)==META_OWNER_RECOVERY);CHECK(meta_key_owner_save(&owner,changed)==META_OWNER_RECOVERY);CHECK(meta_key_owner_end(&owner)==META_OWNER_RECOVERY);CHECK(meta_key_owner_begin(&owner)==META_OWNER_RECOVERY);CHECK(meta_key_owner_begin(&other_owner)==META_OWNER_RECOVERY);CHECK(key_calls==calls && !_fmemcmp(live,saved_live,540));
  if(mode<96){CHECK(exists(stage)==owner.write.stage_exists && exists(backup)==owner.write.original_in_backup);if(owner.write.original_in_backup)CHECK(matches(backup,original,540));if(owner.write.stage_exists && mode!=KF_DELETE_STAGE)CHECK(matches(stage,changed,540));if(mode==KF_DELETE_STAGE)CHECK(matches(stage,changed,1));if(owner.write.installed)CHECK(matches(path,changed,540) && !_fmemcmp(owner.baseline,changed,540));}
  /* Test-only knowledge: release any deliberately left-open injected handle
   * immediately before this process terminates. It does not clear owner HELD. */
  key_fault_cleanup();CHECK(owner.phase==META_OWNER_HELD && !meta_key_owner_exec_allowed());
 }else{
  CHECK(status==(mode==KF_SHORT_READ?META_OWNER_OK:mode==97?META_OWNER_LOAD:META_OWNER_SAVE) && owner.phase==META_OWNER_ACTIVE);
  if(mode==KF_STALE_RECHECK || mode==97){for(r=0;r<10;++r){memset(competitor+r*54,0xa5,54);competitor[r*54]=3;competitor[r*54+1]=0;competitor[r*54+2]='E';competitor[r*54+3]=0;}CHECK(matches(path,competitor,540));}
  else CHECK(matches(path,mode==KF_SHORT_READ?changed:original,540));
  CHECK(!_fmemcmp(live,saved_live,540));
  CHECK(!meta_key_owner_end(&owner) && meta_key_owner_exec_allowed());
 }
 printf("PASS mode %u checks %u quarantine %u;prior/current bytes and lease outcomes\r\n",mode,checks,want_held);return 0;
}
