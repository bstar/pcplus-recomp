#!/usr/bin/env python3
"""Bind Chat viewer geometry protection, height coverage and compatibility gates."""
import argparse,json
from pathlib import Path
from build_path_session import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--terminal',type=Path,required=True);p.add_argument('--cold',type=Path,required=True)
 a=p.parse_args();binary=a.terminal.resolve();m=json.loads(binary.with_name('manifest.json').read_text());mod=m['chat_loader']['module']
 assert sha(binary)==m['binary_sha256'] and mod['api_version']==0x106 and mod['state_bytes']==480
 assert mod['image_bytes']==11396 and mod['window_bytes']==12288 and mod['relocations']==4
 assert mod['DGROUP_bytes']==mod['own_stack_bytes']==mod['minimum_extra_paragraphs']==0
 assert sha(binary.parent/'PCCHAT.OVL')==mod['binary_sha256']
 layout=m['memory_layout'];assert layout['near_bytes']==65504 and layout['resident_CS_extent_bytes']==65386 and layout['minimum_allocated_module_bytes']==479392
 paths=dict(matrix='build/chat-view-geometry-matrix-final-20261106/result.json',ASPECT='build/chat-view-geometry-aspect-20261106/result.json',TEXT='build/chat-view-geometry-ten-20261106/result.json',echo='build/chat-view-geometry-echo-20261106/result.json',pressure='build/chat-view-geometry-pressure-20261106/result.json',flow='build/chat-view-geometry-flow-20261106/result.json',Synchronet='build/bbs-lab/results/synchronet/chat-view-geometry-sync-20261106/proxy-integration.json',Enigma='build/bbs-lab/results/enigma/chat-view-geometry-carrier-20261106/carrier-checks.json',Enigma_audit='build/chat-view-geometry-carrier-audit-20261106/result.json',control='build/chat-view-geometry-control-pointer-20261106/result.json')
 reports={n:json.loads((ROOT/path).read_text()) for n,path in paths.items()};sources=dict(m['sources'])
 def source_check(report):
  for n,h in report.get('sources',{}).items():
   assert sha(ROOT/n)==h,n
   assert n not in sources or sources[n]==h,n
   sources[n]=h
 for name,r in reports.items():
  assert r['passed'],name;source_check(r)
  if name not in ('Enigma','Enigma_audit','control'):assert r['binary_sha256']==sha(binary),name
 assert reports['Enigma']['products']['TERMINAL.EXE']['sha256']==sha(binary) and reports['Enigma_audit']['terminal_sha256']==sha(binary)
 assert reports['Enigma_audit']['exact_retry_bytes']==65539
 matrix=reports['matrix'];expected={f'quarantine-r{r}-f{f}' for r in (25,28,43,50) for f in (0,1,2)}|{f'main-r{r}' for r in (25,28,43,50)}
 assert {c['name'] for c in matrix['cases']}==expected and len(matrix['cases'])==16
 cases=[]
 for case in matrix['cases']:
  path=ROOT/case['receipt'];r=json.loads(path.read_text());assert case['passed'] and r['passed'] and sha(path)==case['receipt_sha256']
  assert r['binary_sha256']==sha(binary) and r['module_sha256']==mod['binary_sha256'];source_check(r)
  if case['name'].startswith('main'):
   assert r['checks']['actual_BIOS_rows'] and r['observer_words'][5]==r['rows'] and all(r['checks'].values())
   detail=dict(checks=len(r['checks']),BIOS_rows=r['observer_words'][5])
  else:
   assert f"rows={r['rows']} fault={r['fault']}" in r['output'] and 'errors=0' in r['output']
   assert r['checks']>4000 and not r['timed_out'];detail=dict(assertions=r['checks'],rows=r['rows'],fault=r['fault'])
  cases.append(dict(name=case['name'],receipt=case['receipt'],sha256=sha(path),**detail))
 assert len(reports['ASPECT']['checks'])==26 and reports['ASPECT']['interpreter_sha256']=='cbdee1949f0ac6bba34f56ae9c594a17888ef9b5143ee5dca9cd76498737ccfd'
 assert len(reports['TEXT']['checks'])==11 and len(reports['echo']['cases'])==9
 assert reports['pressure']['pressure_keys']==40 and len(reports['pressure']['cases'])==4
 assert reports['pressure']['observer_constants']['CHAT_API_VERSION']==0x106 and reports['pressure']['observer_constants']['CHAT_STEP_OPERATION']==14
 assert reports['flow']['pressure_keys']==40 and reports['flow']['observer_words'][5]==32
 assert len(reports['Synchronet']['checks'])==25 and len(reports['Enigma']['checks'])==16
 cold=json.loads((a.cold/'result.json').read_text());assert cold['passed'] and cold['original_inputs']==[]
 assert cold['binary_sha256']==sha(binary) and cold['module_sha256']==mod['binary_sha256'] and cold['lease_checks']==75085
 assert cold['main_rows']==cold['geometry_rows']==50 and cold['geometry_fault']==2 and all(cold['main_checks'].values())
 for name in ('lease','main','geometry'):
  path=a.cold/'public-source/build'/name/'result.json';r=json.loads(path.read_text());assert r['passed'] and sha(path)==cold['receipts'][name];source_check(r)
 for n,h in m['sources'].items():assert cold['sources'][n]==h and sha(a.cold/'public-source'/n)==h,n
 for n in ('standalone/test_chat_redisplay_cold.py','standalone/test_chat_redisplay_geometry_dos.py','standalone/chat_redisplay_geometry_host.c','standalone/build_chat_redisplay_profile.py','standalone/chat_redisplay_profile.json'):
  assert cold['sources'][n]==sha(ROOT/n)==sha(a.cold/'public-source'/n),n;sources[n]=sha(ROOT/n)
 control=ROOT/'build/chat-view-geometry-control-20261106/TERMINAL.EXE';cm=json.loads(control.with_name('manifest.json').read_text());assert sha(control)==reports['control']['binary_sha256']==cm['binary_sha256']=='432fc6944fda1683f8f18deaf1c4915cdd3b06224cbfe7b2120bff9fade01696'
 assert cm['chat_loader']['module']['binary_sha256']=='83b77da00ded8f2e6df652d5058ae313dc673ef15d3865304aa755f590bc3eff'
 source_check(cm)
 negatives=[]
 for path,reason in [('build/chat-view-geometry-negative2-20261106/result.json','API0105 height-change guard failure: key/RX admission, arena retention and text-frame protection.'),('build/chat-view-geometry-matrix-20261106/result.json','API0106 initial graphics fixture compared disabled B800 aperture; corrected to guard all64000 visible A000 bytes.')]:
  r=json.loads((ROOT/path).read_text());assert not r['passed'];negatives.append(dict(path=path,sha256=sha(ROOT/path),binary_sha256=r['binary_sha256'],reason=reason))
 sources['standalone/record_chat_view_geometry.py']=sha(Path(__file__))
 result=dict(passed=True,software_profile_validated=True,physical_deployed=False,whole_original_parity=False,binary_sha256=sha(binary),module_sha256=mod['binary_sha256'],ASPECT_sha256=reports['ASPECT']['interpreter_sha256'],api=0x106,request_bytes=50,state_bytes=480,descriptor_bytes=54,lease_bytes=12,lease_range=[14600,14612],module_image_bytes=11396,code_window_bytes=12288,relocations=4,module_DGROUP_bytes=0,module_stack_bytes=0,parent_bytes=479392,prior_Chat_parent_bytes=479408,near_bytes=65504,resident_CS_bytes=65386,
  checks=dict(geometry_recovery_cases=12,normal_main_heights=[25,28,43,50],graphics_frame_bytes_guarded_per_case=64000,cold_lease_assertions=75085,cold_main_rows=50,cold_geometry_rows=50,cold_geometry_fault=2,cold_source_files=cold['source_files'],ASPECT=26,TEXT=11,echo_groups=9,pressure_cases=4,pressure_keys=40,flow=len(reports['flow']['checks']),Synchronet=25,Enigma=16,Enigma_retry_bytes=65539,control_pointer=True),
  geometry_cases=cases,sources=sources,receipts={n:dict(path=path,sha256=sha(ROOT/path)) for n,path in paths.items()},cold_receipt_sha256=sha(a.cold/'result.json'),retained_negatives=negatives,
  limitations=['Fault matrix supplies coherent initial canonical layout and invokes real parent/module/BIOS entries. Independent normal-main cases use actual imported display preferences and BIOS state at each height.',
   'External BIOS changes are injected at a viewer-visible foreground boundary. Asynchronous changes during a frame copy or pending-RX screen update are not proved.',
   'DOS free-failure injection, export cancellation during carrier loss, logging/printer faults, sustained saturation and physical flow/carrier acceptance remain open.',
   'BBS regressions keep Chat inactive; no physical Boca/SPA2102/SynthModem audio test, private configuration/call-history change, selected package update or full original feature parity claim.'])
 (ROOT/'docs/validation/chat-view-geometry.json').write_text(json.dumps(result,indent=2)+'\n');print('Recorded API0106:12 BIOS recovery cases,4 normal-main heights, exact cold rebuild and regression suite; physical deployment unchanged.')
if __name__=='__main__':main()
