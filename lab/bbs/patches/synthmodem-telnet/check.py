#!/usr/bin/env python3
"""Stage a checksum-pinned, isolated SynthModem proxy candidate; never deploy."""
import argparse
import hashlib
import json
import shutil
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
REVISION = 'b1752e4d0039e0cff72735924e03aa99922723a8'
PINS = {
 'src/telnet/TelnetProxy.js': '98efcb975e4fbe64303d7bb54820ccf8cf8199fe1fe8552272b00ce9c0993fd0',
 'src/logger.js': '9ce9d913744df9fb0f3c4c1573f683608c4de19e6c3e2ba475a8d91411d7f2a5',
 'config.js': '3d6d33a25b8d86cde88d02ae538846592a020e8d64063abdb231a6ba7b27d49e',
 'COPYING': '0ed8b6028dc07428234531de5a5ec59c878ec622f599e4c353520a10be909cd9',
}


def digest(path):
 return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
 parser = argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--output', type=Path, required=True)
 args = parser.parse_args()
 out = args.output.resolve()
 assert out.is_relative_to(ROOT / 'build'), 'Keep downloaded/candidate source under ignored build/'
 out.mkdir(parents=True, exist_ok=False)
 cache = ROOT / 'build/bbs-lab/synthmodem-cache' / REVISION
 for name, expected in PINS.items():
  path = cache / name
  if not path.exists():
   data = urllib.request.urlopen(f'https://raw.githubusercontent.com/synexo/synthmodem/{REVISION}/{name}', timeout=30).read()
   assert hashlib.sha256(data).hexdigest() == expected, name
   path.parent.mkdir(parents=True, exist_ok=True)
   path.write_bytes(data)
  assert digest(path) == expected, name
  for variant in ('stock', 'candidate'):
   target = out / variant / name
   target.parent.mkdir(parents=True, exist_ok=True)
   shutil.copyfile(path, target)
 inputs = {p.name: digest(p) for p in HERE.iterdir() if p.is_file()}
 subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-i', str(HERE / 'proxy.patch')],
                cwd=out / 'candidate', check=True)
 shutil.copyfile(HERE / 'TelnetCodec.js', out / 'candidate/src/telnet/TelnetCodec.js')
 versions = subprocess.check_output(['node', '--version'], text=True).strip()
 with (out / 'checks.log').open('w') as log:
  process = subprocess.run(['node', str(HERE / 'check.js'), str(out)], stdout=log, stderr=subprocess.STDOUT, timeout=45)
 assert process.returncode == 0, (out / 'checks.log').read_text()
 checks = json.loads((out / 'checks.json').read_text())
 assert checks['passed']
 assert inputs == {p.name: digest(p) for p in HERE.iterdir() if p.is_file()}, 'Lab inputs changed during execution'
 assert all(digest(out / 'stock' / p) == h for p, h in PINS.items())
 receipt = {'passed': True, 'upstream_revision': REVISION, 'upstream_sha256': PINS,
            'lab_input_sha256': inputs, 'node': versions, 'checks': checks,
            'candidate_sha256': {p: digest(out / 'candidate' / p) for p in ['src/telnet/TelnetProxy.js', 'src/telnet/TelnetCodec.js']},
            'scope': 'Actual upstream proxy and isolated source candidate; modeled socket fragmentation plus real loopback TCP. No DSP, SIP/RTP, analog modem, DOS client, remote BBS, installed service or upstream submission.'}
 (out / 'result.json').write_text(json.dumps(receipt, indent=2) + '\n')
 print(json.dumps({'passed': True, 'output': str(out), 'checks': checks}, indent=2))


if __name__ == '__main__':
 main()
