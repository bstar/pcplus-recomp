#!/usr/bin/env python3
"""Full-capacity lazy near numeric banks with real DOS allocation and faults."""
import argparse,json,os,re,subprocess
from pathlib import Path
from build_context_help import ROOT,sha
NAMES=['src/aspect/numeric_bank_runtime.c','src/aspect/numeric_bank_runtime.h','src/aspect/runtime.h','standalone/numeric_bank_diagnostic.c','standalone/test_numeric_banks_dos.py','standalone/build_context_help.py']
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(exist_ok=False)
 sources={n:sha(ROOT/n)for n in NAMES}
 flags=['-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-i='+str(ROOT/'src/aspect')]
 subprocess.run(['wcc',*flags,'-d_nmalloc=probe_allocate','-d_nfree=probe_free','-fo='+str(out/'bank.obj'),str(ROOT/NAMES[0])],cwd=out,check=True)
 subprocess.run(['wcl',*flags,'-k8192','-fe=BANKS.EXE',str(ROOT/'standalone/numeric_bank_diagnostic.c'),str(out/'bank.obj')],cwd=out,check=True)
 (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nc:\nBANKS >REPORT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\nexit\n:failed\necho FAIL>FAIL.TXT\nexit\n')
 with (out/'dosbox.log').open('w')as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=30)
 text=(out/'REPORT.TXT').read_text();match=re.fullmatch(r'NUMERIC BANK PASS (\d+) checks (\d+) allocations (\d+) frees\s*',text)
 assert match and (out/'PASS.TXT').exists()and not(out/'FAIL.TXT').exists(),text
 assert int(match[1])>30000 and int(match[2])==int(match[3])+5
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 report=dict(passed=True,checks=int(match[1]),allocations=int(match[2]),frees=int(match[3]),sources=sources,binary_sha256=sha(out/'BANKS.EXE'),original_inputs=[],scope=__doc__+' Full256-system/128-float slots,8bytes each, stable per-slot near identity, within-group contiguity, isolation/reset; first/second-bank and same-bank group allocation faults retain other owner;100 reuse cycles and foreign allocation preservation. Native operand adapters and VM/parent memory are separate integration gates.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(text.strip())
if __name__=='__main__':main()
