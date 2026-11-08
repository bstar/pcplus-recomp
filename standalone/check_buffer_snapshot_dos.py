#!/usr/bin/env python3
"""Actual8086 DOS exact disk snapshots, corruption, failures and handle ownership."""
import argparse,json,os,re,subprocess
from pathlib import Path
from build_path_session import ROOT,sha


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
 names=['src/aspect/buffer_snapshot.c','src/aspect/buffer_snapshot.h','src/aspect/runtime.h',
        'standalone/buffer_snapshot_fixture.c','standalone/check_buffer_snapshot_dos.py']
 sources={n:sha(ROOT/n) for n in names}
 subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-os','-w4','-we',
  '-d_dos_creatnew=snapshot_create','-d_dos_write=snapshot_write','-d_dos_read=snapshot_read',
  '-d_dos_close=snapshot_close','-dremove=snapshot_remove','-fo='+str(out/'backend.obj'),
  str(ROOT/'src/aspect/buffer_snapshot.c')],cwd=out,check=True)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192',
  '-i='+str(ROOT/'src/aspect'),'-fm=SNAPSHOT.map','-fe=SNAPSHOT.EXE',
  str(ROOT/'standalone/buffer_snapshot_fixture.c'),str(out/'backend.obj')],cwd=out,check=True)
 (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nc:\nSNAPSHOT >REPORT.TXT\nif errorlevel 1 goto failed\nSNAPSHOT 9 >QUAR9.TXT\nif errorlevel 1 goto failed\nSNAPSHOT 10 >QUAR10.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\ngoto done\n:failed\necho FAIL>FAIL.TXT\n:done\nexit\n')
 with (out/'dosbox.log').open('w') as log:
  r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,
   env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=35)
 raw=(out/'REPORT.TXT').read_text();m=re.fullmatch(r'SNAPSHOTS (\d+) checks 0 failures\n',raw)
 assert r.returncode==0 and m and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),raw
 quarantined=sorted(out.glob('LPS*.TMP'))
 assert [p.name for p in quarantined]==['LPS00000.TMP','LPS00001.TMP']
 for path in quarantined:assert path.stat().st_size==519 and path.read_bytes()[:6]==b'LPS1\x01\0'
 assert (out/'FOREIGN.BIN').read_bytes()==b'SAFE'
 quarantine_checks=0
 for name in ['QUAR9.TXT','QUAR10.TXT']:
  q=re.fullmatch(r'QUARANTINE (\d+) checks 0 failures\n',(out/name).read_text());assert q
  quarantine_checks+=int(q[1])
 assert all(sha(ROOT/n)==h for n,h in sources.items())
 result=dict(passed=True,checks=int(m[1]),quarantine_checks=quarantine_checks,quarantined_files={p.name:sha(p) for p in quarantined},sources=sources,original_inputs=[],binary_sha256=sha(out/'SNAPSHOT.EXE'),
  scope=__doc__+' Actual raw DOS file IO and PSP JFT;0..6 full buffers, exclusive collision preservation,24 single-byte corruption positions across6 slots, owner mutation, header/tag/truncation/trailing bytes, create/write/read/close/unlink failures and cleanup retry. Persistent uncertain-close cases deliberately retain their two owned files until inspection; later discard never closes a reused descriptor. DOS process exit retires remaining handles. Component only; full VM/PROGRAM and physical acceptance separate.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',m[1],'snapshot checks')


if __name__=='__main__':main()
