#!/usr/bin/env python3
"""Private original-ASPCOMP arithmetic emission oracle; no generated ASX execution.

Reports source-owned scripts, compiler return classifications and exact offsets.
Arithmetic expectations are deliberately not inferred from compilation success.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
SHA='5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a'


def sha(data):return hashlib.sha256(data).hexdigest()


def corpus():
 cases={}
 def add(name,declarations,body,intent):
  source=declarations+'\nproc main\n'+body+'\nendproc\n'
  assert name not in cases, 'Duplicate authored fixture name: '+name
  cases[name]=(source.replace('\n','\r\n').encode('ascii'),intent)
 for prefix,kind,a,b in [('I','integer','17','5'),('L','long','65537','5L')]:
  declarations=f'{kind} va,vb,vc,outcome'
  initialization=f'va = {a}\nvb = {b}\nvc = {b}\n'
  for label,op in [('ADD','+'),('SUB','-'),('MUL','*'),('DIV','/'),('MOD','%')]:
   add(prefix+label,declarations,initialization+f'outcome = va {op} vb',f'{kind} variable operands {op}')
   add(prefix+'C'+label,declarations,initialization+f'outcome = va\noutcome {op}= vb',f'{kind} compound {op}=')
  for label,expression in [('NEGVAR','-va'),('DOUBLE','--va'),('NEGPAR','-(va + vb)'),
   ('PREC','va + vb * vc'),('PAREN','(va + vb) * vc'),('PSUB','va - vb - vc'),
   ('PDIV','va / vb / vc'),('PMIX','va * vb + vc'),('UNIT','+va'),('LEFT','va + (vb * vc)')]:
   add(prefix+label,declarations,initialization+'outcome = '+expression,f'{kind} expression {expression}')
  for label,expression in [('KCONST','17 + 5'),('KDIV','17 / 5'),('KMOD','17 % 5'),
   ('DZ','va / 0'),('MZ','va % 0'),('CDZ','17 / 0'),('CMZ','17 % 0')]:
   add(prefix+label,declarations,initialization+'outcome = '+expression,f'{kind} constant/mixed expression {expression}')
 for name,kind,expression in [
  ('IMAX','integer','32767 + 1'),('IMIN','integer','-32768 - 1'),
  ('INEGDIV','integer','-17 / 5'),('INEGMOD','integer','-17 % 5'),
  ('IDIVOV','integer','-32768 / -1'),('INEGMIN','integer','-(-32768)'),
  ('I65535','integer','65535'),('I32768','integer','32768'),
  ('LNEG','long','-65537'),('LMAX','long','2147483647 + 1L'),
  ('LMIN','long','-2147483648 - 1L'),('LDIVOV','long','-2147483648 / -1L'),
  ('LNEGDIV','long','-65537 / 5L'),('LNEGMOD','long','-65537 % 5L'),
  ('LTOOWIDE','long','4294967296'),('LHEXSIGN','long','0xffffffff'),
  ('LSUFF','long','17L + 5L'),('LMIX','long','65537 + 5'),
  ('LCONST','long','17 + 5'),('LCMIX','long','17L + 5'),
  ('IWRAP','integer','65535 + 1'),('LFLOAT','long','17.0 + 5')]:
  add(name,f'{kind} outcome','outcome = '+expression,f'{kind} boundary {expression}')
 for name,kind,a,b,op in [('IADDEDGE','integer','32767','1','+'),('ISUBEDGE','integer','-32768','1','-'),('IDIVEDGE','integer','-32768','-1','/'),('IMODEDGE','integer','-32768','-1','%'),('LADDEDGE','long','2147483647','1L','+'),('LSUBEDGE','long','-2147483648','1L','-'),('LDIVEDGE','long','-2147483648','-1L','/'),('LMODEDGE','long','-2147483648','-1L','%')]:
  add(name,f'{kind} va,vb,outcome',f'va = {a}\nvb = {b}\noutcome = va {op} vb',f'{kind} variable boundary operation {op}')
 add('MIXVAR','integer va\nlong vb,outcome','va = 5\nvb = 65537\noutcome = va + vb','mixed integer/long variable addition')
 add('MIXREV','integer va\nlong vb,outcome','va = 5\nvb = 65537\noutcome = vb + va','reversed mixed integer/long variable addition')
 add('CHAIN','integer va,vb,outcome','va = 17\nvb = 5\noutcome = va = vb + 1','chained assignment combined with addition')
 add('PREFIX','integer outcome','outcome = 1\n++outcome','prefix increment syntax')
 return cases


def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--output',type=Path,required=True);p.add_argument('--only',action='append')
 a=p.parse_args();out=a.output.resolve()
 assert out.parent==ROOT/'analysis/aspect-arithmetic' and out.name.startswith('compiler-')
 binary=(ROOT/'analysis/pcplus-install/ASPCOMP.EXE').read_bytes();assert sha(binary)==SHA
 out.mkdir(parents=True,exist_ok=False);(out/'ASPCOMP.EXE').write_bytes(binary)
 cases=corpus()
 if a.only:
  assert all(n in cases for n in a.only) and len(set(a.only))==len(a.only)
  cases={n:cases[n] for n in a.only}
 batch=['@echo off']
 for name,(source,_) in cases.items():
  assert len(name)<=8
  (out/(name+'.ASP')).write_bytes(source)
  batch += [f'ASPCOMP {name}.ASP > {name}.LOG',f'if errorlevel 1 goto E{name}',f'echo ZERO>{name}.RC',
   f'goto D{name}',f':E{name}',f'echo NONZERO>{name}.RC',f':D{name}']
 batch+=['echo COMPLETE>DONE.TXT'];(out/'RUN.BAT').write_bytes(('\r\n'.join(batch)+'\r\n').encode())
 config=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=386
cycles=fixed 6000
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{out}"
c:
call RUN.BAT
exit
'''
 (out/'dosbox.conf').write_text(config)
 with (out/'dosbox.log').open('w') as log:
  result=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,
   env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=60)
 assert result.returncode==0 and (out/'DONE.TXT').read_text().strip()=='COMPLETE'
 records=[]
 for name,(source,intent) in cases.items():
  log=(out/(name+'.LOG')).read_bytes();compiled=out/(name+'.ASX');success=b'Script file successfully compiled!' in log
  rc=(out/(name+'.RC')).read_text().strip();assert rc in ('ZERO','NONZERO') and (rc=='ZERO')==success and success==compiled.exists()
  errors=[s for s in log.decode('cp437').splitlines() if s.startswith('Error')]
  record=dict(name=name,intent=intent,source=source.decode('ascii'),source_sha256=sha(source),success=success,
   return_class=rc,errors=errors,log_sha256=sha(log))
  if success:
   data=compiled.read_bytes();record.update(bytes=len(data),asx_sha256=sha(data),hex=data.hex(' '),
    indexed_bytes=[dict(offset=i,hex=f'{byte:02x}') for i,byte in enumerate(data)])
  records.append(record)
 report=dict(compiler_sha256=SHA,harness_sha256=sha(Path(__file__).read_bytes()),cases=records,
  scope='Original compiler arithmetic emission only. All ASP scripts authored here; no ASX executed. Compilation success does not establish computed result, overflow policy, divide-by-zero handling or complete compiler grammar.')
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 for r in records:print(r['name'],r.get('hex',r['errors']))
 print(json.dumps(dict(cases=len(records),accepted=sum(r['success'] for r in records)),indent=2))


if __name__=='__main__':main()
