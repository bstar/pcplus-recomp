#!/usr/bin/env python3
"""Build the composed Chat/Redisplay parent with native global Help companions."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
from build_context_help import ROOT,sha
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--chat-help',action='store_true');a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 flags=json.loads((ROOT/'standalone/chat_redisplay_profile.json').read_text())+['--global-help']
 if a.chat_help:flags+=['--chat-help']
 subprocess.run([sys.executable,str(ROOT/'standalone/build_terminal.py'),'--output-dir',str(out),*flags],check=True)
 subprocess.run([sys.executable,str(ROOT/'standalone/build_help_program.py'),'--output',str(out/'help-build')],check=True)
 shutil.copyfile(out/'help-build/PCHELP.RTE',out/'PCHELP.RTE')
 subprocess.run([sys.executable,str(ROOT/'standalone/build_context_help_resource.py'),'--output',str(out/'PCPLUS.HLP')],check=True)
 parent=json.loads((out/'manifest.json').read_text());helper=json.loads((out/'help-build/manifest.json').read_text());resource=json.loads((out/'PCPLUS.json').read_text())
 sources={**parent['sources'],**helper['sources'],**resource['sources']}
 for name in ['standalone/build_global_help_profile.py','standalone/chat_redisplay_profile.json']:sources[name]=sha(ROOT/name)
 report=dict(passed=True,mapped_contexts=[3,41] if a.chat_help else [41],sources=sources,products={n:sha(out/n) for n in ['TERMINAL.EXE','PCCHAT.OVL','PCHELP.RTE','PCPLUS.HLP']},parent_manifest_sha256=sha(out/'manifest.json'),helper_manifest_sha256=sha(out/'help-build/manifest.json'),resource_manifest_sha256=sha(out/'PCPLUS.json'),scope='Opt-in source-only parent/Chat/global-Help components. The native descriptor runs through the existing PROGRAM owner; mapped_contexts records the selected entry paths. ASPECT companion remains separately versioned. No physical deployment or whole-parity claim.')
 (out/'package.json').write_text(json.dumps(report,indent=2)+'\n');print('Global Help components',report['products'])
if __name__=='__main__':main()
