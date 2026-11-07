#!/usr/bin/env python3
"""Source-only DOS KEY persistence and filesystem-failure diagnostic."""
import argparse,hashlib,json,os,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 sources=['src/key_mapping/key_editor_file.c','src/key_mapping/key_actions_dos.c','src/key_mapping/key_file_fs.c','src/directory/directory_replace.c','src/directory/directory_replace_fs.c','standalone/key_editor_faults.c','standalone/key_editor_file_driver.c']
 flags=['-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-os','-i='+str(ROOT/'src/key_mapping'),'-i='+str(ROOT/'standalone')]
 objects=[]
 for source in sources:
  obj=out/(Path(source).stem+'.obj');defines=[]
  if source.endswith('key_actions_dos.c'):defines=['-dKEY_EDITOR_FS','-dKEY_RESOURCE_PRIVATE_READS']
  if source.endswith('key_file_fs.c'):defines=['-dkey_file_'+n+'=key_real_'+n for n in ('attr','open','create','read','write','close','rename','delete')]
  subprocess.run(['wcc',*flags,*defines,'-fo='+str(obj),str(ROOT/source)],check=True);objects.append(str(obj))
 subprocess.run(['nasm','-fobj',str(ROOT/'standalone/key_editor_file_banks.asm'),'-o',str(out/'banks.obj')],check=True)
 subprocess.run(['wcl',*flags,'-k8192','-fd=KEYFILE.lnk','-fm=KEYFILE.map','-fe=KEYFILE.EXE',str(out/'banks.obj'),*objects],cwd=out,check=True)
 response=out/'KEYFILE.lnk';response.write_text(response.read_text()+'\norder clname CODE clname FARSTATE clname BEGDATA clname DATA clname BSS clname STACK\n');subprocess.run(['wlink','@KEYFILE.lnk'],cwd=out,check=True)
 listing=(out/'KEYFILE.map').read_text()
 group=re.search(r'^DGROUP\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)',listing,re.M|re.I);assert group and int(group[2],16)==0
 data=int(group[1],16)*16
 null=re.search(r'^_NULL\s+BEGDATA\s+DGROUP\s+([0-9a-f]+):([0-9a-f]+)',listing,re.M|re.I);assert null and int(null[1],16)*16+int(null[2],16)==data
 records=re.search(r'^([0-9a-f]+):([0-9a-f]+)\s+_key_records\s*$',listing,re.M|re.I);assert records and int(records[1],16)*16+int(records[2],16)+1620<=data
 (out/'LAB').mkdir();(out/'drive-d/LAB').mkdir(parents=True)
 (out/'CHECK.BAT').write_text('@echo off\nC:\\KEYFILE >C:\\CHECK.LOG\nif errorlevel 1 goto failed\necho PASS>C:\\RESULT.TXT\ngoto done\n:failed\necho FAIL>C:\\RESULT.TXT\n:done\nexit\n')
 (out/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\nmount c "{out}"\nmount d "{out}/drive-d"\nd:\ncd \\LAB\nC:\\CHECK.BAT\nexit\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),check=True,timeout=60)
 text=(out/'CHECK.LOG').read_text();assert (out/'RESULT.TXT').read_text().strip()=='PASS',text
 inputs=sources+['src/key_mapping/key_editor_file.h','src/key_mapping/key_actions_dos.h','src/key_mapping/key_file_fs.h','src/directory/directory_replace.h','src/directory/directory_replace_fs.h','src/directory/directory_dos.h','standalone/key_editor_faults.h','standalone/key_editor_file_banks.asm','standalone/build_key_editor_file.py']
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 result=dict(passed=True,binary_sha256=sha(out/'KEYFILE.EXE'),original_inputs=[],cpu='8086',transcript=text.strip(),sources={s:sha(ROOT/s) for s in inputs},scope='Real DOS IO with explicit injected boundaries on owned scratch files; no parent integration, concurrent locking, power-loss guarantee or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(text.strip())
if __name__=='__main__':main()
