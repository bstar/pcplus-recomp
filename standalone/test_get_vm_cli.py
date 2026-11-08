#!/usr/bin/env python3
"""DOS8086 full GET-enabled CLI: globals, healthy return and unattached refusal."""
import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('child','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();child=a.child.resolve();out=a.output.resolve()
 assert child.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
 manifest=json.loads((child/'manifest.json').read_text());assert manifest['experimental_get_VM'] and manifest['experimental_near_globals']
 assert sha(child/'ASPECT.EXE')==manifest['binary_sha256']
 for name,h in manifest['sources'].items():assert sha(ROOT/name)==h,name
 sys.path.insert(0,str(ROOT/'src/aspect'));from compiler import compile_source
 many=''.join('string s%d\n'%i for i in range(128))
 vectors=[('HEALTHY','proc main\nmessage "HEALTHY"\nendproc\n',0,b'HEALTHY'),
  ('GLOBALS',many+'proc main\ns0="FIRST"\ns127="LAST"\nmessage s0\nmessage s127\nendproc\n',0,b'FIRST\r\nLAST'),
  ('LONGSTR',many+'proc main\ns127="'+('X'*80)+'"\nmessage s127\nendproc\n',0,b'X'*80),
  ('MIXED',many+'integer n\nlong wide\nproc main\nn=32767\nwide=65536\nitoa n s0\nltoa wide s127\nfopen 0 \"MIXED.TXT\" \"wb\"\nfputs 0 s0\nfputs 0 s127\nfclose 0\nmessage s0\nmessage s127\nendproc\n',0,b'32767\r\n65536'),
  ('DIVZERO','string a,b\ninteger n,z\nproc main\na="KEPT"\nn=1/z\nendproc\n',11,None),
  ('RAWGET',None,3,None),('MISSING',None,1,None)]
 out.mkdir();shutil.copyfile(child/'ASPECT.EXE',out/'ASPECT.EXE');commands=['@echo off'];records=[]
 for index,(name,source,error,expected) in enumerate(vectors):
  if source is not None:wire=compile_source(source);(out/(name+'.ASX')).write_bytes(wire)
  elif name=='RAWGET':wire=bytes.fromhex('01cf498c0001ab0a0094');(out/(name+'.ASX')).write_bytes(wire)
  else:wire=None
  commands+=['ASPECT '+name+'.ASX >R'+str(index)+'.TXT',
   'if errorlevel '+str(error+1)+' goto failed',
   *(['if not errorlevel '+str(error)+' goto failed'] if error else [])]
  records.append(dict(case=name,expected_exit=error,expected_stdout_hex=expected.hex() if expected else None,script_sha256=sha(out/(name+'.ASX')) if wire else None))
 commands+=['echo PASS>STATUS.TXT','goto done',':failed','echo FAIL>STATUS.TXT',':done','exit']
 (out/'RUN.BAT').write_bytes(('\r\n'.join(commands)+'\r\n').encode())
 (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\nmount c "'+str(out)+'"\nc:\nRUN\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=30)
 assert (out/'STATUS.TXT').read_text().strip()=='PASS'
 for index,record in enumerate(records):
  data=(out/('R'+str(index)+'.TXT')).read_bytes();expected=record['expected_stdout_hex']
  if expected:assert bytes.fromhex(expected) in data,(record['case'],data)
  record.update(passed=True,stdout_sha256=sha(out/('R'+str(index)+'.TXT')))
 assert (out/'MIXED.TXT').read_bytes()==b'3276765536'
 report=dict(passed=True,cases=records,child_sha256=manifest['binary_sha256'],original_inputs=[],compiler_GET_enabled=False,
  sources={str(Path(__file__).resolve().relative_to(ROOT)):sha(__file__),'src/aspect/compiler.py':sha(ROOT/'src/aspect/compiler.py')},
  scope=__doc__+' Full actual CLI/DOS files/near-global allocator/native dispatch/near-far GET entry and abort.128 global strings, integer/long co-residency, an owned stream and80-character value retain capacity; error and unattached GET explicitly refuse. No renderer/UART/BBS/physical or near-exhaustion/far-fallback acceptance.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS GET full CLI:',len(records),'cases,128 globals,80-byte string,DOS8086')

if __name__=='__main__':main()
