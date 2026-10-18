#!/usr/bin/env python3
"""Build the offline DOS table editor from source through the Nix toolchain."""
import hashlib
import json
from pathlib import Path
import subprocess
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/xlt-editor'
SOURCES = ['editor_main.c', 'editor_document.c', 'editor_fs.c', 'xlt_dos.c', 'xlt_dos_fs.c']
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sources = [ROOT / 'src/translation' / name for name in SOURCES]
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192',
                    '-i='+str(ROOT/'src/translation'),'-fm=editor.map','-fe=XLTEDIT.EXE',
                    *map(str,sources)],cwd=OUT,check=True)
    inputs = sources + sorted((ROOT/'src/translation').glob('*.h')) + [Path(__file__).resolve()]
    report = dict(binary_sha256=hashlib.sha256((OUT/'XLTEDIT.EXE').read_bytes()).hexdigest(),
                  sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
                  scope='Source-only offline DOS XLT editor. Explicit new-file identity, staged editing, checked replacement and recovery; no live UART/PRM mutation or original executable input.')
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Built XLTEDIT.EXE',report['binary_sha256'])
if __name__=='__main__':main()
