#!/usr/bin/env python3
"""Replay passive audits and retain stock BBS clipboard/download evidence."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from test_transfer_dos import ROOT, audit_protocol, timestamp, offset_after, audit_controls as xmodem_controls
from audit_ymodem import audit_batch, audit_controls as ymodem_controls
import enigma
import synchronet


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def read(path):
    return json.loads((ROOT / path).read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='append', required=True, help='SERVER:LABEL')
    args = parser.parse_args()
    runtime = sha('build/terminal/TERMINAL.EXE')
    rows = []
    artifacts = []
    for selector in args.run:
        server, label = selector.split(':', 1)
        assert server in ('synchronet', 'enigma')
        assert label and all(c.isalnum() or c in '-_' for c in label)
        folder = Path('build/bbs-lab/results') / server / label
        result = read(folder / 'result.json')
        assert result['binary_sha256'] == runtime
        assert result['name'] == server and result['label'] == label
        assert result['mode'] == 'download'
        invocation = Path('build/bbs-lab') / (label + '-command.json')
        argv = read(invocation)
        # The remote filename must come from a local clipboard add + Single;
        # the local DOS destination remains separately typed in the recipe.
        edit = 'a p c x t e s t . b i n enter p300 s p400 escape'
        recipe = 'a-= p300 ' + edit
        menu_recipe = 'a-z p300 right p200 right p200 f p300 ' + edit
        via_menu = menu_recipe in result['keys']
        assert recipe in result['keys'] or via_menu
        row = dict(server=server, label=label, result=result)
        if server == 'synchronet':
            provenance_path = Path('build/bbs-lab/synchronet/provenance.json')
            provenance = read(provenance_path)
            assert provenance['source_commit'] == synchronet.COMMIT
            for name, digest in synchronet.ARTIFACTS.items():
                assert sha(Path('build/bbs-lab/synchronet') / name) == digest
            row['server_identity'] = dict(source_commit=synchronet.COMMIT,
                                         verified_archives=synchronet.ARTIFACTS)
            artifacts.extend([provenance_path, Path('build/bbs-lab/synchronet/runtime/exec/sbbs'),
                              Path('build/bbs-lab/synchronet/runtime/exec/sexyz')])
        else:
            head = subprocess.check_output(['git', '-C', str(enigma.SOURCE), 'rev-parse', 'HEAD'], text=True).strip()
            assert head == enigma.COMMIT
            row['server_identity'] = dict(source_commit=head)
            artifacts.extend([Path('build/bbs-lab/enigma/helpers/sexyz'),
                              Path('build/bbs-lab/enigma/source/core/file_base_search.js'),
                              Path('build/bbs-lab/enigma/source/config/menus/loc-file_base.hjson')])
        session_path = folder / 'server-session-audit.json'
        if (ROOT / session_path).exists():
            row['server_session'] = read(session_path)
        diagnosis_path = folder / 'fixture-diagnosis.json'
        if (ROOT / diagnosis_path).exists():
            row['fixture_diagnosis'] = read(diagnosis_path)
        if result['passed']:
            assert all(result['checks'].values()) and not result['errors']
            metadata = read(folder / 'server-source-metadata.json')
            assert metadata['passed'] and all(metadata['checks'].values())
            assert metadata['server_commit'] == row['server_identity']['source_commit']
            row['official_source_metadata'] = metadata
            assert (ROOT / folder / 'PASS.TXT').exists()
            assert not (ROOT / folder / 'FAIL.TXT').exists()
            before = (ROOT / folder / 'BEFORE.BIN').read_bytes()
            assert len(before) == 42 and before == (ROOT / folder / 'AFTER.BIN').read_bytes()
            display = (ROOT / folder / 'display.bin').read_bytes()
            wire = (ROOT / folder / 'serial-received.bin').read_bytes()
            trace = read(folder / 'trace.json')
            source = Path('build/bbs-lab/synchronet/runtime/data/dirs/pcplab/PCXTEST.BIN') if server == 'synchronet' else Path('build/bbs-lab/enigma/source/file_base/pcplus_transfer/PCXTEST.BIN')
            payload = (ROOT / source).read_bytes()
            if server == 'synchronet':
                audit = audit_protocol(display, payload)
                assert (ROOT / folder / 'PCXTEST.BIN').read_bytes() == audit.pop('padded_payload')
            else:
                audit = audit_batch(display, {'PCXTEST.BIN': payload})
                assert len(audit['files']) == 1
                assert (ROOT / folder / 'RECV/PCXTEST.BIN').read_bytes() == audit['files'][0].pop('source')
                session = read(folder / 'server-session-audit.json')
                assert session['passed'] and all(session['checks'].values())
                assert session['menus'].index('fileBaseSearch') < session['menus'].index('fileTransferProtocolSelection')
            saved = read(folder / 'protocol.json')
            assert all(saved[key] == value for key, value in audit.items())
            end_time = timestamp(trace, 'bbs', audit['end'] - 1)
            after = offset_after(trace, 'dos', end_time)
            assert after is not None
            post = bytes.fromhex(argv[argv.index('--post-input-hex') + 1])
            post_at = wire.find(post, after)
            assert post_at >= 0
            post_time = timestamp(trace, 'dos', post_at)
            controls = xmodem_controls(audit, display, wire, trace, 'bbs', post_time) if server == 'synchronet' else ymodem_controls(audit, wire, trace, 'bbs', post_time, False)
            assert controls == saved['controls']
            first_time = timestamp(trace, 'bbs', audit['start'])
            cut = offset_after(trace, 'dos', first_time)
            prefix = wire[:cut] if cut is not None else wire
            packet = b'PCXTEST.BIN\r'
            assert prefix.count(packet) == 1 and b'pcxtest.bin' not in prefix
            at = prefix.index(packet)
            assert timestamp(trace, 'dos', at) < first_time
            row['clipboard_selection'] = dict(packet_hex=packet.hex(), wire_offset=at,
                                             observed_before_first_protocol_frame=True,
                                             lowercase_local_edit_not_sent=True)
            if via_menu:
                assert b'\x1b[C' not in prefix
                row['clipboard_selection'].update(command_menu_View_F_handoff=True,
                                                  local_menu_arrow_sequences_not_transmitted=True)
            if server == 'enigma':
                assert post == b'S\r'
                again = wire.find(packet, post_at + len(post))
                assert again >= 0 and b'pcxtest.bin' not in wire
                response_offset = offset_after(trace, 'bbs', timestamp(trace, 'dos', again + len(packet) - 1))
                assert response_offset is not None
                rendered = re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]', b'', display[response_offset:])
                assert b'PCXTEST.BIN - 11.25 KB' in rendered
                row['posttransfer_clipboard_search'] = dict(packet_hex=packet.hex(), wire_offset=again,
                                                           exact_filename_and_size_in_search_result=True)
            row['passive_protocol_replayed'] = True
            row['protocol'] = saved
            artifacts.append(source)
        if server == 'synchronet':
            fixture = folder.parent / (label + '-logon.json')
            state = read(fixture)
            verify = read(fixture.with_suffix('.verify.json'))
            assert state['restored'] and state['before'] == state['after']
            assert verify['number'] == state['number'] and verify['exemptions'] == state['before']
            row['temporary_logon_fixture'] = dict(state=state, independent_persisted_readback=verify)
            artifacts.extend(p.relative_to(ROOT) for p in sorted((ROOT / folder.parent).glob(label + '-logon.*')) if p.is_file())
        artifacts.extend(p.relative_to(ROOT) for p in sorted((ROOT / folder).rglob('*'))
                         if p.is_file() and p.name != '.lock')
        row['invocation'] = argv
        artifacts.append(invocation)
        rows.append(row)
    sources = ['lab/bbs/record_clipboard_transfers.py', 'lab/bbs/test_transfer_dos.py',
               'lab/bbs/test_ymodem_dos.py', 'lab/bbs/audit_ymodem.py', 'lab/bbs/modem.py',
               'lab/bbs/synchronet_logon_fixture.py', 'standalone/test_terminal.py',
               'lab/bbs/synchronet.py', 'lab/bbs/enigma.py',
               'standalone/terminal_config_fixtures.py', 'standalone/modem_fixtures.py',
               'standalone/directory_fixtures.py', 'standalone/directory_test_support.py']
    selected = {row['server']: row for row in rows}
    report = dict(binary_sha256=runtime, all_recorded_runs_passed=all(r['result']['passed'] for r in rows),
                  latest_selected_workflows={server: row['label'] for server, row in selected.items()},
                  latest_selected_workflows_passed=all(row['result']['passed'] for row in selected.values()),
                  runs=rows, sources={p: sha(p) for p in sources},
                  retained_artifacts={str(p): sha(p) for p in artifacts},
                  scope='Actual stock local BBS menu filename selection using maintained DOS clipboard, '
                        'then stock XMODEM/YMODEM download helpers and real post-transfer menu input. '
                        'Passive audit replay and exact DOS destination bytes. Synthetic owned '
                        'accounts/media, loopback Hayes/Telnet bridge; no physical modem claim, '
                        'complete clipboard UI parity or whole-application completion.')
    destination = ROOT / 'docs/validation/bbs-clipboard-transfers.json'
    history = []
    if destination.exists():
        previous = json.loads(destination.read_text())
        history = previous.get('prior_runtime_reports', [])
        if previous['binary_sha256'] != runtime:
            previous = {key: value for key, value in previous.items() if key != 'prior_runtime_reports'}
            if previous not in history:
                history.append(previous)
    report['prior_runtime_reports'] = history
    destination.write_text(json.dumps(report, indent=2) + '\n')
    print('Recorded', len(rows), 'stock BBS clipboard transfer attempts')


if __name__ == '__main__':
    main()
