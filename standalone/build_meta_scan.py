#!/usr/bin/env python3
"""Actual DOS source-only KEY picker enumeration, DTA and fault composition."""
import argparse,hashlib,json,os,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 sources=['src/key_mapping/'+n+'.c' for n in ('meta_picker','meta_picker_scan','meta_scan_fs')]+['src/directory/directory_replace.c','src/directory/directory_replace_fs.c','standalone/meta_scan_faults.c','standalone/meta_scan_driver.c']
 flags=['-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-os','-i='+str(ROOT/'src/key_mapping'),'-i='+str(ROOT/'standalone')];objects=[]
 for source in sources:
  obj=out/(Path(source).stem+'.obj');extra=[]
  if source.endswith('/meta_picker.c'):extra=['-nt=META_PICKER_CODE','-nc=FARCODE']
  if source.endswith('meta_scan_fs.c'):extra=['-dmeta_scan_fs_first=meta_scan_real_first','-dmeta_scan_fs_next=meta_scan_real_next']
  subprocess.run(['wcc',*flags,*extra,'-fo='+str(obj),str(ROOT/source)],check=True);objects.append(str(obj))
 owned_segments={}
 for name in ('meta_picker_scan','meta_scan_fs'):
  listing=out/(name+'.dis');subprocess.run(['wdis','-l='+str(listing),str(out/(name+'.obj'))],check=True)
  segments={n:int(size,16) for n,size in re.findall(r'^Segment: (\S+).*?([0-9A-Fa-f]{8}) bytes$',listing.read_text(),re.M)}
  assert segments and all(size==0 for n,size in segments.items() if n!='_TEXT');owned_segments[name]=segments
 asm='standalone/meta_scan_banks.asm';subprocess.run(['nasm','-fobj',str(ROOT/asm),'-o',str(out/'banks.obj')],check=True)
 subprocess.run(['wcl',*flags,'-k8192','-fd=KEYSCAN.lnk','-fm=KEYSCAN.map','-fe=KEYSCAN.EXE',str(out/'banks.obj'),*objects],cwd=out,check=True)
 response=out/'KEYSCAN.lnk';response.write_text(response.read_text()+'\norder clname CODE clname FARCODE clname FARSTATE clname BEGDATA clname DATA clname BSS clname STACK\n');subprocess.run(['wlink','@KEYSCAN.lnk'],cwd=out,check=True)
 listing=(out/'KEYSCAN.map').read_text();data=re.search(r'^DGROUP\s+([0-9a-f]+):0000',listing,re.M|re.I);null=re.search(r'^_NULL\s+BEGDATA\s+DGROUP\s+([0-9a-f]+):0000',listing,re.M|re.I);assert data and null and data[1]==null[1]
 entries=re.search(r'^([0-9a-f]+):([0-9a-f]+)\s+_entries\s*$',listing,re.M|re.I);assert entries and int(entries[1],16)*16+int(entries[2],16)+9009<=int(data[1],16)*16
 for d in ('LAB','LAB/FOLDER.KEY','EMPTY','MANY','ALT','OTHER','drive-d/KEEP'):(out/d).mkdir(parents=True)
 fixtures={f'LAB/{n}':b'synthetic KEY scan fixture\r\n' for n in ('A.KEY','Z.KEY','READONLY.KEY','IGNORE.TXT')}
 fixtures.update({f'MANY/K{i:04}.KEY':i.to_bytes(2,'little') for i in range(1002)})
 fixtures.update({f'OTHER/{i}.TXT':bytes([i]) for i in range(3)})
 for n,v in fixtures.items():(out/n).write_bytes(v)
 before={n:sha(out/n) for n in fixtures}
 (out/'CHECK.BAT').write_text('@echo off\nC:\\KEYSCAN >C:\\CHECK.LOG\nif errorlevel 1 goto failed\necho PASS>C:\\RESULT.TXT\ngoto done\n:failed\necho FAIL>C:\\RESULT.TXT\n:done\nexit\n')
 (out/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\nmount c "{out}"\nmount d "{out}/drive-d"\nc:\ncd \\ALT\nd:\ncd \\KEEP\nC:\\CHECK.BAT\nexit\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),check=True,timeout=60)
 text=(out/'CHECK.LOG').read_text();assert (out/'RESULT.TXT').read_text().strip()=='PASS',text
 assert before=={n:sha(out/n) for n in fixtures}
 headers=['src/key_mapping/'+n+'.h' for n in ('meta_picker','meta_picker_scan','meta_scan_fs')]+['src/directory/directory_replace.h','src/directory/directory_replace_fs.h','src/directory/directory_dos.h','standalone/meta_scan_faults.h']
 inputs=sources+headers+[asm,'standalone/build_meta_scan.py'];result=dict(passed=True,binary_sha256=sha(out/'KEYSCAN.EXE'),transcript=text.strip(),cpu='8086',original_inputs=[],unchanged_files=len(fixtures),scanner_owned_segments=owned_segments,scanner_owned_DGROUP_bytes=0,sources={s:sha(ROOT/s) for s in inputs},scope='Actual DOS enumeration plus declared errors/malformed find records over owned scratch files. Interleaved find context/DTA/current drive and per-drive CWD preserved; bounded calls/sorting,1001 limit,partial-list failures. No native original comparison, resource search/claims, modal UI/live parent or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(text.strip())
if __name__=='__main__':main()
