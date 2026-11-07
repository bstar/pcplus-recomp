#!/usr/bin/env python3
"""Record exact native Meta Keys components and their finite DOS/source gates."""
import argparse,json
from pathlib import Path
from build_meta_editor import ROOT,sha


def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('build','proof','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();sources={};receipts={}
 def load(path):
  path=path.resolve();assert path.is_relative_to(ROOT/'build');v=json.loads(path.read_text());assert v['passed'] and v['original_inputs']==[]
  receipts[str(path.relative_to(ROOT))]=sha(path)
  for n,h in v['sources'].items():assert sha(ROOT/n)==h;sources[n]=h
  return v
 build=a.build.resolve();v=load(build/'result.json');cold=load(a.proof.resolve()/'result.json')
 assert sha(build/'METAEDIT.EXE')==v['binary_sha256']==cold['binary_sha256']
 assert v['field_keys']==cold['field_keys']==65536 and v['row_scenarios']==cold['row_scenarios']==320
 assert v['defaults_cases']==cold['defaults_cases']==3 and v['cpu']=='8086' and cold['ancestor_git_unavailable'] and cold['source_count']==8
 provenance=ROOT/'reconstruction/meta_editor/provenance.json';native=json.loads(provenance.read_text())
 assert sum(r['bytes'] for r in native['ranges'])==v['exact_bytes']==347
 for r in native['ranges']:assert sha(build/(r['name']+'.bin'))==r['sha256']
 for n in ('standalone/record_meta_editor.py','standalone/prove_meta_editor_source.py','reconstruction/meta_editor/recover.py','docs/META_EDITOR_RECOVERY.md'):sources[n]=sha(ROOT/n)
 result=dict(passed=True,component_only=True,terminal_changed=False,installed_changed=False,physical_runtime_verified=False,
  diagnostic_sha256=v['binary_sha256'],exact_bytes=347,field_keys=65536,row_scenarios=320,defaults_cases=3,isolated_source_files=8,
  native_ranges=native['ranges'],sources=sources,receipts=receipts,original_inputs=[],
  limitations=['Static native analysis image was never executed; native code ranges independently match original file bytes. Ordinary component builds use public source only.',
   'Actual DOS8086 replay uses authored key/cursor/render/text services. Canceled text-service writes demonstrate aliasing, not the original shared-editor cancellation policy.',
   'No full Alt-M UI, checked KEY persistence, live action-table adoption, UART service, physical acceptance or whole F02/F05/F06 parity claim.'])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS native Meta Keys receipt:347 bytes,65536 keys,320 row scenarios,8-file source reproduction')


if __name__=='__main__':main()
