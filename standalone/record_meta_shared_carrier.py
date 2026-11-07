#!/usr/bin/env python3
"""Bind shared-parent carrier cleanup, ASPECT return and same-process redial."""
import json
import struct
from build_context_help import ROOT, sha


def main():
    parent = ROOT / 'build/meta-shared-help-seventh-20261107'
    digest = sha(parent / 'TERMINAL.EXE')
    runner_digest = sha(ROOT / 'build/meta-shared-aspect-sixth-20261107/ASPECT.EXE')
    receipts, sources, groups = {}, {}, {}
    selections = {
        'x-carrier-accepted': {'receive-negotiation', 'receive-partial', 'upload-unacked', 'upload-partial'},
        'batch-carrier-accepted': {f'{p}-{k}' for p in ('ymodem', 'zmodem') for k in
                                  ('receive-metadata', 'receive-partial', 'receive-retained', 'upload-metadata', 'upload-partial')},
        'fragment-carrier-accepted': {f'{p}-fragment-{policy}' for p in ('ymodem', 'zmodem') for policy in ('legacy', 'strict')},
        'aspect-carrier-upper': {'aspect-wait', 'aspect-when', 'aspect-wait-window', 'aspect-when-window'},
    }
    for group, expected in selections.items():
        folder = ROOT / f'build/phone-log-carrier-terminal/meta-shared-{group}-20261107'
        path = folder / 'result.json'
        result = json.loads(path.read_text())
        assert result['passed'] and all(result['checks'].values())
        assert result['terminal_sha256'] == digest and not result['original_inputs']
        assert {row['case'] for row in result['cases']} == expected
        high = group.startswith('aspect')
        for row in result['cases']:
            assert row['passed'] and all(row['checks'].values())
            assert row['cpu'] == ('386' if high else '8086')
            assert row['observer_high_requested'] == high
            assert len(row['sessions']) == 2
            if high:
                assert row['aspect']['runner_sha256'] == runner_digest
                assert row['aspect']['record_limit'] == 8
                config = (folder / row['case'] / 'dosbox.conf').read_text()
                assert 'umb=true' in config and sum(line.startswith('LH ') for line in config.splitlines()) == 2
            for name, expected_sha in row['artifacts'].items():
                assert sha(ROOT / name) == expected_sha, name
                receipts[name] = expected_sha
        for name, expected_sha in result['sources'].items():
            assert sha(ROOT / name) == expected_sha, name
            assert name not in sources or sources[name] == expected_sha
            sources[name] = expected_sha
        receipts[str(path.relative_to(ROOT))] = sha(path)
        groups[group] = result['cases']
    diagnostic = ROOT / 'build/phone-log-carrier-terminal/meta-shared-aspect-program-diagnostic-20261107/PLSTATE.BIN'
    data = diagnostic.read_bytes()
    assert len(data) == 4022 + 4 * 722 + 26
    program = struct.unpack('<4H', data[-8:])
    assert program[:2] == (3, 8)  # PROCESS_EXEC, DOS insufficient memory.
    receipts[str(diagnostic.relative_to(ROOT))] = sha(diagnostic)
    for name in ('build/meta-aspect-program-diagnostic-20261107.py',
                 'build/phone-log-carrier-terminal/meta-shared-aspect-program-diagnostic-20261107/program-watch.asm'):
        receipts[name] = sha(ROOT / name)
    for name in ('standalone/record_meta_shared_carrier.py', 'docs/META_SHARED_CARRIER.md'):
        sources[name] = sha(ROOT / name)
    report = dict(checkpoint_verified=True, release_eligible=False, installed_changed=False,
                  physical_verified=False, parent_sha256=digest,
                  runner_sha256=runner_digest,
                  groups=groups, sources=sources, receipts=receipts,
                  low_memory_diagnostic=dict(program_result=list(program), accepted_ASPECT_workflow=False),
                  limitations=[
                      'Transfer cases use ordinaryDOS8086; ASPECT observed cases require386/UMB for the diagnostic TSRs.',
                      'Low-memory diagnostic witnesses PROCESS_EXEC/DOS8 only; it does not pass the script/reconnect workflow.',
                      'Carrier peers use the existing bounded payload fixtures, not the all256-byte large-transfer matrix.',
                      'Virtual modem DCD/results follow actual socket closure; physical CTS/SIP/audio and live-BBS transfers remain separate.',
                      'No application bytes or installed files changed; full original feature parity remains open.'])
    output = ROOT / 'docs/validation/meta-shared-carrier.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('Verified shared-parent carrier cases:', sum(len(rows) for rows in groups.values()))


if __name__ == '__main__':
    main()
