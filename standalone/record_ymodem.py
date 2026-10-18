#!/usr/bin/env python3
"""Publish selected synthetic YMODEM evidence and hashes, never raw media.

Historical failures remain explicit, including an expected peer ACK defect.
Each entry retains its own tested binary identity; only current checkpoints
may be counted as validation of the workspace executable.
"""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
VALIDATION=ROOT/'docs/validation'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def label(value):
 assert value.replace('-','').replace('_','').isalnum(),value
 return value
def artifacts(folder):
 return {str(p.relative_to(ROOT)):digest(p) for p in sorted(folder.rglob('*'))
  if p.is_file() and p.name!='.lock'}
def write(name,result):
 (VALIDATION/name).write_text(json.dumps(result,indent=2)+'\n')
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--dos-run',action='append',required=True)
 p.add_argument('--bbs-run',action='append',required=True)
 a=p.parse_args();binary=digest(ROOT/'build/terminal/TERMINAL.EXE')
 dos=[]
 for value in a.dos_run:
  folder=ROOT/'build/terminal-ymodem-dos'/label(value)
  result=read(folder/'checks.json')
  dos.append(dict(label=value,result=result,retained_artifacts=artifacts(folder)))
 current=[r for r in dos if r['result']['binary_sha256']==binary]
 assert current and all(r['result']['passed'] for r in current),'Current DOS checkpoint failed'
 report=dict(binary_sha256=binary,runs=dos,
  current_runtime_case_count=sum(len(r['result']['cases']) for r in current),
  current_runtime_all_cases_passed=True,
  all_recorded_runs_passed=all(r['result']['passed'] for r in dos),
  scope='Actual isolated DOS/UI/BIOS/UART/files against independent CRC YMODEM peers; historical runtime identities remain explicit. No physical modem claim.')
 write('terminal-ymodem-dos.json',report)
 bbs=[]
 for value in a.bbs_run:
  server,run=value.split(':',1);assert server in ('synchronet','enigma')
  folder=ROOT/'build/bbs-lab/results'/server/label(run)
  result=read(folder/'result.json');entry=dict(server=server,label=run,result=result)
  for name,key in [('protocol.json','protocol'),('server-audit.stdout','server_metadata'),('server-session-audit.json','server_session')]:
   path=folder/name
   if path.exists():entry[key]=read(path)
  entry['retained_artifacts']=artifacts(folder);bbs.append(entry)
 current_bbs=[r for r in bbs if r['result']['binary_sha256']==binary]
 latest={}
 for entry in bbs:
  latest[entry['server']+':'+entry['result']['mode']]=entry
 latest_summary={key:dict(label=entry['label'],passed=entry['result']['passed'],
  binary_sha256=entry['result']['binary_sha256'],
  standard_final_ACK=entry['result'].get('standard_final_ACK'))
  for key,entry in latest.items()}
 write('bbs-ymodem.json',dict(binary_sha256=binary,runs=bbs,
  current_runtime_run_count=len(current_bbs),
  current_runtime_all_selected_cases_passed=bool(current_bbs) and all(r['result']['passed'] for r in current_bbs),
  all_recorded_runs_passed=all(r['result']['passed'] for r in bbs),
  latest_selected_workflows=latest_summary,
  latest_four_current_workflows_passed=len(latest)==4 and all(
   r['passed'] and r['binary_sha256']==binary for r in latest_summary.values()),
  enigma_ymodem_setup=read(ROOT/'build/bbs-lab/enigma/ymodem/setup.json'),
  scope=['Actual owned local Synchronet/ENiGMA helper peers, DOS files and post-transfer menus through the observed Hayes/Telnet bridge.',
   'Each result records its own runtime hash. Historical failures remain distinct from retries.',
   'An explicitly expected missing-final-ACK case may pass compatibility checks while standard_final_ACK is false. It never counts as ACK-confirmed protocol success.',
   'No physical Wi-Fi modem timing/wiring, public BBS account, editor fix or complete PCPlus application claim.']))
 for source,target in [('build/batch-download/result.json','batch-download.json'),
  ('build/batch-upload/checks.json','batch-upload.json'),
  ('build/terminal/terminal-ymodem-live-checks.json','terminal-ymodem-live.json'),
  ('build/terminal/terminal-transfer-live-checks.json','terminal-transfer-live.json'),
  ('build/terminal/terminal-upload-live-checks.json','terminal-upload-live.json')]:
  result=read(ROOT/source)
  assert result['passed'],source
  if 'binary_sha256' in result and source.startswith('build/terminal/'):
   assert result['binary_sha256']==binary,source
  write(target,result)
 print(json.dumps(dict(binary_sha256=binary,DOS_current_cases=report['current_runtime_case_count'],BBS_current_runs=len(current_bbs))))
if __name__=='__main__':main()
