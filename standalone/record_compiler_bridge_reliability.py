#!/usr/bin/env python3
"""Bind current package bytes to reconnect/endurance and stock-editor evidence."""
import argparse,hashlib,json,re,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('package','busy','endurance','wrapper','output'):p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--enigma-label',action='append',required=True);p.add_argument('--sync-label',required=True)
 p.add_argument('--controls',type=Path,action='append',required=True)
 a=p.parse_args();receipts={}
 def read(path,passed=True):
  path=path.resolve();assert path.is_relative_to(ROOT/'build')
  r=json.loads(path.read_text());assert not passed or r['passed'],path
  receipts[str(path.relative_to(ROOT))]=sha(path)
  for key in ('sources','product_inputs'):
   for name,digest in r.get(key,{}).items():assert sha(ROOT/name)==digest,name
  return r
 m=read(a.package/'manifest.json',False);parent=m['files']['TERMINAL.EXE']
 for name,digest in m['files'].items():assert sha(a.package/m['dos_directory']/name)==digest
 busy=read(a.busy/'result.json');assert busy['terminal_sha256']==parent
 assert [r['case'] for r in busy['cases']]==['busy-exit','busy-redial','three-calls']
 busy_rows=[]
 for case in busy['cases']:
  path=ROOT/case['result'];r=read(path);folder=path.parent
  assert all(r['checks'].values()) and r['binary_sha256']==parent and r['cpu']=='8086'
  count={'busy-exit':1,'busy-redial':2,'three-calls':3}[case['case']]
  assert r['commands']==['ATZ','ATDCaseTest:23']*count
  assert (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes() and (folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists()
  config=(folder/'dosbox.conf').read_text();assert config.count('C:\\TERMINAL ')==1
  if count==3:
   wire=(folder/'serial.bin').read_bytes();assert wire.count(b'\x1b[1;16R')==3 and wire.count(b'\x1b[?1;2c')==3
   assert all(wire.count(word+b'\r')==1 for word in (b'one',b'two',b'three'))
  busy_rows.append(dict(case=case['case'],attempts=count,checks=r['checks'],actual_seconds=r['seconds']))
 endurance=read(a.endurance/'result.json');assert endurance['terminal_sha256']==parent and endurance['acceptance_duration'] and endurance['seconds']>=300 and endurance['frames']==601
 native_path=ROOT/endurance['native_result'];native=read(native_path);folder=native_path.parent
 assert native['seconds']>=300 and all(native['checks'].values()) and native['binary_sha256']==parent
 assert (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
 wire=(folder/'serial.bin').read_bytes().replace(b'\x11',b'').replace(b'\x13',b'')
 assert re.findall(rb'\x1b\[\d+;\d+R',wire)==[b'\x1b[1;16R']+[f'\x1b[{2+i%16};80R'.encode() for i in range(601)]
 expected=[];last={}
 for i in range(601):
  row=2+i%16;text=(f'FRAME {i:04d} ROW {row:02d} '+''.join(chr(65+(i+j)%26) for j in range(79))).encode()[:79]
  expected.append(f'\x1b[{row};1H'.encode()+text+b'\x1b[6n');last[row]=text
 assert (folder/'flow-payload.bin').read_bytes()==b''.join(expected) and wire.count(b'ready\r')==1
 screen=(folder/'SCREEN.BIN').read_bytes()
 for row,text in last.items():
  start=(row-1)*160;assert screen[start:start+158:2]==text and screen[start+1:start+158:2]==bytes([7])*79
 wrapper=read(a.wrapper/'result.json');assert len(wrapper['cases'])==4 and all(r['passed'] for r in wrapper['cases'])
 for name,digest in wrapper['artifacts'].items():assert sha(a.wrapper/name)==digest,name
 editors=[]
 assert len(a.enigma_label)==3
 for server,label in [('enigma',n) for n in a.enigma_label]+[('synchronet',a.sync_label)]:
  assert re.fullmatch('[a-z0-9-]+',label)
  folder=ROOT/'build/bbs-lab/results'/server/label
  r=read(folder/'proxy-integration.json');assert r['binary_sha256']==parent and all(r['checks'].values())
  cells=read(folder/'screen-reference-audit.json');assert cells['binary_sha256']==parent and all(cells['checks'].values())
  assert cells['different_cells']==0 and cells['matched_cells']==1920 and cells['logical_rows']==24 and cells['physical_rows']==25
  for name,digest in cells['captures'].items():assert sha(ROOT/name)==digest,name
  if server=='enigma':
   semantic=read(folder/'semantic-audit.json');assert all(semantic['checks'].values())
   detail=semantic['authority'].get('multiline');mode=detail['mode'] if detail else 'baseline'
   if detail:assert detail['actual_body']==detail['expected_body']
   modal=r.get('reference_observer')
  else:
   mode='keymap-help';modal=read(folder/'keymap-audit.json');assert all(modal['checks'].values())
   assert r['interpreter_sha256']==m['files']['ASPECT.EXE'] and (folder/'SCRIPT.OK').read_bytes()==b'PASS'
   native=read(folder/'result.json');assert native['status_runner_high_requested'] and native['checks']['status_wrapper_environment_preserved']
   env=struct.unpack('<6H',(folder/'ENVPROOF.BIN').read_bytes());assert env[:2]==(0x5354,1) and env[3]>=0xa000 and env[5]==1
  editors.append(dict(server=server,label=label,mode=mode,checks=r['checks'],matched_cells=1920,different_cells=0,CPR=cells['actual_CPR'],modal=modal))
 assert {r['mode'] for r in editors if r['server']=='enigma'}=={'baseline','page-up','page-down'}
 controls=[]
 for folder in a.controls:
  r=read(folder/'result.json');assert len(r['cases'])==9 and all(row['passed'] and row['rejected']==(row['case']!='unchanged') for row in r['cases'])
  controls.append(dict(path=str(folder),cases=r['cases']))
 assert len(controls)==2
 for name in ('aspect-compiler-package.json','aspect-compiler-connection.json'):
  path=ROOT/'docs/validation'/name;j=json.loads(path.read_text());assert j['checkpoint_verified'];receipts[str(path.relative_to(ROOT))]=sha(path)
  if name=='aspect-compiler-package.json':assert j['files']==m['files']
  else:
   for leaf,digest in j['products'].items():assert m['files'][leaf]==digest,leaf
 names=['standalone/record_compiler_bridge_reliability.py','standalone/test_busy_retry_dos.py','standalone/test_terminal_endurance_dos.py','lab/bbs/test_dos.py','lab/bbs/test_synchronet_screen_reference_dos.py','lab/bbs/enigma_multiline.py','standalone/dos_status_runner.asm','standalone/test_status_runner_high_dos.py','nix/flake.nix','nix/flake.lock']
 result=dict(checkpoint_verified=True,tool_source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),application_bytes_changed=False,installed_changed=False,selector_changed=False,physical_verified=False,
  package_files=m['files'],busy_and_reconnect=busy_rows,endurance=dict(seconds=endurance['seconds'],actual_seconds=read(native_path)['seconds'],frames=601,scope=endurance['scope']),
  editors=editors,screen_controls=controls,wrapper_controls=wrapper['cases'],receipts=receipts,sources={n:sha(ROOT/n) for n in names},
  scope='Current unchanged17-file candidate: actual DOS/synthetic modem plus stock loopback BBS editors through actual Telnet proxy. Default25-row display/status visible; paced endurance is not saturation/SIP/audio/physical acceptance.',
  remaining=['Physical/private-machine admission and deployed-byte confirmation.','Saturation/CTS timing and every owner/geometry/profile combination.','Full original ASPECT/emulation/protocol/Host and remaining helper/UI equivalence.'])
 a.output.write_text(json.dumps(result,indent=2)+'\n');print('Verified current BUSY/three-call/endurance and four exact stock editor snapshots')


if __name__=='__main__':main()
