#!/usr/bin/env python3
"""Bind real receive/skip/receive handoff and unchanged existing DOS file."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def main():
 base='build/bbs-lab/results/enigma/owned-game-repeat-01'
 path=base+'/repeat-checks.json';data=read(path)
 assert data['passed'] and all(data['checks'].values()) and not data['errors']
 terminal=sha('build/terminal/TERMINAL.EXE');assert data['terminal_sha256']==terminal
 assert data['runner_sha256']==sha('lab/bbs/enigma_repeat_download_dos.py')
 for key,p in [('terminal','build/terminal/TERMINAL.EXE'),('runner','lab/bbs/enigma_repeat_download_dos.py'),('harness','lab/bbs/test_dos.py'),('observer','lab/bbs/test_transfer_dos.py'),('auditor','lab/bbs/audit_zmodem.py')]:assert data['input_hashes'][key]==sha(p),p
 assert data['wire_names']==['PCPLUS PROBE 01 (1991).ZIP','PCPLUS PROBE 02 (1991).ZIP']
 assert data['local_names']==['8868026D.ZIP','FFF6D09D.ZIP']
 assert [t['kind'] for t in data['transactions']]==['received','skipped-existing','received']
 assert all(t['post_menu'] for t in data['transactions'])
 a,b=data['local_names'];snapshots=data['snapshots'];assert len(snapshots)==3
 assert [set(s['files']) for s in snapshots]==[{a},{a},{a,b}]
 assert snapshots[0]['files'][a]==snapshots[1]['files'][a]==snapshots[2]['files'][a]
 assert sha(base+'/RECV/'+a)==snapshots[0]['files'][a]['sha256']
 assert sha(base+'/RECV/'+b)==snapshots[2]['files'][b]['sha256']
 assert all(not (ROOT/base/'RECV'/n).exists() for n in ['PCRX.$$$','PCZRX.$$$'])
 negatives_path=base+'/audit-negative-checks.json';negatives=read(negatives_path)
 assert negatives['passed'] and len(negatives['cases'])==7 and all(c['rejected'] for c in negatives['cases'])
 assert negatives['checker_sha256']==sha('lab/bbs/check_enigma_repeat_audit.py')
 assert negatives['auditor_sha256']==sha('lab/bbs/enigma_repeat_download_dos.py')
 for p,h in negatives['capture_hashes'].items():assert sha(base+'/'+p)==h,p
 previous_path='docs/validation/zmodem-long-names.json';previous=read(previous_path)
 assert previous['passed'] and previous['terminal_sha256']==terminal
 proof_path='docs/validation/application-components-source-build.json';proof=read(proof_path)
 assert proof['passed'] and proof['outputs']['terminal/TERMINAL.EXE']['sha256']==terminal
 assert read('build/dos-package/manifest.json')['files']['TERMINAL.EXE']==terminal
 result=dict(passed=True,terminal_sha256=terminal,DOS=dict(path=path,sha256=sha(path),checks=data['checks'],scope=data['scope']),
  transactions=[dict(kind=t['kind'],wire_name=t['wire_name'],local_name=t['local_name'],post_menu=t['post_menu']) for t in data['transactions']],
  existing_file_identity_preserved=True,files={n:dict(sha256=sha(base+'/RECV/'+n),bytes=(ROOT/base/'RECV'/n).stat().st_size) for n in (a,b)},
  negative_audit=dict(path=negatives_path,sha256=sha(negatives_path),checks=negatives['cases']),source_modules=data['source_modules'],
  filename_validation=dict(path=previous_path,sha256=sha(previous_path)),source_build_proof=dict(path=proof_path,sha256=sha(proof_path),outputs=proof['output_count']),
  recorder_sha256=sha(Path(__file__).relative_to(ROOT)),whole_application_gates_closed=[],live_server_modified=False,
  limitations=['Synthetic generated archives and selected owned source/menu/art on the staged isolated ENiGMA fixture; live board/catalog installation remains pending.',
   'Modem/UART timing is modeled19200/HARD; physical Wi-Fi modem timing/flow control and complete application gates remain open.',
   'Filesystem snapshots are captured after each confirmed sender finish; source captures and per-finish host identity/timestamps remain in ignored build artifacts.'])
 (ROOT/'docs/validation/enigma-repeat-download.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Recorded actual DOS receive/skip/receive, unchanged existing file, three NFO handoffs and seven rejected audit corruptions')
if __name__=='__main__':main()
