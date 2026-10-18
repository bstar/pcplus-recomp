#!/usr/bin/env python3
"""Build the source-owned CWD-changing settings diagnostic child."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'build/live-translation-child'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = ROOT/'standalone/live_translation_child.c'
    subprocess.run(['wcl', '-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we', '-k8192',
                    '-fe=CHDIR.EXE', str(source)], cwd=OUT, check=True)
    result = dict(binary_sha256=hashlib.sha256((OUT/'CHDIR.EXE').read_bytes()).hexdigest(),
                  sources={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in [source, Path(__file__).resolve()]},
                  scope='Synthetic DOS diagnostic child: edit only PRM mode1e0, close checked file, change shared CWD. Not the user editor or original PCSETUP.')
    (OUT/'manifest.json').write_text(json.dumps(result, indent=2)+'\n')
    print('Built CHDIR.EXE', result['binary_sha256'])


if __name__ == '__main__':
    main()
