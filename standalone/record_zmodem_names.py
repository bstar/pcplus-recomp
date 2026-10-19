#!/usr/bin/env python3
"""Bind long wire-name support to codecs, DOS storage and actual BBS downloads."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def sources(data):
 for p,h in data['sources'].items():assert sha(p)==h,p
def main():
 terminal=sha('build/terminal/TERMINAL.EXE');reports={}
 for key,path,count in [('names','build/zmodem-names/checks.json',446),('engine','build/zmodem-session/checks.json',92),('window','build/zmodem-window/checks.json',79),('DOS','build/zmodem-dos/checks.json',68)]:
  data=read(path);assert data['passed'];sources(data)
  actual=data.get('DOS_cases',len(data['cases']) if isinstance(data['cases'],list) else data['cases'])
  assert actual==count,(key,actual)
  reports[key]=dict(path=path,sha256=sha(path),cases=count,scope=data['scope'])
 names=read(reports['names']['path']);assert names['checker_sha256']==sha('standalone/check_zmodem_names.py')
 assert names['collision']['alias']=='4F09E7D3.ZIP'
 dos=read(reports['DOS']['path']);assert dos['isolated_source_build_byte_identical']
 assert all(c['passed'] for c in dos['cases'])
 assert {c['result']['workspace'] for c in dos['cases']}=={9554}
 path='build/bbs-lab/results/enigma/owned-game-transfer-long-01-wrapper/characterization.json';game=read(path)
 assert game['transfer_passed'] and game['harness_exit']==0 and game['inputs_unchanged'] and game['no_post_saved']
 assert game['terminal_sha256']==terminal and game['runner_sha256']==sha('lab/bbs/enigma_game_transfer_dos.py')
 assert game['expected_local_name']=='8868026D.ZIP' and game['received_files']==['8868026D.ZIP']
 assert all(game['protocol_checks'].values()) and not game['protocol_errors']
 offered=game['archive'];assert offered['name']=='PCPLUS PROBE 01 (1991).ZIP'
 local='build/bbs-lab/results/enigma/owned-game-transfer-long-01/RECV/8868026D.ZIP'
 assert sha(local)==offered['sha256'] and (ROOT/local).stat().st_size==offered['bytes']==1301
 protocol_path='build/bbs-lab/results/enigma/owned-game-transfer-long-01/result.json';protocol=read(protocol_path)
 assert protocol['passed'] and protocol['standard_completion'] and protocol['binary_sha256']==terminal and all(protocol['checks'].values())
 proof_path='docs/validation/application-components-source-build.json';proof=read(proof_path)
 assert proof['passed'] and proof['output_count']==178 and all(o['matches_workspace'] for o in proof['outputs'].values())
 assert proof['outputs']['terminal/TERMINAL.EXE']['sha256']==terminal
 manifest=read('build/terminal/manifest.json');assert manifest['data_stack_bytes']==64800
 assert all(s['bytes']<=65536 for s in manifest['memory_layout']['code_segments'])
 assert read('build/dos-package/manifest.json')['files']['TERMINAL.EXE']==terminal
 regression_path='docs/validation/aspect-key-output.json';regressions=read(regression_path)
 assert regressions['passed'] and regressions['terminal_sha256']==terminal and all(all(b['checks'].values()) for b in regressions['BBS'])
 result=dict(passed=True,terminal_sha256=terminal,wire_name_limit=255,local_name_policy='Preserve safe DOS83; otherwise ASCII-case-folded CRC32 as eight hex digits plus safe short extension or DAT',
  collision_policy='Exact active wire identity; existing local targets explicitly ZSKIP with no overwrite',collision_example=names['collision'],
  reports=reports,game_download=dict(path=path,sha256=sha(path),checks=game['protocol_checks'],wire_name=offered['name'],local_name=game['expected_local_name'],bytes=1301,payload_sha256=sha(local),protocol_sha256=sha(protocol_path)),
  regressions=dict(path=regression_path,sha256=sha(regression_path)),source_proof=dict(path=proof_path,sha256=sha(proof_path),outputs=proof['output_count']),
  data_stack_bytes=manifest['data_stack_bytes'],code_segments=manifest['memory_layout']['code_segments'],
  sources={p:sha(p) for p in ['src/transfer/zmodem.c','src/transfer/zmodem.h','src/transfer/zmodem_name.c','src/transfer/zmodem_name.h','src/transfer/batch_header.c','src/transfer/batch_header.h','src/transfer/terminal_zmodem.c']},
  reference_checkers={p:sha(p) for p in ['standalone/check_batch_header.py','standalone/check_zmodem.py','standalone/check_zmodem_wire.py','standalone/check_zmodem_names.py']},
  recorder_sha256=sha(Path(__file__).relative_to(ROOT)),original_inputs=[],whole_application_gates_closed=[],live_server_modified=False,
  retained_failure=dict(path='build/zmodem-session/long-name-regression.log',reason='Initial adapter padded a short-name missing metadata terminator; existing regression rejected it. Final codec requires both terminators within the actual frame.'),
  limitations=['A different remote name with the same local alias is explicitly skipped if that target exists; receiving to another directory preserves both.',
   'Full filename UI/catalog mapping remains unfinished; wire names are bounded opaque bytes with ASCII-only case folding.',
   'Actual BBS download uses an isolated staged ENiGMA decoder; live install/catalog and physical RS-232 Wi-Fi modem validation remain open.',
   'No complete PCPlus or universal BBS compatibility claim.'])
 (ROOT/'docs/validation/zmodem-long-names.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Recorded long-name game ZIP download,446 name checks,68 DOS cases and178 source-only outputs; no application gate closed')
if __name__=='__main__':main()
