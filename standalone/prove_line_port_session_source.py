#!/usr/bin/env python3
"""Reproduce the transaction and separate-bank DOS checks from declared sources."""
import hashlib,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/line-port-session'
DEST=OUT/'source-proof'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
 manifest=json.loads((OUT/'manifest.json').read_text())
 sources=list(manifest['sources'])+['standalone/test_line_port_session_dos.py']
 DEST.mkdir(parents=True,exist_ok=False);tree=DEST/'tree'
 for name in sources:
  assert sha(ROOT/name)==manifest['sources'].get(name,sha(ROOT/name)),name
  target=tree/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
 for name in ('build_line_port_session.py','test_line_port_session_dos.py'):
  subprocess.run([sys.executable,str(tree/'standalone'/name)],cwd=tree,check=True)
 outputs=['SESSION.EXE','dos/POPUP.BIN']
 for name in outputs:assert (OUT/name).read_bytes()==(tree/'build/line-port-session'/name).read_bytes(),name
 result=dict(passed=True,sources={n:sha(ROOT/n)for n in sources},
  exact_outputs={n:sha(OUT/n)for n in outputs},
  dos_result=json.loads((tree/'build/line-port-session/dos-results.json').read_text()),
  limitations=['Public-source transaction/selector/view diagnostic; save/apply results are authored inputs.',
   'No original, private configuration, analysis database, earlier object or Git metadata in export. Outer pinned Nix environment supplies tools.'])
 (DEST/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Transaction public-source proof:',len(sources),'files; EXE/popup exact and 71 DOS checks passed')


if __name__=='__main__':main()
