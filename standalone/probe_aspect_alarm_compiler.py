#!/usr/bin/env python3
"""Optional private original-compiler oracle for authored ALARM grammar."""
import json,sys
from pathlib import Path
import aspect_compiler_probe as oracle

def corpus():
 cases={}
 def add(label,body,helper=''):
  text='integer i\nlong l\nfloat f\nstring s\nproc main\n'+body+'\nendproc\n'+helper
  cases['C'+str(len(cases))]=(label,text.replace('\n','\r\n'))
 for arg in ('','0','1','3','-1','-32768','-32769','32767','32768','65535','65536','1L','0.0','i','l','f','s','i0','i9','l0','s0','forever','success','failure','found','(1)','(i)','1+1','i+1','"3"',',1','1,','1 2',',','; comment'):
  add('alarm '+arg,'alarm '+arg)
 add('case insensitive','AlArM 1')
 add('local','integer local\nalarm local')
 add('parameter','call worker with 1',helper='proc worker\nintparm duration\nalarm duration\nendproc\n')
 add('two alarms','alarm\nalarm 0')
 return cases

def main():
 cases=corpus();oracle.corpus=lambda:{n:s.encode('cp437') for n,(_,s) in cases.items()};oracle.main()
 out=Path(sys.argv[sys.argv.index('--output')+1]).resolve();r=json.loads((out/'report.json').read_text());records=[]
 for c in r['cases']:
  label,source=cases[c['name']];assert oracle.digest(source.encode('cp437'))==c['source_sha256']
  records.append(dict(label=label,source=source,source_sha256=c['source_sha256'],success=c['success'],**({'hex':c['hex']} if c['success'] else {})))
 result=dict(compiler_sha256=r['compiler_sha256'],probe_sha256=oracle.digest(Path(__file__).read_bytes()),cases=records,scope='Authored ALARM original compiler grammar/emission only; no ASX executed, no maintained compiler or VM binding implied.')
 (out/'fixture.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
