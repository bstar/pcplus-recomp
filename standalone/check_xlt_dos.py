#!/usr/bin/env python3
"""Actual DOS checked XLT reader and separate declared DOS fault tests."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/translation-dos'
MODULE = ROOT / 'src/translation'
COMMON = r'''
#include "xlt_dos.h"
#include <stdio.h>
#include <string.h>
static unsigned char guarded[258],prior[258];
#define selected (guarded+1)
static xlt_dos_result result;
static unsigned checks,failures;
static void check(unsigned good,const char *label)
{++checks;if(!good)++failures;printf("%s %s\n",good?"PASS":"FAIL",label);}
static void poison(void){memset(guarded,0xa5,sizeof(guarded));memcpy(prior,guarded,sizeof(guarded));}
static unsigned correct(void)
{unsigned i;for(i=0;i<256;++i)if(selected[i]!=(unsigned char)(i*73+19))return 0;return guarded[0]==0xa5 && guarded[257]==0xa5;}
'''
REAL = COMMON + r'''
int main(void)
{
 unsigned i,good=1;const char *bad[]={"EMPTY.XLT","ONE.XLT","SHORT.XLT","SUFFIX.XLT","LONG.XLT"};
 poison();check(xlt_dos_read("NORMAL.XLT",selected,&result)==0 && correct() && result.bytes_read==256 && !result.dos_error && !result.close_error,"all256 byte values including NUL SUB FF loaded with guards");
 poison();check(xlt_dos_read("ABSENT.XLT",selected,&result)==XLT_DOS_OPEN && !memcmp(guarded,prior,258),"missing file preserves destination");
 for(i=0;i<5;++i){poison();check(xlt_dos_read(bad[i],selected,&result)==XLT_DOS_SIZE && !memcmp(guarded,prior,258),bad[i]);}
 poison();check(xlt_dos_read("ZERO.XLT",selected,0)==0 && selected[0]==0 && selected[255]==0,"nonbijective allzero table and optional result accepted");
 poison();for(i=0;i<48;++i)if(xlt_dos_read("SHORT.XLT",selected,&result)!=XLT_DOS_SIZE)good=0;
 check(good && xlt_dos_read("NORMAL.XLT",selected,&result)==0 && correct(),"48 rejected reads close handles followed by valid load");
 printf("XLT REAL %u checks %u failures\n",checks,failures);return failures?1:0;
}
'''
FAULT = COMMON + r'''
static unsigned mode,opens,closes,reads,position;
static void reset(unsigned m){mode=m;opens=closes=reads=position=0;poison();memset(&result,0x97,sizeof(result));}
unsigned __cdecl xlt_fault_open(const char *path,unsigned flags,int *handle)
{(void)path;(void)flags;++opens;*handle=mode==10?0:9;return mode==1?2:0;}
unsigned __cdecl xlt_fault_close(int handle)
{(void)handle;++closes;return mode==4 || mode==5?6:0;}
unsigned __cdecl xlt_fault_read(int handle,void *buffer,unsigned size,unsigned *count)
{
 unsigned i,n=size;unsigned char *out=buffer;(void)handle;++reads;*count=0;
 if(mode==2 || mode==5 || (mode==3 && reads==2))return 5;
 if(mode==7 && position>=32)return 0;
 if(mode==8 && position==256){out[0]=88;*count=1;++position;return 0;}
 if(position>=256)return 0;
 if(mode==6 && n>13)n=13;
 if(mode==7 && n>32)n=32;
 for(i=0;i<n;++i)out[i]=(unsigned char)((position+i)*73+19);
 position+=n;*count=n;return 0;
}
int main(void)
{
 unsigned i;unsigned status;char longpath[65];xlt_dos_result before;
 for(i=0;i<=10;++i){
  if(i==9)continue;
  reset(i);status=xlt_dos_read("X",selected,&result);
  if(i==0 || i==6 || i==10)check(status==0 && correct() && closes==1 && result.bytes_read==256,"valid onechunk fragmented and DOS handle0");
  else {
   unsigned want=i==1?XLT_DOS_OPEN:(i==2 || i==3 || i==5)?XLT_DOS_READ:i==4?XLT_DOS_CLOSE:XLT_DOS_SIZE;
   check(status==want && !memcmp(guarded,prior,258) && closes==(i==1?0:1),"failure preserves complete destination and closes once");
   if(i==5)check(result.dos_error==5 && result.close_error==6,"primary read error retained alongside close error");
  }
 }
 reset(0);before=result;check(xlt_dos_read(0,selected,&result)==1 && !opens && !memcmp(&before,&result,sizeof(result)),"null path no IO result unchanged");
 check(xlt_dos_read("",selected,&result)==1 && !opens,"empty path");
 check(xlt_dos_read("X",0,&result)==1 && !opens,"null destination");
 check(xlt_dos_read("X",(unsigned char *)0xff01,&result)==1 && !opens,"destination wrap");
 *(char *)0xffff='X';check(xlt_dos_read((char *)0xffff,selected,&result)==1 && !opens,"path extent wrap");
 check(xlt_dos_read("X",selected,(xlt_dos_result *)0xfffc)==1 && !opens,"result wrap");
 check(xlt_dos_read("X",selected,(xlt_dos_result *)selected)==1 && !opens && !memcmp(guarded,prior,258),"result destination alias");
 memcpy(selected,"X",2);memcpy(prior,guarded,258);
 check(xlt_dos_read((char *)selected,selected,&result)==1 && !opens && !memcmp(guarded,prior,258),"path destination alias");
 memcpy(&result,"X",2);before=result;
 check(xlt_dos_read((char *)&result,selected,&result)==1 && !opens && !memcmp(&before,&result,sizeof(result)),"path result alias");
 memset(longpath,'A',64);longpath[64]=0;check(xlt_dos_read(longpath,selected,&result)==1 && !opens,"64byte path rejected");
 reset(6);check(xlt_dos_read("X",selected,0)==0 && correct() && reads==21 && closes==1,"optional result fragmented read and EOF probe");
 printf("XLT FAULT %u checks %u failures\n",checks,failures);return failures?1:0;
}
'''


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fixtures = {'NORMAL.XLT': bytes((i * 73 + 19) & 255 for i in range(256)),
                'ZERO.XLT': bytes(256)}
    fixtures.update({name: bytes((i * 29 + 7) & 255 for i in range(size))
                     for name, size in [('EMPTY.XLT', 0), ('ONE.XLT', 1), ('SHORT.XLT', 255),
                                        ('SUFFIX.XLT', 257), ('LONG.XLT', 512)]})
    for name, blob in fixtures.items():
        (OUT / name).write_bytes(blob)
    for name, text in [('real', REAL), ('fault', FAULT)]:
        host = OUT / (name + '.c')
        host.write_text(text)
        definitions = [] if name == 'real' else ['-dxlt_fs_open=xlt_fault_open',
            '-dxlt_fs_read=xlt_fault_read', '-dxlt_fs_close=xlt_fault_close']
        subprocess.run(['wcl', '-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we', '-k8192',
                        '-i=' + str(MODULE), '-fe=' + name.upper() + '.EXE',
                        *definitions, str(MODULE / 'xlt_dos.c'), *([str(MODULE / 'xlt_dos_fs.c')] if name == 'real' else []), str(host)], cwd=OUT, check=True)
    for name in ('PASS.TXT', 'FAIL.TXT', 'REAL.TXT', 'FAULT.TXT'):
        (OUT / name).unlink(missing_ok=True)
    config = f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 10000
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{OUT}"
c:
REAL >REAL.TXT
if errorlevel 1 goto fail
FAULT >FAULT.TXT
if errorlevel 1 goto fail
echo PASS>PASS.TXT
goto done
:fail
echo FAIL>FAIL.TXT
:done
exit
'''
    (OUT / 'dosbox.conf').write_text(config)
    with (OUT / 'dosbox.log').open('w') as log:
        subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(OUT / 'dosbox.conf')],
                       env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'),
                       stdout=log, stderr=log, check=True, timeout=35)
    logs = {name: (OUT / name).read_text() for name in ('REAL.TXT', 'FAULT.TXT') if (OUT / name).exists()}
    for name, log in logs.items():
        print(name + '\n' + log)
    assert (OUT / 'PASS.TXT').exists() and not (OUT / 'FAIL.TXT').exists(), logs
    counts = {}
    for name, log in logs.items():
        match = re.search(r'XLT (REAL|FAULT) (\d+) checks 0 failures', log)
        assert match, log
        counts[match[1]] = int(match[2])
    for name, blob in fixtures.items():
        assert (OUT / name).read_bytes() == blob
    inputs = [Path(__file__).resolve(), *sorted(MODULE.glob('xlt_dos*'))]
    report = {'passed': True, 'checks': counts,
              'sources': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
              'binaries': {name: hashlib.sha256((OUT / name).read_bytes()).hexdigest() for name in ('REAL.EXE', 'FAULT.EXE')},
              'fixtures_unchanged': {name: hashlib.sha256(blob).hexdigest() for name, blob in fixtures.items()},
              'scope': 'Actual DOSBox-X 8086 strict loader and separate declared DOS error/short-read model; no live terminal integration.'}
    (OUT / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print('XLT DOS checks:', counts)


if __name__ == '__main__':
    main()
