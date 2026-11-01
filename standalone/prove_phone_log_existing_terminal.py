#!/usr/bin/env python3
"""Rebuild committed public sources and repeat existing-file and menu DOS tests."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from build_phone_log_queue import ROOT, sha
from prove_phone_log_startup_terminal import flags


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terminal', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--extended', action='store_true', help='Also repeat preexisting-startup and failed-rollback cases')
    parser.add_argument('--permissions', action='store_true', help='Repeat real DOS read-only startup/runtime cases')
    parser.add_argument('--slow', action='store_true', help='Repeat delayed-write and paced traffic cases')
    parser.add_argument('--watermark', action='store_true', help='Repeat driver high-watermark handoff cases')
    parser.add_argument('--carrier', action='store_true', help='Repeat actual emulated DCD loss and same-parent redial')
    parser.add_argument('--transfer-carrier', action='store_true', help='Repeat receive/upload loss, cleanup and logged redial')
    parser.add_argument('--aspect-carrier', action='store_true', help='Rebuild ASPECT and repeat script/window carrier-loss cases')
    parser.add_argument('--runner', type=Path)
    args = parser.parse_args()
    parent, output = args.terminal.resolve(), args.output.resolve()
    assert parent.is_relative_to(ROOT/'build') and output.is_relative_to(ROOT/'build')
    assert not output.exists()
    manifest = json.loads((parent/'manifest.json').read_text())
    assert manifest['experimental_phone_log_controls']
    assert sha(parent/'TERMINAL.EXE') == manifest['binary_sha256']
    revision = subprocess.check_output(['git', 'rev-parse', args.commit+'^{commit}'], text=True).strip()
    tracked = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', revision], text=True).splitlines()
    names = set(manifest['sources']) | {n for n in tracked if n.startswith('standalone/') and n.endswith('.py')}
    names |= {'standalone/phone_log_events_watch.asm', 'standalone/phone_log_close_fault.asm',
              'standalone/phone_log_write_fault.asm', 'standalone/program_handoff_child.asm',
              'nix/flake.nix', 'nix/flake.lock', 'tools/dev'}
    if args.permissions:
        names |= {'standalone/phone_log_attributes.asm','standalone/phone_log_clear_attributes.asm',
                  'standalone/phone_log_startup_watch.asm'}
    if args.slow or args.watermark or args.carrier or args.aspect_carrier or args.transfer_carrier:names |= {'standalone/phone_log_slow_write.asm'}
    if args.carrier or args.aspect_carrier or args.transfer_carrier:names |= {'lab/bbs/phone_log_evidence.py','lab/bbs/product_inputs.py'}
    runner_manifest = None
    if args.aspect_carrier:
        assert args.runner
        runner = args.runner.resolve()
        assert runner.is_relative_to(ROOT/'build') and runner.name == 'ASPECT.EXE'
        runner_manifest = json.loads((runner.parent/'manifest.json').read_text())
        assert not runner_manifest['original_inputs'] and sha(runner) == runner_manifest['binary_sha256']
        assert all(sha(ROOT/name) == digest for name,digest in runner_manifest['sources'].items())
        names |= set(runner_manifest['sources']) | {'src/aspect/compiler.py'}
    output.mkdir(parents=True)
    fresh, sources = output/'source', {}
    for name in sorted(names):
        relative = Path(name)
        assert not relative.is_absolute() and '..' not in relative.parts
        assert relative.parts[0] not in ('build', 'analysis', 'install', 'original', 'originals', '.git')
        assert relative.suffix.lower() not in ('.exe', '.obj', '.img', '.com', '.db', '.prm', '.fon')
        data = subprocess.check_output(['git', 'show', revision+':'+name])
        target = fresh/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        stamp = (ROOT/name).stat()
        os.utime(target, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
        sources[name] = sha(target)
        assert sha(ROOT/name) == sources[name], name
    reports = {}
    with (output/'build.log').open('w') as log:
        subprocess.run([sys.executable, 'standalone/build_terminal.py', *flags(manifest, True)],
                       cwd=fresh, stdout=log, stderr=log, check=True)
        rebuilt = fresh/'build'/parent.name
        assert sha(rebuilt/'TERMINAL.EXE') == manifest['binary_sha256']
        if args.aspect_carrier:
            subprocess.run([sys.executable,'standalone/build_aspect_process.py',
                            '--notice-bank','--notice-sound','--notice-input','--notice-help','--help-resource',
                            '--serial-bank','--register-handoff','--custom-irq'],
                           cwd=fresh,stdout=log,stderr=log,check=True)
            rebuilt_runner = fresh/'build'/runner.parent.name/'ASPECT.EXE'
            assert sha(rebuilt_runner) == runner_manifest['binary_sha256']
        matrices = [('public-existing', ['--existing'], 5), ('public-controls', [], 19)]
        if args.extended:
            matrices += [('public-preexisting', ['--existing', '--preexisting'], 5),
                         ('public-io-failures', ['--io-failures'], 3)]
        if args.permissions:matrices += [('public-permissions',['--permissions'],2)]
        for label, extra, expected in matrices:
            subprocess.run([sys.executable, 'standalone/test_phone_log_events_terminal.py',
                            '--terminal', str(rebuilt), '--label', label, *extra],
                           cwd=fresh, stdout=log, stderr=log, check=True)
            path = fresh/'build/phone-log-events-terminal'/label/'result.json'
            report = json.loads(path.read_text())
            assert report['passed'] and all(report['checks'].values())
            assert len(report['cases']) == expected
            assert report['terminal_sha256'] == manifest['binary_sha256']
            assert all(row['passed'] and all(row['checks'].values()) for row in report['cases'])
            reports[label] = {'path': str(path.relative_to(ROOT)), 'sha256': sha(path), 'cases': expected}
        if args.permissions:
            subprocess.run([sys.executable,'standalone/test_phone_log_startup_terminal.py',
                            '--terminal',str(rebuilt),'--label','public-readonly','--readonly'],
                           cwd=fresh,stdout=log,stderr=log,check=True)
            path=fresh/'build/phone-log-startup-terminal/public-readonly/result.json'
            report=json.loads(path.read_text())
            assert report['passed'] and report['readonly_matrix'] and len(report['cases'])==2
            assert all(report['checks'].values()) and all(row['passed'] and all(row['checks'].values()) for row in report['cases'])
            assert report['terminal_sha256']==manifest['binary_sha256']
            reports['public-readonly']={'path':str(path.relative_to(ROOT)),'sha256':sha(path),'cases':2}
        if args.slow:
            subprocess.run([sys.executable,'standalone/test_phone_log_slow_terminal.py',
                            '--terminal',str(rebuilt),'--label','public-slow'],
                           cwd=fresh,stdout=log,stderr=log,check=True)
            path=fresh/'build/phone-log-slow-terminal/public-slow/result.json'
            report=json.loads(path.read_text())
            assert report['passed'] and len(report['cases'])==3 and all(report['checks'].values())
            assert all(row['passed'] and all(row['checks'].values()) for row in report['cases'])
            assert report['terminal_sha256']==manifest['binary_sha256']
            reports['public-slow']={'path':str(path.relative_to(ROOT)),'sha256':sha(path),'cases':3}
        if args.watermark:
            subprocess.run([sys.executable,'standalone/test_phone_log_slow_terminal.py',
                            '--terminal',str(rebuilt),'--label','public-watermark','--watermark'],
                           cwd=fresh,stdout=log,stderr=log,check=True)
            path=fresh/'build/phone-log-slow-terminal/public-watermark/result.json'
            report=json.loads(path.read_text())
            assert report['passed'] and report['watermark_matrix'] and len(report['cases'])==3
            assert all(report['checks'].values()) and all(row['passed'] and all(row['checks'].values()) for row in report['cases'])
            assert report['terminal_sha256']==manifest['binary_sha256']
            reports['public-watermark']={'path':str(path.relative_to(ROOT)),'sha256':sha(path),'cases':3}
        if args.carrier:
            subprocess.run([sys.executable,'standalone/test_phone_log_carrier_terminal.py',
                            '--terminal',str(rebuilt),'--label','public-carrier'],
                           cwd=fresh,stdout=log,stderr=log,check=True)
            path=fresh/'build/phone-log-carrier-terminal/public-carrier/result.json'
            report=json.loads(path.read_text())
            assert report['passed'] and len(report['cases'])==3 and all(report['checks'].values())
            assert all(row['passed'] and all(row['checks'].values()) for row in report['cases'])
            assert report['terminal_sha256']==manifest['binary_sha256']
            reports['public-carrier']={'path':str(path.relative_to(ROOT)),'sha256':sha(path),'cases':3}
        if args.aspect_carrier:
            subprocess.run([sys.executable,'standalone/test_phone_log_carrier_terminal.py',
                            '--terminal',str(rebuilt),'--label','public-aspect-carrier',
                            '--aspect','--runner',str(rebuilt_runner)],
                           cwd=fresh,stdout=log,stderr=log,check=True)
            path=fresh/'build/phone-log-carrier-terminal/public-aspect-carrier/result.json'
            report=json.loads(path.read_text())
            assert report['passed'] and report['aspect_matrix'] and len(report['cases'])==4
            assert all(report['checks'].values()) and all(row['passed'] and all(row['checks'].values()) for row in report['cases'])
            assert report['terminal_sha256']==manifest['binary_sha256']
            assert all(row['aspect']['runner_sha256']==runner_manifest['binary_sha256'] for row in report['cases'])
            reports['public-aspect-carrier']={'path':str(path.relative_to(ROOT)),'sha256':sha(path),'cases':4}
        if args.transfer_carrier:
            subprocess.run([sys.executable,'standalone/test_phone_log_carrier_terminal.py',
                            '--terminal',str(rebuilt),'--label','public-transfer-carrier','--transfer'],
                           cwd=fresh,stdout=log,stderr=log,check=True)
            path=fresh/'build/phone-log-carrier-terminal/public-transfer-carrier/result.json'
            report=json.loads(path.read_text())
            assert report['passed'] and report['transfer_matrix'] and len(report['cases'])==4
            assert all(report['checks'].values()) and all(row['passed'] and all(row['checks'].values()) for row in report['cases'])
            assert report['terminal_sha256']==manifest['binary_sha256']
            reports['public-transfer-carrier']={'path':str(path.relative_to(ROOT)),'sha256':sha(path),'cases':4}
    assert all(sha(fresh/name) == digest and sha(ROOT/name) == digest for name, digest in sources.items())
    result = dict(passed=True, source_commit=revision, source_count=len(sources), sources=sources,
                  terminal_sha256=sha(rebuilt/'TERMINAL.EXE'), reports=reports, original_inputs=[],
                  build_log_sha256=sha(output/'build.log'),
                  scope=__doc__+' Exact unchanged application; separate real partial-write/error fixtures; '
                  'no original installs, previous objects or Git metadata exported. '
                  'No physical disk failure, sustained transport or full-application acceptance.')
    if args.aspect_carrier:result['runner_sha256']=sha(rebuilt_runner)
    (output/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print('PASS:', len(sources), 'public sources; exact terminal;', sum(r['cases'] for r in reports.values()), 'DOS cases')


if __name__ == '__main__':
    main()
