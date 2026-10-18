#!/usr/bin/env python3
"""Actual DOS KBD selection plus declared IO/seek faults; synthetic files only."""
import hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/keymap-dos';MODULE=ROOT/'src/key_mapping'
COMMON=r'''
#include "keymap_dos.h"
#include "keymap_dos_fs.h"
#include <stdio.h>
#include <string.h>
static unsigned char selected[948],before[948];
static keymap_dos_result result;
static unsigned checks,failures;
static void check(unsigned good,const char *label)
{++checks;if(!good)++failures;printf("%s %s\n",good?"PASS":"FAIL",label);}
static unsigned char pattern(unsigned profile,unsigned at)
{
 unsigned slot=at/12,byte=at%12;
 if(byte==0)return 27;if(byte==1)return '[';if(byte==2)return (unsigned char)('A'+profile%26);
 if(byte==3)return 255;if(byte==4)return (unsigned char)('A'+slot%26);if(byte==5)return 0;
 return (unsigned char)(profile*17+at*7);
}
static unsigned correct(unsigned profile)
{unsigned i;for(i=0;i<948;++i)if(selected[i]!=pattern(profile,i))return 0;return 1;}
static void poison(void){memset(selected,0xa5,948);memcpy(before,selected,948);}
'''
REAL=COMMON+r'''
int main(void)
{
 unsigned i,good=1;
 for(i=0;i<80;++i)if(keymap_dos_read("NORMAL.KBD",i,selected,&result) || !correct(i) ||
 result.file_bytes!=75840UL || result.bytes_read!=948 || result.dos_error || result.close_error)good=0;
 check(good,"all80 profiles exact raw slots and32bit filelength/seek beyond64K");
 poison();check(keymap_dos_read("ABSENT.KBD",6,selected,&result)==KEYMAP_DOS_OPEN && !memcmp(selected,before,948),"missing no destination mutation");
 check(keymap_dos_read("EMPTY.KBD",0,selected,&result)==KEYMAP_DOS_SIZE && !memcmp(selected,before,948),"empty rejected");
 check(keymap_dos_read("SHORT.KBD",0,selected,&result)==KEYMAP_DOS_SIZE && !memcmp(selected,before,948),"nonwhole short block rejected");
 check(keymap_dos_read("SUFFIX.KBD",6,selected,&result)==KEYMAP_DOS_SIZE && !memcmp(selected,before,948),"onebyte suffix rejected");
 check(keymap_dos_read("NORMAL.KBD",80,selected,&result)==KEYMAP_DOS_SIZE && !memcmp(selected,before,948),"absent profile rejected");
 check(keymap_dos_read("BAD.KBD",6,selected,&result)==KEYMAP_DOS_SLOT && !memcmp(selected,before,948),"last selected slot unterminated rejected");
 check(keymap_dos_read("BAD.KBD",4,selected,0)==0 && correct(4),"unselected malformed profile not interpreted optional result");
 good=1;for(i=0;i<48;++i)if(keymap_dos_read("BAD.KBD",6,selected,&result)!=KEYMAP_DOS_SLOT)good=0;
 check(good && keymap_dos_read("NORMAL.KBD",79,selected,&result)==0 && correct(79),"48 errors close handles followed by real valid seek");
 printf("KEYMAP REAL %u checks %u failures\n",checks,failures);return failures?1:0;
}
'''
FAULT=COMMON+r'''
static unsigned mode,opens,closes,reads,seeks;
static unsigned long position;
static void reset(unsigned m)
{mode=m;opens=closes=reads=seeks=0;position=0;poison();}
unsigned keymap_fault_open(const char *path,unsigned flags,int *handle)
{(void)path;(void)flags;++opens;*handle=9;return mode==1?2:0;}
unsigned keymap_fault_close(int handle)
{(void)handle;++closes;return mode==7 || mode==8?6:0;}
unsigned keymap_dos_seek(int handle,unsigned long offset,unsigned origin,unsigned long *out)
{
 (void)handle;++seeks;
 if(mode==2 || (mode==3 && seeks==2))return 5;
 if(origin==2)*out=mode==4?75839UL:mode==5?0:75840UL;
 else {position=offset;*out=mode==6?offset+1:offset;}
 return 0;
}
unsigned keymap_fault_read(int handle,void __far *buffer,unsigned size,unsigned *count)
{
 unsigned i,n=size,profile=(unsigned)(position/948),at=(unsigned)(position%948);
 unsigned char __far *out=(unsigned char __far *)buffer;(void)handle;++reads;*count=0;
 if(mode==8 || mode==9)return 5;
 if(mode==10)return 0;
 if(mode==11 && n>13)n=13;
 for(i=0;i<n;++i)out[i]=mode==12?88:pattern(profile,at+i);
 position+=n;*count=n;return 0;
}
int main(void)
{
 unsigned i,status,want,good;keymap_dos_result prior;char longpath[65];
 for(i=1;i<=12;++i){
  reset(i);status=keymap_dos_read("X",6,selected,&result);
  want=i==1?KEYMAP_DOS_OPEN:(i==2 || i==3 || i==6)?KEYMAP_DOS_SEEK:
   (i==4 || i==5 || i==10)?KEYMAP_DOS_SIZE:i==7?KEYMAP_DOS_CLOSE:
   (i==8 || i==9)?KEYMAP_DOS_READ:i==12?KEYMAP_DOS_SLOT:KEYMAP_DOS_OK;
  good=status==want && result.status==want && opens==1 && closes==(i==1?0:1);
  if(i==11)good=good && correct(6) && reads==73 && result.bytes_read==948;
  else good=good && !memcmp(selected,before,948);
  if(i==7 || i==8)good=good && result.close_error==6;
  if(i==8)good=good && result.dos_error==5;
  check(good,"declared open/seek/read/close/slot fault or fragmented read with atomic commit");
 }
 reset(0);memset(&result,0x77,sizeof(result));prior=result;
 check(keymap_dos_read(0,6,selected,&result)==1 && !opens && !memcmp(&result,&prior,sizeof(result)),"null path rejects before result mutation");
 check(keymap_dos_read("",6,selected,&result)==1 && !opens,"empty path rejected");
 check(keymap_dos_read("X",6,0,&result)==1 && !opens,"null destination rejected");
 check(keymap_dos_read("X",6,(unsigned char *)0xff00,&result)==1 && !opens,"destination wrap rejected");
 check(keymap_dos_read("X",6,selected,(keymap_dos_result *)0xfffc)==1 && !opens,"result wrap rejected");
 check(keymap_dos_read("X",6,selected,(keymap_dos_result *)selected)==1 && !opens && !memcmp(selected,before,948),"result destination alias rejected");
 memcpy(selected,"X",2);memcpy(before,selected,948);
 check(keymap_dos_read((char *)selected,6,selected,&result)==1 && !opens && !memcmp(selected,before,948),"path destination alias rejected");
 memcpy(&result,"X",2);prior=result;
 check(keymap_dos_read((char *)&result,6,selected,&result)==1 && !opens && !memcmp(&result,&prior,sizeof(result)),"path result alias rejected");
 memset(longpath,'A',64);longpath[64]=0;
 check(keymap_dos_read(longpath,6,selected,&result)==1 && !opens,"path64bytes rejected");
 check(keymap_dos_read("X",79,selected,0)==0 && correct(79) && closes==1,"optional result and no33profile ceiling");
 printf("KEYMAP FAULT %u checks %u failures\n",checks,failures);return failures?1:0;
}
'''
def payload():
 def byte(profile,at):
  part=at%12
  return [27,91,65+profile%26,255,65+(at//12)%26,0][part] if part<6 else (profile*17+at*7)&255
 return b''.join(bytes(byte(profile,at) for at in range(948)) for profile in range(80))
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 (OUT/'real.c').write_text(REAL);(OUT/'fault.c').write_text(FAULT)
 for stem,host,extra,sources in [('KMREAL','real.c',[],[MODULE/'keymap_dos_fs.c']),('KMFAULT','fault.c',['-d_dos_open=keymap_fault_open','-d_dos_read=keymap_fault_read','-d_dos_close=keymap_fault_close'],[])]:
  subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-i='+str(MODULE),'-fm='+stem+'.map','-fe='+stem+'.EXE',*extra,str(MODULE/'keymap_dos.c'),*map(str,sources),str(OUT/host)],cwd=OUT,check=True)
 normal=payload();bad=bytearray(normal);bad[6*948+78*12:6*948+79*12]=b'X'*12
 fixtures={'NORMAL.KBD':normal,'BAD.KBD':bytes(bad),'SHORT.KBD':normal[:947],'SUFFIX.KBD':normal+b'X','EMPTY.KBD':b''}
 for name,value in fixtures.items():(OUT/name).write_bytes(value)
 before={name:hashlib.sha256(value).hexdigest() for name,value in fixtures.items()}
 for name in ['PASS.TXT','FAIL.TXT','REAL.TXT','FAULT.TXT']:(OUT/name).unlink(missing_ok=True)
 config=f'''[sdl]\noutput=surface\n[cpu]\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{OUT}"\nc:\nKMREAL >REAL.TXT\nif errorlevel 1 goto fail\nKMFAULT >FAULT.TXT\nif errorlevel 1 goto fail\necho PASS>PASS.TXT\ngoto done\n:fail\necho FAIL>FAIL.TXT\n:done\nexit\n'''
 (OUT/'dosbox.conf').write_text(config)
 with (OUT/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=35)
 logs={name:(OUT/name).read_text() for name in ['REAL.TXT','FAULT.TXT'] if (OUT/name).exists()}
 for name,log in logs.items():print(name+'\n'+log)
 assert (OUT/'PASS.TXT').exists(),logs
 assert 'KEYMAP REAL 9 checks 0 failures' in logs['REAL.TXT'] and 'KEYMAP FAULT 22 checks 0 failures' in logs['FAULT.TXT']
 assert before=={name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in fixtures}
 result={'passed':True,'real_DOS_checks':9,'declared_fault_checks':22,'profiles_tested':80,'destination_size':948,'result_size':14,'synthetic_files_unchanged':before,'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(MODULE.glob('keymap_dos*'))+[Path(__file__).resolve()]},'binary_sha256':{name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in ['KMREAL.EXE','KMFAULT.EXE']},'scope':'Actual DOS source-only reader and separate declared DOS/seek fault model. Synthetic80profile files prove32bit seek/length; selected79strings validated, rawFF and tails preserved. No installed keymap/config/private macros.'}
 (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
