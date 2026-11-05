#!/usr/bin/env python3
"""Bind Gateway sink preservation and current-parent transfer/reconnect evidence."""
import argparse,hashlib,json,re,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'lab/bbs'))
from product_inputs import select_product,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['terminal','sinks','ansi','vt220','transfer-audit','output']:p.add_argument('--'+n,required=True,type=Path)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 binary,inputs=select_product(a.terminal,'TERMINAL.EXE');digest=sha(binary)
 def bind(path):
  path=Path(path).resolve();assert path.is_relative_to(ROOT/'build');return dict(path=str(path.relative_to(ROOT)),sha256=sha(path))
 def checked(path):
  d=json.loads(Path(path).read_text());assert d['passed']
  for n,h in d.get('sources',{}).items():assert sha(ROOT/n)==h,n
  return d
 sinks=checked(a.sinks);assert sinks['binary_sha256']==digest
 flags={'capture':(1,0,0),'hold':(1,1,0),'capture-printer':(1,0,1),'hold-printer':(1,1,1),'printer':(0,0,1)}
 assert {c['case'] for c in sinks['cases']}==set(flags)
 entries={n:(int(seg,16),int(off,16)) for seg,off,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+]?\s+(\w+)\s*$',binary.with_name('terminal.map').read_text(),re.M|re.I)}
 cases=[]
 for c in sinks['cases']:
  assert c['passed'] and all(c['checks'].values()) and c['binary_sha256']==digest
  folder=a.sinks.parent/c['case'];capture,hold,printer=flags[c['case']]
  expected=b'FIRST\r\n'+(b'' if hold else b'A'*3200+b'\r\n')+b'LAST\r\n'
  print_expected=b'FIRST\r\n'+(b'PAUSED\r\n' if hold else b'')+b'A'*3200+b'\r\nLAST\r\n'
  if capture:assert (folder/'CAP.LOG').read_bytes()==expected
  else:assert not (folder/'CAP.LOG').exists()
  if printer:assert (folder/'PRINTER.RAW').read_bytes()==print_expected
  child=struct.unpack('<32H',(folder/'CHILD.BIN').read_bytes());assert child[:30]==(6,6)*15 and child[30:]==(5,0xd00)
  uart=(folder/'GUSHELL.BIN').read_bytes();assert len(uart)==16 and uart[:4]==uart[4:8] and uart[8]==uart[11]==9 and uart[9]==11 and uart[12]==9 and struct.unpack_from('<H',uart,14)[0]>=54
  trace=(folder/'TRACE.BIN').read_bytes();assert len(trace)==8218 and trace[:6]==b'GS21\x0f\0'
  head=struct.unpack_from('<10H',trace,6);assert head[:2]==(0xc51b,1) and head[2]<=1024 and head[3]==0
  records=[struct.unpack_from('<4H',trace,26+i*8) for i in range(head[2])]
  calls=[(i,r) for i,r in enumerate(records) if r[0]==0x4b00 and r[1]==entries['process_parameters'][1]];assert len(calls)==1
  at,call=calls[0];ds=call[3]
  if capture:
   writes=[(i,r) for i,r in enumerate(records) if r[0]>>8==0x40 and r[3]==ds and r[2]>1]
   prior=[(i,r) for i,r in writes if i<at];later=[(i,r) for i,r in writes if i>at];assert prior and later
   fd=prior[-1][1][1];assert fd==later[0][1][1]
   assert not any(prior[-1][0]<i<later[-1][0] and r[0]>>8==0x3e and r[3]==ds and r[1]==fd for i,r in enumerate(records))
  files=['result.json','TEST.PRM','CHILD.BIN','GUSHELL.BIN','OWN.DAT','TRACE.BIN','wire.bin','peer-text.bin','BEFORE.BIN','AFTER.BIN','AFTERCD.TXT','dosbox.conf','SHELL.COM','TRACE.COM','TDUMP.COM']
  if capture:files.append('CAP.LOG')
  if printer:files.append('PRINTER.RAW')
  assert (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes() and b'\x13' in (folder/'wire.bin').read_bytes() and b'\x11' in (folder/'wire.bin').read_bytes()
  cases.append(dict(case=c['case'],passed=True,checks=c['checks'],capture_bytes=c['capture_bytes'],printer_bytes=c['printer_bytes'],evidence=[bind(folder/f) for f in files]))
 reconnect=[]
 for path,profile in [(a.ansi,4),(a.vt220,6)]:
  r=checked(path);assert all(r['checks'].values()) and r['normal_display_startup'] and r['profile']==profile and r['physical_rows']==25 and r['flow']=='both'
  assert r['inputs'][str(binary.relative_to(ROOT))]==digest
  for n,h in r['inputs'].items():assert sha(ROOT/n)==h,n
  for n,h in r['captures'].items():assert sha(path.parent/'run'/n)==h,n
  assert (path.parent/'run/SECOND.OK').read_bytes()==b'RECONNECTED'
  reconnect.append(dict(profile=profile,passed=True,report=bind(path),checks=r['checks'],observations=r['observations'],modem_commands=r['modem_commands'],scope=r['scope']))
 transfer=checked(a.transfer_audit);assert transfer['terminal_sha256']==digest and transfer['payload_bytes']==65539 and transfer['same_DOS_process'] and transfer['exact_retry'] and transfer['partial_disk_bytes']>0
 for n,h in transfer['captures'].items():assert sha(ROOT/n)==h,n
 names=['standalone/record_gateway_composition.py','standalone/test_gateway_sinks_dos.py','standalone/gateway_sinks_trace_install.asm','standalone/gateway_sinks_trace_dump.asm','standalone/test_modem_large_reconnect_dos.py','lab/bbs/audit_proxy_cancel_retry.py']
 result=dict(passed=True,binary_sha256=digest,terminal=bind(binary),manifest=bind(binary.with_name('manifest.json')),map=bind(binary.with_name('terminal.map')),sinks={'report':bind(a.sinks),'cases':cases},reconnect=reconnect,transfer={'report':bind(a.transfer_audit),'payload_bytes':transfer['payload_bytes'],'partial_disk_bytes':transfer['partial_disk_bytes'],'server_exit_codes':transfer['server_exit_codes'],'scope':transfer['scope']},sources={n:sha(ROOT/n) for n in names},original_inputs=[],physical_deployment_changed=False,
  scope='Unchanged normal Gateway-enabled parent: five actual DOS foreground Gateway sink combinations with3200-byte child pressure; ANSI/VT220 same-process modem loss/redial and ASPECT recovery; independently audited stock Enigma cancel/cleanup/exact65539-byte retry. Reconnect and transfer cases regress the enabled image but do not invoke Gateway during those operations. Synthetic DOSBox modem/nullmodem and explicit staged proxy, not SIP/DSP/analog or physical acceptance.',
  remaining=['Unverified device faults, other complete owner combinations and sustained real BBS/physical flow timing.','Transfers interrupted by real carrier loss, uploads and wider protocol/layout/profile combinations on this parent.','Microsoft DOS6.22 and physical Boca/SPA2102/SynthModem acceptance; physical deployment unchanged.','Remaining original file/DOS, directory/key, Chat, ASPECT/emulation/protocol/Host parity.'])
 out.mkdir(parents=True);(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS five Gateway sink cases, two normal-parent reconnect profiles and stock Enigma cancel/retry audit')
if __name__=='__main__':main()
