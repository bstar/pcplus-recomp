#!/usr/bin/env python3
"""Bind the opt-in Chat Redisplay candidate to its exact regression evidence."""
import argparse,json
from pathlib import Path
from build_path_session import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--terminal',type=Path,required=True);p.add_argument('--cold',type=Path,required=True)
 a=p.parse_args();binary=a.terminal.resolve();m=json.loads(binary.with_name('manifest.json').read_text())
 assert sha(binary)==m['binary_sha256'] and m['experimental_chat_redisplay']
 module=m['chat_loader']['module'];assert module['api_version']==0x105 and module['state_bytes']==480 and module['image_bytes']==11140
 assert sha(binary.parent/'PCCHAT.OVL')==module['binary_sha256'] and module['window_bytes']==12288
 assert module['DGROUP_bytes']==module['own_stack_bytes']==module['minimum_extra_paragraphs']==0 and module['relocations']==4
 assert m['memory_layout']['minimum_allocated_module_bytes']==479344 and m['memory_layout']['near_bytes']==65504 and m['memory_layout']['resident_CS_extent_bytes']==65386
 paths={
  'lease':'build/chat-redisplay-funded3-dos-20261106/result.json',
  'normal_main':'build/chat-redisplay-main-final-20261106/result.json',
  'ASPECT':'build/chat-redisplay-aspect-funded3-20261106/result.json',
  'TEXT':'build/chat-redisplay-ten-20261106/result.json',
  'echo_CPU':'build/chat-redisplay-echo-20261106/result.json',
  'pressure':'build/chat-redisplay-pressure-20261106/result.json',
  'flow':'build/chat-redisplay-flow-20261106/result.json',
  'Synchronet':'build/bbs-lab/results/synchronet/chat-redisplay-sync-20261106/proxy-integration.json',
  'Enigma':'build/bbs-lab/results/enigma/chat-redisplay-carrier-20261106/carrier-checks.json',
  'Enigma_audit':'build/chat-redisplay-carrier-audit-20261106/result.json',
  'control_pointer':'build/chat-redisplay-control-pointer-final-20261106/result.json'}
 reports={name:json.loads((ROOT/path).read_text()) for name,path in paths.items()}
 sources=dict(m['sources'])
 for name,r in reports.items():
  assert r['passed'],name
  for n,h in r.get('sources',{}).items():
   assert sha(ROOT/n)==h,(name,n)
   assert n not in sources or sources[n]==h,(name,n)
   sources[n]=h
  if name not in ('Enigma','Enigma_audit','control_pointer'):assert r['binary_sha256']==sha(binary),name
 assert reports['Enigma']['products']['TERMINAL.EXE']['sha256']==sha(binary)
 assert reports['Enigma_audit']['terminal_sha256']==sha(binary) and reports['Enigma_audit']['exact_retry_bytes']==65539
 assert reports['lease']['checks']==75085 and not reports['lease']['timed_out']
 assert len(reports['normal_main']['checks'])==12 and reports['normal_main']['observer_words'][1]==23
 assert len(reports['ASPECT']['checks'])==26 and reports['ASPECT']['interpreter_sha256']=='cbdee1949f0ac6bba34f56ae9c594a17888ef9b5143ee5dca9cd76498737ccfd'
 assert len(reports['TEXT']['checks'])==11 and len(reports['echo_CPU']['cases'])==9
 assert reports['pressure']['pressure_keys']==40 and len(reports['pressure']['cases'])==4
 assert reports['pressure']['observer_constants']['CHAT_API_VERSION']==0x105 and reports['pressure']['observer_constants']['CHAT_STEP_OPERATION']==14
 assert reports['flow']['pressure_keys']==40 and reports['flow']['observer_words'][5]==32
 assert len(reports['Synchronet']['checks'])==25 and len(reports['Enigma']['checks'])==16
 cold=json.loads((a.cold/'result.json').read_text());assert cold['passed'] and cold['original_inputs']==[]
 assert cold['binary_sha256']==sha(binary) and cold['module_sha256']==module['binary_sha256'] and cold['lease_checks']==75085 and all(cold['main_checks'].values())
 for n,h in m['sources'].items():assert cold['sources'][n]==h and sha(a.cold/'public-source'/n)==h,n
 for n in ('standalone/test_chat_redisplay_dos.py','standalone/chat_redisplay_host.c','standalone/test_chat_redisplay_main_dos.py','standalone/chat_redisplay_watch.asm','standalone/test_chat_redisplay_cold.py','standalone/build_chat_redisplay_profile.py','standalone/chat_redisplay_profile.json'):
  assert cold['sources'][n]==sha(ROOT/n)==sha(a.cold/'public-source'/n),n
  sources[n]=sha(ROOT/n)
 control=ROOT/'build/chat-redisplay-disabled-control-20261106/TERMINAL.EXE';cm=json.loads(control.with_name('manifest.json').read_text())
 assert sha(control)==cm['binary_sha256']==reports['control_pointer']['binary_sha256'] and not cm['experimental_chat_redisplay']
 assert cm['chat_loader']['module']['api_version']==0x104 and cm['chat_loader']['module']['binary_sha256']=='83b77da00ded8f2e6df652d5058ae313dc673ef15d3865304aa755f590bc3eff'
 assert cm['memory_layout']['minimum_allocated_module_bytes']==479408
 for n,h in cm['sources'].items():assert sha(ROOT/n)==h,n
 negatives=[]
 for n in ('build/chat-redisplay-aspect-first-20261106/result.json','build/chat-redisplay-binding-debug2-20261106/result.json','build/chat-redisplay-main-20261106/result.json'):
  r=json.loads((ROOT/n).read_text());assert not r['passed']
  negatives.append(dict(path=n,sha256=sha(ROOT/n),binary_sha256=r['binary_sha256'],passed=False))
 sources['standalone/record_chat_redisplay.py']=sha(Path(__file__))
 result=dict(passed=True,source_profile_validated=True,physical_deployed=False,whole_original_parity=False,
  binary_sha256=sha(binary),module_sha256=module['binary_sha256'],ASPECT_sha256=reports['ASPECT']['interpreter_sha256'],
  api=0x105,state_bytes=480,request_bytes=50,code_window_bytes=12288,module_image_bytes=11140,module_DGROUP_bytes=0,module_stack_bytes=0,
  parent_bytes=479344,prior_parent_bytes=479408,parent_savings_bytes=64,near_bytes=65504,resident_CS_bytes=65386,
  temporary_arena_bytes=dict(rows25=67008,rows50=71008),
  frozen_layout=dict(code=[0,12288],state=[12288,12768],presentation=[13000,13016],request=[13200,13250],translation=[14000,14256],native_cursor=[14500,14522],lease=[14600,14610],row_index=[63000,63494]),
  checks=dict(DOS_lease_assertions=75085,lease_sessions=5,full_wrapped_snapshot_bytes=63000,normal_main_checks=12,ASPECT_checks=26,TEXT_checks=11,CPU_echo_groups=9,pressure_cases=4,pressure_keys=40,flow_checks=len(reports['flow']['checks']),Synchronet_checks=25,Enigma_checks=16,Enigma_retry_bytes=65539,cold_source_files=cold['source_files'],control_pointer=True),
  preserved_capacities=['8192-byte parent stack, six ASPECT stream buffers,512-byte ASPECT heap growth.', '63000-byte history/frozen snapshot, existing8000-byte live/view frames,32-key FIFO and247-row index.'],
  sources=sources,receipts={name:dict(path=path,sha256=sha(ROOT/path)) for name,path in paths.items()},cold_receipt_sha256=sha(a.cold/'result.json'),
  disabled_control=dict(binary_sha256=sha(control),module_sha256=cm['chat_loader']['module']['binary_sha256'],api=0x104,parent_bytes=479408),
  retained_negatives=negatives,limitations=[
   'DOS lease fixture invokes real parent/module/viewer/DOS instructions but supplies entry calls and parent state. Normal-main gate separately verifies real keyboard, UART delivery, hidden-frame RX and resume.',
   'Current live Chat/Redisplay matrix is80x25;25/28/43/50-row backing capacities are retained, but this does not establish new live-mode acceptance at every height.',
   'Allocation refusal is exercised. Forged DOS arenas/free failures, geometry changes during nesting, logging/printer faults, sustained saturation and physical DCD/CTS/RTS remain separate acceptance work.',
   'BBS regressions exercise the actual new parent with Chat inactive. No physical Boca/SPA2102/SIP/audio route, deployment or full original feature parity is claimed.',
   'Global Help/Alt-Z and full original D95C viewer recovery are separate; this integrates the existing serviced viewer against the recovered entry/return contract.'])
 (ROOT/'docs/validation/chat-redisplay.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Recorded opt-in Chat Redisplay: exact source/cold identities,11 passing reports, no physical deployment.')

if __name__=='__main__':main()
