#!/usr/bin/env python3
"""Native filename-field replay plus checked Meta dialog/file composition in DOS."""
import argparse,hashlib,json,os,re,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 fixture='standalone/fixtures/meta_filename_native.json';v=json.loads((ROOT/fixture).read_text());assert v['passed'] and v['format']=='meta-filename-traces-v1'
 with (out/'CASES.BIN').open('wb') as f:
  f.write(struct.pack('<2H',0x4e46,len(v['cases'])))
  for c in v['cases']:
   f.write(struct.pack('<H',len(c['states'])))
   for key,field,cursor,shape,bells in c['states']:f.write(struct.pack('<H',key));f.write(bytes.fromhex(v['fields'][field]));f.write(struct.pack('<3H',cursor,shape,bells))
   f.write(bytes.fromhex(c['output']));f.write(struct.pack('<3H',c['result'],c['bells'],c['shape']))
 flags=['-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-os','-i='+str(ROOT/'src/key_mapping')]
 sources=['src/key_mapping/'+stem+'.c' for stem in ('meta_text','meta_dialog','meta_filename','meta_file_prompt','key_editor_file','key_file_fs','key_actions_dos')]+['src/directory/directory_replace.c','src/directory/directory_replace_fs.c','standalone/meta_filename_driver.c']
 objects=[]
 for source in sources:
  obj=out/(Path(source).stem+'.obj');extra=[]
  if Path(source).stem in ('meta_text','meta_dialog','meta_filename','meta_file_prompt'):extra=['-nt='+Path(source).stem.upper()+'_CODE','-nc=FARCODE']
  if source.endswith('key_actions_dos.c'):extra=['-dKEY_RESOURCE_PRIVATE_READS']
  subprocess.run(['wcc',*flags,*extra,'-fo='+str(obj),str(ROOT/source)],check=True);objects.append(str(obj))
 asm='standalone/meta_filename_banks.asm';subprocess.run(['nasm','-fobj',str(ROOT/asm),'-o',str(out/'banks.obj')],check=True)
 subprocess.run(['wcl',*flags,'-k8192','-fd=KEYNAME.lnk','-fm=KEYNAME.map','-fe=KEYNAME.EXE',str(out/'banks.obj'),*objects],cwd=out,check=True)
 response=out/'KEYNAME.lnk';response.write_text(response.read_text()+'\norder clname CODE clname FARCODE clname FARSTATE clname BEGDATA clname DATA clname BSS clname STACK\n');subprocess.run(['wlink','@KEYNAME.lnk'],cwd=out,check=True)
 listing=(out/'KEYNAME.map').read_text();data=re.search(r'^DGROUP\s+([0-9a-f]+):0000',listing,re.M|re.I);null=re.search(r'^_NULL\s+BEGDATA\s+DGROUP\s+([0-9a-f]+):0000',listing,re.M|re.I);assert data and null and data[1]==null[1]
 (out/'LAB').mkdir();(out/'drive-d/LAB').mkdir(parents=True)
 (out/'CHECK.BAT').write_text('@echo off\nC:\\KEYNAME >C:\\CHECK.LOG\nif errorlevel 1 goto failed\necho PASS>C:\\RESULT.TXT\ngoto done\n:failed\necho FAIL>C:\\RESULT.TXT\n:done\nexit\n')
 (out/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\nmount c "{out}"\nmount d "{out}/drive-d"\nd:\ncd \\LAB\nC:\\CHECK.BAT\nexit\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),check=True,timeout=60)
 text=(out/'CHECK.LOG').read_text();assert (out/'RESULT.TXT').read_text().strip()=='PASS',text
 assert not (out/'LAB/ABSENT.KEY').exists() and not (out/'LAB/KEYSTG.$$$').exists() and not (out/'LAB/KEYBAK.$$$').exists()
 headers=['src/key_mapping/'+n+'.h' for n in ('meta_text','meta_dialog','meta_filename','meta_file_prompt','key_editor_file','key_file_fs','key_actions_dos')]+['src/directory/directory_replace.h','src/directory/directory_replace_fs.h','src/directory/directory_dos.h']
 inputs=sources+headers+[fixture,asm,'standalone/build_meta_filename.py']
 result=dict(passed=True,binary_sha256=sha(out/'KEYNAME.EXE'),native_cases=len(v['cases']),native_states=sum(len(c['states']) for c in v['cases']),transcript=text.strip(),cpu='8086',original_inputs=[],sources={s:sha(ROOT/s) for s in inputs},scope='Native filename field versus frozen original instructions, plus actual DOS checked files composed with serviced Meta dialog. External picker completion modeled, fixture resource resolver explicit; no live parent, file claim/EXEC owner, application memory or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(text.strip())
if __name__=='__main__':main()
