#!/usr/bin/env python3
"""Native mixed integer/long aliasing at sparse-group boundaries."""
import argparse,json,os,re,shutil,subprocess,sys
from pathlib import Path
from build_context_help import ROOT,sha
from test_terminal import SAMPLER
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source
SOURCE='''integer i
long l
string value_text
proc main
ltoa l value_text
message value_text
l=305419896L
ltoa l value_text
message value_text
itoa i value_text
message value_text
i=4660
ltoa l value_text
message value_text
itoa i value_text
message value_text
endproc
'''
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runner',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();runner=a.runner.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(exist_ok=False)
 template=compile_source(SOURCE);shutil.copyfile(runner,out/'ASPECT.EXE');batch=['@echo off'];rows=[]
 for i in (0,15,16,31,32,127,128,239,240,255):
  value=re.sub(rb'[\x8d\x8e]\x00',lambda m:bytes([0x79 if m[0][0]==0x8d else 0x7a,i]),template);name=f'A{i:03}'
  (out/(name+'.ASX')).write_bytes(value);batch.extend([f'ASPECT {name}.ASX >{name}.TXT','if errorlevel 1 goto failed']);rows.append(dict(slot=i,name=name,ASX_sha256=sha(out/(name+'.ASX'))))
 batch+=['echo PASS>PASS.TXT','goto done',':failed','echo FAIL>FAIL.TXT',':done'];(out/'RUN.BAT').write_bytes(('\r\n'.join(batch)+'\r\n').encode())
 (out/'snap.asm').write_text(SAMPLER);subprocess.run(['nasm','-fbin',str(out/'snap.asm'),'-o',str(out/'SNAP.COM')],check=True)
 (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nmount d "'+str(out)+'"\nc:\ncall RUN.BAT\nSNAP S\nexit\n')
 with(out/'dosbox.log').open('w')as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=30)
 assert(out/'PASS.TXT').exists()and not(out/'FAIL.TXT').exists()
 for row in rows:
  file=out/(row['name']+'.TXT');assert file.read_bytes()==b'0\r\n305419896\r\n22136\r\n305402420\r\n4660\r\n',(row['slot'],file.read_bytes());row['output_sha256']=sha(file)
 assert sha(out/'ASPECT.EXE')==sha(runner)
 result=dict(passed=True,runner_sha256=sha(runner),cases=rows,source=SOURCE,sources={n:sha(ROOT/n)for n in ['standalone/test_numeric_group_alias_dos.py','standalone/test_terminal.py','standalone/build_context_help.py','src/aspect/compiler.py']},original_inputs=[],scope=__doc__+' Authored global references mapped to one system slot. Integer writes preserve the high long word and integer reads observe the low word, through native VM address/read and ITOA/LTOA adapters and far global strings. Includes slot0 without condition temporaries clobbering the alias. No float arithmetic/physical claim.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS ten native mixed-view aliases')
if __name__=='__main__':main()
