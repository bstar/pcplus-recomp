#!/usr/bin/env python3
"""Compose real editor, ASIOv7 recovery and guarded helpers on IRQ5/7 in DOS8086."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

from build_guarded_helper import ROOT, LOOKUP
from package_special_edition import sha

TERMINAL = ROOT / 'build' / (LOOKUP + '-custom-irq') / 'TERMINAL.EXE'
CHILD = ROOT / 'build/aspect-register-parent-custom-irq/ASPECT.EXE'
EDITOR = ROOT / 'build/setup-mouse-notice-sound-custom-irq/PRMEDIT.EXE'
SETUP_CASES = {'same-5-to7': (1, 1, 5, 7, True), 'same-7-to5': (2, 2, 7, 5, True),
               'move-1-to2': (1, 2, 5, 7, True), 'decline-same': (1, 1, 5, 7, False)}


def setup_worker(out, case):
    import test_setup_port_dos as setup
    setup.OUT = out / 'setup'
    setup.BINARY = TERMINAL
    setup.EDITOR = EDITOR
    source, target, source_irq, target_irq, accept = SETUP_CASES[case]
    assert not (setup.OUT / case).exists()
    setup.run(case, source, target, source_irq=source_irq, target_irq=target_irq, accept=accept)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--setup-case', choices=SETUP_CASES)
    args = p.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build')
    if args.setup_case:
        setup_worker(out, args.setup_case)
        return
    assert not out.exists()
    out.mkdir(parents=True)
    sources = {}
    products = {}
    for binary in (TERMINAL, CHILD, EDITOR):
        manifest = json.loads((binary.parent / 'manifest.json').read_text())
        assert manifest['experimental_custom_irq'] and sha(binary) == manifest['binary_sha256']
        products[binary.name] = sha(binary)
        sources.update(manifest['sources'])
    for name in ['standalone/test_parent_custom_irq_dos.py', 'standalone/test_setup_port_dos.py',
                 'standalone/port_watch.asm', 'standalone/test_register_handoff_dos.py',
                 'standalone/test_hook_apply_dos.py', 'standalone/hook_apply_child.c',
                 'standalone/test_connection_dos.py', 'standalone/test_terminal.py']:
        sources[name] = sha(ROOT / name)
    for name, digest in sources.items():
        assert sha(ROOT / name) == digest, name
    jobs = []
    for case in SETUP_CASES:
        jobs.append(('setup-' + case, [sys.executable, str(Path(__file__)), '--output', str(out),
                                      '--setup-case', case], out / 'setup' / case / 'result.json'))
    for port, irq in [(1, 5), (2, 7)]:
        for case in ('normal', 'bad-token', 'missing-script', 'missing-helper', 'divide', 'budget', 'abort'):
            label = 'irq-' + out.name + '-' + str(port) + '-' + case
            jobs.append(('register-' + str(port) + '-' + case,
                         [sys.executable, 'standalone/test_register_handoff_dos.py', '--label', label,
                          '--port', str(port), '--irq', str(irq), '--case', case,
                          '--terminal', str(TERMINAL), '--runner', str(CHILD)],
                         ROOT / 'build/register-handoff-dos' / label / 'result.json'))
        for online, modes in [(False, (0, 1)), (True, (0, 1, 9))]:
            for mode in modes:
                name = 'helper-' + str(port) + '-' + str(mode) + ('-online' if online else '-offline')
                jobs.append((name, [sys.executable, 'standalone/test_hook_apply_dos.py', '--output', str(out / name),
                                    '--port', str(port), '--irq', str(irq), '--mode', str(mode),
                                    '--terminal', str(TERMINAL), *(['--online'] if online else [])],
                             out / name / 'result.json'))

    def execute(job):
        name, command, report_path = job
        with (out / (name + '.log')).open('w') as log:
            proc = subprocess.run(command, cwd=ROOT, stdout=log, stderr=log, timeout=150)
        if proc.returncode:
            raise RuntimeError('failed ' + name + '; see ' + str(out / (name + '.log')))
        report = json.loads(report_path.read_text())
        assert report['passed'], name
        print('PASS', name, flush=True)
        return dict(case=name, report=str(report_path.relative_to(ROOT)), report_sha256=sha(report_path))

    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(execute, jobs))
    for name, digest in sources.items():
        assert sha(ROOT / name) == digest, name
    result = dict(passed=True, cases=results, products=products, sources=sources, original_inputs=[],
                  scope=__doc__ + ' Synthetic serial modems, maintained native-operand register fixtures. '
                  'No stock BBS, source-compiler parity, physical or shared-IRQ acceptance.')
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
