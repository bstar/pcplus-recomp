#!/usr/bin/env python3
"""Qualify Watcom standard far overlays with the maintained small-model DS=SS ABI."""
import argparse,json,os,subprocess
from pathlib import Path
from build_path_session import ROOT,sha


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--manager',choices=['none','small','standard'],default='standard');p.add_argument('--code-model',choices=['small','medium'],default='small');p.add_argument('--nested',action='store_true');p.add_argument('--root-pad',type=int,default=0);a=p.parse_args();assert 0<=a.root_pad<=60000
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
 root=r'''#include <stdio.h>
extern unsigned __far __cdecl overlay_a(unsigned);
extern unsigned __far __cdecl overlay_b(unsigned);
static unsigned calls,failures;
static unsigned context(void);
#pragma aux context = "mov ax,ds" "mov dx,ss" "cmp ax,dx" "je done" "xor ax,ax" "done:" value [ax] modify [dx];
unsigned __far __cdecl overlay_callback(unsigned n){++calls;if(!context())++failures;return n;}
int main(void){unsigned i,before=context();
 for(i=0;i<100;++i){if(overlay_a(i)!=i+7)++failures;if(overlay_b(i)!=i+11)++failures;if(overlay_a(i)!=i+7)++failures;if(context()!=before)++failures;}
 printf("OVERLAYS calls=%u failures=%u\n",calls,failures);return failures||calls!=300?1:0;}
'''
 if a.nested:
  root=root.replace('static unsigned calls,failures;','static unsigned calls,failures,busy;')
  root=root.replace('++calls;if(!context())', '++calls;if(!busy){busy=1;if(overlay_b(n)!=n+11)++failures;busy=0;}if(!context())')
  root=root.replace('calls!=300','calls!=600')
 (out/'root.c').write_text(root)
 subprocess.run(['wcc','-q','-bt=dos','-0',('-ms' if a.code_model=='small' else '-mm'),'-ecc','-s','-os','-w4','-we','-fo=root.obj','root.c'],cwd=out,check=True)
 for bank,increment in [('a',7),('b',11)]:
  (out/(bank+'.asm')).write_text('BITS 16\nCPU 8086\nSEGMENT BANK_'+bank.upper()+' public class=CODE use16\nextern _overlay_callback\nglobal _overlay_'+bank+'\n_overlay_'+bank+':\npush bp\nmov bp,sp\npush word [bp+6]\ncall far _overlay_callback\nadd sp,2\nadd ax,'+str(increment)+'\npop bp\nretf\ntimes 2048 db 0\n')
  subprocess.run(['nasm','-fobj',bank+'.asm','-o',bank+'.obj'],cwd=out,check=True)
 if a.root_pad:
  (out/'pad.asm').write_text('BITS 16\nCPU 8086\nSEGMENT _TEXT public class=CODE use16\ntimes '+str(a.root_pad)+' db 0\n')
  subprocess.run(['nasm','-fobj','pad.asm','-o','pad.obj'],cwd=out,check=True)
 (out/'overlay.lnk').write_text('system dos\nname OVERLAY.EXE\noption map=OVERLAY.map\noption stack=8192\nfile root.obj\n'+('file pad.obj\n' if a.root_pad else '')+('file a.obj,b.obj\n' if a.manager=='none' else 'option '+a.manager+'\nbegin\nsection\nfile a.obj\nsection\nfile b.obj\nend\n'))
 subprocess.run(['wlink','@overlay.lnk'],cwd=out,check=True)
 (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nc:\nOVERLAY >REPORT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\ngoto done\n:failed\necho FAIL>FAIL.TXT\n:done\nexit\n')
 with (out/'dosbox.log').open('w') as log:
  r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,
   env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=30)
 raw=(out/'REPORT.TXT').read_text();assert r.returncode==0 and raw=='OVERLAYS calls='+str(600 if a.nested else 300)+' failures=0\n',raw
 assert (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists()
 result=dict(passed=True,manager=a.manager,code_model=a.code_model,callbacks=600 if a.nested else 300,nested=a.nested,root_pad=a.root_pad,original_inputs=[],binary_sha256=sha(out/'OVERLAY.EXE'),
  sources={n:sha(out/n) for n in ['root.c','a.asm','b.asm','overlay.lnk']+(['pad.asm'] if a.root_pad else [])},checker_sha256=sha(Path(__file__)),
  scope=__doc__+' Actual8086 DOS A/B/A switches, far cdecl stack arguments and resident callbacks.'+(' Resident callbacks reenter sibling B before returning to A.' if a.nested else '')+' No application overlay lifetime, interrupts, nonlocal unwind or memory-admission claim.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS standard far overlay ABI probe')


if __name__=='__main__':main()
