#!/usr/bin/env python3
"""Optional private original-compiler oracle for authored DATE/TIME sources."""
import hashlib,json,sys
from pathlib import Path
import aspect_compiler_probe as oracle
ROOT=oracle.ROOT

def corpus():
 cases={}
 def add(label,body,decl='integer i\nlong l\nfloat f\nstring result',helper=''):
  text=decl+'\nproc main\n'+body+'\nendproc\n'+helper
  cases['C'+str(len(cases))]=(label,text.replace('\n','\r\n'))
 for dest in ('result','s0','s9','i','l','f','i0','$null','"literal"','(result)','result+"x"',''):
  add('date '+dest,'date '+dest)
  for arg in ('0','1','2','-1','i','l','f','(0)','1+0','"24"',''):
   add('time '+dest+' '+arg,'time '+dest+' '+arg)
 for command in ('date local','time local 0','time local 1'):
  add('local '+command,'string local\n'+command+'\nstrcpy result local')
 for command in ('date value','time value 0','time value 1'):
  add('parameter '+command,'call worker with "OLD"',helper='proc worker\nstrparm value\n'+command+'\nstrcpy result value\nendproc\n')
 for body in ('date result 0','date result,','time result,0','time result,1','time result,,1','time result 0 1','time result 32767','time result 32768','time result 65535','time result 1L','time 0 result'):
  add(body,body)
 return cases

def main():
 cases=corpus();oracle.corpus=lambda:{n:s.encode('cp437') for n,(_,s) in cases.items()}
 oracle.main()
 args=sys.argv;out=Path(args[args.index('--output')+1]).resolve();report=json.loads((out/'report.json').read_text())
 records=[]
 for r in report['cases']:
  label,source=cases[r['name']];assert hashlib.sha256(source.encode('cp437')).hexdigest()==r['source_sha256']
  records.append(dict(label=label,source=source,source_sha256=r['source_sha256'],success=r['success'],**({'hex':r['hex']} if r['success'] else {})))
 fixture=dict(compiler_sha256=report['compiler_sha256'],probe_sha256=oracle.digest(Path(__file__).read_bytes()),cases=records,scope='Authored original compiler DATE/TIME grammar and emitted ASX only. No generated script executed; no original compiler or resource is a normal build input.')
 (out/'fixture.json').write_text(json.dumps(fixture,indent=2)+'\n')
if __name__=='__main__':main()
