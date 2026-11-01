#!/usr/bin/env python3
"""Frozen setup compare/publication, accounting refusal and later real PRM reloads."""
import argparse,hashlib,json,os,shutil,struct,subprocess
from pathlib import Path
from directory_fixtures import prm,directory
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
NAMES=['first-directory-selection','replace-context-after-check','stale-accounting-context','reconciled-accounting-context','pending-accounting-flags','pending-setup-transaction','unacknowledged-settings-offer','invalid-extents-and-aliases','invalid-selection-identities','invalid-baseline-and-record','63-byte-canonical-directory']
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 built=ROOT/'build/setup-selection';m=json.loads((built/'manifest.json').read_text());assert not m['original_inputs']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 assert sha(built/'SELECT.EXE')==m['binary_sha256'];shutil.copyfile(built/'SELECT.EXE',out/'SELECT.EXE')
 raw=bytearray(directory(entry=1,baud=5));struct.pack_into('<H',raw,250+114+46,4)
 files={'TEST.PRM':prm(port=1,baud=6),'TEST.DIR':bytes(raw)}
 for n,b in files.items():(out/n).write_bytes(b)
 commands=[]
 for i in range(len(NAMES)):commands+=['cd \\',f'C:\\SELECT {i} >C:\\R{i:02}.TXT','if errorlevel 1 goto failed',f'ren C:\\REPORT.BIN R{i:02}.BIN']
 commands+=['cd \\','echo PASS>PASS.TXT','exit',':failed','cd \\','echo FAIL>FAIL.TXT','exit']
 config='[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 12000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nc:\n'+'\n'.join(commands)+'\n';(out/'dosbox.conf').write_text(config)
 with (out/'dosbox.log').open('w') as log:r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=120)
 assert r.returncode==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),[(q.name,q.read_text()) for q in sorted(out.glob('R*.TXT'))]
 cases=[]
 for i,n in enumerate(NAMES):
  mode,checks,opens,reads,closes,canonical=struct.unpack('<6H',(out/f'R{i:02}.BIN').read_bytes());assert mode==i and opens==closes
  cases.append(dict(case=n,passed=True,native_assertions=checks,opens=opens,reads=reads,closes=closes,canonicalizations=canonical))
 for n,b in files.items():assert (out/n).read_bytes()==b,n
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 fixtures=['standalone/test_setup_selection_dos.py','standalone/directory_fixtures.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py']
 result=dict(passed=True,binary_sha256=m['binary_sha256'],sources=m['sources'],case_count=len(cases),cases=cases,native_assertions=sum(c['native_assertions'] for c in cases),original_inputs=[],test_sources={n:sha(ROOT/n) for n in fixtures},artifacts={str(q.relative_to(out)):sha(q) for q in out.rglob('*') if q.is_file()},scope=__doc__+' Actual production decoders, setup owner, expansion and DOS filesystem. IO counters must remain unchanged within every selection API invocation. Later settings finishes read the real PRM and prove retained negotiated speed/session separator. No application selection/UART/dialing/physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(cases),'DOS workflows;',result['native_assertions'],'native assertions')
if __name__=='__main__':main()
