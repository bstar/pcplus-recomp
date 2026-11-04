#!/usr/bin/env python3
"""Independent startup BIOS geometry, PRM words, raw wire and screen verification.
Owned DOS captures only; no physical/BBS/NAWS acceptance.
"""
import argparse,hashlib,json,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 run=a.run.resolve();out=a.output.resolve();assert run.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 report=json.loads((run/'result.json').read_text());assert report['passed']
 for n,h in report['sources'].items():assert sha(ROOT/n)==h,n
 for parent in report['parents'].values():assert sha(ROOT/parent['path'])==parent['sha256']
 expected={f'rows-{rows}-hidden-{hidden}' for rows in (25,28,43,50) for hidden in (0,1)}|{f'selector-{selector}-hidden-{hidden}' for selector in (0,3,4) for hidden in (0,1)}|{f'fallback-{mode}-hidden-{hidden}' for mode in (0,18) for hidden in (0,1)}|{'invalid-5','invalid-65535','no-import','disabled-control'}
 assert len(report['cases'])==22 and {r['case']['name'] for r in report['cases']}==expected
 utility=out/'GEOM.COM';subprocess.run(['nasm','-fbin',str(ROOT/'standalone/display_startup_geometry.asm'),'-o',str(utility)],check=True)
 cases=[]
 for r in report['cases']:
  c=r['case'];assert r['passed'] and all(r['checks'].values());parent=report['parents']['disabled' if c.get('disabled') else 'enabled'];assert r['terminal_sha256']==parent['sha256']
  for n,h in r['artifacts'].items():assert sha(ROOT/n)==h,n
  folder=(ROOT/r['parent_result']).parent;raw=(folder/'TEST.PRM').read_bytes()
  assert tuple(struct.unpack_from('<H',raw,at)[0] for at in (0x1c2,0x1c8,0x1ca,0x4ec))==(c['hidden'],c['selector'],c['preferred'],c['mode'])
  physical=25 if c.get('disabled') or c.get('no_import') or c.get('invalid') or c['selector'] in (0,1,3) or not c['mode'] and c['selector']==4 or c['mode']==18 else c['preferred']
  hidden=c['hidden'] if not c.get('no_import') and not c.get('disabled') else 0;logical=physical-(not hidden)
  geometry=struct.unpack('<4H',(folder/'GEOM.BIN').read_bytes());assert geometry[0]==physical and geometry[1]==(14 if physical==28 else 8 if physical in (43,50) else 16)
  assert geometry[2]==0x5003 and geometry[3]>>8==0 and sha(folder/'GEOM.COM')==sha(utility)
  assert (folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists() and len((folder/'BEFORE.BIN').read_bytes())==42 and (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
  assert 'cputype=8086' in (folder/'dosbox.conf').read_text()
  wire=(folder/'serial.bin').read_bytes();screen=(folder/'SCREEN.BIN').read_bytes();assert len(screen)==8000
  if c.get('invalid'):assert wire==b''
  else:
   wanted=b'\x1b[0n\x1b[1;16R\x1b[?1;2c'+b'\x1b'+f'[8;{logical};80t'.encode()+b'\x1b'+f'[{logical};5R'.encode()+b'a'+b'\x1b'+f'[8;{logical};80t'.encode()+b'\x1b'+f'[{logical};80R'.encode()
   assert wire==wanted and screen[:30:2]==b'FIRST BYTE SAFE' and screen[(logical-1)*160:(logical-1)*160+8:2]==b'BOOT'
   assert (b'Alt-Z FOR HELP' in screen[(physical-1)*160:physical*160:2])==bool(not hidden)
  cases.append(dict(case=c['name'],physical_rows=physical,logical_rows=logical,invalid=c.get('invalid',False),no_transmit_before_failed_startup=c.get('invalid',False),passed=True))
 sources=['standalone/check_display_startup_artifacts.py','standalone/test_display_startup_dos.py','standalone/test_connection_dos.py','standalone/display_startup_geometry.asm']
 result=dict(passed=True,DOS_workflows=len(cases),successful_layouts=sum(not c['invalid'] for c in cases),failed_startups_without_transmit=sum(c['invalid'] for c in cases),cases=cases,report_sha256=sha(run/'result.json'),sources={n:sha(ROOT/n) for n in sources},scope=__doc__+' Rebuilds geometry observer; actual imported-selector startup/fallback/absence/disabled control, full physical pixels and exact area/CPR/key bytes. Model-only BIOS faults remain separate.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS independent display startup',len(cases),'DOS workflows')
if __name__=='__main__':main()
