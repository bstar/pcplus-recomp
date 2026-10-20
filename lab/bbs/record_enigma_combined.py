#!/usr/bin/env python3
"""Record accepted cumulative routes and controlled-error persistence evidence."""
import argparse
import json
from pathlib import Path

from enigma_key_stream_fixture import ROOT, owned, sha
from enigma_v86_fixture import state
from check_enigma_combined import REPORTS


def record(args):
    candidate = owned(args.candidate)
    results = ROOT / 'build/bbs-lab/results/enigma'
    suite_folder = results / (args.prefix + '-suite')
    suite = json.loads((suite_folder / 'suite.json').read_text())
    audited = json.loads((suite_folder / 'combined-audit.json').read_text())
    assert suite['passed'] and audited['passed'] and all(audited['checks'].values())
    assert sha(suite_folder / 'suite.json') == audited['captures'][str((suite_folder / 'suite.json').relative_to(ROOT))]
    meta = json.loads((candidate / 'combined-instance.json').read_text())
    for name, digest in meta['final_inputs'].items():
        assert sha(candidate / name) == digest
    for name, digest in meta['source_inputs'].items():
        assert sha(args.server_root / name) == digest
    assert all(state(args.server_root / name) == old for name, old in meta['source_images'].items())
    dependencies = json.loads((candidate / 'v86-door-instance.json').read_text())['dependency_inputs']
    assert all(sha(candidate / 'node_modules' / name) == digest for name, digest in dependencies.items())
    base_path = ROOT / 'docs/validation/enigma-upload-time.json'
    base = json.loads(base_path.read_text())
    assert all(sha(ROOT / 'build' / name) == digest for name, digest in base['source_products'].items())
    assert all(sha(ROOT / name) == digest for name, digest in base['source_hashes'].items())
    evidence, workflows = {}, {}
    def keep(path):
        evidence[str(path.relative_to(ROOT))] = sha(path)
    for name, files in REPORTS.items():
        folder = results / (args.prefix + '-' + name)
        runtime, audit = [json.loads((folder / file).read_text()) for file in files]
        assert runtime['passed'] and audit['passed'] and all(runtime['checks'].values())
        workflows[name] = dict(checks=runtime['checks'], corruptions_rejected=len(audit['cases']))
        for file in files:
            keep(folder / file)
    probes = {}
    for label in ['owned-v86-error-baseline-02', 'owned-v86-error-fixed-01', 'owned-v86-error-partial-01',
                  'combined-v86-error-01', 'combined-v86-partial-01']:
        folder = results / label
        probe = json.loads((folder / 'shutdown-checks.json').read_text())
        audit = json.loads((folder / 'shutdown-audit.json').read_text())
        assert probe['passed'] and audit['passed'] and all(probe['checks'].values())
        probes[label] = dict(classification=probe['classification'], modeled_flush_fault=probe['modeled_flush_fault'],
            checks=probe['checks'], corruptions_rejected=len(audit['cases']),
            first_menu_return_ms=probe['first']['return_ms'],
            first_stopped_ms=next(e['ms'] for e in probe['events'] if e['id'] == 1 and e['event'] == 'message' and e['value']['type'] == 'stopped'),
            cold_guest_readback=probe['second']['marker_in_serial'])
        for file in ('shutdown-checks.json', 'shutdown-audit.json', 'serial-1.bin', 'serial-2.bin', 'probe.img'):
            keep(folder / file)
    components = {}
    for name, path in [
        ('atomic_image', ROOT / 'build/bbs-lab/v86-shutdown-components-01.json'),
        ('transfer_owner', ROOT / 'build/bbs-lab/combined-components-01/owners/checks.json'),
        ('save_read', ROOT / 'build/bbs-lab/combined-components-01/saves/checks.json'),
    ]:
        value = json.loads(path.read_text())
        assert value['passed']
        components[name] = dict(checks=value.get('count', len(value.get('cases', []))), passed=True)
        keep(path)
    worker = ROOT / 'build/bbs-lab/combined-components-01/worker/checks.json'
    value = json.loads(worker.read_text())
    assert value['completed_control_paths'] and value['corrupt_restore_survived'] and value['overwrite_changed_save'] and not value['errors']
    components['actual_ZMachine_worker'] = value
    keep(worker)
    regressions = ROOT / 'build/bbs-lab/combined-v86-regressions-01/run.log'
    assert '9 passing' in regressions.read_text() and 'failing' not in regressions.read_text()
    components['owned_v86_registry_IPC_regressions'] = 9
    keep(regressions)
    keep(suite_folder / 'suite.json')
    keep(suite_folder / 'combined-audit.json')
    concurrency = None
    if args.concurrent_label:
        assert args.concurrent_label.replace('-', '').replace('_', '').isalnum()
        folder = results / args.concurrent_label
        runtime = json.loads((folder / 'concurrent-checks.json').read_text())
        audit = json.loads((folder / 'concurrent-audit-negative-checks.json').read_text())
        assert runtime['passed'] and audit['passed'] and all(runtime['checks'].values())
        assert runtime['composition_adapter']['sha256'] == sha(ROOT / 'lab/bbs/enigma_combined_concurrent.py')
        concurrency = dict(label=args.concurrent_label, checks=runtime['checks'],
            corruptions_rejected=len(audit['cases']),
            scope='Two reference peers on the same preserved combined instance after stopped synthetic-peer enrollment and restart. Not concurrent DOS clients.')
        preservation = json.loads((folder / 'existing-upload-audit.json').read_text())
        assert preservation['passed']
        concurrency['earlier_uploads_preserved'] = preservation['preserved_files']
        concurrency['preservation_corruptions_rejected'] = len(preservation['cases'])
        for file in ('concurrent-checks.json', 'concurrent-audit-negative-checks.json',
                     'server-session.jsonl', 'server-upload-metadata.json', 'existing-upload-audit.json',
                     'existing-upload-baseline.json', 'snapshots.json'):
            keep(folder / file)
    source_paths = [ROOT / 'lab/bbs' / name for name in ('enigma_combined_fixture.py', 'enigma_combined_run.py',
        'enigma_combined_concurrent.py', 'check_enigma_combined_concurrent.py',
        'enigma_v86_shutdown_probe.js', 'check_enigma_v86_shutdown.py', 'check_enigma_combined.py',
        'enigma_key_stream_fixture.py', 'enigma_v86_fixture.py', 'enigma_infocom_save_fixture.py')]
    source_paths += [p for p in (ROOT / 'lab/bbs/patches/enigma-v86-shutdown').iterdir() if p.is_file()]
    result = dict(date='2026-10-20', passed=True, compatibility_complete=False, whole_application_gates_closed=[],
        controlled_error_probes=probes, components=components, DOS_workflows=workflows, concurrent_upload=concurrency,
        retained_failures=[
            dict(label='combined-02-concurrent', reason='The fresh-directory reference recipe rejected valid earlier DOS uploads; no earlier file was removed.'),
            dict(label='combined-02-concurrent-preserve-02', reason='A queued Main achievement consumed F; retry waits for the actual visible Main prompt.'),
        ],
        cumulative_audit=dict(checks=audited['checks'], corruptions_rejected=len(audited['cases'])),
        composition=dict(patches=meta['patches'], final_inputs=meta['final_inputs'], source_inputs=meta['source_inputs'], dependency_inputs=dependencies,
            original_images={name: value['sha256'] for name, value in meta['source_images'].items()}, original_images_unchanged=True),
        source_products=base['source_products'], unchanged_products=len(base['source_products']),
        unchanged_application_source_files=len(base['source_hashes']),
        source_baseline=dict(path=str(base_path.relative_to(ROOT)), sha256=sha(base_path)),
        tools={str(p.relative_to(ROOT)): sha(p) for p in source_paths}, recorder_sha256=sha(Path(__file__)),
        nix_lock_sha256=sha(ROOT / 'nix/flake.lock'), evidence=evidence,
        limitations=['One isolated synthetic composed instance; no live deployment or complete custom board acceptance.',
            'Controlled input errors and explicit retry tested; abrupt process crashes, power cuts and every BBS retry route remain unproven.',
            'Partial-write ENOSPC and component syscall errors are modeled; actual DOS writes and cold guest reads are real.',
            'Physical RS-232/Wi-Fi modem behavior, concurrent guest writes and source-date preservation remain open.',
            'Source-built DOS terminal and maintained ASPECT subset are not the completed original PCPlus application. All full feature gates remain open.',
            'Original game/story/BIOS images, databases, credentials and raw captures remain private under ignored build/.'])
    output = ROOT / 'docs/validation/enigma-combined.json'
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(output, len(workflows), 'DOS workflows recorded')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--server-root', type=Path, required=True)
    parser.add_argument('--prefix', required=True)
    parser.add_argument('--concurrent-label')
    record(parser.parse_args())
