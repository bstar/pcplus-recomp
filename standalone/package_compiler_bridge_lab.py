#!/usr/bin/env python3
"""Stage matched compiler-bridge artifacts and source-built Help for BBS labs.

No selector, DOS installation or archive is updated. This is a lab payload,
not a complete connection release or a statement of physical acceptance.
"""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
from build_context_help import ROOT,sha


def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('parent','child','compiler','output'):p.add_argument('--'+name,required=True,type=Path)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 sources={};inputs={};manifests=[]
 for folder,leaf in ((a.parent,'TERMINAL.EXE'),(a.child,'ASPECT.EXE'),(a.compiler,'ASPCOMP.EXE')):
  folder=folder.resolve();assert folder.is_relative_to(ROOT/'build')
  m=json.loads((folder/'manifest.json').read_text());assert not m.get('original_inputs') and sha(folder/leaf)==m['binary_sha256']
  for name,digest in m['sources'].items():
   rel=Path(name);assert not rel.is_absolute() and '..' not in rel.parts and rel.parts[0] not in ('build','analysis','original','originals','install')
   assert sha(ROOT/rel)==digest and (name not in sources or sources[name]==digest),name
   sources[name]=digest
  inputs[str((folder/'manifest.json').relative_to(ROOT))]=sha(folder/'manifest.json');manifests.append(m)
 parent,child,compiler=manifests
 assert parent['experimental_compiler_lease_bridge'] and parent['experimental_global_help'] and parent['experimental_chat_loader']
 assert child['experimental_compiler_parent_lease'] and compiler['experimental_get_compiler']
 leaves={'TERMINAL.EXE':a.parent/'TERMINAL.EXE','terminal.map':a.parent/'terminal.map','manifest.json':a.parent/'manifest.json',
  'PCCHAT.OVL':a.parent/'PCCHAT.OVL','PCLINE.OVL':a.parent/'PCLINE.OVL','PCMETA.OVL':a.parent/'PCMETA.OVL',
  'ASPECT.json':a.child/'manifest.json',
  'PCCOMP.OVL':a.parent/'PCCOMP.OVL','ASPECT.EXE':a.child/'ASPECT.EXE','ASPCOMP.EXE':a.compiler/'ASPCOMP.EXE'}
 for key,leaf in (('line_port_overlay','PCLINE.OVL'),('meta_editor_overlay','PCMETA.OVL'),('experimental_compiler_lease_module','PCCOMP.OVL')):
  assert sha(leaves[leaf])==parent[key]['sha256'],leaf
 aspect_resource=None
 if child.get('experimental_help_resource'):
  resource_path=a.child/'help-resource.json'
  aspect_resource=json.loads(resource_path.read_text())
  assert aspect_resource['original_inputs']==[] and sha(a.child/'LOCHELP.HLP')==aspect_resource['sha256']
  for name,digest in aspect_resource['sources'].items():
   assert sha(ROOT/name)==digest and (name not in sources or sources[name]==digest),name
   sources[name]=digest
  leaves['LOCHELP.HLP']=a.child/'LOCHELP.HLP'
  leaves['LOCHLP.JSON']=resource_path
 out.mkdir()
 for leaf,path in leaves.items():shutil.copyfile(path,out/leaf);assert sha(out/leaf)==sha(path)
 subprocess.run([sys.executable,str(ROOT/'standalone/build_help_program.py'),'--output',str(out/'help-build')],check=True)
 shutil.copyfile(out/'help-build/PCHELP.RTE',out/'PCHELP.RTE')
 subprocess.run([sys.executable,str(ROOT/'standalone/build_context_help_resource.py'),'--output',str(out/'PCPLUS.HLP')],check=True)
 for path in (out/'help-build/manifest.json',out/'PCPLUS.json'):
  for name,digest in json.loads(path.read_text())['sources'].items():
   assert sha(ROOT/name)==digest and (name not in sources or sources[name]==digest),name
   sources[name]=digest
 sources['standalone/package_compiler_bridge_lab.py']=sha(Path(__file__))
 report=dict(schema=2,passed=True,original_inputs=[],sources=sources,inputs=inputs,
  products={leaf:sha(out/leaf) for leaf in leaves if leaf not in ('terminal.map','manifest.json','ASPECT.json','LOCHLP.JSON')},
  aspect_manifest_sha256=sha(out/'ASPECT.json'),aspect_help_resource_manifest_sha256=sha(out/'LOCHLP.JSON') if aspect_resource else None,
  parent_manifest_sha256=sha(out/'manifest.json'),helper_manifest_sha256=sha(out/'help-build/manifest.json'),
  resource_manifest_sha256=sha(out/'PCPLUS.json'),installed_changed=False,selector_changed=False,
  release_eligible=False,physical_verified=False,scope=__doc__)
 for leaf in ('PCHELP.RTE','PCPLUS.HLP'):report['products'][leaf]=sha(out/leaf)
 (out/'package.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Staged lab payload:',out,'files',len(report['products']))


if __name__=='__main__':main()
