#!/usr/bin/env python3
"""Exercise controller read-ahead, cached/rescanned paging and cancellation in DOS8086."""
import argparse,json,os,re,shutil,struct,subprocess
from pathlib import Path
from build_path_session import ROOT,sha
from test_viewer_decode_dos import reference

def fixtures():
 return {'LONG.DAT':b'L'*79+b'A\r\n'+b'M'*80+b'B\r\n'+b'X'*132+b'1\r\n'+b'Y'*133+b'2\r\nDONE\r\n',
 'BINARY.DAT':b'TAB\tMID\r\nC\rR\nNUL\0HIDDEN\r\nZ\x1aAFTER\r\nE\x1b[31mRED\r\n'+bytes([0x80,0x81,0xdb,0xb0,0xff])+b'\r\nTRAIL  \t\x1a\r\n \t\r\n',
 'EMPTY.DAT':b'', 'EXACT.DAT':b''.join(('L%03d\r\n'%i).encode() for i in range(1,25)),
 'LINES25.DAT':b''.join(('L%03d\r\n'%i).encode() for i in range(1,26)),
 'PAGES.DAT':b''.join(('L%04d'%i).encode()+b'X'*125+b'\r\n' for i in range(1,3001)),
 'NO-LF.DAT':b'A'*4096,'CHUNK.DAT':b'X'*(133*24)}

def scenarios():
 files=fixtures();results=[]
 def make(name,file,width,rows,commands):
  data=files[file];pages=[];at=0
  while True:
   used,status,next_at,page=reference(data[at:],width,rows,at);pages.append((next_at,status,page));at=next_at
   if status==2:break
  current=0;actions=[]
  for command in [0]+commands:
   need_rescan=command==6
   if need_rescan:command=2
   status=0
   if command==1:current=0
   elif command==2:
    if current:current-=1
    else:status=4
   elif command==3:
    if pages[current][1]==2:status=5
    else:current+=1
   next_at,_,page=pages[current]
   actions.append(dict(op=command,status=status,phase=2,rescan=int(need_rescan),page=current,next=next_at,characters=page))
  results.append(dict(name=name,path='D:\\'+file,width=width,rows=rows,start_status=0,actions=actions))
 make('binary-original','BINARY.DAT',80,24,[3,2,1])
 make('long-read-ahead','LONG.DAT',80,2,[3,3,3,3,2,2,2,1,2])
 make('exact-EOF','EXACT.DAT',80,24,[3,3,2,2,1])
 make('partial-EOF','LINES25.DAT',80,24,[3,3,2,1])
 make('empty','EMPTY.DAT',80,24,[3,2,1])
 make('wide-no-LF','NO-LF.DAT',132,49,[3,1])
 make('exact-chunks','CHUNK.DAT',80,24,[3,3,2,1])
 # After page101, cache spans39..102. Previous to38 must rescan from0.
 make('past-native-cap-and-rescan','PAGES.DAT',80,24,[3]*101+[2]*62+[6]+[3,1,3])
 results.append(dict(name='cancel-before-read',path='D:\\LONG.DAT',width=80,rows=24,start_status=0,
  actions=[dict(op=3,status=2,phase=1,rescan=0,page=0,next=0),dict(op=4,status=0,phase=5,rescan=0,page=0,next=0)]))
 results.append(dict(name='cancel-after-one-read',path='D:\\LONG.DAT',width=80,rows=24,start_status=0,
  actions=[dict(op=5,status=0,phase=1,rescan=0,page=0,next=0),dict(op=4,status=0,phase=5,rescan=0,page=0,next=0)]))
 results.append(dict(name='missing-open',path='D:\\MISSING.DAT',width=80,rows=24,start_status=6,
  actions=[dict(op=0,status=6,phase=3,rescan=0,page=0,next=0),dict(op=4,status=6,phase=5,rescan=0,page=0,next=0)]))
 return results

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['program','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();binary=a.program.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 manifest=json.loads(binary.with_name('manifest.json').read_text());assert sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 out.mkdir(parents=True);c=out/'c';d=out/'d';c.mkdir();d.mkdir();shutil.copyfile(binary,c/'VIEWPAGE.EXE')
 for name,data in fixtures().items():(d/name).write_bytes(data)
 input_hashes={name:sha(d/name) for name in fixtures()};cases=scenarios();blob=b'VS01'+struct.pack('<H',len(cases))
 for case in cases:
  blob+=struct.pack('<64s4H',case['path'].encode(),case['width'],case['rows'],len(case['actions']),case['start_status'])
  for a0 in case['actions']:
   blob+=struct.pack('<4H2L',a0['op'],a0['status'],a0['phase'],a0['rescan'],a0['page'],a0['next'])+a0.get('characters',b'')
 (c/'SCENARIO.BIN').write_bytes(blob)
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
mount c "{c}"
mount d "{d}"
c:
VIEWPAGE > RESULT.TXT
if errorlevel 1 echo FAIL>EXIT.TXT
if not errorlevel 1 echo PASS>EXIT.TXT
cd>AFTERCD.TXT
exit
''')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(config)],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=180)
 text=(c/'RESULT.TXT').read_text();match=re.search(r'VIEWPAGE scenarios=(\d+) checks=(\d+) failures=0 maxsteps=(\d+)',text)
 assert match and int(match[1])==len(cases) and 'FAIL' not in text and (c/'EXIT.TXT').read_text().strip()=='PASS',text
 assert (c/'SCENARIO.BIN').read_bytes()==blob and (c/'AFTERCD.TXT').read_text().strip()=='C:\\'
 assert {name:sha(d/name) for name in input_hashes}==input_hashes and {p.name for p in d.iterdir()}==set(fixtures())
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 names=['standalone/test_viewer_session_dos.py','standalone/test_viewer_decode_dos.py']
 r=dict(passed=True,binary_sha256=sha(binary),scenarios=len(cases),checks=int(match[2]),max_steps_per_action=int(match[3]),
  cases=[{**case,'actions':[{k:v for k,v in a0.items() if k!='characters'} for a0 in case['actions']]} for case in cases],
  sources={**manifest['sources'],**{n:sha(ROOT/n) for n in names}},original_inputs=[],cpu='8086',FPU=False,
  input_hashes=input_hashes,artifacts={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()},
  scope=__doc__+' Actual source controller+decoder+DOS owner/canonical capture reservation. Exact pages/offsets, read-ahead invariant,64-entry cache eviction and previous-page rescan, page101 beyond native inferred cap, exact/partial EOF, Home/Previous/Next, cancellation and missing-file cleanup. Far page guards and unchanged payloads/CWD. No UI/UART/physical acceptance.')
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS',len(cases),'paging scenarios,',r['checks'],'DOS checks')
if __name__=='__main__':main()
