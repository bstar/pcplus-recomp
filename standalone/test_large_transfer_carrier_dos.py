#!/usr/bin/env python3
"""Actual DOS binary-transfer carrier loss and same-parent modem redial.
Selected-height parents, owned binary peers, passive storage/log/BIOS observers.
The virtual modem supplies DCD/results from real socket closure; no product
state, UART result, protocol callback or terminal reply is injected.
"""
import argparse,asyncio,inspect,json,re,types
from pathlib import Path
import test_phone_log_carrier_terminal as carrier
import batch_carrier_peer as batch
from test_large_transfers_dos import watcher,inspect_rows
ROOT=carrier.ROOT;sha=carrier.sha
def recipes():
 rows=[(n,dict(upload=n.startswith('upload'),partial=n.endswith('partial'))) for n in ['receive-negotiation','receive-partial','upload-unacked','upload-partial']]
 rows += [(f'{p}-{k}',dict(protocol=i,upload='upload' in k,partial=k.endswith(('partial','retained')),retained=k.endswith('retained'))) for p,i in [('ymodem',1),('zmodem',2)] for k in ['receive-metadata','receive-partial','receive-retained','upload-metadata','upload-partial']]
 rows += [(f'{p}-fragment-{policy}',dict(protocol=i,upload=True,partial=False,retained=False,fragment=True,strict=policy=='strict')) for p,i in [('ymodem',1),('zmodem',2)] for policy in ['legacy','strict']]
 return rows
def adapter(rows):
 b=types.ModuleType('large_binary_batch_peer');b.__dict__.update(batch.__dict__)
 source=inspect.getsource(batch.run);old='received=bytes(65+i%26 for i in range(9216))';assert source.count(old)==1;source=source.replace(old,'received=bytes(range(256))*36')
 exec(compile(source,batch.__file__,'exec'),b.__dict__)
 source=inspect.getsource(carrier.run_case)
 replacements={
  "out.mkdir(parents=True);binary=parent/'TERMINAL.EXE'":"out.mkdir(parents=True);binary=parent/'TERMINAL.EXE'\n    watcher(out,dict(protocol=transfer.get('protocol',0)),binary,SELECTED_ROWS)",
  'upload_body=bytes(65+i%26 for i in range(4096))':'upload_body=bytes(range(256))*16',
  'received_body=bytes(65+i%26 for i in range(11264))':'received_body=bytes(range(256))*44',
  'from batch_carrier_peer import run as batch_peer':'batch_peer=selected_batch_peer',
  'sampler=SAMPLER':"sampler=SAMPLER.replace('mov cx,4000','mov cx,8000')",
  'cycles=fixed 6000':'cycles=fixed 12000',
  'D:\\\\PLWATCH T\nADDKEY':'D:\\\\PLWATCH T\nD:\\\\TRWATCH T\nADDKEY',
  'D:\\\\SNAP S\nD:\\\\PLWATCH':'D:\\\\SNAP S\nD:\\\\TRWATCH\nD:\\\\PLWATCH',
  '32 if aspect else 28 if transfer else 23':'60',
  "banner=b'\\x1b[2J\\x1b[HFIRST BYTE SAFE\\x1b[6n\\x1b[0c'":"banner=b'\\x1b[2J\\x1b[HFIRST BYTE SAFE\\x1b[6n\\x1b[0c'+LOWER_BANNER",
  "while b'\\x1b[1;16R' not in item['received'] or b'\\x1b[?1;2c' not in item['received']:":"while b'\\x1b[1;16R' not in item['received'] or b'\\x1b[?1;2c' not in item['received'] or LOWER_REPLY not in item['received']:",
  "data=await reader.read(4096)\n                    if not data:raise ConnectionError('Lost before terminal replies')":"data=await reader.read(1)\n                    if not data:raise ConnectionError('Lost before terminal replies')",
 }
 for old,new in replacements.items():assert source.count(old)==1,(old,source.count(old));source=source.replace(old,new)
 m=types.ModuleType('large_transfer_modem');m.__dict__.update(carrier.__dict__)
 m.SELECTED_ROWS=rows;m.watcher=watcher;m.selected_batch_peer=b.run
 m.LOWER_BANNER=b'\x1b'+f'[{rows-1};1HLOWER-{rows}'.encode()+b'\x1b[6n\x1b[H'
 m.LOWER_REPLY=b'\x1b'+f'[{rows-1};9R'.encode()
 exec(compile(source,carrier.__file__,'exec'),m.__dict__);return m
