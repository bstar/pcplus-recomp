#!/usr/bin/env python3
"""Exhaustively compare source branches of the parent handoff's four hex digits."""
import argparse,json,os,subprocess
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(exist_ok=False)
 source=(ROOT/'src/terminal/script_launch.c').read_text();block=source[source.index('static char digit('):source.index('/* Fixed script buffers:')]
 (out/'words.h').write_text(block)
 program=r'''
#include <stdio.h>
#include <string.h>
#define digit original_digit
#define hexword original_hexword
#include "words.h"
#undef digit
#undef hexword
#define ASPECT_EMULATE_POLICY 1
#define digit compact_digit
#define hexword compact_hexword
#include "words.h"
int main(void){
 unsigned long n;unsigned i;char a[8],b[8],*x,*y;
 for(n=0;n<65536UL;++n){
  memset(a,'Z',8);memset(b,'Z',8);
  x=original_hexword(a+2,(unsigned)n);y=compact_hexword(b+2,(unsigned)n);
  if(x!=a+6||y!=b+6||memcmp(a,b,8)||a[0]!='Z'||a[1]!='Z'||a[6]!='Z'||a[7]!='Z')return 1;
  for(i=2;i<6;++i)if(!((a[i]>='0'&&a[i]<='9')||(a[i]>='A'&&a[i]<='F')))return 2;
 }
 puts("SCRIPT_WORD 65536 cases 0 failures");return 0;
}
'''
 (out/'test.c').write_text(program)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-ob','-os','-w4','-we','-k4096','-fe=WORDS.EXE',str(out/'test.c')],cwd=out,check=True)
 (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nc:\nWORDS >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\nexit\n:failed\necho FAIL>FAIL.TXT\nexit\n')
 with(out/'dosbox.log').open('w')as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=60)
 text=(out/'RESULT.TXT').read_text();assert (out/'PASS.TXT').exists() and not(out/'FAIL.TXT').exists() and text.strip()=='SCRIPT_WORD 65536 cases 0 failures',text
 names=['src/terminal/script_launch.c','standalone/test_script_word_compact_dos.py','standalone/build_context_help.py']
 result=dict(passed=True,cases=65536,sources={n:sha(ROOT/n)for n in names},artifacts={p.name:sha(p)for p in out.iterdir()if p.is_file()},original_inputs=[],scope=__doc__+' Actual DOS8086, all16-bit values, exact four uppercase digits, return pointer and surrounding bytes. Both actual C source branches under the same flags. No descriptor/EXEC, arbitrary pointer or hardware acceptance claim.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(text.strip())
if __name__=='__main__':main()
