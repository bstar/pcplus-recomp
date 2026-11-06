#!/usr/bin/env python3
"""Probe external-viewer PRM/parameters/command-tail behavior in the unmodified original."""
import argparse,hashlib,json,os,shutil,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--case',choices=['relative','absolute','options','spaces','empty','cancel','long'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True);c=out/'c';c.mkdir();d=out/'d';d.mkdir()
 original=ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE';assert sha(original)=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
 shutil.copyfile(original,c/'PCPLUS.EXE')
 baseline=ROOT/'build/cwd-ui-recovery-20261104/first/c/PCPLUS.PRM';raw=bytearray(baseline.read_bytes());assert len(raw)==1264
 command=b'D:\\VTEST.COM'+(b' /Q /X' if a.case=='options' else b'')
 raw[0x35d:0x35d+len(command)+1]=command+b'\0';(c/'PCPLUS.PRM').write_bytes(raw)
 for n in ['PCPLUS.KEY','PCPLUS.KBD','PCPLUS.XLT']:
  source=ROOT/'analysis/pcplus-install'/n
  if source.exists():shutil.copyfile(source,c/n)
 subprocess.run(['nasm','-fbin',str(ROOT/'standalone/viewer_external_child.asm'),'-o',str(d/'VTEST.COM')],check=True)
 subprocess.run(['nasm','-fbin',str(ROOT/'standalone/viewer_original_watch.asm'),'-o',str(c/'WATCH.COM')],check=True)
 parameters={'relative':'PAGE.DAT','absolute':'D:\\PAGE.DAT','options':'PAGE.DAT','spaces':'D:\\A B.DAT','empty':'','cancel':'','long':'A'*48}[a.case]
 (c/'PAGE.DAT').write_bytes(b'OWNED VIEWER INPUT\r\n');(d/'PAGE.DAT').write_bytes(b'OWNED VIEWER INPUT\r\n')
 action='escape' if a.case=='cancel' else ' '.join('space' if c==' ' else c for c in parameters)+' enter'
 keys='p750 enter p3250 a-v p900 '+action+' p2000 space p700 escape p500 a-x p400 y enter p500 a-x p400 y enter'
 cfg=out/'dosbox.conf';cfg.write_text(f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
fpu=false
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=dummy
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{c}"
mount d "{d}"
c:
set PCPLUS=
WATCH T
ADDKEY {keys}
C:\\PCPLUS
C:\\WATCH
cd>C:\\AFTERCD.TXT
echo DONE>C:\\DONE.TXT
exit
''')
 generated={str(p.relative_to(out)):sha(p) for p in [c/'PCPLUS.EXE',d/'VTEST.COM',c/'WATCH.COM',cfg]}
 with (out/'dosbox.log').open('w') as log:
  try:code=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(cfg)],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=50).returncode
  except subprocess.TimeoutExpired:code=None
 capture=c/'EDITVIEW.BIN'
 if capture.exists():
  frames=capture.read_bytes();magic,count,ticks=struct.unpack_from('<3H',frames);assert magic==0x4544 and count
  for i in range(count):
   frame=frames[10+i*4004:4010+i*4004];(out/('frame-%d.bin'%i)).write_bytes(frame)
   (out/('frame-%d.txt'%i)).write_text('\n'.join(frame[r*160:(r+1)*160:2].decode('cp437') for r in range(25)))
 child=d/'VCHILD.BIN';data=child.read_bytes() if child.exists() else b'';tail=data[8:136] if len(data)==202 else b''
 report=dict(observed=True,case=a.case,process_exit=code,DOS_done=(c/'DONE.TXT').exists(),original_sha256=sha(original),command=command.decode(),parameters=parameters,PRM_offset=0x35d,PRM_fixture_sha256=hashlib.sha256(raw).hexdigest(),child_report_sha256=sha(child) if child.exists() else None,child_report_bytes=len(data),child_tail_hex=tail.hex(),child_tail_length=tail[0] if tail else None,child_tail_text=tail[1:1+tail[0]].decode('cp437') if tail else None,child_drive=struct.unpack_from('<H',data,136)[0] if data else None,child_cwd=data[138:202].split(b'\0',1)[0].decode('cp437') if data else None,generated_unchanged=generated=={str((out/n).relative_to(out)):sha(out/n) for n in generated},sources={n:sha(ROOT/n) for n in ['standalone/test_viewer_external_original.py','standalone/viewer_external_child.asm','standalone/viewer_original_watch.asm']},scope=__doc__+' Only copied PRM changes. Original executable is unmodified; owned COM child records actual PSP tail and DOS CWD. Synthetic analysis images are never executed. Observations require separate acceptance, not a full viewer or hardware claim.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['sources','child_tail_hex']}))
if __name__=='__main__':main()
