#!/usr/bin/env python3
"""Bind composed paging DOS/fault/source proofs and original character ordering."""
import argparse,json
from pathlib import Path
from build_path_session import ROOT,sha
from test_viewer_session_dos import scenarios

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['program','dos','linked','public-source','original','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 def bind(path):
  path=path.resolve();return dict(path=str(path.relative_to(ROOT)),sha256=sha(path))
 def checked(path):
  r=json.loads(path.read_text());assert r['passed'],path
  for n,h in r.get('sources',{}).items():assert sha(ROOT/n)==h,n
  return r
 binary=a.program.resolve();manifest=json.loads(binary.with_name('manifest.json').read_text());digest=sha(binary)
 assert digest==manifest['binary_sha256'] and manifest['original_inputs']==[]
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 dos=checked(a.dos);linked=checked(a.linked);public=checked(a.public_source);original=checked(a.original)
 assert dos['binary_sha256']==linked['binary_sha256']==public['binary_sha256']==digest
 assert dos['scenarios']==11 and dos['checks']==21727 and dos['max_steps_per_action']==1001
 assert linked['inputs']==26 and linked['bounded_steps']==158 and linked['max_DOS_data_calls_per_step']==1
 assert all(c['passed'] for c in linked['cases']) and public['source_files']==18
 for n,h in dos['artifacts'].items():assert sha(a.dos.parent/n)==h,n
 for n,h in dos['input_hashes'].items():assert sha(a.dos.parent/'d'/n)==h,n
 assert (a.dos.parent/'c/AFTERCD.TXT').read_bytes().strip()==b'C:\\'
 segments=manifest['component_segments']
 for obj in segments.values():assert obj['FILE_CODE']['class']=='FARCODE' and all(not s['bytes'] for n,s in obj.items() if n!='FILE_CODE')
 cases=scenarios();comparisons=[]
 for maintained,native in [('binary-original','binary'),('exact-EOF','exact-page'),('empty','empty'),('long-read-ahead','long')]:
  case=next(c for c in cases if c['name']==maintained)
  chars=case['actions'][0]['characters'] if native!='long' else b''.join(c['characters'] for c in case['actions'][:4]).ljust(1920,b' ')
  frame=next(c for c in original['cases'] if c['case']==native)['captures'][2];path=ROOT/frame['path'];assert sha(path)==frame['sha256']
  assert path.read_bytes()[:3840:2]==chars
  comparisons.append(dict(case=maintained,matched_character_bytes=1920,capture=frame,scope='Content only; long fixture concatenates four2-row controller pages in order.'))
 ready=sum(a0['phase']==2 for c in cases for a0 in c['actions']);actions=sum(len(c['actions']) for c in cases)
 r=dict(passed=True,binary_sha256=digest,session_bytes=596,owner_bytes=90,persistent_DGROUP_bytes=0,
  DOS=dict(scenarios=11,checks=21727,actions=actions,ready_page_checks=ready,matched_character_bytes=sum(len(a0.get('characters',b'')) for c in cases for a0 in c['actions']),max_steps_per_action=1001,report=bind(a.dos)),
  linked=dict(inputs=26,bounded_steps=158,max_DOS_data_calls_per_step=1,report=bind(a.linked)),public_source=bind(a.public_source),
  original_comparisons=comparisons,manifest=bind(binary.with_name('manifest.json')),original_inputs=[],
  compiler_recovery=dict(rejected_runtime=bind(ROOT/'build/viewer-session-observe-dos-20261105/c/RESULT.TXT'),
   rejected_object=bind(ROOT/'build/viewer-session-observe-20261105/session.obj'),
   rejected_disassembly=bind(ROOT/'build/viewer-session-observe-20261105/session.dis'),
   accepted_disassembly=bind(ROOT/'build/viewer-session-volatile-20261105/session.dis'),
   observation='Nonvolatile banked object stores old current into target before incrementing current; actualDOS stops with page1/target0. Volatile state orders current increment before target reload/store; unchanged paging expectations pass.'),
  sources={**dos['sources'],**linked['sources'],'standalone/record_viewer_session.py':sha(Path(__file__))},
  scope='Composed controller/decoder/read-only owner, not terminal UI. ActualDOS8086 exact paging/read-ahead/cache/rescan/cancel/error checks, linked modeled-DOS budget/cleanup cases, four original content comparisons and byte-identical18-file original-free rebuild. No UART/UI/hardware acceptance.',
  remaining=['Serviced viewer UI/frame/footer/cursor and Alt-V dispatch.',
    'Child/exit admission for uncertain viewer ownership and foreground shared-buffer admission.',
    'Capture/HOLD/PRN, live Enigma/Synchronet editor, carrier-loss/reconnect/transfer composition.',
    'Configured external viewer, DOS6.22/SHARE/media faults, physical Boca/SIP acceptance and full remaining parity inventory.'])
 out.mkdir(parents=True);(out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS composed paging proofs,',actions,'actions,',ready,'exact page checks')
if __name__=='__main__':main()
