#!/usr/bin/env python3
"""Build the source-only legacy-ABI PCHELP program with bounded services."""
import argparse,json,subprocess
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 names=['src/help/program.c','src/help/parent.c','src/help/parent_dos.c','src/help/format.c','src/help/document.c']
 sources=names+['src/help/parent.h','src/help/format.h','src/help/document.h','standalone/build_help_program.py','standalone/build_context_help.py']
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-ecc','-k8192','-fe=PCHELP.RTE','-fm=PCHELP.MAP',*[str(ROOT/name) for name in names]],cwd=out,check=True)
 report=dict(passed=True,original_inputs=[],sources={name:sha(ROOT/name) for name in sources},products={'PCHELP.RTE':sha(out/'PCHELP.RTE')},scope='Source-owned legacy PCHELP process consumer and original-derived VGA topic/search UI; validated parent admission and streamed HLP reader. Not linked into the terminal and not a claim of full original helper/runtime parity.')
 (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('Built source-only PCHELP.RTE',report['products']['PCHELP.RTE'])

if __name__=='__main__':main()
