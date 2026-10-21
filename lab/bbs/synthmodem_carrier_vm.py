#!/usr/bin/env python3
"""Run the real software-carrier-loss cohort against the staged normal image."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
from synthmodem_vm_control import ROOT, sha
from synthmodem_carrier_runtime import validate


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); runtime = a.runtime.resolve(); out = a.output.resolve()
    assert out.is_relative_to(ROOT/'build'); inputs = validate(runtime)
    names = ['lab/bbs/synthmodem_carrier_vm.py', 'lab/bbs/synthmodem_carrier_vm.js',
             'lab/bbs/synthmodem_carrier_runtime.py', 'docs/validation/synthmodem-carrier-runtime.json',
             'nix/flake.lock', 'tools/modem-dev']
    frozen = {name:sha(ROOT/name) for name in names}
    out.mkdir(parents=True, exist_ok=False)
    with (out/'node.log').open('w') as log:
        process = subprocess.Popen(['node',str(ROOT/'lab/bbs/synthmodem_carrier_vm.js'),str(runtime),str(out)],
                                   stdout=log,stderr=log,start_new_session=True)
        try: process.wait(timeout=130)
        finally:
            if process.poll() is None:
                os.killpg(process.pid,signal.SIGTERM)
                try: process.wait(timeout=3)
                except subprocess.TimeoutExpired: os.killpg(process.pid,signal.SIGKILL);process.wait()
    result = json.loads((out/'node-result.json').read_text())
    result['checks']['immutable_inputs'] = (all(sha(Path(n))==h for n,h in inputs.items())
                                           and all(sha(ROOT/n)==h for n,h in frozen.items()))
    result.update(runtime_inputs=inputs,frozen_inputs=frozen,producer_exit=process.returncode,
                  captures_sha256={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.bin','.log')})
    result['passed'] = process.returncode==0 and all(result['checks'].values())
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'passed':result['passed'],'checks':result['checks'],'errors':result['errors']},indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__': raise SystemExit(main())
