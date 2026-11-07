#!/usr/bin/env python3
"""Bind checked KEY persistence, isolated replay and default reader control."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('build','proof','control','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();sources={};receipts={}
 def load(path):
  path=path.resolve();assert path.is_relative_to(ROOT/'build');v=json.loads(path.read_text());assert v['passed'];receipts[str(path.relative_to(ROOT))]=sha(path)
  for n,h in v.get('sources',{}).items():assert sha(ROOT/n)==h;sources[n]=h
  return v
 build=a.build.resolve();core=load(build/'result.json');cold=load(a.proof.resolve()/'result.json');control=load(a.control.resolve()/'result.json');reader=load(ROOT/'build/key-actions-dos/checks.json')
 assert core['original_inputs']==cold['original_inputs']==[] and core['cpu']=='8086' and 'PASS 5899 checks;' in core['transcript']
 assert sha(build/'KEYFILE.EXE')==core['binary_sha256']==cold['binary_sha256'] and core['transcript']==cold['transcript']
 assert cold['source_count']==16 and cold['ancestor_git_unavailable']
 assert reader['real_DOS_checks']==11 and reader['declared_fault_checks']==22 and reader['binary_sha256']['KAREAL.EXE']==control['disabled_reader_binary_sha256']
 for n in ('standalone/record_key_editor_file.py','standalone/prove_key_editor_file_source.py','docs/KEY_EDITOR_FILES.md'):sources[n]=sha(ROOT/n)
 result=dict(passed=True,component_only=True,installed_changed=False,terminal_changed=False,physical_runtime_verified=False,binary_sha256=core['binary_sha256'],checks=5899,save_boundary_modes=18,rejected_load_cases=8,isolated_source_files=16,reader_real_checks=11,reader_fault_checks=22,default_reader_exact_control=control['disabled_reader_binary_sha256'],baseline_commit=control['baseline_commit'],original_inputs=[],sources=sources,receipts=receipts,
 limitations=['Maintained checked IO, not recovered original file-picker behavior; no original-binary input or native behavior comparison in these tests.', 'Injected wrappers perform real DOS IO in owned fixtures; close uncertainty requires owner quarantine/recovery. Optimistic comparison is not an external lock or power-loss guarantee; attributes/timestamps are not preserved.', 'No live Meta dialog linkage, filename selection, resource/EXEC ownership, live action adoption, application memory/capacity admission, BBS regression or physical acceptance. Installed RCE81708 unchanged.'])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS KEY persistence receipt:5899 checks,16-file rebuild,33 reader checks,exact default control')
if __name__=='__main__':main()
