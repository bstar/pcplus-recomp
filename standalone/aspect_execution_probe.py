#!/usr/bin/env python3
"""Private original compiler oracle for source-owned numeric execution fixtures."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SHA='5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a'
def sha(data):return hashlib.sha256(data).hexdigest()
def corpus():
 cases={
 'EMPTY':('proc main\nendproc\n',{}),
 'ASSIGN':('integer result\nproc main\nresult = 7\nendproc\n',{'integer0':7}),
 'LONG':('long result\nproc main\nresult = 65535\nendproc\n',{'long0':65535}),
 'IFTRUE':('integer result\nproc main\nif 1\nresult = 7\nelse\nresult = 9\nendif\nendproc\n',{'integer0':7}),
 'IFFALSE':('integer result\nproc main\nif 0\nresult = 7\nelse\nresult = 9\nendif\nendproc\n',{'integer0':9}),
 'CALL':('integer result\nproc main\ncall helper\nendproc\nproc helper\nresult = 23\nendproc\n',{'integer0':23}),
 'FRAME':('integer result\nproc main\ninteger first\nfirst = 23\ncall helper\nendproc\nproc helper\ninteger second\nsecond = 42\nresult = second\nendproc\n',{'integer0':42}),
 'CMP':('integer result\nproc main\nif 3 < 7\nresult = 11\nelse\nresult = 13\nendif\nendproc\n',{'integer0':11}),
 'WHILE':('integer result\nproc main\nresult = 3\nwhile result\nresult--\nendwhile\nendproc\n',{'integer0':0}),
 'POSTDEC':('integer result\nproc main\nresult = 3\nresult--\nendproc\n',{'integer0':2}),
 'POSTINC':('integer result\nproc main\nresult = 3\nresult++\nendproc\n',{'integer0':4}),
 'BOOLEAN':('integer result\nproc main\nif 1 && 0\nresult = 2\nelse\nresult = 6\nendif\nendproc\n',{'integer0':6}),
 'LONGCMP':('integer result\nlong wide\nproc main\nwide = 65535\nif wide > 32768\nresult = 17\nelse\nresult = 19\nendif\nendproc\n',{'integer0':17,'long0':65535}),
 'FLOAT':('float value\nproc main\nvalue = 7.0\nendproc\n',{'error':'float'}),
 'STRINGS':('string first,second\nproc main\nendproc\n',{'allocated':2}),
 'STR128':(''.join(f'string value{i}\n' for i in range(128))+'proc main\nendproc\n',{'allocated':128}),
 'ENDLESS':('proc main\nwhile 1\nendwhile\nendproc\n',{'error':'budget'}),
 'RECURSE':('proc main\ncall main\nendproc\n',{'error':'stack','limit':65000}),
 'PAUSE':('proc main\npause 7\nendproc\n',{'error':'unsupported'}),
 }
 return {name:(text.replace('\n','\r\n').encode('ascii'),expect) for name,(text,expect) in cases.items()}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
 out=args.output.resolve();assert out.parent==ROOT/'analysis/aspect-vm-runtime' and out.name.startswith('execution-')
 data=(ROOT/'analysis/pcplus-install/ASPCOMP.EXE').read_bytes();assert sha(data)==SHA
 out.mkdir(parents=True,exist_ok=False);(out/'ASPCOMP.EXE').write_bytes(data)
 batch=['@echo off'];cases=corpus()
 for name,(source,_) in cases.items():
  (out/(name+'.ASP')).write_bytes(source)
  batch += [f'ASPCOMP {name}.ASP > {name}.LOG',f'if errorlevel 1 goto E{name}',f'echo ZERO>{name}.RC',f'goto D{name}',f':E{name}',f'echo NONZERO>{name}.RC',f':D{name}']
 batch+=['echo COMPLETE>DONE.TXT'];(out/'RUN.BAT').write_bytes(('\r\n'.join(batch)+'\r\n').encode())
 conf=f'''[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=386\ncycles=fixed 6000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{out}"\nc:\ncall RUN.BAT\nexit\n'''
 (out/'dosbox.conf').write_text(conf)
 with (out/'dosbox.log').open('w') as log:
  r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=60)
 assert r.returncode==0 and (out/'DONE.TXT').read_text().strip()=='COMPLETE'
 records=[]
 for name,(source,expect) in cases.items():
  log=(out/(name+'.LOG')).read_bytes();asx=out/(name+'.ASX');ok=b'Script file successfully compiled!' in log
  assert ok==asx.exists() and ((out/(name+'.RC')).read_text().strip()=='ZERO')==ok
  record=dict(name=name,success=ok,source_sha256=sha(source),source=source.decode('ascii'),expected=expect,log_sha256=sha(log))
  if ok:record.update(asx_sha256=sha(asx.read_bytes()),hex=asx.read_bytes().hex(' '))
  else:record['diagnostic']=log.decode('cp437')
  records.append(record)
 report=dict(compiler_sha256=SHA,harness_sha256=sha(Path(__file__).read_bytes()),cases=records,scope='Original compiler only; source-owned fixtures, no ASX execution or maintained compiler claim.')
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 for r in records:print(r['name'],r.get('hex',r.get('diagnostic','')[-200:]))
 print('accepted',sum(r['success'] for r in records),'of',len(records))
if __name__=='__main__':main()
