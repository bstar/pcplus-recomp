#!/usr/bin/env python3
"""Bind actual shared-parent protocol runs; physical acceptance stays separate."""
import json
from build_context_help import ROOT, sha
from test_release_transfers_dos import recipes


def main():
    folder = ROOT / 'build/release-transfers-dos/meta-shared-transfer-final-20261107'
    path = folder / 'result.json'
    result = json.loads(path.read_text())
    assert result['passed'] and result['sources_unchanged']
    assert {r['case'] for r in result['cases']} == {r['name'] for r in recipes()}
    parent = ROOT / 'build/meta-shared-help-seventh-20261107'
    digest = sha(parent / 'TERMINAL.EXE')
    assert result['terminal_sha256'] == digest
    for name, expected in result['sources'].items():
        assert sha(ROOT / name) == expected, name
    for row in result['cases']:
        assert row['passed'] and all(row['checks'].values()) and not row['errors']
        assert row['terminal_sha256'] == digest and row['cpu'] == '8086'
        assert row['serial'] == dict(com=3, irq=5, baud=19200, framing='8N1', flow='HARD')
    captures = {str(p.relative_to(ROOT)): sha(p) for p in folder.rglob('*') if p.is_file()}
    carrier_path = ROOT / 'build/phone-log-carrier-terminal/meta-shared-carrier-final-20261107/result.json'
    carrier = json.loads(carrier_path.read_text())
    assert carrier['passed'] and all(carrier['checks'].values())
    assert carrier['terminal_sha256'] == digest and not carrier['original_inputs']
    assert {r['case'] for r in carrier['cases']} == {'idle-hard', 'write-hard', 'write-soft'}
    for row in carrier['cases']:
        assert row['passed'] and all(row['checks'].values())
    for name, expected in carrier['sources'].items():
        assert sha(ROOT / name) == expected, name
    for name, expected in carrier['artifacts'].items():
        assert sha(ROOT / name) == expected, name
        captures[name] = expected
    captures[str(carrier_path.relative_to(ROOT))] = sha(carrier_path)
    report = dict(checkpoint_verified=True, release_eligible=False,
                  physical_verified=False, installed_changed=False,
                  parent_sha256=digest, cases=result['cases'], carrier_cases=carrier['cases'],
                  product_hashes={name: sha(parent / name) for name in ('TERMINAL.EXE', 'PCMETA.OVL', 'PCLINE.OVL')},
                  sources={**result['sources'], **carrier['sources'],
                           'docs/META_SHARED_TRANSFERS.md': sha(ROOT / 'docs/META_SHARED_TRANSFERS.md')}, captures=captures,
                  recorder_sha256=sha(ROOT / 'standalone/record_meta_shared_transfers.py'),
                  limitations=[
                      'Actual DOS8086 with independent UART peers/lrzsz; not physical CTS, SIP/audio or live BBS transfer acceptance.',
                      'Shared disk-loaded reference is allowed3000ms before navigation; YMODEM upload peer delays its initial CRC request by the same extra3s. Earlier fixture failures before negotiation are not accepted evidence.',
                      'Carrier gates cover idle and held call-log writes with same-process browser redial. Carrier loss during binary transfer and ASPECT remains open on these exact products.',
                      'No application bytes or installed package changed.'])
    output = ROOT / 'docs/validation/meta-shared-transfers.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Verified shared-parent transfer cases:', len(result['cases']), 'carrier/reconnect:', len(carrier['cases']))


if __name__ == '__main__':
    main()
