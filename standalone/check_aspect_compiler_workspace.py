#!/usr/bin/env python3
"""Actual DOS borrowed compiler workspace, alias/bounds checks and ownership."""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
from build_aspect_compiler_dos import ROOT,MODULES
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source
DRIVER=r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dos.h>
#include "compiler_program_internal.h"
#include "compiler_heap_snapshot.h"
static struct _heapinfo before[128],after[128];
static unsigned checks,failures;
static void ck(unsigned ok){++checks;if(!ok)++failures;}
static void owned(unsigned count){
 unsigned n=0,i;ck(!compiler_far_heap_snapshot(after,128,&n));ck(n==count);
 for(i=0;i<n&&i<count;++i)ck(before[i]._pentry==after[i]._pentry&&before[i]._size==after[i]._size);
}
int main(void){
 FILE *in,*out;aspect_compiler_report r;unsigned n=sizeof(pc_compiler),count=0,i;
 unsigned char *area,*foreign,*work;unsigned char saved[sizeof(r)];
 in=fopen("OWNER.ASP","rb");out=fopen("OWNER.ASX","w+b");if(!in||!out)return 98;
 ck(!aspect_compiler_program(in,out,&r));
 area=malloc(n+8);foreign=malloc(37);if(!area||!foreign)return 97;
 memset(area,0xa5,n+8);memset(foreign,0x5a,37);work=area+4;
 ck(!compiler_far_heap_snapshot(before,128,&count));
 ck(aspect_compiler_program_workspace(in,out,&r,0,n)==ASPECT_COMPILE_STATE);
 ck(aspect_compiler_program_workspace(in,out,&r,work,n-1)==ASPECT_COMPILE_STATE);
 ck(aspect_compiler_program_workspace(in,out,&r,work+1,n)==ASPECT_COMPILE_STATE);
 ck(aspect_compiler_program_workspace(in,out,&r,MK_FP(FP_SEG(work),65534U),n)==ASPECT_COMPILE_STATE);
 ck(aspect_compiler_program_workspace(in,out,&r,MK_FP(65535U,0),n)==ASPECT_COMPILE_STATE);
 memset(&r,0xa5,sizeof(r));memcpy(saved,&r,sizeof(r));
 ck(aspect_compiler_program_workspace(in,out,&r,&r,n)==ASPECT_COMPILE_STATE);
 ck(!memcmp(saved,&r,sizeof(r)));
 if(FP_OFF(&r)>=16){
  ck(aspect_compiler_program_workspace(in,out,&r,MK_FP(FP_SEG(&r)+1,FP_OFF(&r)-16),n)==ASPECT_COMPILE_STATE);
  ck(!memcmp(saved,&r,sizeof(r)));
 }
 ck(aspect_compiler_program_workspace(in,out,&r,in,n)==ASPECT_COMPILE_STATE);
 ck(aspect_compiler_program_workspace(in,out,&r,out,n)==ASPECT_COMPILE_STATE);
 ck(aspect_compiler_program_workspace(in,in,&r,work,n)==ASPECT_COMPILE_STATE);
 owned(count);
 for(i=0;i<n+8;++i)ck(area[i]==0xa5);
 for(i=0;i<100;++i){
  unsigned j;rewind(in);rewind(out);ck(!aspect_compiler_program_workspace(in,out,&r,work,n));
  for(j=0;j<4;++j)ck(area[j]==0xa5&&area[n+4+j]==0xa5);
  ck(foreign[0]==0x5a&&foreign[36]==0x5a);owned(count);
 }
 ck(!fclose(in));ck(!fclose(out));
 in=fopen("BAD.ASP","rb");out=fopen("BAD.ASX","w+b");if(!in||!out)return 96;
 ck(aspect_compiler_program_workspace(in,out,&r,work,n)==ASPECT_COMPILE_SYNTAX);
 ck(foreign[0]==0x5a&&foreign[36]==0x5a);ck(!fclose(in));ck(!fclose(out));
 for(i=0;i<4;++i)ck(area[i]==0xa5&&area[n+4+i]==0xa5);
 free(area);free(foreign);
 printf("WORKSPACE %u bytes VALUE %u NODE %u CHECKS %u FAILURES %u\n",n,sizeof(aspect_compiler_value),sizeof(aspect_compiler_node),checks,failures);
 return failures?1:0;
}
'''
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    driver=out/'workspace.c';driver.write_text(DRIVER)
    sources=[ROOT/'src/aspect'/(name+'.c')for name in MODULES]
    subprocess.run(['wcl','-q','-bt=dos','-0','-ml','-fpc','-ecc','-s','-w4','-we','-k32768',
        '-i='+str(ROOT/'src/aspect'),'-i='+str(ROOT/'standalone'),'-fe=WORK.EXE',str(driver),
        str(ROOT/'standalone/compiler_heap_snapshot.c'),*map(str,sources)],cwd=out,check=True)
    source='integer a\nproc main\na=1+2*3\nif a\nmessage "workspace"\nendif\nendproc\n'
    (out/'OWNER.ASP').write_text(source);(out/'BAD.ASP').write_text('proc main\nunknown\nendproc\n')
    config=out/'dosbox.conf';config.write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 12000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nc:\nWORK >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\nexit\n:failed\necho FAIL>FAIL.TXT\nexit\n')
    with (out/'dosbox.log').open('w')as log:
        run=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(config)],cwd=out,
            env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=30)
    assert run.returncode==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),(out/'RESULT.TXT').read_text()
    assert (out/'OWNER.ASX').read_bytes()==compile_source(source)
    result=dict(passed=True,summary=(out/'RESULT.TXT').read_text().strip(),borrowed_cycles=100,
        binary_sha256=sha(out/'WORK.EXE'),checker_sha256=sha(Path(__file__)),
        sources={str(path.relative_to(ROOT)):sha(path)for path in [*sources,*sorted((ROOT/'src/aspect').glob('compiler_*.h')),ROOT/'standalone/compiler_heap_snapshot.c',ROOT/'standalone/compiler_heap_snapshot.h']},
        scope=__doc__+' All context/foreign allocations and guard bytes remain owned by their callers. API failures preserve the borrowed span; real-mode physical aliases and wraps reject.')
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(result['summary'])
if __name__=='__main__':main()
