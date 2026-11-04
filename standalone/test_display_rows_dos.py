#!/usr/bin/env python3
"""Exercise actual BIOS row/font services across owned DOSBox display models."""
import argparse, hashlib, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--component',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 component,out=a.component.resolve(),a.output.resolve()
 assert component.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build')
 out.mkdir(parents=True,exist_ok=False);manifest=json.loads((component/'manifest.json').read_text())
 for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
 assert sha(component/'ROWS.EXE')==manifest['binary_sha256']
 results={}
 expected={'vga':(3,1,1),'vga-mono':(7,1,1),'ega':(3,1,0),'cga':(3,0,0),'hercules':(7,0,0)}
 for label,machine,argument in [('vga','svga_s3',''),('vga-mono','svga_s3',' /MONO'),('ega','ega',''),('cga','cga',''),('hercules','hercules',' /MONO')]:
  run=out/label;run.mkdir();shutil.copyfile(component/'ROWS.EXE',run/'ROWS.EXE')
  (run/'CHECK.BAT').write_bytes(('@echo off\r\nROWS'+argument+' >CHECKS.TXT\r\nif errorlevel 1 goto bad\r\necho PASS>RESULT.TXT\r\ngoto done\r\n:bad\r\necho FAIL>RESULT.TXT\r\n:done\r\nexit\r\n').encode())
  config=f'''[sdl]
output=surface
[dosbox]
machine={machine}
[cpu]
core=normal
cputype=8086
cycles=fixed 3000
[mixer]
nosound=true
[serial]
serial1=disabled
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
mount c "{run}"
c:
CHECK.BAT
exit
'''
  (run/'dosbox.conf').write_text(config)
  with (run/'dosbox.log').open('w') as log:
   result=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(run/'dosbox.conf')],
    env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=30)
  text=(run/'CHECKS.TXT').read_text(errors='replace') if (run/'CHECKS.TXT').exists() else ''
  match=re.search(r'DISPLAY_ROWS (\d+) checks (\d+) failures',text)
  adapter=re.search(r'ADAPTER mode=(\d+) font=(\d+) scanline=(\d+) vendor=(\d+) rows=(\d+)',text)
  capability_matches=bool(adapter) and tuple(int(adapter[i]) for i in (1,2,3))==expected[label] and adapter[5]=='25'
  passed=result.returncode==0 and bool(match) and match[2]=='0' and capability_matches and (run/'RESULT.TXT').read_text().strip()=='PASS'
  results[label]=dict(passed=passed,checks=int(match[1]) if match else 0,machine=machine,argument=argument,
   capability_matches=capability_matches,
   artifacts={x.name:sha(x) for x in run.iterdir() if x.is_file()})
  print(label, text.strip(),flush=True)
 # Rebuild the entire component in an isolated source-only tree with no Git or
 # original binaries. Producer and input identities stay frozen throughout.
 with tempfile.TemporaryDirectory(prefix='pcplus-display-rows-source-') as temporary:
  exported=Path(temporary)
  assert not any((parent/'.git').exists() for parent in [exported,*exported.parents]),'Source proof has ancestor Git'
  for name in manifest['sources']:
   target=exported/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
  rebuilt=exported/'build/rebuilt'
  subprocess.run([sys.executable,str(exported/'standalone/build_display_rows.py'),'--output',str(rebuilt)],check=True)
  assert sha(rebuilt/'ROWS.EXE')==manifest['binary_sha256'],'Source-only executable differs'
  shutil.copytree(exported,out/'source-export')
 rebuilt=out/'source-export/build/rebuilt'
 for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
 assert sha(component/'ROWS.EXE')==manifest['binary_sha256']
 report=dict(passed=all(x['passed'] for x in results.values()),models=results,binary_sha256=manifest['binary_sha256'],
  manifest_sha256=sha(component/'manifest.json'),checker_sha256=sha(Path(__file__)),
  source_only_rebuild=True,source_rebuild_ancestor_git_absent=True,source_only_rebuild_sha256=sha(rebuilt/'ROWS.EXE'),sources=manifest['sources'],
  scope='Actual8086 DOSBox BIOS execution on VGA(S3), EGA, CGA and Hercules models. Recovered detection/font/row/geometry code, maintained validation and verified fallback after diagnostic INT10 refusal. No function/instruction/return-address patches. No live terminal/parser/frame/reset/bridge, UART, BBS, real Cirrus card or physical acceptance.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
 assert report['passed'],'Display-model matrix failed; inspect retained CHECKS.TXT'
 print('PASS actual BIOS display matrix and exact Git-free source rebuild')
if __name__=='__main__':main()
