#!/usr/bin/env python3
"""Publish identities/checks for a successful current live DOS Infocom run."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+', args.label)
    folder = ROOT / 'build/bbs-lab/results/enigma-owned' / args.label
    report_path = folder / 'owned-server-checks.json'
    report = json.loads(report_path.read_text())
    assert report['passed'] and report['mode'] == 'infocom'
    assert all(report['checks'].values())
    audit_path = folder / 'audit-negative-checks.json'
    audit = json.loads(audit_path.read_text())
    assert audit['passed'] and len(audit['negative_cases']) == 8
    assert all(c['rejected'] for c in audit['negative_cases'])
    assert audit['report_sha256'] == sha(report_path)
    for path, digest in audit['inputs'].items():
        assert sha(ROOT / path) == digest
    for path, digest in report['input_hashes'].items():
        assert sha(Path(path)) == digest, path
    assert audit['audit_sha256'] == sha(ROOT / 'lab/bbs/enigma_infocom_probe.py')
    assert audit['checker_sha256'] == sha(ROOT / 'lab/bbs/check_enigma_infocom_audit.py')
    identities = {}
    for name in ('TERMINAL.EXE', 'ASPECT.EXE', 'ASPCOMP.EXE'):
        path = folder / 'program' / name
        current = ROOT / 'build' / {'TERMINAL.EXE': 'terminal', 'ASPECT.EXE': 'aspect-runner',
                                  'ASPCOMP.EXE': 'aspect-compiler-dos'}[name] / name
        assert sha(path) == sha(current)
        identities[name] = sha(path)
    server = Path(report['server_root'])
    inputs = {str(Path(p).relative_to(server)): h for p, h in report['input_hashes'].items()
              if Path(p).is_relative_to(server)}
    result = dict(passed=True, compatibility_complete=False,
                  server_revision=report['server_revision'],
                  live_client_sha256=sha(server / 'core/client.js'),
                  application_binaries=identities, main_menu_text=report['main_menu_text'],
                  checks=report['checks'], server_inputs=inputs,
                  evidence={str(p.relative_to(ROOT)): sha(p) for p in
                            (report_path, audit_path, folder / 'display.bin',
                             folder / 'bbs-sent.bin', folder / 'server-session.jsonl')},
                  audit_negative_cases=audit['negative_cases'],
                  driver_sha256=sha(ROOT / 'lab/bbs/enigma_owned_dos.py'),
                  probe_sha256=audit['audit_sha256'], checker_sha256=audit['checker_sha256'],
                  recorder_sha256=sha(Path(__file__)), live_server_modified=False,
                  physical_modem_validated=False, whole_application_gates_closed=[],
                  limitations=[
                      'One installed Zork release, basic input, paging and clean return; no full playthrough.',
                      'No SAVE/RESTORE, Global War or Barren Realms Elite DOS acceptance.',
                      'Live NFO/editor decoder failures remain separate; no decoder installation.',
                      'Modeled UART/modem; physical RS-232 Wi-Fi modem is unverified.'])
    (ROOT / 'docs/validation/enigma-infocom.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Recorded actual DOS/live Infocom route and eight rejected corruptions; full gates remain open')


if __name__ == '__main__':
    main()
