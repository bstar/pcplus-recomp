#!/usr/bin/env python3
"""Execute banked decoder vectors in DOS8086, including original viewer row oracles."""
import argparse,json,os,random,re,shutil,struct,subprocess
from pathlib import Path
from build_path_session import ROOT,sha

def reference(data,width,rows,start=0):
 lines=[];at=0;limit=min(len(data),0xffffffff-start)
 while at<limit and len(lines)<rows:
  end=min(at+133,limit);lf=data.find(b'\n',at,end)
  if lf>=0:end=lf+1
  chunk=data[at:end];at=end
  # An overflow has not completed its partial chunk: bytes stay untrimmed.
  complete=chunk.endswith(b'\n') or len(chunk)==133 or limit==len(data)
  visible=chunk[:width].split(b'\0',1)[0]
  if complete:visible=visible.rstrip(bytes(range(33)))
  lines.append(visible.ljust(width,b' '))
  if not complete:break
 status=1 if len(lines)==rows and complete else 4 if limit<len(data) else 2
 return at,status,start+at,b''.join(lines).ljust(width*rows,b' ')

def vectors():
 long=b'L'*79+b'A\r\n'+b'M'*80+b'B\r\n'+b'X'*132+b'1\r\n'+b'Y'*133+b'2\r\nDONE\r\n'
 binary=b'TAB\tMID\r\nC\rR\nNUL\0HIDDEN\r\nZ\x1aAFTER\r\nE\x1b[31mRED\r\n'+bytes([0x80,0x81,0xdb,0xb0,0xff])+b'\r\nTRAIL  \t\x1a\r\n \t\r\n'
 fixtures=[('long',long),('binary',binary),('empty',b''),('unterminated',b'NO FINAL NEWLINE'),
  ('no-lf',b'A'*400),('exact-page',b''.join(('L%03d\r\n'%i).encode() for i in range(1,25))),
  ('large',b''.join(('L%04d'%i).encode()+b'X'*125+b'\r\n' for i in range(529,553))),
  ('retry',b'FOUND AFTER RETRY\r\n')]
 # Explicit original-frame row expectations, independent of the generic model.
 original_rows=[[b'L'*79+b'A',b'M'*80,b'X'*80,b'',b'Y'*80,b'2',b'DONE'],
  [b'TAB\tMID',b'C\rR',b'NUL',b'Z\x1aAFTER',b'E\x1b[31mRED',bytes([0x80,0x81,0xdb,0xb0,0xff]),b'TRAIL'],
  [],[b'NO FINAL NEWLINE'],[b'A'*80]*3+[b'A'],
  [('L%03d'%i).encode() for i in range(1,25)],
  [('L%04d'%i).encode()+b'X'*75 for i in range(529,553)],[b'FOUND AFTER RETRY']]
 result=[]
 for (name,data),lines in zip(fixtures,original_rows):
  start=69696 if name=='large' else 0;want=b''.join(r.ljust(80,b' ') for r in lines).ljust(1920,b' ')
  used,status,next_at,page=reference(data,80,24,start);assert page==want
  for block in [1,2,7,80,132,133,134,256]:
   result.append(dict(name=name,width=80,rows=24,block=block,start=start,data=data,used=used,status=status,next=next_at,page=want,original_oracle=True))
 rng=random.Random(0x5650);random_bytes=bytes(rng.randrange(256) for _ in range(600))
 for width in [1,2,79,80,81,131,132]:
  for rows in [1,2,24,49]:
   for block in [1,127,256]:
    used,status,next_at,page=reference(random_bytes,width,rows,0x123456)
    result.append(dict(name='geometry-random',width=width,rows=rows,block=block,start=0x123456,data=random_bytes,used=used,status=status,next=next_at,page=page,original_oracle=False))
 extras=[('all-control',bytes(range(33))*8,80,24,0),('NUL-first',b'\0HIDDEN\r\nNEXT\0LAST\n',80,24,0),
  ('all-space',b' '*399,132,49,0),('large-input',b'A'*4096,132,49,0),
  ('overflow-partial',b'AB',80,24,0xfffffffe),('overflow-control',b'\tX',80,24,0xfffffffe),
  ('overflow-immediate',b'A',80,24,0xffffffff),('max-offset-EOF',b'A',80,24,0xfffffffe),
  ('max-offset-page',b'\nX',80,1,0xfffffffe)]
 for name,data,width,rows,start in extras:
  for block in [1,133,256]:
   used,status,next_at,page=reference(data,width,rows,start)
   result.append(dict(name=name,width=width,rows=rows,block=block,start=start,data=data,used=used,status=status,next=next_at,page=page,original_oracle=False))
 return result

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['program','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();binary=a.program.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 manifest=json.loads(binary.with_name('manifest.json').read_text());assert sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 out.mkdir(parents=True);drive=out/'drive';drive.mkdir();shutil.copyfile(binary,drive/'DECODE.EXE');cases=vectors()
 blob=b'VD01'+struct.pack('<H',len(cases))
 for v in cases:blob+=struct.pack('<6H2L',v['width'],v['rows'],v['block'],len(v['data']),v['used'],v['status'],v['start'],v['next'])+v['data']+v['page']
 (drive/'VECTORS.BIN').write_bytes(blob)
 config=out/'dosbox.conf';config.write_text(f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
fpu=false
cycles=fixed 6000
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{drive}"
c:
DECODE > RESULT.TXT
if errorlevel 1 echo FAIL>EXIT.TXT
if not errorlevel 1 echo PASS>EXIT.TXT
exit
''')
 with (out/'dosbox.log').open('w') as log:
  subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(config)],cwd=out,
   env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=180)
 text=(drive/'RESULT.TXT').read_text();match=re.search(r'VIEWDECODE vectors=(\d+) checks=(\d+) failures=0',text)
 assert match and int(match[1])==len(cases) and 'FAIL' not in text and (drive/'EXIT.TXT').read_text().strip()=='PASS',text
 assert (drive/'VECTORS.BIN').read_bytes()==blob and sha(drive/'DECODE.EXE')==sha(binary)
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 r=dict(passed=True,binary_sha256=sha(binary),vectors=len(cases),state_placements=2,checks=int(match[2]),
  cases=[{k:v for k,v in c.items() if k not in ['data','page']} for c in cases],cpu='8086',FPU=False,
  sources={**manifest['sources'],'standalone/test_viewer_decode_dos.py':sha(Path(__file__))},original_inputs=[],
  artifacts={str(f.relative_to(out)):sha(f) for f in out.rglob('*') if f.is_file()},
  scope=__doc__+' Actual8086 code with near/DGROUP and far/FILE_CODE state, bounded feeds, exact pages/consumption/offset/status, invalid argument no-change checks and memory guards. Original row expectations are explicit, not original executable inputs. Component only; no DOS file owner, UI/UART, full viewer or hardware acceptance.')
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS viewer decoder:',len(cases),'vectors,',r['checks'],'DOS checks')
if __name__=='__main__':main()
