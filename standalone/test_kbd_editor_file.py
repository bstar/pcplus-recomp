#!/usr/bin/env python3
"""DOS KBD persistence with injected failures at real IO boundaries."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 sources=['src/key_mapping/kbd_editor_file.c','src/key_mapping/key_file_fs.c','src/directory/directory_replace.c','src/directory/directory_replace_fs.c','standalone/kbd_editor_faults.c','standalone/kbd_editor_file_driver.c'];objects=[]
 flags=['-q','-bt=dos','-0','-ms','-ecc','-s','-os','-w4','-we','-i='+str(ROOT/'src/key_mapping'),'-i='+str(ROOT/'standalone')]
 for name in sources:
  obj=out/(Path(name).stem+'.obj');extra=['-dkey_file_'+n+'=key_real_'+n for n in ('attr','open','create','read','write','close','rename','delete')] if name.endswith('key_file_fs.c') else []
  subprocess.run(['wcc',*flags,*extra,'-fo='+str(obj),str(ROOT/name)],check=True);objects.append(str(obj))
 subprocess.run(['wcl',*flags,'-k4096','-fe=KBDFILE.EXE',*objects],cwd=out,check=True)
 (out/'LAB').mkdir();(out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nc:\nKBDFILE >RESULT.TXT\nexit\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=40)
 text=(out/'RESULT.TXT').read_text();assert '19 SAVE BOUNDARIES; 8 LOAD CASES' in text,text
 names=sources+['src/key_mapping/kbd_editor_file.h','src/key_mapping/key_file_fs.h','src/directory/directory_replace.h','src/directory/directory_dos.h','src/directory/directory_replace_fs.h','standalone/key_editor_faults.h','standalone/test_kbd_editor_file.py']
 result=dict(passed=True,original_inputs=[],cpu='8086',transcript=text.strip(),sources={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names},scope='Actual DOS full-size KBD IO with fault injection and retained-byte checks. No crash atomicity, external locking, parent or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(text)
if __name__=='__main__':main()
