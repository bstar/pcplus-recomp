#!/usr/bin/env python3
"""Bare parent nested source compilation and recovery on selected IRQ5/7."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

from build_guarded_helper import ROOT, LOOKUP
from package_special_edition import sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    out.mkdir(parents=True)
    terminal = ROOT / 'build' / (LOOKUP + '-custom-irq') / 'TERMINAL.EXE'
    child = ROOT / 'build/aspect-register-parent-custom-irq/ASPECT.EXE'
    jobs = [(port, irq, case) for port, irq in [(1, 5), (2, 7)]
            for case in ('explicit', 'fallback', 'chain', 'rejected')]

    def execute(job):
        port, irq, case = job
        name = str(port) + '-' + case
        command = [sys.executable, 'standalone/test_nested_compiler_memory_dos.py', '--output', str(out / name),
                   '--port', str(port), '--irq', str(irq), '--case', case,
                   '--terminal', str(terminal), '--runner', str(child)]
        with (out / (name + '.log')).open('w') as log:
            subprocess.run(command, cwd=ROOT, stdout=log, stderr=log, timeout=100, check=True)
        path = out / name / 'result.json'
        report = json.loads(path.read_text())
        assert report['passed'] and report['connection']['serial_irq'] == irq
        print('PASS source', name, flush=True)
        return dict(report=str(path.relative_to(ROOT)), report_sha256=sha(path), irq=irq)

    with ThreadPoolExecutor(max_workers=3) as pool:
        cases = list(pool.map(execute, jobs))
    result = dict(passed=True, cases=cases, original_inputs=[],
                  checker_sha256=sha(Path(__file__)), scope=__doc__)
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
