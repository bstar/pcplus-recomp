#!/usr/bin/env python3
"""Bind the modem-response fix to its scoped native/component regressions."""
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 binary=ROOT/'build/terminal/TERMINAL.EXE';digest=sha(binary)
 names=['build/terminal/zmodem-upload-response-checks.json',
  'build/terminal/config-far-checks.json','build/terminal/far-code-live-checks.json',
  'build/terminal/ymodem-far-checks.json','build/terminal/terminal-zmodem-live-checks.json',
  'build/terminal/zmodem-cancel-checks.json','build/terminal/zmodem-completed-replay-checks.json',
  'build/terminal/carrier-transfer-deadline-checks.json',
  'build/zmodem-link-policy/checks.json','build/zmodem-completion-bounds/checks.json',
  'build/zmodem-session/checks.json','build/zmodem-window/checks.json',
  'build/zmodem-dos/checks.json','build/terminal-zmodem-dos/upload-response-auto/checks.json']
 checks={n:json.loads((ROOT/n).read_text()) for n in names}
 for name,d in checks.items():
  assert d['passed'],name
  if name.startswith('build/terminal/') or name.startswith('build/terminal-zmodem-dos/'):
   assert d['binary_sha256']==digest,name
 current=checks[names[0]];assert len(current['cases'])==22
 faults=[row for row in current['cases'] if row['interrupt_tick'] is not None]
 assert len(faults)==10 and all(0<=row['interrupt_reaction_ticks']<38 for row in faults)
 assert current['compiler_helpers']['exact_OMF_roundtrip']
 assert current['checker_sha256']==sha(ROOT/'standalone/check_zmodem_upload_timing.py')
 for name,value in current['source_sha256'].items():assert sha(ROOT/name)==value,name
 policy=checks['build/zmodem-link-policy/checks.json'];assert len(policy['cases'])==11
 for name,value in policy['sources'].items():assert sha(ROOT/name)==value,name
 predecessor_name='build/terminal/zmodem-upload-response-counterexample-recheck.json'
 predecessor=json.loads((ROOT/predecessor_name).read_text())
 assert not predecessor['passed'] and predecessor['counterexample_reproduced']
 assert predecessor['checker_sha256']==current['checker_sha256']
 assert predecessor['binary_sha256']==sha(ROOT/'build/terminal/upload-response-baseline/TERMINAL.EXE')
 for name,value in predecessor['source_sha256'].items():assert sha(ROOT/name)==value,name
 peers=checks['build/zmodem-session/checks.json'];assert len(peers['independent_peers'])==24
 assert checks['build/terminal/terminal-zmodem-live-checks.json']['inputs']==78
 assert checks['build/terminal/config-far-checks.json']['configuration_bridge_pairs_verified']==80
 manifest_path=ROOT/'build/terminal/manifest.json';manifest=json.loads(manifest_path.read_text())
 assert manifest['binary_sha256']==digest and manifest['data_stack_bytes']==64832
 for name,value in manifest['sources'].items():assert sha(ROOT/name)==value,name
 sources=['src/transfer/zmodem.c','src/transfer/zmodem.h','src/transfer/terminal_zmodem.c',
  'src/transfer/ymodem.h','src/terminal/ymodem_actions.asm','src/terminal/config_abi.inc',
  'standalone/build_terminal.py','standalone/terminal_memory.py',
  'standalone/check_zmodem.py','standalone/check_zmodem_link_policy.py',
  'standalone/check_zmodem_upload_timing.py','standalone/check_config_far_live.py',
  'standalone/check_far_code_live.py',str(Path(__file__).relative_to(ROOT)),
  'docs/ZMODEM_MODEM_RESPONSE.md','Makefile','nix/flake.nix','nix/flake.lock']
 result={'passed':True,'binary_sha256':digest,'map_sha256':sha(ROOT/'build/terminal/terminal.map'),
  'DS_equals_SS_bytes':64832,'timing_cases':current['cases'],'compiler_helpers':current['compiler_helpers'],
  'predecessor':predecessor,'host_policy_cases':policy['cases'],
  'regressions':{n:{'passed':True,'receipt_sha256':sha(ROOT/n),
   'scope':d.get('scope'),'case_count':len(d['cases']) if isinstance(d.get('cases'),list) else d.get('inputs')} for n,d in checks.items()},
  'independent_peer_count':24,'source_sha256':{n:sha(ROOT/n) for n in sources},
  'artifact_sha256':{n:sha(ROOT/n) for n in [*names,predecessor_name,'build/terminal/manifest.json','build/terminal/zmodem-compiler-helper-adapters.json']},
  'scope':'Native buffered-modem sender response fix with linked hardware/kernel models, strict C89 independent wire peers, retained real DOS component and automatic three-file evidence.22 timing cases include10 completed Escape/carrier-loss runs across metadata/data/EOF, serviced read chunks and midnight, two timeout/noise cases, eight successful response cases and two deliberately stopped unchanged-policy witnesses. Every interruption retains source/file-owner cleanup and a bounded reaction. Same checker reproduces the predecessor failure. Original fixed-policy and audio receipts remain unchanged. No new actual audio fault, physical or F01-F16 acceptance.'}
 (ROOT/'docs/validation/zmodem-upload-response-faults.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'passed':True,'binary_sha256':digest,'timing_cases':22,'interruption_cases':10,'host_policy_cases':11,'independent_peers':24}))


if __name__=='__main__':main()
