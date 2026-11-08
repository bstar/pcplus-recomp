#!/usr/bin/env python3
"""Actual DOS controls for the optional high status wrapper; no application inputs."""
import argparse,hashlib,json,os,shutil,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
 child=out/'child';child.mkdir()
 (child/'child.c').write_text('''#include <dos.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(void){union REGS in,out;FILE *f;unsigned psp;
in.h.ah=0x62;intdos(&in,&out);psp=out.x.bx;
if(psp>=0xa000 || *(unsigned __far *)MK_FP(psp,0x16)<0xa000)return 91;
if(!getenv("LOC_ENV") || strcmp(getenv("LOC_ENV"),"KEEP ME"))return 92;
if(!getenv("PCPLUS") || strcmp(getenv("PCPLUS"),"D:\\\\OWNED"))return 93;
if(!getenv("COMSPEC") || strcmp(getenv("COMSPEC"),"Z:\\\\COMMAND.COM"))return 94;
f=fopen("D:\\\\CHILD.OK","wb");if(!f)return 95;
fputs("ENVIRONMENT+LOW-CHILD",f);if(fclose(f))return 96;return 17;}
''')
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-k1024','-fe=TERMINAL.EXE','child.c'],cwd=child,check=True)
 source=ROOT/'standalone/dos_status_runner.asm';rows=[]
 for case in ('high','not-loaded-high','no-UMB','missing-child'):
  folder=out/case;folder.mkdir()
  if case!='missing-child':shutil.copyfile(child/'TERMINAL.EXE',folder/'TERMINAL.EXE')
  subprocess.run(['nasm','-fbin','-DSTATUS_RUNNER_HIGH',str(source),'-o',str(folder/'RUNSTAT.COM')],check=True)
  subprocess.run(['nasm','-fbin',str(ROOT/'standalone/dos_strategy_sample.asm'),'-o',str(folder/'STRAT.COM')],check=True)
  umb=case!='no-UMB';prefix='' if case=='not-loaded-high' else 'LOADHIGH '
  (folder/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncputype=386\n[mixer]\nnosound=true\n[dos]\nxms=true\nems=false\numb='+str(umb).lower()+'\n[autoexec]\n@echo off\nmount c "'+str(folder)+'"\nmount d "'+str(folder)+'"\nc:\nset LOC_ENV=KEEP ME\nset PCPLUS=D:\\OWNED\nset COMSPEC=Z:\\COMMAND.COM\nSTRAT B\nMEM /C >BEFORE.TXT\n'+prefix+'RUNSTAT\nSTRAT A\nMEM /C >AFTER.TXT\nexit\n')
  with (folder/'dosbox.log').open('w') as log:
   subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],cwd=folder,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=15,check=True)
  status=struct.unpack('<3H',(folder/'EXITCODE.BIN').read_bytes())
  assert (folder/'STRATB.BIN').read_bytes()==(folder/'STRATA.BIN').read_bytes()==b'\0\0'
  assert (folder/'BEFORE.TXT').read_bytes()==(folder/'AFTER.TXT').read_bytes()
  if case=='high':
   assert status==(0,0,17) and (folder/'CHILD.OK').read_bytes()==b'ENVIRONMENT+LOW-CHILD'
  else:assert status==(1,2 if case=='missing-child' else 8,0xff7e) and not (folder/'CHILD.OK').exists(),(case,status)
  if case in ('high','missing-child'):
   proof=struct.unpack('<6H',(folder/'ENVPROOF.BIN').read_bytes());assert proof[:2]==(0x5354,1) and proof[3]>=0xa000 and proof[4]>0 and proof[5]==1
  else:proof=None
  rows.append(dict(case=case,passed=True,status=status,environment_proof=proof,strategy_and_free_memory_restored=True))
  print(case,'PASS',status,flush=True)
 names=['standalone/test_status_runner_high_dos.py','standalone/dos_status_runner.asm','standalone/dos_strategy_sample.asm']
 r=dict(passed=True,cases=rows,original_inputs=[],sources={n:sha(ROOT/n) for n in names},artifacts={str(f.relative_to(out)):sha(f) for f in out.rglob('*') if f.is_file()},scope=__doc__+' Synthetic environment/child only; copied full environment checked before freeing old owned block. Child verifies inherited values and conventional placement with high wrapper parent. Known exit17 and missing-file error2, low/no-UMB refusal8, allocation strategy and MEM byte reports checked. No BBS/SIP/hardware acceptance.')
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n')


if __name__=='__main__':main()
