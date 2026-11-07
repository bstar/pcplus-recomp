#!/usr/bin/env python3
"""Archive only the verified public application payload; never select or deploy it."""
import argparse,json,zipfile
from pathlib import Path
from package_connection_test import ROOT,sha,validate_dos_directory

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--package',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 package=a.package.resolve();out=a.output.resolve()
 assert package.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
 m=json.loads((package/'manifest.json').read_text());directory=validate_dos_directory(m['dos_directory'])
 assert m['original_inputs']==[] and not m['card_written']
 allowed={'TERMINAL.EXE','ASPECT.EXE','ASPCOMP.EXE','PRMEDIT.EXE','XLTEDIT.EXE','LOCHELP.HLP','START.BAT','SETUP.BAT','README.TXT','VERSION.TXT'}
 if m.get('experimental_chat_loader'):allowed.add('PCCHAT.OVL')
 if m.get('experimental_keymap_editor'):
  allowed.add('PCKEYMAP.EXE')
  profile=json.loads((ROOT/'standalone/keymap_helper_profile.json').read_text())
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
