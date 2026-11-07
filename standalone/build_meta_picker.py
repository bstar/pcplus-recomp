#!/usr/bin/env python3
"""Source-only serviced file-picker native trace, view and prompt composition."""
import argparse,hashlib,json,os,re,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 fixture='standalone/fixtures/meta_picker_native.json';v=json.loads((ROOT/fixture).read_text());assert v['passed'] and v['format']=='meta-picker-traces-v1'
 with (out/'CASES.BIN').open('wb') as f:
  f.write(struct.pack('<2H',0x4b50,len(v['cases'])))
  for c in v['cases']:
   names=v['tables'][c['names']];sorted_names=v['tables'][c['sorted']];f.write(struct.pack('<H',len(names)))
   for name in names+sorted_names:f.write(name.encode('latin1').ljust(9,b'\0'))
   f.write(struct.pack('<H',len(c['states'])))
   for state in c['states']:f.write(struct.pack('<4H',*state))
   f.write(struct.pack('<H',c['result']));f.write((c['selected'].split('.')[0] if c['result'] else '').encode('latin1').ljust(9,b'\0'));f.write(struct.pack('<H',c['bells']))
 sources=['src/key_mapping/'+n+'.c' for n in ('meta_filename','meta_file_prompt','meta_picker')]+['standalone/meta_picker_driver.c'];headers=['src/key_mapping/'+n+'.h' for n in ('meta_filename','meta_file_prompt','meta_picker')]
 flags=['-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-os','-i='+str(ROOT/'src/key_mapping')];objects=[]
 for source in sources:
  obj=out/(Path(source).stem+'.obj');extra=[] if 'driver' in source else ['-nt='+Path(source).stem.upper()+'_CODE','-nc=FARCODE']
  subprocess.run(['wcc',*flags,*extra,'-fo='+str(obj),str(ROOT/source)],check=True);objects.append(str(obj))
 asm='standalone/meta_picker_banks.asm';subprocess.run(['nasm','-fobj',str(ROOT/asm),'-o',str(out/'banks.obj')],check=True)
 subprocess.run(['wcl',*flags,'-k8192','-fd=KEYPICK.lnk','-fm=KEYPICK.map','-fe=KEYPICK.EXE',str(out/'banks.obj'),*objects],cwd=out,check=True)
 response=out/'KEYPICK.lnk';response.write_text(response.read_text()+'\norder clname CODE clname FARCODE clname FARSTATE clname BEGDATA clname DATA clname BSS clname STACK\n');subprocess.run(['wlink','@KEYPICK.lnk'],cwd=out,check=True)
 listing=(out/'KEYPICK.map').read_text();data=re.search(r'^DGROUP\s+([0-9a-f]+):0000',listing,re.M|re.I);null=re.search(r'^_NULL\s+BEGDATA\s+DGROUP\s+([0-9a-f]+):0000',listing,re.M|re.I);assert data and null and data[1]==null[1]
 entries=re.search(r'^([0-9a-f]+):([0-9a-f]+)\s+_entries\s*$',listing,re.M|re.I);assert entries and int(entries[1],16)*16+int(entries[2],16)+9009<=int(data[1],16)*16
 (out/'CHECK.BAT').write_text('@echo off\nKEYPICK >CHECK.LOG\nif errorlevel 1 goto failed\necho PASS>RESULT.TXT\ngoto done\n:failed\necho FAIL>RESULT.TXT\n:done\nexit\n')
 (out/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\nmount c "{out}"\nc:\nCHECK.BAT\nexit\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),check=True,timeout=60)
 text=(out/'CHECK.LOG').read_text();assert (out/'RESULT.TXT').read_text().strip()=='PASS',text
 inputs=sources+headers+[fixture,asm,'standalone/build_meta_picker.py'];result=dict(passed=True,binary_sha256=sha(out/'KEYPICK.EXE'),native_cases=len(v['cases']),native_states=sum(len(c['states']) for c in v['cases']),transcript=text.strip(),cpu='8086',original_inputs=[],sources={s:sha(ROOT/s) for s in inputs},scope='Frozen original sorting/navigation traces with modeled enumeration/UI; source frame at every native state plus maintained1001-entry test and filename prompt composition. No actual DOS enumeration, VGA, resource ownership, live parent, memory admission or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(text.strip())
if __name__=='__main__':main()
