#!/usr/bin/env python3
"""Bind serviced Meta text code, native traces and exact DOS/source checks."""
import argparse,json
from pathlib import Path
from build_meta_text import ROOT,sha


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
 assert sha(build/'METATEXT.EXE')==v['binary_sha256']==cold['binary_sha256']
 assert v['cases']==cold['cases']==554 and v['key_states']==cold['key_states']==8418
 assert v['API_guards']==12 and v['state_bytes']==64 and v['separate_code_segment'] and v['data_equals_stack'] and v['cpu']=='8086'
 assert cold['ancestor_git_unavailable'] and cold['source_count']==6
 fixture=ROOT/'standalone/fixtures/meta_text_native.json';native=json.loads(fixture.read_text());assert native['passed'] and native['format']=='meta-field-traces-v1'
 assert len(native['cases'])==554 and sum(len(c['states']) for c in native['cases'])==8418
 assert {c['states'][0][0] for c in native['cases'] if c['name'].startswith('byte-key-')}==set(range(256))
 for n in ('standalone/record_meta_text.py','standalone/prove_meta_text_source.py','standalone/capture_meta_text_original.py','docs/META_TEXT_MODEL.md'):sources[n]=sha(ROOT/n)
 result=dict(passed=True,component_only=True,terminal_changed=False,installed_changed=False,physical_runtime_verified=False,
  diagnostic_sha256=v['binary_sha256'],cases=554,key_states=8418,API_guards=12,state_bytes=64,isolated_source_files=6,
  native_authority=dict(original_sha256=native['original_sha256'],ranges=native['native_ranges'],REA_pseudocode=native['REA_pseudocode'],scope=native['scope']),sources=sources,receipts=receipts,original_inputs=[],
  limitations=['Frozen traces derive from actual original instructions with synthetic text and modeled peripheral UI services; they are not VGA/BIOS/UART or physical observations.',
   'Serviced memory-only field API, actual source-built DOS8086 with separate CS and DS=SS; no original executable, private data, prior objects or Git metadata in the isolated build.',
   'Alt-M window/navigation, persistence/resource identity, action-table adoption, application capacity, physical acceptance and full shared-editor/F02/F05/F06 parity remain open.'])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS Meta text receipt:554 cases,8418 key states,12 guards,separate CS,6-file source rebuild')


if __name__=='__main__':main()
