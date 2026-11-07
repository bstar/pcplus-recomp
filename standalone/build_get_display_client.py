#!/usr/bin/env python3
"""Real DOS child-client lifecycle tests with controlled parent scalar responses."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
 flags=['ASPECT_EXTERNAL_RENDER','ASPECT_EXTERNAL_UNWIND','ASPECT_SNAPSHOT_LEASE','ASPECT_ALARM_VM','ASPECT_EMULATE_VM','ASPECT_GET_DISPLAY']
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-ob','-os','-w4','-we','-k8192',*['-d'+f for f in flags],'-i='+str(ROOT/'src/aspect'),'-fe=CLIENT.EXE',str(ROOT/'src/aspect/resident_render.c'),str(ROOT/'standalone/get_display_client_driver.c')],cwd=out,check=True)
 (out/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\nmount c "{out}"\nc:\nCLIENT >CHECK.LOG\nif errorlevel 1 goto failed\necho PASS>RESULT.TXT\nexit\n:failed\necho FAIL>RESULT.TXT\nexit\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),check=True,timeout=30)
 transcript=(out/'CHECK.LOG').read_text().strip();assert (out/'RESULT.TXT').read_text().strip()=='PASS',transcript
 assert transcript.startswith('PASS FIELD CLIENT ') and transcript.endswith('retirement, owners, callbacks, quarantine'),transcript
 names=['src/aspect/resident_render.c','src/aspect/resident_render.h','src/aspect/runtime.h','src/aspect/serial.h','src/aspect/serial_handoff.h','src/aspect/serial_runtime.h','src/aspect/receive_runtime.h','src/aspect/when_runtime.h','standalone/get_display_client_driver.c','standalone/build_get_display_client.py']
 result=dict(passed=True,original_inputs=[],binary_sha256=sha(out/'CLIENT.EXE'),transcript=transcript,sources={n:sha(ROOT/n) for n in names},scope=__doc__+' Actual source client in DOS8086. Parent request/client-stack validation/serial boundaries are controlled services; no real resident bridge/parent/child EXE integration or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(transcript)
if __name__=='__main__':main()
