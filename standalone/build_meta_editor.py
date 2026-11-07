#!/usr/bin/env python3
"""Build recovered Meta Keys components without originals or analysis inputs."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 core=ROOT/'reconstruction/meta_editor';proof=json.loads((core/'provenance.json').read_text());objects=[];include=str(ROOT/'reconstruction/uart')+'/'
 for part in proof['ranges']:
  source=core/(part['name']+'.asm');flat=out/(part['name']+'.bin')
  subprocess.run(['nasm','-fbin','-I',include,str(source),'-o',str(flat)],check=True)
  assert flat.stat().st_size==part['bytes'] and sha(flat)==part['sha256']
  target=out/(part['name']+'.obj');subprocess.run(['nasm','-fobj','-DMETA_EDITOR_OMF','-I',include,str(source),'-o',str(target)],check=True);objects.append(target)
 target=out/'host.obj';subprocess.run(['nasm','-fobj',str(ROOT/'standalone/meta_editor_host.asm'),'-o',str(target)],check=True);objects.append(target)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-fm=METAEDIT.map','-fe=METAEDIT.EXE',str(ROOT/'standalone/meta_editor_driver.c'),*[str(v) for v in objects]],cwd=out,check=True)
 (out/'CHECK.BAT').write_text('@echo off\nMETAEDIT >CHECK.LOG\nif errorlevel 1 goto failed\necho PASS>RESULT.TXT\ngoto done\n:failed\necho FAIL>RESULT.TXT\n:done\nexit\n')
 (out/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\nmount c "{out}"\nc:\nCHECK.BAT\nexit\n')
 with (out/'dosbox.log').open('w') as log:
  subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),check=True,timeout=60)
 text=(out/'CHECK.LOG').read_text();assert (out/'RESULT.TXT').read_text().strip()=='PASS' and '320 row scenarios' in text,text
 names=['standalone/build_meta_editor.py','standalone/meta_editor_host.asm','standalone/meta_editor_driver.c','reconstruction/uart/encodings.inc','reconstruction/meta_editor/provenance.json']+[f'reconstruction/meta_editor/{v["name"]}.asm' for v in proof['ranges']]
 result=dict(passed=True,original_inputs=[],exact_bytes=sum(v['bytes'] for v in proof['ranges']),binary_sha256=sha(out/'METAEDIT.EXE'),field_keys=65536,row_scenarios=320,defaults_cases=3,cpu='8086',sources={n:sha(ROOT/n) for n in names},
  scope='Actual source-built DOS8086 component replay; native field filter/defaults/row instructions with authored external services. No real text editor, file writes, UI/terminal integration, UART or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(text.strip())


if __name__=='__main__':main()
