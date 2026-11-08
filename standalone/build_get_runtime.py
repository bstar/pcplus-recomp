#!/usr/bin/env python3
"""Compose actual GET checkpoint, session, WHEN and renderer-client in DOS8086."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 flags=['ASPECT_RUNTIME_SERIAL','ASPECT_GET_VM','ASPECT_GET_SERVICE','ASPECT_GET_DISPLAY','ASPECT_ALARM_SERVICE','ASPECT_EXTERNAL_RENDER','ASPECT_EXTERNAL_UNWIND','ASPECT_SNAPSHOT_LEASE','ASPECT_ALARM_VM','ASPECT_EMULATE_VM']
 options=['-q','-bt=dos','-0','-ms','-ecc','-s','-os','-w4','-we',*['-d'+f for f in flags],'-i='+str(ROOT/'src/aspect')]
 units=['src/aspect/get_checkpoint.asm','src/aspect/get_runtime_storage.asm','standalone/get_runtime_bindings.asm'];objects=[]
 for i,n in enumerate(units):
  target=out/f'unit{i}.obj';subprocess.run(['nasm','-fobj',*['-D'+f for f in flags],str(ROOT/n),'-o',str(target)],check=True);objects.append(str(target))
 subprocess.run(['wcc',*options,'-nt=GET_FIELD_CODE','-nc=FARCODE','-fo='+str(out/'field.obj'),str(ROOT/'src/aspect/get_field.c')],check=True);objects.append(str(out/'field.obj'))
 cs=['src/aspect/get_runtime.c','src/aspect/when_runtime.c','src/aspect/resident_render.c','standalone/get_runtime_driver.c']
 subprocess.run(['wcl',*options,'-k8192','-fd=SESSION.lnk','-fm=SESSION.map','-fe=SESSION.EXE',*[str(ROOT/n) for n in cs],*objects],cwd=out,check=True)
 with (out/'SESSION.lnk').open('a') as f:f.write('\noption packcode=0\n')
 subprocess.run(['wlink','@SESSION.lnk'],cwd=out,check=True)
 layout=(out/'SESSION.map').read_text()
 storage=[line.split() for line in layout.splitlines() if line.startswith('GET_RUNTIME_STORAGE')];assert len(storage)==1 and storage[0][1:3]==['FAR_DATA','AUTO'] and int(storage[0][-1],16)==200,storage
 field=[line.split() for line in layout.splitlines() if line.startswith('GET_FIELD_CODE')];assert len(field)==1 and field[0][3].split(':')[0]!='0000',field
 (out/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\nmount c "{out}"\nc:\nSESSION >CHECK.LOG\nif errorlevel 1 goto failed\necho PASS>RESULT.TXT\nexit\n:failed\necho FAIL>RESULT.TXT\nexit\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),timeout=30,check=True)
 transcript=(out/'CHECK.LOG').read_text().strip();assert (out/'RESULT.TXT').read_text().strip()=='PASS',transcript
 names=units+cs+['src/aspect/get_field.c','src/aspect/get_field.h','src/aspect/get_runtime.h','src/aspect/get_checkpoint.h','src/aspect/resident_render.h','src/aspect/when_runtime.h','src/aspect/runtime.h','src/aspect/serial.h','src/aspect/serial_handoff.h','src/aspect/serial_runtime.h','src/aspect/receive_runtime.h','src/aspect/alarm_cooperative.h','standalone/build_get_runtime.py']
 r=dict(passed=True,binary_sha256=sha(out/'SESSION.EXE'),transcript=transcript,sources={n:sha(ROOT/n) for n in names},original_inputs=[],scope=__doc__+' Authored command body and modeled parent display/BIOS keys/serial/native WHEN actions. Actual native stack restoration and C ownership/field machinery. Not recovered GET operands/full dispatcher, live parent parser/UART, BBS, package capacity or physical acceptance.')
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(transcript)
if __name__=='__main__':main()
