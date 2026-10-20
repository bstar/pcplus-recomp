#!/usr/bin/env python3
"""Read-only audit of DOS/proxy transfer evidence using the older lab codec."""
import argparse
import hashlib
import json
from pathlib import Path

from modem import Telnet

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
 return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(out, candidate):
 report = json.loads((out / 'result.json').read_text())
 assert report['passed'], 'Do not relabel failed producer attempts'
 for name, digest in report['frozen_inputs'].items(): assert sha(ROOT / name) == digest, name
 for name, digest in report['candidate_sha256'].items(): assert sha(candidate / name) == digest, name
 rows = []
 for case in report['cases']:
  folder = out / case['direction']
  assert case['passed'] and all(case['checks'].values())
  for name, digest in case['trace_sha256'].items(): assert sha(folder / name) == digest, name
  # This pre-existing Python codec is independent of the JS candidate and the
  # server-side capture decoder; its replies are observed only, never injected.
  for wire, plain in [('telnet-in.bin', 'terminal-in.bin'), ('telnet-out.bin', 'terminal-out.bin')]:
   decoded, _ = Telnet().feed((folder / wire).read_bytes())
   assert decoded == (folder / plain).read_bytes(), (case['direction'], wire)
  source = folder / ('PEER' if case['direction'] == 'rx' else 'SEND')
  destination = folder / ('RECV' if case['direction'] == 'rx' else 'PEER')
  assert {p.name:sha(p) for p in source.iterdir()} == case['files']
  assert {p.name:sha(p) for p in destination.iterdir()} == case['files']
  before = (folder / 'BEFORE.BIN').read_bytes()
  assert len(before) == 42 and before == (folder / 'AFTER.BIN').read_bytes()
  assert case['peer_exit'] == 0
  rows.append({'direction':case['direction'], 'checks':len(case['checks']),
               'files':{p.name:p.stat().st_size for p in destination.iterdir()},
               'both_decoded_streams_exact':True, 'files_and_hardware_exact':True})
 return {'passed':True, 'cases':rows,
         'auditor_sha256':sha(Path(__file__)), 'independent_codec_sha256':sha(ROOT / 'lab/bbs/modem.py')}


if __name__ == '__main__':
 parser = argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--output', type=Path, required=True)
 parser.add_argument('--candidate', type=Path, required=True)
 args = parser.parse_args()
 out, candidate = args.output.resolve(), args.candidate.resolve()
 assert out.is_relative_to(ROOT / 'build') and candidate.is_relative_to(ROOT / 'build')
 print(json.dumps(audit(out, candidate), indent=2))
