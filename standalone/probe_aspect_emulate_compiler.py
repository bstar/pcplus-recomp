#!/usr/bin/env python3
"""Private original-compiler oracle for authored EMULATE syntax; no ASX execution."""
import json,sys
from pathlib import Path
import aspect_compiler_probe as oracle
NAMES='TTY VT52 VT100 VT102 VT220 VT320 ANSI IBMPC WYSE75 ATT605 ATT4410 TV922 H19 IBM3101 IBM3161 DGD100 DGD200 DGD210 ADDS60 ADDS90 ADM3 ADM5 ADM31 ESPRIT3 IBM3270 TV910 TV912 TV920 TV925 TV950 TV955 WYSE50 WYSE100'.split()
def corpus():
 cases={}
 def add(label,body):
  source=('integer i\nlong l\nfloat f\nstring s\nproc main\n'+body+'\nendproc\n').replace('\n','\r\n')
  cases['C'+str(len(cases))]=(label,source)
 for name in NAMES:
  add('name '+name,'emulate '+name)
  add('local reserved '+name,'integer '+name+'\nemulate '+name)
 for arg in ('','0','1','6','32','33','255','256','-1','i','l','f','s','i0','l0','s0','"ANSI"','unknown','(ANSI)','ANSI+1',',ANSI','ANSI,','ANSI 1','ANSI VT100','VT420','IBM','ON','OFF','ANSI ; comment'):
  add('operand '+arg,'emulate '+arg)
 add('mixed case','EmUlAtE aNsI');add('two commands','emulate tty\nemulate ansi')
 add('local named ANSI','integer ansi\nemulate ansi')
 return cases

def main():
 cases=corpus();oracle.corpus=lambda:{n:s.encode('cp437') for n,(_,s) in cases.items()};oracle.main()
 out=Path(sys.argv[sys.argv.index('--output')+1]).resolve();r=json.loads((out/'report.json').read_text());records=[]
 for c in r['cases']:
  label,source=cases[c['name']];assert oracle.digest(source.encode('cp437'))==c['source_sha256']
  records.append(dict(label=label,source=source,source_sha256=c['source_sha256'],success=c['success'],**({'hex':c['hex']} if c['success'] else {})))
 (out/'fixture.json').write_text(json.dumps(dict(compiler_sha256=r['compiler_sha256'],probe_sha256=oracle.digest(Path(__file__).read_bytes()),cases=records,scope=__doc__),indent=2)+'\n')
if __name__=='__main__':main()
