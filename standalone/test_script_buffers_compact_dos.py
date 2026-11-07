#!/usr/bin/env python3
"""Compare legacy and fixed64/96 script-buffer admission across16-bit boundaries."""
import argparse,json,os,subprocess
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(exist_ok=False)
 source=(ROOT/'src/terminal/script_launch.c').read_text()
 block=source[source.index('/* Fixed script buffers:'):source.index('#ifndef ASPECT_EMULATE_POLICY\nstatic unsigned folded(')]
 block+='\n#ifndef ASPECT_EMULATE_POLICY\nstatic unsigned buffers(const void *e,const void *t){return span(e,64)&&span(t,96)&&apart(e,64,t,96);}\n#endif\n'
 (out/'buffers.h').write_text(block)
 program=r'''
#include <stdio.h>
#define span original_span
#define apart original_apart
#define buffers original_buffers
#include "buffers.h"
#undef span
#undef apart
#undef buffers
#define ASPECT_EMULATE_POLICY 1
#define buffers compact_buffers
#include "buffers.h"
static unsigned long failures;
static unsigned long count;
static void pair(unsigned a,unsigned b){
 if(original_buffers((void *)a,(void *)b)!=compact_buffers((void *)a,(void *)b))++failures;
 ++count;
}
int main(void){
 static const unsigned fixed[]={0,1,63,64,95,96,65439,65440,65441,65471,65472,65473,65535};
 static const int delta[]={-97,-96,-95,-65,-64,-63,-1,0,1,63,64,65,95,96,97};
 unsigned long a;unsigned i,b;
 if(!compact_buffers((void *)1,(void *)65)||!compact_buffers((void *)97,(void *)1)||
 compact_buffers((void *)1,(void *)64)||compact_buffers((void *)65473,(void *)1)||
 !compact_buffers((void *)65472,(void *)1)||compact_buffers((void *)1,(void *)65441))return 2;
 for(a=0;a<65536UL;++a){
  for(i=0;i<sizeof(fixed)/sizeof(fixed[0]);++i){pair((unsigned)a,fixed[i]);pair(fixed[i],(unsigned)a);}
  for(i=0;i<sizeof(delta)/sizeof(delta[0]);++i){b=(unsigned)((long)a+delta[i]);pair((unsigned)a,b);}
 }
 printf("SCRIPT_BUFFERS %lu cases %lu failures\n",count,failures);return failures?1:0;
}
'''
 (out/'test.c').write_text(program)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-ob','-os','-w4','-we','-k4096','-fe=BUFFERS.EXE',str(out/'test.c')],cwd=out,check=True)
 (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nc:\nBUFFERS >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\nexit\n:failed\necho FAIL>FAIL.TXT\nexit\n')
 with(out/'dosbox.log').open('w')as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=90)
 count=65536*(26+15);text=(out/'RESULT.TXT').read_text();assert (out/'PASS.TXT').exists() and not(out/'FAIL.TXT').exists() and text.strip()=='SCRIPT_BUFFERS '+str(count)+' cases 0 failures',text
 names=['src/terminal/script_launch.c','standalone/test_script_buffers_compact_dos.py','standalone/build_context_help.py']
 result=dict(passed=True,cases=count,sources={n:sha(ROOT/n)for n in names},artifacts={p.name:sha(p)for p in out.iterdir()if p.is_file()},original_inputs=[],scope=__doc__+' Actual DOS8086 source branches: all offsets against fixed end/wrap/null boundaries in both positions and all offsets at relative overlap/touch edges. Pure extent/separation only; no pointer dereference or all2^32 pair enumeration. Buffer sizes remain64/96, with exact end65536 admitted.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(text.strip())
if __name__=='__main__':main()
