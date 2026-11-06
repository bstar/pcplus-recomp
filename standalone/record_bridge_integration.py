#!/usr/bin/env python3
"""Bind the exported SynthModem integration to unit/session and actual DOS evidence."""
import argparse,json,re,subprocess
from pathlib import Path
from build_path_session import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['synthmodem','replay','probe','fixed','unit-log','session-log','baseline-log','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 def bind(path):return dict(path=str(path.resolve().relative_to(ROOT)),sha256=sha(path))
 replay=json.loads(a.replay.read_text());assert replay['passed']
 patch=ROOT/'lab/bbs/patches/synthmodem-menu-size/integration.patch';assert sha(patch)==replay['patch_sha256']
 current=subprocess.check_output(['git','rev-parse','HEAD'],cwd=a.synthmodem,text=True).strip();assert current==replay['source_commit']
 changed=set(subprocess.check_output(['git','diff','--name-only','f0e8d5f',current],cwd=a.synthmodem,text=True).splitlines())
 assert changed==set(replay['files']),'Integration commits must contain only seven scoped targets'
 for n,h in replay['files'].items():assert sha(a.synthmodem/n)==h,n
 units=a.unit_log.read_text();baseline=a.baseline_log.read_text();sessions=a.session_log.read_text()
 assert re.search(r'(?m)^ℹ pass 25$',units) and re.search(r'(?m)^ℹ fail 0$',units)
 assert re.search(r'(?m)^ℹ pass 6$',baseline) and re.search(r'(?m)^ℹ fail 1$',baseline)
 assert '7 passed, 0 failed' in sessions
 rows=[]
 for name,folder,want in [('probe',a.probe,True),('fixed',a.fixed,False)]:
  r=json.loads((folder/'proxy-integration.json').read_text());audit=json.loads((folder/'screen-reference-audit.json').read_text());base=json.loads((folder/'result.json').read_text())
  assert r['passed'] and audit['passed'] and base['passed'] and all(r['checks'].values())
  assert r['binary_sha256']==audit['binary_sha256']==base['binary_sha256']=='2d626fb001bed53d3fb3c3a49ea1859f17e69b6ade07792c3a160043ff0a6c02'
  assert r['bridge']['terminalSizeProbe'] is want and audit['different_cells']==0 and audit['matched_cells']==1920
  assert r['external_viewer']['passed'] and all(r['external_viewer']['checks'].values())
  if not want:
   adapter=json.loads((folder/'fixed-geometry-adapter.json').read_text());assert adapter['passed']
   for n,h in adapter['sources'].items():assert sha(ROOT/n)==h,n
  rows.append(dict(mode=name,size_probe=want,report=bind(folder/'proxy-integration.json'),audit=bind(folder/'screen-reference-audit.json'),matched_cells=1920,different_cells=0,delivered_bytes=audit['delivered_bytes']))
 result=dict(passed=True,synthmodem_local_commit=current,public_patch=bind(patch),patch_replay=bind(a.replay),integrated_files=replay['files'],unit_tests=25,session_tests=7,heartbeat_baseline=dict(passed=6,failed=1,log=bind(a.baseline_log)),unit_log=bind(a.unit_log),session_log=bind(a.session_log),DOS_Enigma=rows,
  live_service_restarted=False,production_probe_enabled=False,physical_deployment_changed=False,
  sources={n:sha(ROOT/n) for n in ['standalone/record_bridge_integration.py','standalone/build_path_session.py']},
  limits=['The exported GPL patch applies with zero fuzz to public f0e8d5f sources; unrelated VM/backend/performance/config changes remain outside these commits.','Session tests run against the existing worktree and stub SIP/backend objects; they do not establish readiness of its pending VM/backend work or real SIP/audio.','Both actual DOS8086 editor paths use the integrated on-disk proxy in isolated loopback processes. The existing running service was not restarted and its active module identity is unverified.','Probe absent/zero retains fixed geometry; opt-in requires a terminal that supports CSI18t replies. Do not enable globally for unsupported clients.','Heartbeat timing tests establish byte/deadline behavior, not physical UART resynchronization.','Physical Boca/SPA2102/SIP/audio/DSP/CTS acceptance and full original PCPlus parity remain open.'])
 out.mkdir();(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS scoped bridge patch,25 Telnet tests,7 session tests and two exact DOS/Enigma paths')
if __name__=='__main__':main()
