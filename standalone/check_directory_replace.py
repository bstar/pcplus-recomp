#!/usr/bin/env python3
"""Actual DOS streaming record replacement plus injected filesystem failures."""
from pathlib import Path
import hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/directory-replace'
COMMON=r'''
#include "directory_replace.h"
#include "directory_replace_fs.h"
#include <dos.h>
#include <stdio.h>
#include <string.h>
static unsigned failures,checks;
static unsigned char expected[114],replacement[114];
static directory_replace_result result;
static char stage[64],backup[64];
static void check(int good,const char *name)
{ ++checks;if(!good)++failures;printf("%s %s\n",good?"PASS":"FAIL",name); }
static unsigned char pattern(unsigned at){return (unsigned char)(at*17U+3U);}
static void records(unsigned entry)
{ unsigned i;for(i=0;i<114;++i){expected[i]=pattern(250+(entry-1)*114+i);replacement[i]=expected[i]^0x5a;} }
'''
REAL=COMMON+r'''
int main(void)
{
 unsigned i,status,entries[3]={1,97,200};directory_dos_selection selection;
 char oldstage[64],oldbackup[64];
 check(directory_replace_paths("c:/sub/test.dir",stage,backup)==0 &&
  !strcmp(stage,"C:\\SUB\\PCPSTG.$$$") && !strcmp(backup,"C:\\SUB\\PCPBAK.$$$"),"derive normalized same-parent drive paths");
 for(i=0;i<3;++i){
  records(entries[i]);status=directory_replace_record("C:\\SUB\\TEST.DIR",stage,backup,entries[i],expected,replacement,&result);
  check(status==0 && result.installed==1 && !result.original_in_backup && !result.stage_exists &&
   result.bytes_processed==23050 && result.source_bytes==23050,"streaming first/middle/final replacement committed with clean recovery flags");
  check(directory_dos_read("C:\\SUB\\TEST.DIR",entries[i],&selection,0)==0 &&
   !memcmp(selection.record,replacement,114),"actual DOS read verifies changed114-byte record");
 }
 records(2);expected[3]^=1;
 check(directory_replace_record("C:\\SUB\\TEST.DIR",stage,backup,2,expected,replacement,&result)==DIRECTORY_REPLACE_STALE &&
  !result.installed && !result.original_in_backup && !result.stage_exists,"stale expected record rejects before rename");
 records(2);
 check(directory_replace_record("C:\\SUB\\TEST.DIR","C:\\SUB\\EXIST.$$$",backup,2,expected,replacement,&result)==DIRECTORY_REPLACE_CONFLICT,"existing stage never overwritten");
 check(directory_replace_record("C:\\SUB\\TEST.DIR",stage,"C:\\SUB\\EXIST.$$$",2,expected,replacement,&result)==DIRECTORY_REPLACE_CONFLICT,"existing backup never overwritten");
 check(directory_replace_record("C:\\SUB\\SHORT.DIR",stage,backup,2,expected,replacement,&result)==DIRECTORY_REPLACE_SIZE &&
  !result.installed && !result.stage_exists,"short original untouched");
 check(directory_replace_record("C:\\SUB\\LONG.DIR",stage,backup,2,expected,replacement,&result)==DIRECTORY_REPLACE_SIZE &&
  !result.installed && !result.stage_exists,"suffix original untouched");
 check(directory_replace_record("C:\\SUB\\ABSENT.DIR",stage,backup,2,expected,replacement,&result)==DIRECTORY_REPLACE_INSPECT,"missing original not created");
 check(_dos_setfileattr("C:\\SUB\\READONLY.DIR",_A_RDONLY)==0,"set synthetic readonly fixture attribute");
 check(directory_replace_record("C:\\SUB\\READONLY.DIR",stage,backup,2,expected,replacement,&result)==DIRECTORY_REPLACE_INSPECT &&
  result.dos_error==5,"readonly original refused");
 _dos_setfileattr("C:\\SUB\\READONLY.DIR",_A_NORMAL);
 memset(stage,0xa5,64);memset(backup,0x5a,64);memcpy(oldstage,stage,64);memcpy(oldbackup,backup,64);
 check(directory_replace_paths("C:\\SUB\\..\\TEST.DIR",stage,backup)==DIRECTORY_REPLACE_ARGUMENT &&
  !memcmp(stage,oldstage,64) && !memcmp(backup,oldbackup,64),"dot alias paths reject without output mutation");
 check(directory_replace_paths("C:\\SUB\\CON.DIR",stage,backup)==DIRECTORY_REPLACE_ARGUMENT,"DOS reserved device rejected");
 check(directory_replace_paths("C:\\SUB\\PCPSTG.$$$",stage,backup)==DIRECTORY_REPLACE_ARGUMENT,"recovery name not accepted as target");
 check(directory_replace_paths("D:TEST.DIR",stage,backup)==0 && !strcmp(stage,"D:PCPSTG.$$$"),"drive-relative parent preserved");
 check(directory_replace_paths("TEST.DIR",stage,backup)==0 && !strcmp(stage,"PCPSTG.$$$"),"current-directory leaf supported");
 check(directory_replace_paths("\\SUB\\TEST.DIR",stage,backup)==0 && !strcmp(stage,"\\SUB\\PCPSTG.$$$"),"current-drive rooted path supported");
 printf("DIRECTORY REPLACE REAL %u checks %u failures\n",checks,failures);return failures?1:0;
}
'''
FAULT=COMMON+r'''
static unsigned mode,target_exists,stage_exists,backup_exists,target_new,source_live,stage_live;
static unsigned source_position,write_position,open_calls,rename_calls,delete_calls,close_calls;
static unsigned kind(const char *name)
{ return !strcmp(name,"T.DIR")?1:!strcmp(name,"S.DIR")?2:!strcmp(name,"B.DIR")?3:0; }
static void reset(unsigned value)
{
 mode=value;target_exists=1;stage_exists=mode==1;backup_exists=mode==2;target_new=0;
 source_live=stage_live=source_position=write_position=open_calls=rename_calls=delete_calls=close_calls=0;
 records(2);memset(&result,0xcc,sizeof(result));
}
unsigned directory_fault_attr(const char *name,unsigned *attr)
{
 unsigned k=kind(name);*attr=0;if(mode==21 && k==1)return 5;
 if(k==1 && mode==3)*attr=_A_RDONLY;
 return (k==1?target_exists:k==2?stage_exists:backup_exists)?0:2;
}
unsigned directory_fault_open(const char *name,unsigned flags,int *handle)
{ (void)name;(void)flags;++open_calls;if(mode==4)return 5;source_live=1;*handle=1;return 0; }
unsigned directory_fault_create(const char *name,unsigned attr,int *handle)
{
 (void)name;(void)attr;if(mode==5)return 5;
 if(mode==23){stage_exists=1;return 80;}
 if(stage_exists)return 80;stage_exists=stage_live=1;*handle=2;return 0;
}
unsigned directory_fault_read(int handle,void __far *buffer,unsigned amount,unsigned *bytes)
{
 unsigned i,count,limit=mode==17?23049:mode==18?23051:23050;
 unsigned char __far *out=(unsigned char __far *)buffer;
 (void)handle;*bytes=0;
 if(mode==6 || mode==15 || (mode==20 && source_position==23050))return 5;
 count=source_position<limit?limit-source_position:0;if(count>amount)count=amount;
 if(mode==16 && count>13)count=13;
 for(i=0;i<count;++i){out[i]=pattern(source_position+i);if(mode==19 && source_position+i==367)out[i]^=1;}
 source_position+=count;*bytes=count;return 0;
}
unsigned directory_fault_write(int handle,const void __far *buffer,unsigned amount,unsigned *bytes)
{
 unsigned i,at,count=amount;const unsigned char __far *in=(const unsigned char __far *)buffer;
 (void)handle;*bytes=0;if(mode==7)return 5;
 if(mode==8)count=amount/2;
 for(i=0;i<count;++i){at=write_position+i;
  if(in[i]!=(at>=364 && at<478?replacement[at-364]:pattern(at)))return 13;
 }
 write_position+=count;*bytes=count;return 0;
}
unsigned directory_fault_close(int handle)
{
 ++close_calls;if(handle==1)source_live=0;else stage_live=0;
 return (mode==9 && handle==2) || (mode==10 && handle==1) || mode==22?6:0;
}
unsigned directory_replace_rename(const char *from,const char *to)
{
 unsigned f=kind(from),t=kind(to);++rename_calls;
 if(source_live || stage_live)return 6;
 if(f==1 && t==3){if(mode==11)return 5;target_exists=0;backup_exists=1;return 0;}
 if(f==2 && t==1){if(mode==12 || mode==13)return 5;stage_exists=0;target_exists=target_new=1;return 0;}
 if(f==3 && t==1){if(mode==13)return 5;backup_exists=0;target_exists=1;return 0;}
 return 13;
}
unsigned directory_replace_delete(const char *name)
{
 unsigned k=kind(name);++delete_calls;
 if(k==2){if(mode==15)return 5;stage_exists=0;return 0;}
 if(k==3){if(mode==14)return 5;backup_exists=0;return 0;}
 return 13;
}
int main(void)
{
 static const unsigned statuses[24]={0,2,2,3,4,5,6,9,9,10,10,11,12,12,13,6,0,7,7,8,6,3,10,5};
 unsigned i,status,good;directory_replace_result prior;
 check(directory_replace_paths("T.DIR",stage,backup)==0 && !strcmp(stage,"PCPSTG.$$$") && !strcmp(backup,"PCPBAK.$$$"),"path helper pure fault-build invocation");
 for(i=0;i<24;++i){
  reset(i);status=directory_replace_record("T.DIR","S.DIR","B.DIR",2,expected,replacement,&result);
  good=status==statuses[i] && result.status==status && !source_live && !stage_live;
  if(i==0 || i==16)good=good && target_exists && target_new && !stage_exists && !backup_exists &&
   result.installed && !result.original_in_backup && !result.stage_exists && result.bytes_processed==23050 && result.source_bytes==23050;
  else if(i==14)good=good && target_exists && target_new && backup_exists && result.installed && result.original_in_backup && result.cleanup_error==5;
  else if(i==13)good=good && !target_exists && backup_exists && !result.installed && result.original_in_backup && result.rollback_error==5;
  else good=good && target_exists && !target_new && !result.installed;
  if(i==15)good=good && stage_exists && result.stage_exists && result.cleanup_error==5;
  if(i==9 || i==10 || i==22)good=good && !rename_calls && result.close_error==6;
  if(i==12)good=good && !backup_exists && !result.original_in_backup && !result.rollback_error;
  if(i==23)good=good && stage_exists && !result.stage_exists && !delete_calls;
  if(i==6 || i==7 || i==8 || i==17 || i==18 || i==19 || i==20)good=good && !rename_calls;
  check(good,"injected orchestration case: exact status/original/recovery/close/rename invariants");
 }
 reset(0);prior=result;
 check(directory_replace_record("T.DIR","t.dir","B.DIR",2,expected,replacement,&result)==1 && !open_calls && !memcmp(&result,&prior,sizeof(result)),"case alias rejected before IO/result mutation");
 check(directory_replace_record("C:\\A\\T.DIR","C:\\B\\S.DIR","C:\\A\\B.DIR",2,expected,replacement,&result)==1 && !open_calls,"different parents rejected");
 check(directory_replace_record("T.DIR","S.DIR","B.DIR",0,expected,replacement,&result)==1 && !open_calls,"entry0 rejected");
 check(directory_replace_record("T.DIR","S.DIR","B.DIR",201,expected,replacement,&result)==1 && !open_calls,"entry201 rejected");
 check(directory_replace_record("T.DIR","S.DIR","B.DIR",2,(unsigned char *)0xffe0,replacement,&result)==1 && !open_calls,"expected near-wrap rejected");
 check(directory_replace_record("T.DIR","S.DIR","B.DIR",2,expected,(unsigned char *)0xffe0,&result)==1 && !open_calls,"replacement near-wrap rejected");
 check(directory_replace_record("T.DIR","S.DIR","B.DIR",2,expected,replacement,(directory_replace_result *)expected)==1 && !open_calls,"result/input overlap rejected");
 check(directory_replace_record("T.DIR","S.DIR","B.DIR",2,expected,replacement,(directory_replace_result *)0xfff0)==1 && !open_calls,"result near-wrap rejected");
 reset(0);check(directory_replace_record("T.DIR","S.DIR","B.DIR",2,expected,replacement,0)==0 && target_new,"optional result success");
 printf("DIRECTORY REPLACE FAULT %u checks %u failures\n",checks,failures);return failures?1:0;
}
'''
def main():
 OUT.mkdir(parents=True,exist_ok=True);sub=OUT/'SUB';sub.mkdir(exist_ok=True)
 (OUT/'real.c').write_text(REAL);(OUT/'fault.c').write_text(FAULT)
 directory=ROOT/'src/directory'
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-i='+str(directory),'-fe=DRREAL.EXE',str(directory/'directory_replace.c'),str(directory/'directory_replace_fs.c'),str(directory/'directory_dos.c'),str(OUT/'real.c')],cwd=OUT,check=True)
 macros=['-d_dos_getfileattr=directory_fault_attr','-d_dos_open=directory_fault_open','-d_dos_creatnew=directory_fault_create','-d_dos_read=directory_fault_read','-d_dos_write=directory_fault_write','-d_dos_close=directory_fault_close']
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-i='+str(directory),'-fe=DRFAULT.EXE',*macros,str(directory/'directory_replace.c'),str(OUT/'fault.c')],cwd=OUT,check=True)
 data=bytes((i*17+3)&255 for i in range(23050));want=bytearray(data)
 for entry in (1,97,200):
  at=250+(entry-1)*114;want[at:at+114]=bytes(value^0x5a for value in data[at:at+114])
 fixtures={'TEST.DIR':data,'SHORT.DIR':data[:-1],'LONG.DIR':data+b'X','READONLY.DIR':data,'EXIST.$$$':b'existing recovery file; do not overwrite'}
 for name,value in fixtures.items():(sub/name).write_bytes(value)
 for name in ('PCPSTG.$$$','PCPBAK.$$$','ABSENT.DIR'):(sub/name).unlink(missing_ok=True)
 for name in ('PASS.TXT','FAIL.TXT','REAL.TXT','FAULT.TXT'):(OUT/name).unlink(missing_ok=True)
 conf=f'''[sdl]\noutput=surface\n[cpu]\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{OUT}"\nc:\nDRREAL >REAL.TXT\nif errorlevel 1 goto fail\nDRFAULT >FAULT.TXT\nif errorlevel 1 goto fail\necho PASS>PASS.TXT\ngoto done\n:fail\necho FAIL>FAIL.TXT\n:done\nexit\n'''
 (OUT/'dosbox.conf').write_text(conf)
 with (OUT/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=40)
 logs={name:(OUT/name).read_text() for name in ('REAL.TXT','FAULT.TXT') if (OUT/name).exists()}
 for name,log in logs.items():print(name+'\n'+log)
 assert (OUT/'PASS.TXT').exists(),logs
 assert (sub/'TEST.DIR').read_bytes()==want
 assert all((sub/name).read_bytes()==value for name,value in fixtures.items() if name!='TEST.DIR')
 assert not any((sub/name).exists() for name in ('PCPSTG.$$$','PCPBAK.$$$','ABSENT.DIR'))
 result={'passed':True,'real_DOS_checks':logs['REAL.TXT'].count('PASS '),'fault_checks':logs['FAULT.TXT'].count('PASS '),'full_target_matches_exact_three_record_patch':True,'other_fixtures_unchanged':True,'recovery_files_absent_after_success':True,'binary_sha256':{name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in ('DRREAL.EXE','DRFAULT.EXE')},'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (directory/'directory_replace.c',directory/'directory_replace.h',directory/'directory_replace.inc',directory/'directory_replace_fs.c',directory/'directory_replace_fs.h',Path(__file__).resolve())},'scope':'Actual source-built DOS streaming replacement at absolute same-parent paths; synthetic files only. Separate declared DOS/rename/delete fault injection exercises recovery states. No original/private files, crash-atomic or concurrent-writer guarantee.'}
 (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
