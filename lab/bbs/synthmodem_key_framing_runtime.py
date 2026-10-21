#!/usr/bin/env python3
"""Stage opt-in serial-key framing on the exact accepted carrier runtime."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
from synthmodem_vm_control import ROOT, sha
from synthmodem_carrier_runtime import validate as validate_carrier

REFERENCE = ROOT/'build/bbs-lab/synthmodem-carrier-runtime-01/runtime'
HERE = ROOT/'lab/bbs/patches/synthmodem-key-framing'
LEDGER = ROOT/'docs/validation/synthmodem-key-framing-runtime.json'


def validate(runtime):
    ledger = json.loads(LEDGER.read_text()); assert ledger['passed']
    expected = ledger['files']
    assert {str(p.relative_to(runtime)) for p in runtime.rglob('*') if p.is_file()} == set(expected)
    for name, digest in expected.items(): assert sha(runtime/name) == digest, name
    return {str(runtime/name): digest for name, digest in expected.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    out = parser.parse_args().output.resolve(); assert out.is_relative_to(ROOT/'build')
    inputs = validate_carrier(REFERENCE)
    names = ['lab/bbs/synthmodem_key_framing_runtime.py', 'lab/bbs/synthmodem_carrier_runtime.py',
             'docs/validation/synthmodem-carrier-runtime.json']
    names += [str(p.relative_to(ROOT)) for p in sorted(HERE.iterdir()) if p.is_file()]
    frozen = {n: sha(ROOT/n) for n in names}
    out.mkdir(parents=True, exist_ok=False); runtime = out/'runtime'; shutil.copytree(REFERENCE, runtime)
    subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-i', str(HERE/'proxy.patch')],
                   cwd=runtime/'source', check=True)
    leaf = 'source/src/telnet/InputSequenceFramer.js'
    shutil.copyfile(HERE/'InputSequenceFramer.js', runtime/leaf)
    changed = [str(Path(n).relative_to(REFERENCE)) for n, h in inputs.items()
               if sha(runtime/Path(n).relative_to(REFERENCE)) != h]
    assert changed == ['source/src/telnet/TelnetProxy.js']
    assert all(sha(Path(n)) == h for n, h in inputs.items())
    assert all(sha(ROOT/n) == h for n, h in frozen.items())
    result = {'passed': True, 'runtime_inputs': inputs, 'frozen_inputs': frozen,
              'changed_files': changed, 'added_files': [leaf],
              'files': {str(p.relative_to(runtime)): sha(p) for p in runtime.rglob('*') if p.is_file()},
              'scope': 'Only TelnetProxy source changes and one source module is added. Config defaults, kernel, boot archive, DSPs, helper and backend are unchanged. Framing requires explicit inputSequenceTimeoutMs configuration; no runtime/BBS/hardware acceptance or installed service change.'}
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'passed': True, 'runtime': str(runtime), 'changed': changed, 'added': [leaf]}))


if __name__ == '__main__': main()
