#!/usr/bin/env python3
"""Bind the complete compiler-bridge candidate to source, archive and DOS checks."""
import argparse,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('package','proof','contract','archive','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--dos-check',type=Path,action='append',required=True)
 a=p.parse_args();receipts={}
 def read(path):
  path=path.resolve();assert path.is_relative_to(ROOT/'build')
  r=json.loads(path.read_text());receipts[str(path.relative_to(ROOT))]=sha(path);return r
 m=read(a.package/'manifest.json');proof=read(a.proof/'result.json');contract=read(a.contract/'result.json');archive=read(a.archive/'result.json')
 assert m['parent_render_capability']==23 and m['experimental_compiler_lease_bridge'] and not m['card_written'] and not m['original_inputs']
 for n,h in m['files'].items():assert sha(a.package/m['dos_directory']/n)==h,n
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 assert proof['passed'] and proof['ancestor_git_unavailable'] and not proof['original_inputs']
 assert proof['connection_package']['files']==archive['files']==m['files'] and len(m['files'])==17
 assert proof['connection_package']['archive_sha256']==archive['archive_sha256']==sha(a.archive/archive['archive'])
 assert contract['passed'] and len(contract['cases'])==34 and all(c['accepted']==(c['case'] in ('matched-pair','module-valid','archive-valid')) for c in contract['cases'])
 assert archive['passed'] and not archive['card_written'] and not archive['selector_changed']
 assert archive['package_manifest_sha256']==contract['package_manifest_sha256']==sha(a.package/'manifest.json')
 # Check the exported sources against the declared public commit, rather than
 # treating the presence of local source files as proof of committed provenance.
 revision=m['source_base_commit'];tracked=set(subprocess.check_output(['git','ls-tree','-r','--name-only',revision],cwd=ROOT,text=True).splitlines())
 assert set(proof['sources'])<=tracked
 assert subprocess.run(['git','diff','--quiet',revision,'--',*sorted(proof['sources'])],cwd=ROOT).returncode==0
 for n,h in proof['sources'].items():assert sha(ROOT/n)==h,n
 dos=[]
 for folder in a.dos_check:
  r=read(folder/'result.json');assert r['passed'] and r['cpu']=='8086'
  assert r['package_manifest_sha256']==sha(a.package/'manifest.json') and r['package_files']==m['files']
  for n,h in r['sources'].items():assert sha(ROOT/n)==h,n
  for n,h in r['artifacts'].items():assert sha(folder/n)==h,n
  dos.append({k:r[k] for k in ('launcher','cpu','port','irq','resident_observer','precompiled_before_terminal','native_line_port','meta_editor','keymap_editor','keymap_profiles','keymap_help','packaged_ASPECT_clock_alarm_exercised','packaged_ASPECT_EMULATE_exercised','checks')})
 assert len(dos)==7 and any(d['launcher']=='SETUP' for d in dos)
 assert any(d['keymap_help'] and d['keymap_profiles']==7 for d in dos)
 assert any(d['meta_editor'] for d in dos) and any(d['native_line_port'] for d in dos)
 assert any(d['precompiled_before_terminal'] and d['packaged_ASPECT_clock_alarm_exercised'] and d['packaged_ASPECT_EMULATE_exercised'] for d in dos)
 assert any(not d['resident_observer'] and not d['precompiled_before_terminal'] and 'nested DOS source compilation produces exact ASX' in d['checks'] for d in dos)
 bbs_path=ROOT/'docs/validation/aspect-compiler-connection.json';bbs=json.loads(bbs_path.read_text());assert bbs['checkpoint_verified']
 for n,h in bbs['products'].items():assert m['files'][n]==h,n
 receipts[str(bbs_path.relative_to(ROOT))]=sha(bbs_path)
 r=dict(checkpoint_verified=True,source_base_commit=revision,files=m['files'],source_count=proof['source_count'],
        source_original_inputs=[],source_ancestor_git_unavailable=True,package_contract_cases=34,
        cold_package_contract_cases=proof['connection_package']['contract_cases'],cold_DOS_cases=proof['DOS_cases'],cold_termination_cases=proof['termination_cases'],
        archive_sha256=archive['archive_sha256'],archive_bytes=archive['archive_bytes'],DOS_checks=dos,
        same_application_as_BBS_checkpoint=True,application_bytes_changed=False,installed_changed=False,selector_changed=False,physical_verified=False,
        receipts=receipts,sources={'standalone/record_compiler_bridge_package.py':sha(__file__)},
        remaining=['Controlled deployment preserving current private configuration and call history.','Physical memory admission, modem/SIP/audio and Enigma/Synchronet acceptance.','Full ASPECT/other emulations/protocols/Host parity.'])
 a.output.write_text(json.dumps(r,indent=2)+'\n');print('Verified17-file compiler-bridge candidate, exact source/archive and seven packaged DOS cases')


if __name__=='__main__':main()
