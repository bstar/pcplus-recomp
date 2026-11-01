#!/usr/bin/env python3
"""Check linked adoption adapters, persistent storage and actual refusal guards."""
import argparse,hashlib,json,struct
from pathlib import Path
from check_directory_identity import Identity
from terminal_memory import inspect_terminal_memory
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args();binary=a.terminal.resolve();m=json.loads((binary.parent/'manifest.json').read_text());assert m['experimental_directory_adopt'] and sha(binary)==m['binary_sha256']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 machine=Identity(binary);header=struct.unpack_from('<14H',binary.read_bytes());start=header[4]*16;entries={n:(seg-machine.base_segment,off) for n,(seg,off) in machine.entries.items()};address=lambda n:entries[n][0]*16+entries[n][1]
 wrappers={'directory_adopt_setup':'live_setup_select','directory_adopt_xlt_check':'xlt_live_resource_check','directory_adopt_xlt_publish':'xlt_live_resource_adopt','directory_adopt_script_read':'directory_script_read'}
 def verify(path):
  data=Path(path).read_bytes();memory=inspect_terminal_memory(path,binary.parent/'terminal.map')
  hook=next(c for c in memory['code_segments'] if c['name']=='HOOK_CODE');config=next(c for c in memory['code_segments'] if c['name']=='CONFIG_CODE')
  for service,target in wrappers.items():
   q=address('_'+service);body=data[start+q:start+q+22]
   assert body[:15]==bytes.fromhex('55 89 e5 ff 76 0c ff 76 0a ff 76 08 ff 76 06'),service
   assert body[15]==0xe8 and body[18:]==bytes.fromhex('89 ec 5d cb'),service
   assert entries['_'+service][0]==entries['_'+target][0]==config['relative_segment'] and (entries['_'+service][1]+18+struct.unpack_from('<h',body,16)[0])&65535==entries['_'+target][1],service
  at=address('directory_adopt_script_storage');assert data[start+at:start+at+80]==bytes(80)
  assert entries['directory_adopt_script_storage'][0]==entries['_terminal_directory_adopt'][0]==hook['relative_segment']
  assert hook['relative_segment']*16<=at<at+80<=hook['relative_segment']*16+hook['bytes']
  assert at+80<=memory['process_loan_critical_paragraphs']*16
  assert 8724+1086==9810 and 9810<=memory['redisplay_snapshot_bytes']
  assert memory['history_bytes']==memory['redisplay_snapshot_bytes']==63000
  return memory
 memory=verify(binary);cases=[];controls=[]
 for service in wrappers:
  at=start+address('_'+service)+5;data=bytearray(binary.read_bytes());data[at]^=2;path=out/(service+'.analysis.exe');path.write_bytes(data)
  try:verify(path)
  except AssertionError:controls.append(dict(case=service+'-wrong-caller-word',rejected=True,sha256=sha(path)))
  else:raise AssertionError(service)
 data=bytearray(binary.read_bytes());data[start+address('directory_adopt_script_storage')]=1;path=out/'dirty-script-owner.analysis.exe';path.write_bytes(data)
 try:verify(path)
 except AssertionError:controls.append(dict(case='dirty-initial-script-owner',rejected=True,sha256=sha(path)))
 else:raise AssertionError('dirty metadata accepted')
 for held in [0,1,2,65535]:
  x=Identity(binary);at=x.symbols['directory_adopt_script_storage'];x.uc.mem_write(at+2,struct.pack('<H',held))
  assert x.bank('_directory_adopt_exec_allowed',far=True)==(held==0)
  assert x.bank('_directory_resources_exec_allowed',far=True)==(held==0) and not x.calls
  cases.append(dict(case='script-claim-EXEC-guard-'+str(held),passed=True))
 for bound,path,held,want in [(0,b'',0,0),(1,b'',0,1),(1,b'C:\\GO.ASX',0,2),(1,b'C:\\GO.ASX',1,1)]:
  x=Identity(binary);before=b'Z'*64;x.uc.mem_write(x.symbols['_command_menu_script'],before)
  x.uc.mem_write(x.symbols['directory_adopt_script_storage'],struct.pack('<HH',bound,held)+path.ljust(64,b'\0')+bytes(12))
  assert x.bank('_directory_adopt_script_name',far=True)==want
  assert bytes(x.uc.mem_read(x.symbols['_command_menu_script'],64))==(path.ljust(64,b'\0') if want==2 else before) and not x.calls
  cases.append(dict(case='canonical-name-'+str(bound)+'-'+str(held)+'-'+str(bool(path)),passed=True))
 defaults={'_terminal_directory_adopt_requested':1,'terminal_program_active':1,'terminal_program_pending':0,'terminal_program_kind':8,'terminal_program_status':2,'connection_state':0,'terminal_parser_active':0,'terminal_tx_count':0,'uart_rx_count':0,'uart_rx_dropped':0,'terminal_transfer_pending':0,'terminal_transfer_active':0,'terminal_controller_active':0,'terminal_monitor_active':0,'process_busy':0,'terminal_macro_active':0,'terminal_directory_context_valid':0}
 for field,value in [('_terminal_directory_adopt_requested',0),('_terminal_directory_adopt_requested',2),('terminal_program_active',0),('terminal_program_kind',6),('terminal_program_status',4),('connection_state',6),('uart_rx_count',1),('uart_rx_dropped',1),('terminal_transfer_active',1),('terminal_macro_active',1),('process_busy',1),('terminal_directory_context_valid',2)]:
  x=Identity(binary)
  for n,v in defaults.items():x.put(n,v)
  x.put(field,value);assert x.bank('_terminal_directory_adopt',(0,0,0,0),far=True)==1 and not x.calls
  cases.append(dict(case='refuse-'+field+'-'+str(value),passed=True))
 result=dict(passed=True,binary_sha256=sha(binary),cases=cases,inputs=len(cases),damaged_controls=controls,memory=memory,original_inputs=[],sources={n:sha(ROOT/n) for n in ['standalone/check_directory_adopt.py','standalone/check_directory_identity.py','standalone/dos_image.py','standalone/terminal_memory.py']},scope=__doc__+' Actual linked guards and four-word adapters execute or are inspected; only canonicalization would be modeled, and these cases perform none. Five damaged executables are inspected only. This is not a successful adoption, complete stack high-water, UART/connection or file-transfer proof; native application tests are separate.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(cases),'linked adoption guard cases;',len(controls),'damaged controls')
if __name__=='__main__':main()
