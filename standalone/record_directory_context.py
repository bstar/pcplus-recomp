#!/usr/bin/env python3
"""Bind retained startup context, real DOS composition and full regression."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def read(p):return json.loads((ROOT/p).read_text())
def sources(r):
 for p,want in r['sources'].items():assert sha(p)==want,p

def main():
 manifest=read('build/terminal/manifest.json');runtime=sha('build/terminal/TERMINAL.EXE')
 assert manifest['binary_sha256']==runtime;sources(manifest)
 diagnostic=read('build/directory-context/manifest.json');sources(diagnostic)
 assert diagnostic['binary_sha256']==sha('build/directory-context/CONTEXT.EXE')
 cpu=read('build/terminal/directory-context-checks.json');dos=read('build/directory-context/dos-results.json');child=read('build/directory-context/terminal-results.json')
 for report in (cpu,dos):assert report['passed'];sources(report)
 assert cpu['inputs']==507 and cpu['binary_sha256']==runtime and cpu['maximum_CPU_call_stack_bytes']<8192
 assert dos['binary_sha256']==diagnostic['binary_sha256'] and all(dos['checks'].values())
 assert child['passed'] and child['binary_sha256']==runtime and all(child['checks'].values())
 assert len(bytes.fromhex(child['sample_hex']))==508
 candidate=read('build/live-configuration/checks.json');sources(candidate)
 assert candidate['passed'] and candidate['inputs']==389 and candidate['binary_sha256']==sha('build/live-configuration/LIVE.EXE')
 regression=read('build/terminal/setup-profile-regression.json')
 assert regression['passed'] and regression['complete'] and regression['binary_sha256']==runtime
 assert [c['command'] for c in regression['commands']]==subprocess.check_output(['make','-n','test-terminal'],cwd=ROOT,text=True).splitlines()
 assert all(c['exit_code']==0 for c in regression['commands'])
 proof=read('docs/validation/application-components-source-build.json');assert proof['passed']
 for path,digest in [('terminal/TERMINAL.EXE',runtime),('directory-context/CONTEXT.EXE',diagnostic['binary_sha256']),('live-configuration/LIVE.EXE',candidate['binary_sha256'])]:
  assert proof['outputs'][path]['matches_workspace'] and proof['outputs'][path]['sha256']==digest
 paths=['build/terminal/directory-context-checks.json','build/directory-context/dos-results.json','build/directory-context/terminal-results.json','build/directory-context/CTXCHILD.COM','build/connection-dos/directory-context/CONTEXT.BIN','build/terminal/setup-profile-regression.json','build/terminal/setup-profile-regression.log']
 scripts=['standalone/record_directory_context.py','standalone/check_directory_context.py','standalone/build_directory_context.py','standalone/test_directory_context_dos.py','standalone/test_directory_context_terminal.py','standalone/directory_context_child.asm','standalone/directory_context_host.c','standalone/test_connection_dos.py','standalone/directory_test_support.py','standalone/modem_fixtures.py','src/directory/codec.py']
 result=dict(passed=True,binary_sha256=runtime,memory_layout=manifest['memory_layout'],linked_context_checks=cpu,DOS_composition=dos,actual_terminal_child=child,candidate_inputs=candidate['inputs'],terminal_regression=regression,source_rebuild=dict(report='docs/validation/application-components-source-build.json',source_snapshot_sha256=proof['source_snapshot_sha256'],output_count=proof['output_count']),source_sha256={p:sha(p) for p in scripts},retained_artifacts={p:sha(p) for p in paths},scope='Retained startup raw selection and logical request identity, separate accounting baseline, failure atomicity and ninth near-cdecl argument. Real DOS file mutation/accounting and actual terminal PROGRAM-child disjoint16KiB allocation/fill verify full496-byte persistence. ASCII lexical request matching is not canonical file identity or a namespace lock. Live configuration UI, active-generation/canonical ownership, UART/profile commit, complete application and physical modem validation remain open.')
 (ROOT/'docs/validation/directory-context.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Recorded context',cpu['inputs'],'inputs, DOS24 checks, actual parent child, regression',len(regression['commands']),'commands')
if __name__=='__main__':main()
