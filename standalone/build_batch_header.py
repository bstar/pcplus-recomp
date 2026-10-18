#!/usr/bin/env python3
"""Build the source-owned DOS metadata-codec diagnostic without running tests."""
import hashlib
import json
import subprocess
from pathlib import Path
from check_batch_header import DOS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/batch-header'
SRC = ROOT / 'src/transfer'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'host.c').write_text(DOS)
    subprocess.run(['wcl', '-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we',
                    '-k8192', '-i='+str(SRC), '-fm=HEADER.map', '-fe=HEADER.EXE',
                    str(SRC/'batch_header.c'), str(OUT/'host.c')], cwd=OUT, check=True)
    sources = [SRC/'batch_header.c', SRC/'batch_header.h',
               ROOT/'standalone/check_batch_header.py', Path(__file__).resolve()]
    result = dict(binary_sha256=hashlib.sha256((OUT/'HEADER.EXE').read_bytes()).hexdigest(),
                  sources={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in sources},
                  scope='Source-built bounded metadata-codec DOS diagnostic. No original artifacts or runtime tests are build inputs.')
    (OUT/'manifest.json').write_text(json.dumps(result, indent=2)+'\n')
    print('Built HEADER.EXE', result['binary_sha256'])


if __name__ == '__main__':
    main()
