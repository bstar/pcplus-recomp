#!/usr/bin/env python3
"""Actual DOS canonical KEY resource lookup, picker fallback and frozen IO."""
import argparse,hashlib,json,os,re,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def table(ch):
 return b''.join(struct.pack('<H',3)+bytes([ch+i,0])+b'\xa5'*50 for i in range(10))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 sources=['src/key_mapping/'+n+'.c' for n in ('meta_key_resource','meta_picker','meta_picker_scan','meta_scan_fs','key_editor_file','key_file_fs','key_actions_dos')]+['src/config/resource_path.c','src/capture/capture_fs.c','src/directory/directory_replace.c','src/directory/directory_replace_fs.c','standalone/meta_resource_faults.c','standalone/meta_resource_driver.c']
 flags=['-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-os','-i='+str(ROOT/'src/key_mapping'),'-i='+str(ROOT/'standalone')];objects=[]
 for source in sources:
  obj=out/(Path(source).stem+'.obj');extra=[]
  if source.endswith('/meta_picker.c'):extra=['-nt=META_PICKER_CODE','-nc=FARCODE']
  if source.endswith('capture_fs.c'):extra=['-dcapture_fs_canonical=meta_resource_real_canonical','-dcapture_fs_attributes=meta_resource_real_attributes']
  if source.endswith('key_actions_dos.c'):extra=['-dKEY_RESOURCE_PRIVATE_READS']
  subprocess.run(['wcc',*flags,*extra,'-fo='+str(obj),str(ROOT/source)],check=True);objects.append(str(obj))
 dis=out/'resource.dis';subprocess.run(['wdis','-l='+str(dis),str(out/'meta_key_resource.obj')],check=True)
 segments={n:int(size,16) for n,size in re.findall(r'^Segment: (\S+).*?([0-9A-Fa-f]{8}) bytes$',dis.read_text(),re.M)};assert segments and all(n=='_TEXT' or not size for n,size in segments.items())
 asm='standalone/meta_resource_banks.asm';subprocess.run(['nasm','-fobj',str(ROOT/asm),'-o',str(out/'banks.obj')],check=True)
 subprocess.run(['wcl',*flags,'-k8192','-fd=KEYRES.lnk','-fm=KEYRES.map','-fe=KEYRES.EXE',str(out/'banks.obj'),*objects],cwd=out,check=True)
 response=out/'KEYRES.lnk';response.write_text(response.read_text()+'\norder clname CODE clname FARCODE clname FARSTATE clname BEGDATA clname DATA clname BSS clname STACK\n');subprocess.run(['wlink','@KEYRES.lnk'],cwd=out,check=True)
 listing=(out/'KEYRES.map').read_text();data=re.search(r'^DGROUP\s+([0-9a-f]+):0000',listing,re.M|re.I);null=re.search(r'^_NULL\s+BEGDATA\s+DGROUP\s+([0-9a-f]+):0000',listing,re.M|re.I);assert data and null and data[1]==null[1]
 for d in ('FALL','ALT','drive-d/KEEP/FOLDER.KEY','drive-d/EMPTY'):(out/d).mkdir(parents=True)
 fixtures={'FALL/BOTH.KEY':table(65),'FALL/ONLY.KEY':table(79),'FALL/!PUNCT.KEY':table(80),'FALL/BAD.KEY':table(66),'drive-d/KEEP/BOTH.KEY':table(68),'drive-d/KEEP/BAD.KEY':table(68)[:-1]}
 for n,v in fixtures.items():(out/n).write_bytes(v)
 before={n:sha(out/n) for n in fixtures}
 (out/'CHECK.BAT').write_text('@echo off\nC:\\KEYRES >C:\\CHECK.LOG\nif errorlevel 1 goto failed\necho PASS>C:\\RESULT.TXT\ngoto done\n:failed\necho FAIL>C:\\RESULT.TXT\n:done\nexit\n')
 (out/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\nmount c "{out}"\nmount d "{out}/drive-d"\nc:\ncd \\ALT\nd:\ncd \\KEEP\nC:\\CHECK.BAT\nexit\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),check=True,timeout=60)
 text=(out/'CHECK.LOG').read_text();assert (out/'RESULT.TXT').read_text().strip()=='PASS',text
 changed=bytearray(fixtures['FALL/ONLY.KEY']);changed[2]=33;assert (out/'FALL/ONLY.KEY').read_bytes()==changed and (out/'drive-d/KEEP/ONLY.KEY').read_bytes()==fixtures['FALL/ONLY.KEY']
 for n,h in before.items():
  if n!='FALL/ONLY.KEY':assert sha(out/n)==h
 assert not (out/'FALL/MISSING.KEY').exists() and not (out/'drive-d/KEEP/MISSING.KEY').exists()
 headers=['src/key_mapping/'+n+'.h' for n in ('meta_key_resource','meta_picker','meta_picker_scan','meta_scan_fs','key_editor_file','key_file_fs','key_actions_dos')]+['src/config/resource_path.h','src/capture/capture_fs.h','src/directory/directory_replace.h','src/directory/directory_replace_fs.h','src/directory/directory_dos.h','standalone/meta_resource_faults.h']
 inputs=sources+headers+[asm,'standalone/build_meta_resource.py'];result=dict(passed=True,binary_sha256=sha(out/'KEYRES.EXE'),transcript=text.strip(),cpu='8086',original_inputs=[],resource_owned_segments=segments,resource_owned_DGROUP_bytes=0,sources={s:sha(ROOT/s) for s in inputs},scope='Actual DOS canonicalization/attributes, bounded synthetic PSP/environment, current/fallback lookup, real picker scans and checked frozen-path load/save. Declared kernel boundary faults. No application claims/adoption/EXEC/modal ownership, native whole-workflow or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(text.strip())
if __name__=='__main__':main()