async def run_case(m,parent,out,name,mode,rows):
 result=await m.run_case(parent,out,name,0,0,None,dict(mode))
 assert result['passed'],[n for n,v in result['checks'].items() if not v]
 leases=inspect_rows(out,dict(name=name,protocol=mode.get('protocol',0)),rows)
 log=(out/'dosbox.log').read_text();commands=re.findall(r'Command sent to modem: ->(.*?)<-',log)
 target=(out/'TEST.DIR').read_bytes()[275:296].split(b'\0',1)[0].decode()
 # The existing separator can terminate the retired SEND.BIN metadata suffix
 # in the legacy ZFILE-fragment case. Its ERROR must precede the new init.
 # All actual initialization commands still require their own clean OK.
 nonempty=[c for c in commands if c]
 expected=['AT&K3','ATD'+target]*2
 retired=mode.get('protocol')==2 and mode.get('fragment') and 'IN' in nonempty
 if retired:expected.insert(2,'IN')
 init=list(re.finditer(re.escape('Command sent to modem: ->AT&K3<-'),log));errors=list(re.finditer('Modem response: ERROR',log));carrier_at=log.find('Modem response: NO CARRIER')
 clean_init=len(init)==2 and all('Modem response: OK' in log[x.end():log.find('Command sent to modem: ->ATD',x.end())] and 'Modem response: ERROR' not in log[x.end():log.find('Command sent to modem: ->ATD',x.end())] for x in init)
 scoped_errors=(len(errors)==1 and carrier_at<errors[0].start()<init[1].start()) if retired and len(init)==2 else not errors
 checks=dict(result['checks'],exact_initialization_and_redial=nonempty in (expected,expected+['ATH']),initializations_acknowledged_OK=clean_init,errors_scoped_to_retired_metadata=scoped_errors,
  first_lower_CPR=m.LOWER_REPLY in (out/'connection-1.bin').read_bytes(),second_lower_CPR=m.LOWER_REPLY in (out/'connection-2.bin').read_bytes(),
  binary_source=(out/'SEND.BIN').read_bytes()==bytes(range(256))*16 if mode['upload'] else True,
  exact_UI_restore=len(leases)==1,full_physical_capture=len((out/'SCREEN.BIN').read_bytes())==8000)
 result.update(passed=all(checks.values()),checks=checks,physical_rows=rows,terminal_sha256=sha(parent/'TERMINAL.EXE'),modem_commands=commands,leases=leases,
  artifacts={str(p.relative_to(ROOT)):sha(p) for p in out.rglob('*') if p.is_file() and p.name!='checks.json'})
 (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(name,'FINAL PASS' if result['passed'] else 'FINAL FAIL '+str([n for n,v in checks.items() if not v]),flush=True);assert result['passed'];return result
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--rows',type=int,choices=[25,28,43,50],required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--case',action='append');p.add_argument('--jobs',type=int,choices=[1,2],default=1);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 parent=(a.build/str(a.rows)).resolve();manifest=json.loads((parent/'manifest.json').read_text());assert manifest['diagnostic_session_rows_probe']==a.rows and sha(parent/'TERMINAL.EXE')==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 selected=[(n,r) for n,r in recipes() if not a.case or n in a.case];assert selected and (not a.case or set(a.case)=={n for n,r in selected})
 m=adapter(a.rows)
 async def all_cases():
  semaphore=asyncio.Semaphore(a.jobs)
  async def bounded(n,r):
   async with semaphore:return await run_case(m,parent,out/n,n,r,a.rows)
  return await asyncio.gather(*(bounded(n,r) for n,r in selected))
 cases=asyncio.run(all_cases())
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 sources=['standalone/test_large_transfer_carrier_dos.py','standalone/test_phone_log_carrier_terminal.py','standalone/batch_carrier_peer.py','standalone/check_zmodem_wire.py','standalone/test_large_transfers_dos.py','standalone/transfer_rows_observer.asm','standalone/phone_log_events_watch.asm','standalone/phone_log_slow_write.asm','lab/bbs/phone_log_evidence.py','standalone/test_phone_log_events_terminal.py','standalone/directory_fixtures.py','standalone/directory_test_support.py','standalone/test_terminal.py']
 report=dict(passed=True,cases=cases,physical_rows=a.rows,terminal_path=str((parent/'TERMINAL.EXE').relative_to(ROOT)),terminal_sha256=sha(parent/'TERMINAL.EXE'),manifest_sha256=sha(parent/'manifest.json'),sources={n:sha(ROOT/n) for n in sources},scope=__doc__+' Payloads use all256 byte values; earlier completed retained files use the original fixed fixture. Actual socket closure supplies virtual DCD. Physical/SIP/BBS acceptance remains separate.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
