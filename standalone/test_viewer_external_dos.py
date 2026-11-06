#!/usr/bin/env python3
"""Source-only DOS8086 checked external-viewer command construction; no launch/UI claim."""
import argparse,json,os,subprocess
from pathlib import Path
from build_path_session import ROOT,sha,object_segments

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 names=['src/filesystem/viewer_external.c','src/filesystem/viewer_external.h','standalone/viewer_external_diagnostic.c','standalone/test_viewer_external_dos.py','standalone/build_path_session.py'];frozen={n:sha(ROOT/n) for n in names}
 flags=['-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we']
 for name,source,bank in [('external','src/filesystem/viewer_external.c',True),('diagnostic','standalone/viewer_external_diagnostic.c',False)]:
  subprocess.run(['wcc',*flags,*(['-nt=FILE_CODE','-nc=FARCODE'] if bank else []),'-fo='+str(out/(name+'.obj')),str(ROOT/source)],cwd=out,check=True)
 subprocess.run(['wcl',*flags,'-k8192','-fm=EXTVIEW.map','-fe=EXTVIEW.EXE','external.obj','diagnostic.obj'],cwd=out,check=True)
 segments=object_segments(out/'external.obj');assert segments['FILE_CODE']['class']=='FARCODE' and all(not s['bytes'] for n,s in segments.items() if n!='FILE_CODE')
 cfg=out/'dosbox.conf';cfg.write_text(f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
fpu=false
cycles=fixed 12000
[autoexec]
mount d "{out}"
d:
EXTVIEW
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto done
:failed
echo FAIL>FAIL.TXT
:done
exit
''')
 with (out/'dosbox.log').open('w') as log:process=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(cfg)],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=30)
 checks,failures=map(int,(out/'RESULT.TXT').read_text().split());assert process.returncode==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists() and checks>33000 and failures==0
 for n,h in frozen.items():assert sha(ROOT/n)==h,n
 (out/'result.json').write_text(json.dumps(dict(passed=True,checks=checks,failures=failures,binary_sha256=sha(out/'EXTVIEW.EXE'),sources=frozen,segments=segments,original_inputs=[],scope=__doc__+' Full64/48-byte length matrix, disabled/malformed fields, exact literal bytes, output guards, no-change failures, alias/segment/20-bit bounds. FILE_CODE has no near data or persistent state. Native launch, title/prompt and full parent integration remain separate.'),indent=2)+'\n');print('PASS',checks,'checks')
if __name__=='__main__':main()
