#!/usr/bin/env python3
"""Archive only the verified public application payload; never select or deploy it."""
import argparse,json,zipfile
from pathlib import Path
from package_connection_test import ROOT,sha,validate_dos_directory,reviewed_keymap_profile,compiler_module_contract,render_capability,validate_render_pair

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--package',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 package=a.package.resolve();out=a.output.resolve()
 assert package.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
 m=json.loads((package/'manifest.json').read_text());directory=validate_dos_directory(m['dos_directory'])
 assert m['original_inputs']==[] and not m['card_written']
 allowed={'TERMINAL.EXE','ASPECT.EXE','ASPCOMP.EXE','PRMEDIT.EXE','XLTEDIT.EXE','LOCHELP.HLP','START.BAT','SETUP.BAT','README.TXT','VERSION.TXT'}
 bridge=bool(m.get('experimental_compiler_lease_bridge'))
 assert bridge==(m.get('parent_render_capability')==23)==bool(m.get('compiler_lease_module')),'Compiler capability/module declarations must match'
 if bridge:
  allowed.add('PCCOMP.OVL')
  identity=m['products']['TERMINAL.EXE'];base=(ROOT/'build'/identity['folder']).resolve()
  assert base.is_relative_to(ROOT/'build') and sha(base/'manifest.json')==identity['manifest_sha256']
  parent=json.loads((base/'manifest.json').read_text())
  assert sha(base/'TERMINAL.EXE')==parent['binary_sha256']==m['files']['TERMINAL.EXE']==identity['binary_sha256']
  assert compiler_module_contract(base/'TERMINAL.EXE',parent)==m['compiler_lease_module']
  assert m['files']['PCCOMP.OVL']==m['compiler_lease_module']['sha256']
  assert m.get('experimental_GET_VM')
  manifests={}
  for leaf,item in m['products'].items():
   folder=(ROOT/'build'/item['folder']).resolve();assert folder.is_relative_to(ROOT/'build')
   proof=folder/('result.json' if leaf=='PCKEYMAP.EXE' else 'manifest.json')
   assert sha(proof)==item['manifest_sha256']
   manifest=json.loads(proof.read_text());assert not manifest.get('original_inputs') and not manifest.get('diagnostic_build')
   assert sha(folder/leaf)==manifest['binary_sha256']==item['binary_sha256']==m['files'][leaf]
   manifests[leaf]=manifest
  assert render_capability(base/'TERMINAL.EXE')==m['parent_render_capability']
  validate_render_pair(m['parent_render_capability'],parent,manifests['ASPECT.EXE'])
  assert manifests['ASPCOMP.EXE'].get('experimental_get_compiler')
 if m.get('experimental_chat_loader'):allowed.add('PCCHAT.OVL')
 if m.get('experimental_keymap_editor'):
  allowed.add('PCKEYMAP.EXE')
  profile=reviewed_keymap_profile()
  if profile['contract']==4:assert m.get('experimental_global_help') and 'PCPLUS.HLP' in m['files']
  assert m['files']['PCKEYMAP.EXE']==m['products']['PCKEYMAP.EXE']['binary_sha256']==profile['helper_sha256']
  assert m['products']['PCKEYMAP.EXE']['contract']==profile['contract']
 if m.get('experimental_global_help'):allowed.update(('PCHELP.RTE','PCPLUS.HLP'))
 if m.get('experimental_line_port_overlay'):allowed.add('PCLINE.OVL')
 assert not m.get('experimental_meta_editor') or m.get('experimental_meta_editor_module'),'Meta frontend requires its module'
 if m.get('experimental_meta_shared_runtime'):
  assert m.get('experimental_meta_editor') and m.get('experimental_meta_editor_module') and m.get('experimental_line_port_overlay'),'Incomplete shared runtime package'
 if m.get('experimental_meta_editor_module'):allowed.add('PCMETA.OVL')
 assert set(m['files'])==allowed,'Only declared public application files may be archived'
 for n,h in m['files'].items():assert sha(package/directory/n)==h,n
 out.mkdir(parents=True)
 archive=out/'PCPLUSSE.ZIP'
 with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9,allowZip64=False) as z:
  for n in sorted(allowed):
   entry=zipfile.ZipInfo(directory+'/'+n,(1980,1,1,0,0,0));entry.create_system=0;entry.external_attr=0x20;entry.compress_type=zipfile.ZIP_DEFLATED
   z.writestr(entry,(package/directory/n).read_bytes(),compresslevel=9)
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None and set(z.namelist())=={directory+'/'+n for n in allowed}
  import hashlib
  for n,h in m['files'].items():assert hashlib.sha256(z.read(directory+'/'+n)).hexdigest()==h,n
 result=dict(passed=True,source_base_commit=m['source_base_commit'],package_manifest_sha256=sha(package/'manifest.json'),files=m['files'],archive=archive.name,archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,original_inputs=[],sources={str(Path(__file__).resolve().relative_to(ROOT)):sha(Path(__file__))},card_written=False,selector_changed=False,scope=__doc__+' Fixed timestamps, sorted ASCII DOS paths and ordinary Deflate without ZIP64; every extracted byte is checked against the staged identity. Excludes private PRM/DIR/FON/KEY/KBD/XLT, lab artifacts and originals. DOS unzip-program compatibility and physical runtime acceptance remain separate.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(archive.relative_to(ROOT),result['archive_sha256'])
if __name__=='__main__':main()
