#!/usr/bin/env python3
"""Capture a declared DOS help executable at scripted BIOS keyboard boundaries."""
import argparse,json,os,re,shutil,struct,subprocess,sys
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--helper',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--rows',type=int,choices=[25,50],default=25);p.add_argument('--keys',default='[27]');p.add_argument('--topic',type=int,default=1);a=p.parse_args()
 helper=a.helper.resolve();assert helper.is_file() and not helper.name.endswith('.analysis.exe')
 out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 keys=json.loads(a.keys);assert 0<len(keys)<=64 and all(isinstance(k,int) and 0<=k<=65535 for k in keys)
 subprocess.run([sys.executable,str(ROOT/'standalone/build_context_help.py'),'--output',str(out/'parent-build')],check=True)
 build=out/'parent-build';objects=[]
 for name in ['standalone/help_screen_observer.asm']:
  obj=out/(Path(name).stem+'.obj');subprocess.run(['nasm','-fobj',str(ROOT/name),'-o',str(obj)],check=True);objects.append(str(obj))
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-ecc','-k8192','-fe=SCREEN.EXE','-fm=SCREEN.MAP',str(ROOT/'standalone/help_screen_parent.c'),*objects,*[str(build/(name+'.obj')) for name in ['state','handoff','strcpy','get_ds']]],cwd=out,check=True)
 shutil.copyfile(helper,out/'PCHELP.RTE')
 records=[];payload=[];offset=3+47*38
 for topic in range(47):
  body=b''.join(('TOPIC %02u LINE %02u - Authored help fixture\n'%(topic,line)).encode() for line in range(40))
  records.append(('Context %02u'%topic).encode().ljust(32,b'\0')+struct.pack('<HI',40,offset));payload.append(body);offset+=len(body)
 (out/'HELP.HLP').write_bytes(struct.pack('<BH',47,47*40)+b''.join(records+payload))
 (out/'KEYS.BIN').write_bytes(struct.pack('<'+'H'*len(keys),*keys))
 (out/'RUN.BAT').write_bytes(('@echo off\r\nSCREEN %u %u >RESULT.TXT\r\nexit\r\n'%(a.rows,a.topic)).encode())
 (out/'dosbox.conf').write_text(f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 12000
[mixer]
nosound=true
[serial]
serial1=disabled
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
mount c "{out}"
c:
RUN.BAT
exit
''')
 timeout=False
 with (out/'dosbox.log').open('w') as log:
  try:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=45,check=True)
  except subprocess.TimeoutExpired:timeout=True
 result=(out/'RESULT.TXT').read_text() if (out/'RESULT.TXT').exists() else ''
 match=re.fullmatch(r'HELPSCREEN status=(\d+) captures=(\d+) rows='+str(a.rows)+r' restored=(\d+)\s*',result)
 for frame in sorted(out.glob('VIEW*.BIN')):
  raw=frame.read_bytes();assert len(raw)==8000
  (frame.with_suffix('.txt')).write_text('\n'.join(raw[row*160:(row+1)*160:2].decode('cp437') for row in range(a.rows))+'\n')
 sources=['standalone/help_screen_parent.c','standalone/help_screen_observer.asm','standalone/capture_help_screen.py']
 metadata=(out/'META.BIN').read_bytes() if (out/'META.BIN').exists() else b''
 report=dict(passed=not timeout and bool(match) and int(match[1])<=255 and int(match[2])>0,timed_out=timeout,child_exit_code=int(match[1]) if match else None,restored=bool(match) and match[3]=='1',metadata=[list(struct.unpack('<HH',metadata[i:i+4])) for i in range(0,len(metadata),4)],helper_sha256=sha(helper),parent_sha256=sha(out/'SCREEN.EXE'),resource_sha256=sha(out/'HELP.HLP'),keys=keys,rows=a.rows,topic=a.topic,captures=int(match[2]) if match else None,observer_sources={name:sha(ROOT/name) for name in sources},frames={frame.name:sha(frame) for frame in sorted(out.glob('VIEW*.BIN'))},scope='Actual DOS helper execution with source-built native descriptor producer. Diagnostic INT16 boundary captures VGA/BDA cursor state and supplies declared BIOS reads; no helper instruction/state patches. Authored LF HLP only. Passed means capture/launch, not an application-behavior or child-exit-code acceptance claim. No physical/UART acceptance.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(result.strip());print('PASS' if report['passed'] else 'FAIL');return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
