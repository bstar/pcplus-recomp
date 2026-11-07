#!/usr/bin/env python3
"""Composed serviced Meta editor with actual DOS picker and checked owner IO."""
import argparse,hashlib,json,os,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 units=('meta_editor','meta_dialog','meta_text','meta_file_prompt','meta_filename','meta_picker','meta_picker_scan','meta_scan_fs','meta_key_owner','meta_key_resource','key_editor_file','key_file_fs','key_actions_dos')
 sources=['src/key_mapping/'+n+'.c' for n in units]+['src/config/resource_path.c','src/capture/capture_fs.c','src/capture/capture_file.c','src/capture/capture_reservation.c','src/directory/directory_replace.c','src/directory/directory_replace_fs.c','standalone/key_editor_faults.c','standalone/meta_editor_flow_driver.c']
 flags=['-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-os','-dCAPTURE_FIXED_RESERVATION','-i='+str(ROOT/'src/key_mapping'),'-i='+str(ROOT/'standalone')];objects=[]
 for source in sources:
  obj=out/(Path(source).stem+'.obj');extra=[]
  if source.endswith('key_actions_dos.c'):extra=['-dKEY_EDITOR_FS','-dKEY_RESOURCE_PRIVATE_READS']
  if source.endswith('key_file_fs.c'):extra=['-dkey_file_'+n+'=key_real_'+n for n in ('attr','open','create','read','write','close','rename','delete')]
  subprocess.run(['wcc',*flags,*extra,'-fo='+str(obj),str(ROOT/source)],check=True);objects.append(str(obj))
 dis=out/'editor.dis';subprocess.run(['wdis','-l='+str(dis),str(out/'meta_editor.obj')],check=True)
 segments={n:int(size,16) for n,size in re.findall(r'^Segment: (\S+).*?([0-9A-Fa-f]{8}) bytes$',dis.read_text(),re.M)};assert segments and all(n=='_TEXT' or not size for n,size in segments.items()),segments
 asm='standalone/meta_editor_banks.asm';subprocess.run(['nasm','-fobj',str(ROOT/asm),'-o',str(out/'banks.obj')],check=True)
 subprocess.run(['wcl',*flags,'-k8192','-fd=METAEDIT.lnk','-fm=METAEDIT.map','-fe=METAEDIT.EXE',str(out/'banks.obj'),*objects],cwd=out,check=True)
 response=out/'METAEDIT.lnk';response.write_text(response.read_text()+'\norder clname CODE clname FARSTATE clname BEGDATA clname DATA clname BSS clname STACK\n');subprocess.run(['wlink','@METAEDIT.lnk'],cwd=out,check=True)
 listing=(out/'METAEDIT.map').read_text();data=re.search(r'^DGROUP\s+([0-9a-f]+):0000',listing,re.M|re.I);null=re.search(r'^_NULL\s+BEGDATA\s+DGROUP\s+([0-9a-f]+):0000',listing,re.M|re.I);assert data and null and data[1]==null[1]
 for n in ('LAB','EMPTY','FALL'):(out/n).mkdir()
 (out/'CHECK.BAT').write_text('@echo off\ncd \\LAB\nC:\\METAEDIT >C:\\NORMAL.LOG\nif errorlevel 1 goto failed\nC:\\METAEDIT 1 >C:\\FATAL.LOG\nif errorlevel 1 goto failed\necho PASS>C:\\RESULT.TXT\ngoto done\n:failed\necho FAIL>C:\\RESULT.TXT\n:done\nexit\n')
 (out/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\nmount c "{out}"\nc:\nC:\\CHECK.BAT\nexit\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),check=True,timeout=60)
 logs={n:(out/n).read_text().strip() for n in ('NORMAL.LOG','FATAL.LOG') if (out/n).exists()};assert (out/'RESULT.TXT').read_text().strip()=='PASS',logs
 headers=['src/key_mapping/'+n+'.h' for n in units]+['src/config/resource_path.h','src/capture/capture_fs.h','src/capture/capture_file.h','src/capture/capture_reservation.h','src/directory/directory_replace.h','src/directory/directory_replace_fs.h','src/directory/directory_dos.h','standalone/key_editor_faults.h']
 inputs=sources+headers+[asm,'standalone/build_meta_editor_flow.py'];result=dict(passed=True,binary_sha256=sha(out/'METAEDIT.EXE'),logs=logs,cpu='8086',original_inputs=[],editor_owned_segments=segments,editor_owned_DGROUP_bytes=0,sources={s:sha(ROOT/s) for s in inputs},scope='Composed editor model/frames, real DOS KEY lookup/enumeration/claims/checked IO and failure quarantine. Explicit admission flag is supplied by test caller; output is an unadopted proposal. No terminal/transient-module/actual VGA/UART/parent capacity/BBS/hardware acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(logs)
if __name__=='__main__':main()
