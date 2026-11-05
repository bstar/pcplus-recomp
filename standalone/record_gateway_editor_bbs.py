#!/usr/bin/env python3
"""Bind real stock-editor Gateway returns, cell audits and negative controls."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'lab/bbs'))
from product_inputs import select_product,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('terminal','runner','runtime','controls','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--enigma-label',required=True);p.add_argument('--synchronet-label',required=True)
 p.add_argument('--launch-control',type=Path);p.add_argument('--large-observer-failure',type=Path)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 binary,inputs=select_product(a.terminal,'TERMINAL.EXE');runner,runner_inputs=select_product(a.runner,'ASPECT.EXE')
 manifest=json.loads(binary.with_name('manifest.json').read_text());assert manifest['experimental_gateway_frontend']
 runtime=a.runtime.resolve();rows=[]
 def record(path):return dict(path=str(path.relative_to(ROOT)),sha256=sha(path))
 for peer,label in [('enigma',a.enigma_label),('synchronet',a.synchronet_label)]:
  capture=ROOT/'build/bbs-lab/results'/peer/label;bridge=ROOT/'build/bbs-lab'/(label+'-proxy')
  docs={n:json.loads((capture/n).read_text()) for n in ['result.json','proxy-integration.json','gateway-audit.json','screen-reference-audit.json']}
  assert all(d['passed'] for d in docs.values()),peer
  base,producer,gateway,cells=[docs[n] for n in docs]
  assert base['binary_sha256']==producer['binary_sha256']==cells['binary_sha256']==sha(binary)
  assert producer['gateway']==gateway and cells['matched_cells']==1920 and cells['different_cells']==0
  assert cells['actual_CPR']==cells['reference_cursor'] and cells['fixture_CPR_consumed']
  assert base['serial']['com']==3 and base['serial']['irq']==5 and base['serial']['flow']=='HARD' and base['cpu']=='8086'
  assert base['comspec_fixture_sha256']==sha(capture/'GWSHELL.COM')
  assert base['video_observer_sha256']==sha(capture/'OBSERVE.COM')
  assert len((capture/'GWVIEW.BIN').read_bytes())==8024
  for d in [gateway,cells]:
   for name,h in d.get('sources',{}).items():assert sha(ROOT/name)==h,(peer,name)
  for name,h in producer['product_inputs'].items():assert sha(ROOT/name)==h,(peer,name)
  for name,h in cells['captures'].items():assert sha(Path(name))==h,(peer,name)
  ready=json.loads((bridge/'ready.json').read_text());closed=json.loads((bridge/'1-closed.json').read_text())
  assert ready['screenReference'] and ready['terminalSizeProbe'] and ready['terminalRows']==24 and closed['source_unchanged']
  assert ready['inputSequenceTimeoutMs']==250 and ready['inputByteDelayMs']==20
  assert all(sha(runtime/n)==h for n,h in ready['installed_sources'].items())
  evidence=[*[(capture/n) for n in docs],capture/'GWVIEW.BIN',capture/'GWCHILD.BIN',capture/'serial-received.bin',capture/'GWSHELL.COM',capture/'OBSERVE.COM',bridge/'ready.json',bridge/'1-closed.json']
  if peer=='enigma':
   semantic=json.loads((capture/'semantic-audit.json').read_text());assert semantic['passed'] and semantic['checks']['no_post_saved'];evidence.append(capture/'semantic-audit.json')
  else:
   assert producer['interpreter_sha256']==sha(runner) and producer['checks']['message_bodies_unchanged'] and producer['checks']['no_message_mail_or_transfer_writes']
  rows.append(dict(peer=peer,passed=True,checks=gateway['checks'],matched_cells=cells['matched_cells'],CPR=cells['actual_CPR'],delivered_bytes=cells['delivered_bytes'],serial=base['serial'],gateway_observer_words=gateway['observer_words'],evidence=[record(path) for path in evidence],runtime_sources=ready['installed_sources']))
 controls=json.loads(a.controls.read_text());assert controls['passed'] and len(controls['cases'])==9 and sum(c['rejected'] for c in controls['cases'])==8
 for name,h in controls['sources'].items():assert sha(ROOT/name)==h,name
 for name,h in controls['inputs'].items():assert sha(ROOT/controls['capture']/name)==h,name
 observations={}
 if a.launch_control:
  folder=a.launch_control.resolve();assert folder.is_relative_to(ROOT/'build')
  control=json.loads((folder/'proxy-integration.json').read_text());cells=json.loads((folder/'screen-reference-audit.json').read_text())
  assert control['passed'] and cells['passed'] and control['binary_sha256']==sha(binary) and control['interpreter_sha256']==sha(runner)
  observations['same_parent_without_Gateway_observer']={'producer':record(folder/'proxy-integration.json'),'cell_audit':record(folder/'screen-reference-audit.json'),'passed':True}
 if a.large_observer_failure:
  folder=a.large_observer_failure.resolve();assert folder.is_relative_to(ROOT/'build')
  failed=json.loads((folder/'proxy-integration.json').read_text());base=json.loads((folder/'result.json').read_text())
  assert failed['passed'] is False and base['passed'] is True and failed['binary_sha256']==sha(binary) and failed['interpreter_sha256']==sha(runner)
  assert failed['checks']['actual_ASPECT_login'] is False and failed['checks']['actual_Gateway_roundtrip'] is False
  assert not (folder/'GWCHILD.BIN').exists()
  assert len((folder/'GWVIEW.BIN').read_bytes())==16024
  observations['oversized_observer_failure']={'producer':record(folder/'proxy-integration.json'),'base_harness':record(folder/'result.json'),'observer':record(folder/'OBSERVE.COM'),'normal_DOS_exit_was_not_accepted':True,
   'scope':'The16000-byte-buffer observer did not reach scripted login or the Gateway. The8000-byte-buffer variant reached both with the same parent/ASPECT. Consistent with conventional-memory pressure; the exact DOS error was not sampled, so root cause is not claimed proven.'}
 sources=['standalone/record_gateway_editor_bbs.py','standalone/check_gateway_bbs_evidence.py','lab/bbs/gateway_bbs_support.py','standalone/gateway_bbs_child.asm','standalone/gateway_bbs_watch.asm','lab/bbs/audio_synchronet_editor_keys.asm','lab/bbs/test_synthmodem_proxy_dos.py','lab/bbs/test_synchronet_screen_reference_dos.py','lab/bbs/test_dos.py','lab/bbs/editor_dos_probe.py','lab/bbs/audit_screen_reference.py','lab/bbs/product_inputs.py']
 result=dict(passed=True,observations=observations,binary_sha256=sha(binary),terminal=record(binary),manifest=record(binary.with_name('manifest.json')),runner=record(runner),runner_manifest=record(runner.with_name('manifest.json')),cases=rows,controls=record(a.controls.resolve()),sources={n:sha(ROOT/n) for n in sources},original_inputs=[],physical_deployment_changed=False,
  scope='Two actual owned stock BBS editor sessions through the staged real SynthModem Telnet proxy, DOS8086 COM3/IRQ5 HARD. Real Alt-F4/empty-tail graphics child, exact25-row frame/cursor return, post-return editing and1920-cell/CPR reference per peer. Explicit250ms key framing and20ms input pacing; no SIP/DSP/analog, physical flow-control or whole-application acceptance.',
  remaining=['Active capture/HOLD and printer composition.','Sustained output, repeated reconnect and binary transfer/cancel/carrier-loss workflows through this Gateway-enabled image.','Microsoft DOS6.22 and physical Boca/SPA2102/SynthModem acceptance.','Full original command, ASPECT/emulation/protocol/Host parity.'])
 out.mkdir(parents=True);(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS two real Gateway editor returns,3840 matching cells and eight copied negative controls')
if __name__=='__main__':main()
