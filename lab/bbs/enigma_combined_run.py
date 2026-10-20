#!/usr/bin/env python3
"""Run existing DOS compatibility routes against one composed, frozen server."""
import argparse
import datetime
import json
from pathlib import Path
import re
import subprocess

from enigma_key_stream_fixture import ROOT, owned, verify_running, sha


def run(args):
    assert re.fullmatch(r'[A-Za-z0-9_-]+', args.prefix)
    candidate = owned(args.candidate)
    verify_running(candidate)
    meta = json.loads((candidate / 'combined-instance.json').read_text())
    for name, digest in meta['final_inputs'].items():
        assert sha(candidate / name) == digest
    out = ROOT / 'build/bbs-lab/results/enigma' / (args.prefix + '-suite')
    out.mkdir(parents=True, exist_ok=False)
    jobs = []
    def add(name, runner, extra=(), auditor=None, audit_candidate=True):
        label = args.prefix + '-' + name
        command = [str(ROOT / 'tools/dev'), '--command', 'python3', 'lab/bbs/' + runner,
                   '--candidate', str(candidate), '--label', label, *extra]
        jobs.append((name, command))
        if auditor:
            command = [str(ROOT / 'tools/dev'), '--command', 'python3', 'lab/bbs/' + auditor, '--label', label]
            if audit_candidate:
                command += ['--candidate', str(candidate)]
            jobs.append((name + '-audit', command))
    add('download', 'enigma_repeat_download_dos.py', ['--observe-labels'], 'check_enigma_repeat_audit.py')
    add('upload', 'enigma_upload_dos.py', ['--cancel-first', '--upload-bytes', '65539'], 'check_enigma_upload_audit.py')
    for mode in ('cancel', 'overwrite', 'corrupt'):
        add('save-' + mode, 'enigma_infocom_edges_dos.py',
            ['--server-root', str(args.server_root), '--mode', mode], 'check_enigma_infocom_edges.py')
    for game in ('bre', 'gwar'):
        add(game, 'enigma_v86_dos.py', ['--server-root', str(args.server_root), '--game', game],
            'check_enigma_v86.py', audit_candidate=False)
    frozen = {str(path.relative_to(ROOT)): sha(path) for path in sorted((ROOT / 'lab/bbs').glob('*'))
              if path.suffix in ('.py', '.js')}
    frozen.update({'candidate/' + name: digest for name, digest in meta['final_inputs'].items()})
    rows = []
    def save():
        result = dict(passed=len(rows) == len(jobs) and all(row['exit_code'] == 0 for row in rows),
            candidate=str(candidate), prefix=args.prefix, steps=rows,
            expected_steps=[name for name, _ in jobs], input_hashes=frozen,
            scope='Seven existing actual DOS workflows and immediate passive audits against one composed server. No source edits, data resets or automatic retry. Individual artifacts define acceptance scope.')
        (out / 'suite.json').write_text(json.dumps(result, indent=2) + '\n')
    save()
    for number, (name, command) in enumerate(jobs):
        print('START', name, flush=True)
        log = out / (str(number).zfill(2) + '-' + name + '.log')
        start = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with log.open('x') as stream:
            process = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
        rows.append(dict(name=name, command=command, exit_code=process.returncode, started=start,
            finished=datetime.datetime.now(datetime.timezone.utc).isoformat(), log=str(log.relative_to(ROOT)), sha256=sha(log)))
        save()
        print('END', name, process.returncode, flush=True)
        if process.returncode:
            return process.returncode
        for path, digest in frozen.items():
            actual = candidate / path[10:] if path.startswith('candidate/') else ROOT / path
            assert sha(actual) == digest, path
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--server-root', type=Path, required=True)
    parser.add_argument('--prefix', required=True)
    raise SystemExit(run(parser.parse_args()))
