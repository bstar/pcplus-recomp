#!/usr/bin/env python3
"""DOS KEY file owner: real capture claims, creation and uncertainty quarantine."""
import argparse,hashlib,json,os,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 sources=['src/key_mapping/'+n+'.c' for n in ('meta_key_owner','meta_key_resource','key_editor_file','key_file_fs','key_actions_dos')]+['src/config/resource_path.c','src/capture/capture_fs.c','src/capture/capture_file.c','src/capture/capture_reservation.c','src/directory/directory_replace.c','src/directory/directory_replace_fs.c','standalone/key_editor_faults.c','standalone/meta_owner_driver.c']
 flags=['-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-os','-dCAPTURE_FIXED_RESERVATION','-i='+str(ROOT/'src/key_mapping'),'-i='+str(ROOT/'standalone')];objects=[]
 for source in sources:
  obj=out/(Path(source).stem+'.obj');extra=[]
  if source.endswith('key_actions_dos.c'):extra=['-dKEY_EDITOR_FS','-dKEY_RESOURCE_PRIVATE_READS']
  if source.endswith('key_file_fs.c'):extra=['-dkey_file_'+n+'=key_real_'+n for n in ('attr','open','create','read','write','close','rename','delete')]
  if source.endswith('capture_reservation.c'):extra=['-dcapture_file_release=meta_release_real']
  subprocess.run(['wcc',*flags,*extra,'-fo='+str(obj),str(ROOT/source)],check=True);objects.append(str(obj))
 dis=out/'owner.dis';subprocess.run(['wdis','-l='+str(dis),str(out/'meta_key_owner.obj')],check=True)
 segments={n:int(size,16) for n,size in re.findall(r'^Segment: (\S+).*?([0-9A-Fa-f]{8}) bytes$',dis.read_text(),re.M)};assert segments and all(n=='_TEXT' or not size for n,size in segments.items()),segments
 asm='standalone/meta_owner_banks.asm';subprocess.run(['nasm','-fobj',str(ROOT/asm),'-o',str(out/'banks.obj')],check=True)
 subprocess.run(['wcl',*flags,'-k8192','-fd=KEYOWN.lnk','-fm=KEYOWN.map','-fe=KEYOWN.EXE',str(out/'banks.obj'),*objects],cwd=out,check=True)
 response=out/'KEYOWN.lnk';response.write_text(response.read_text()+'\norder clname CODE clname FARSTATE clname BEGDATA clname DATA clname BSS clname STACK\n');subprocess.run(['wlink','@KEYOWN.lnk'],cwd=out,check=True)
 listing=(out/'KEYOWN.map').read_text();data=re.search(r'^DGROUP\s+([0-9a-f]+):0000',listing,re.M|re.I);null=re.search(r'^_NULL\s+BEGDATA\s+DGROUP\s+([0-9a-f]+):0000',listing,re.M|re.I);assert data and null and data[1]==null[1]
 (out/'LAB').mkdir();(out/'ALT').mkdir();modes=[0,*range(1,17),96,97,98,99]
 batch='@echo off\n'
 for mode in modes:batch+=f'KEYOWN {mode} >M{mode}.LOG\nif errorlevel 1 goto failed\n'
 batch+='echo PASS>RESULT.TXT\ngoto done\n:failed\necho FAIL>RESULT.TXT\n:done\nexit\n';(out/'CHECK.BAT').write_text(batch)
 (out/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\nmount c "{out}"\nc:\nCHECK.BAT\nexit\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),check=True,timeout=60)
 logs={str(m):(out/f'M{m}.LOG').read_text().strip() for m in modes if (out/f'M{m}.LOG').exists()};assert (out/'RESULT.TXT').read_text().strip()=='PASS',logs
 assert len(logs)==21 and all(v.startswith('PASS') for v in logs.values())
 headers=['src/key_mapping/'+n+'.h' for n in ('meta_key_owner','meta_key_resource','key_editor_file','key_file_fs','key_actions_dos')]+['src/config/resource_path.h','src/capture/capture_fs.h','src/capture/capture_file.h','src/capture/capture_reservation.h','src/directory/directory_replace.h','src/directory/directory_replace_fs.h','src/directory/directory_dos.h','standalone/key_editor_faults.h']
 inputs=sources+headers+[asm,'standalone/build_meta_owner.py'];result=dict(passed=True,binary_sha256=sha(out/'KEYOWN.EXE'),logs=logs,process_cases=len(modes),owner_state_bytes=1518,cpu='8086',original_inputs=[],owner_owned_segments=segments,owner_owned_DGROUP_bytes=0,sources={s:sha(ROOT/s) for s in inputs},scope='Real DOS KEY IO and capture reservation library over owned fixtures, plus declared filesystem/lease-release faults. Separate processes for HELD tests; explicit test-only handle cleanup before exit does not reset owner. No terminal/EXEC admission integration, external lock, verified recovery, live adoption or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS KEY owner:',len(modes),'DOS process cases;',logs['0'])
if __name__=='__main__':main()
