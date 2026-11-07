#!/usr/bin/env python3
"""Build and replay the serviced Meta Keys controller/view; no application update."""
import argparse,hashlib,json,os,re,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 fixture=ROOT/'standalone/fixtures/meta_dialog_native.json';v=json.loads(fixture.read_text());assert v['passed'] and v['format']=='meta-dialog-traces-v1'
 loaded=next(bytes.fromhex(t) for t in v['tables'] if bytes.fromhex(t)[2:7]==b'LOAD0')
 def name(s):return s.encode().ljust(64,b'\0')
 with (out/'CASES.BIN').open('wb') as f:
  f.write(struct.pack('<H',0x4d44));f.write(loaded);f.write(struct.pack('<H',len(v['cases'])))
  for c in v['cases']:
   f.write(bytes.fromhex(v['tables'][c['initial']]));f.write(struct.pack('<H',len(c['states'])))
   for key,phase,row,kind,table,bells,cursor,shape,field,filename,loads,saves in c['states']:
    f.write(struct.pack('<4H',key,phase,row,kind));f.write(bytes.fromhex(v['tables'][table]));f.write(struct.pack('<4H',bells,cursor,shape,int(field>=0)))
    if field>=0:f.write(bytes.fromhex(v['fields'][field]))
    f.write(name(filename));f.write(struct.pack('<2H',loads,saves))
   f.write(bytes.fromhex(v['tables'][c['output']]));f.write(struct.pack('<3H',c['bells'],c['loads'],c['saves']));f.write(name(c['final_name']))
 subprocess.run(['nasm','-fobj',str(ROOT/'standalone/meta_dialog_banks.asm'),'-o',str(out/'banks.obj')],check=True)
 objects=[str(out/'banks.obj')]
 for stem in ('meta_text','meta_dialog'):
  obj=out/(stem+'.obj');subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-os','-nt='+stem.upper()+'_CODE','-nc=FARCODE','-i='+str(ROOT/'src/key_mapping'),'-fo='+str(obj),str(ROOT/'src/key_mapping'/(stem+'.c'))],check=True);objects.append(str(obj))
 subprocess.run(['nasm','-fobj',str(ROOT/'standalone/meta_text_padding.asm'),'-o',str(out/'padding.obj')],check=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/key_mapping'),'-fd=METADLG.lnk','-fm=METADLG.map','-fe=METADLG.EXE',str(ROOT/'standalone/meta_dialog_driver.c'),str(out/'padding.obj'),*objects],cwd=out,check=True)
 response=out/'METADLG.lnk';response.write_text(response.read_text()+'\norder clname CODE clname PADCODE clname FARCODE clname FARSTATE clname BEGDATA clname DATA clname BSS clname STACK\n');subprocess.run(['wlink','@METADLG.lnk'],cwd=out,check=True)
 listing=(out/'METADLG.map').read_text()
 group=re.search(r'^DGROUP\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)',listing,re.M|re.I);assert group and int(group[2],16)==0
 data=int(group[1],16)*16
 null=re.search(r'^_NULL\s+BEGDATA\s+DGROUP\s+([0-9a-f]+):([0-9a-f]+)',listing,re.M|re.I);assert null and int(null[1],16)*16+int(null[2],16)==data
 state=re.search(r'^([0-9a-f]+):([0-9a-f]+)\s+_external_state\s*$',listing,re.M|re.I);assert state
 state_at=int(state[1],16)*16+int(state[2],16);assert state_at+684<=data
 (out/'CHECK.BAT').write_text('@echo off\nMETADLG >CHECK.LOG\nif errorlevel 1 goto failed\necho PASS>RESULT.TXT\ngoto done\n:failed\necho FAIL>RESULT.TXT\n:done\nexit\n')
 (out/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\nmount c "{out}"\nc:\nCHECK.BAT\nexit\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),check=True,timeout=60)
 text=(out/'CHECK.LOG').read_text();assert (out/'RESULT.TXT').read_text().strip()=='PASS',text
 states=sum(len(c['states']) for c in v['cases']);assert f'PASS {len(v["cases"])} dialog cases; {states} native key states and views; 8 guards' in text,text
 names=['standalone/build_meta_dialog.py','standalone/meta_dialog_driver.c','standalone/meta_text_padding.asm','standalone/meta_dialog_banks.asm','standalone/fixtures/meta_dialog_native.json','src/key_mapping/meta_dialog.c','src/key_mapping/meta_dialog.h','src/key_mapping/meta_text.c','src/key_mapping/meta_text.h']
 result=dict(passed=True,original_inputs=[],binary_sha256=sha(out/'METADLG.EXE'),cases=len(v['cases']),key_states=states,view_checks=states,API_guards=8,state_bytes=684,state_outside_DGROUP=True,null_guard_at_DGROUP_start=True,separate_code_segment=True,data_equals_stack=True,cpu='8086',sources={n:sha(ROOT/n) for n in names},
  scope='Actual source-built DOS8086 serviced controller/field/view against frozen original dispatcher/row/field traces. Peripheral UI and file effects modeled in native oracle; authored window decoration, bounded frame writes. No real persistence/VGA comparison, live parent/UART/application memory or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(text.strip())


if __name__=='__main__':main()
