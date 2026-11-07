#!/usr/bin/env python3
"""All256 system slots through native integer/long VM address and read paths."""
import argparse,json,os,shutil,subprocess,sys,re
from pathlib import Path
from build_context_help import ROOT,sha
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source
from test_terminal import SAMPLER
def source(kind,strings=False):
 name='i' if kind==0 else 'l';value='37' if kind==0 else '305419896L'
 if strings:
  conversion='itoa' if kind==0 else 'ltoa'
  return f'''{'integer' if kind==0 else 'long'} {name}
string value_text
proc main
{conversion} {name} value_text
message value_text
{name}={value}
{conversion} {name} value_text
message value_text
endproc
'''
 return f'''{'integer' if kind==0 else 'long'} {name}
proc main
if {name}!=0{'L' if kind else ''}
message "BADZERO"
exit
endif
{name}={value}
if {name}=={value}
message "BANKOK"
else
message "BADBANK"
endif
endproc
'''
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--strings',action='store_true');p.add_argument('--runner',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();runner=a.runner.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(exist_ok=False)
 (out/'snap.asm').write_text(SAMPLER)
 subprocess.run(['nasm','-fbin',str(out/'snap.asm'),'-o',str(out/'SNAP.COM')],check=True)
 binary=sha(runner);shutil.copyfile(runner,out/'ASPECT.EXE');batch=['@echo off'];rows=[]
 for kind in range(2):
  template=compile_source(source(kind,a.strings));token=0x8d+kind
  assert template.count(bytes([token,0]))>=3
  for index in range(256):
   # Simultaneous replacements cannot reinterpret a newly inserted index.
   data=re.sub(bytes([token,0]),lambda m:bytes([0x79+kind,index]),template)
   name=f"{'I' if kind==0 else 'L'}{index:03}";(out/(name+'.ASX')).write_bytes(data)
   batch.extend([f'ASPECT {name}.ASX >{name}.TXT','if errorlevel 1 goto failed'])
   rows.append(dict(slot=index,kind=kind,name=name,ASX_sha256=sha(out/(name+'.ASX'))))
 batch+=['echo PASS>PASS.TXT','goto done',':failed','echo FAIL>FAIL.TXT',':done']
 (out/'RUN.BAT').write_bytes(('\r\n'.join(batch)+'\r\n').encode('ascii'))
 (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nmount d "'+str(out)+'"\nc:\ncall RUN.BAT\nSNAP S\nexit\n')
 with(out/'dosbox.log').open('w')as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=240)
 assert(out/'PASS.TXT').exists()and not(out/'FAIL.TXT').exists()
 for row in rows:
  file=out/(row['name']+'.TXT');assert file.read_bytes()==((b'0\r\n37\r\n' if row['kind']==0 else b'0\r\n305419896\r\n') if a.strings else b'BANKOK\r\n'),(row['slot'],file.read_bytes());row['output_sha256']=sha(file)
 assert sha(out/'ASPECT.EXE')==binary
 report=dict(passed=True,cases=rows,runner_sha256=binary,sources={n:sha(ROOT/n)for n in ['src/aspect/compiler.py','standalone/test_numeric_bank_vm_dos.py','standalone/build_context_help.py','standalone/test_terminal.py']},with_far_global_strings=a.strings,authored_sources=[source(0,a.strings),source(1,a.strings)],original_inputs=[],scope=__doc__+' Authored global references rewritten to full byte-indexed system operands. Zero initialization and native integer/long selection, read/write/conditional through linked production VM. Does not exercise float arithmetic (still unsupported), parent memory or ALARM.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS512 native integer/long system-slot VM cases')
if __name__=='__main__':main()
