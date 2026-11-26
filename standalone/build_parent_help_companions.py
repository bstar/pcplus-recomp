#!/usr/bin/env python3
"""Add the native global-Help companions to an already built --global-help parent.

build_global_help_profile.py composes its own fixed parent flag set. A package
candidate built directly with build_terminal.py (for example the qualified
flags plus BBS opt-ins) gets PCHELP.RTE, PCPLUS.HLP and the same package.json
record here, without rebuilding or changing TERMINAL.EXE.
"""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
from build_context_help import ROOT,sha
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parent',type=Path,required=True,help='build/<dir> holding TERMINAL.EXE and manifest.json');a=p.parse_args()
 out=a.parent.resolve();assert out.is_relative_to(ROOT/'build')
 parent=json.loads((out/'manifest.json').read_text());assert parent['binary_sha256']==sha(out/'TERMINAL.EXE')
 assert parent.get('experimental_global_help'),'Parent was not built with --global-help'
 assert not (out/'package.json').exists() and not (out/'help-build').exists()
 for n,h in parent['sources'].items():assert sha(ROOT/n)==h,n
 subprocess.run([sys.executable,str(ROOT/'standalone/build_help_program.py'),'--output',str(out/'help-build')],check=True)
 shutil.copyfile(out/'help-build/PCHELP.RTE',out/'PCHELP.RTE')
 subprocess.run([sys.executable,str(ROOT/'standalone/build_context_help_resource.py'),'--output',str(out/'PCPLUS.HLP')],check=True)
 helper=json.loads((out/'help-build/manifest.json').read_text());resource=json.loads((out/'PCPLUS.json').read_text())
 sources={**parent['sources'],**helper['sources'],**resource['sources'],'standalone/build_parent_help_companions.py':sha(Path(__file__).resolve())}
 names=['TERMINAL.EXE','PCCHAT.OVL','PCHELP.RTE','PCPLUS.HLP']+[n for n in ('PCLINE.OVL','PCMETA.OVL') if (out/n).exists()]
 report=dict(passed=True,mapped_contexts=[3,41] if parent.get('experimental_chat_help') else [41],sources=sources,products={n:sha(out/n) for n in names},
  parent_manifest_sha256=sha(out/'manifest.json'),helper_manifest_sha256=sha(out/'help-build/manifest.json'),resource_manifest_sha256=sha(out/'PCPLUS.json'),
  scope='Source-only global-Help companions added to an existing parent; TERMINAL.EXE unchanged. No physical deployment or whole-parity claim.')
 (out/'package.json').write_text(json.dumps(report,indent=2)+'\n');print('Global Help components',report['products'])
if __name__=='__main__':main()
