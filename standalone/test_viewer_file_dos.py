#!/usr/bin/env python3
"""Exercise real DOS viewer reads/seeks and shared capture reservations on owned fixtures."""
import argparse,json,os,re,shutil,subprocess
from pathlib import Path
from build_path_session import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['program','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();binary=a.program.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 manifest=json.loads(binary.with_name('manifest.json').read_text());assert sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 out.mkdir(parents=True);c=out/'c';d=out/'d';c.mkdir();d.mkdir();(d/'SUB').mkdir()
 shutil.copyfile(binary,c/'VIEWFILE.EXE');data=bytes(range(256))*371+bytes(range(64));assert len(data)==95040
 (d/'DATA.BIN').write_bytes(data);(d/'READONLY.BIN').write_bytes(b'READONLY');original={n:sha(d/n) for n in ['DATA.BIN','READONLY.BIN']}
 config=out/'dosbox.conf';config.write_text(f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
fpu=false
cycles=fixed 6000
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{c}"
mount d "{d}"
c:
VIEWFILE > RESULT.TXT
if errorlevel 1 echo FAIL>EXIT.TXT
if not errorlevel 1 echo PASS>EXIT.TXT
cd>AFTERCD.TXT
exit
''')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(config)],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=90)
 text=(c/'RESULT.TXT').read_text();match=re.search(r'VIEWFILE checks=(\d+) failures=0',text)
 assert match and 'FAIL' not in text and (c/'EXIT.TXT').read_text().strip()=='PASS',text
 assert (c/'AFTERCD.TXT').read_text().strip()=='C:\\'
 assert {n:sha(d/n) for n in original}==original
 # DOSBox-X stores extra DOS attributes separately; readonly uses host mode.
 sidecar=d/'.DBLOCALFILE_ATR_READONLY.BIN'
 assert sidecar.read_bytes()==b'\x00' and not (d/'READONLY.BIN').stat().st_mode&0o222
 assert {p.name for p in d.iterdir()}=={'DATA.BIN','READONLY.BIN','SUB',sidecar.name}
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 r=dict(passed=True,binary_sha256=sha(binary),checks=int(match[1]),cpu='8086',FPU=False,original_inputs=[],sources={**manifest['sources'],'standalone/test_viewer_file_dos.py':sha(Path(__file__))},
  fixture_hashes=original,artifacts={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()},
  scope=__doc__+' Actual DOS3D/43/44/3F/42/3E/60, far read buffer, binary byte checks,32-bit seek beyond64KB/cross-boundary/EOF, CWD-independent open handle, read-only file, missing/directory/invalid paths, active capture-vs-viewer mutual exclusion,100close/reopens and unchanged payloads. DOSBox, not DOS6.22/SHARE enforcement or physical acceptance; fault injection and UI remain separate.')
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS viewer owner:',r['checks'],'actual DOS checks')
if __name__=='__main__':main()
