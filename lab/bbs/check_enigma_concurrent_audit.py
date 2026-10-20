#!/usr/bin/env python3
"""Passive concurrent-session evidence checks with deliberate corruptions."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re

from enigma_key_stream_fixture import ROOT, owned, sha
from audit_zmodem import audit_batch, scan, packet


def when(events, direction, offset):
    cursor = 0
    for event in events:
        if event['direction'] != direction:
            continue
        end = cursor + len(bytes.fromhex(event['hex']))
        if cursor <= offset < end:
            return event['time']
        cursor = end
    raise AssertionError('No event owns wire offset')


def audit(data, candidate):
    expected, peers = data['expected'], data['peers']
    snapshots, rows = data['snapshots'], data['catalog']
    assert len(snapshots) == 4
    first = snapshots[0]['temporary_files']
    assert len(first) == 1
    path, entry = next(iter(first.items()))
    assert path.startswith('enigul-') and path.endswith('/CONCB.BIN') and '..' not in Path(path).parts
    assert entry['inode'] > 0 and entry['bytes'] > 0
    for snapshot in snapshots[:3]:
        files = snapshot['temporary_files']
        assert set(files) == {path}, 'Active peer temporary file disappeared or unrelated data retained'
        observed = files[path]
        assert observed['inode'] == entry['inode'], 'Active peer file identity changed'
        assert entry['bytes'] <= observed['bytes'] < len(expected['CONCB.BIN'])
        assert observed['sha256'] == hashlib.sha256(expected['CONCB.BIN'][:observed['bytes']]).hexdigest(), 'Active partial differs from source'
    assert not snapshots[0]['installed'] and not snapshots[1]['installed']
    assert all(not row['entries'] for snapshot in snapshots[:2] for row in snapshot['catalog'])
    assert snapshots[2]['installed'] == ['CONCA.BIN']
    assert [len(row['entries']) for row in snapshots[2]['catalog']] == [1, 0]
    assert not snapshots[3]['temporary_files']
    assert snapshots[3]['installed'] == sorted(expected)
    assert rows == snapshots[3]['catalog']
    for row in rows:
        name = row['name']
        assert name in expected and len(row['entries']) == 1
        value = row['entries'][0]
        assert value['fileName'] == name and value['areaTag'] == value['storageTag'] == 'pcplus_upload'
        target = Path(value['filePath'])
        assert target.resolve().parent == candidate / 'file_base/pcplus_upload'
        assert target.read_bytes() == expected[name]
        assert value['fileSha256'] == hashlib.sha256(expected[name]).hexdigest()
        assert value['meta']['byte_size'] == len(expected[name])
        assert value['meta']['upload_by_username'] == ('loclab' if name == 'CONCA.BIN' else 'locpeer')

    sessions = []
    protocol = {}
    for user, name in [('loclab', 'CONCA.BIN'), ('locpeer', 'CONCB.BIN')]:
        peer = peers[user]
        sent, received, events = peer['sent'], peer['received'], peer['events']
        assert b''.join(bytes.fromhex(event['hex']) for event in events if event['direction'] == 'out') == sent
        assert b''.join(bytes.fromhex(event['hex']) for event in events if event['direction'] == 'in') == received
        assert all(a['time'] <= b['time'] for a, b in zip(events, events[1:]))
        minimum = 0
        if user == 'loclab':
            cancel = sent.index(b'\x18' * 8 + b'\x08' * 10)
            headers = [item for item in scan(sent) if item['offset'] < cancel]
            assert not any(item['type'] == 11 for item in headers)
            header = next(item for item in headers if item['type'] == 10)
            prefix = packet(sent, header['end'], header['format'])
            assert prefix['payload'] == expected[name][:1024] and prefix['ending'] == 107
            ack = next(item for item in scan(received) if item['type'] == 3 and item['position'] == 1024)
            assert when(events, 'out', prefix['crc_end'] - 1) <= when(events, 'in', ack['offset']) <= when(events, 'out', cancel)
            minimum = cancel + 18
            cancel_time = when(events, 'out', cancel)
        transfer = audit_batch(sent, {name: expected[name]}, minimum)
        closing = next(item for item in scan(sent, transfer['start']) if item['type'] == 8)
        receiver_finish = next(item for item in scan(received) if item['type'] == 8)
        assert when(events, 'out', closing['end'] - 1) <= when(events, 'in', receiver_finish['offset']) <= when(events, 'out', transfer['end'] - 2)
        for header in scan(sent, transfer['start']):
            if header['type'] != 10 or header['offset'] >= closing['offset']:
                continue
            payload = packet(sent, header['end'], header['format'])
            position = header['position'] + payload['length']
            acknowledgments = [ack for ack in scan(received) if ack['type'] == 3 and ack['position'] == position and
                when(events, 'in', ack['offset']) >= when(events, 'out', payload['crc_end'] - 1)]
            assert acknowledgments, 'Source data lacks actual receiver ACK'
        nfo = b'NFO | lines 1-15/24'
        first_nfo = received.index(nfo)
        assert b'PCPLUS NFO LINE 01 : synthetic game 01' in received[first_nfo:]
        assert when(events, 'in', received.rindex(nfo)) >= when(events, 'out', transfer['end'] - 2)
        if user == 'loclab':
            assert received.count(nfo) >= 2
            assert cancel_time <= when(events, 'in', first_nfo) <= when(events, 'out', transfer['start'])
            retry_finish = when(events, 'out', transfer['end'] - 2)
        else:
            assert received.count(nfo) >= 1
            acknowledgments = [event for event in events if event.get('label') == 'acknowledge achievement pause']
            assert len(acknowledgments) >= 2
            assert all(event['direction'] == 'out' and bytes.fromhex(event['hex']) == b'\r' and
                when(events, 'out', transfer['end'] - 2) < event['time'] < when(events, 'in', first_nfo)
                for event in acknowledgments)
            notices = b''.join(bytes.fromhex(event['hex']) for event in events if event['direction'] == 'in' and
                when(events, 'out', transfer['end'] - 2) <= event['time'] <= when(events, 'in', first_nfo))
            visible = re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]', b'', notices)
            assert visible.count(b'ACHIEVEMENT') >= 2
            assert visible.rfind(b'...cmd:') > visible.rfind(b'>> smash your keyboard <<')
            active_headers = [item for item in scan(sent) if item['type'] == 10 and
                cancel_time < when(events, 'out', item['offset']) < retry_finish]
            assert active_headers, 'Peer B was not active across A recovery'
            assert when(events, 'out', transfer['end'] - 2) > retry_finish
        auth = [row for row in data['server_rows'] if row.get('msg') == f'User "{user}" successfully logged in']
        assert len(auth) == 1
        sessions.append(auth[0]['sessionId'])
        own = [row for row in data['server_rows'] if row.get('sessionId') == sessions[-1]]
        assert sum(row.get('menuName') == 'locGameDetails' for row in own) == (2 if user == 'loclab' else 1)
        executions = [row for row in own if row.get('msg') == 'Executing external protocol']
        exits = [row for row in own if row.get('msg') == 'Process exited']
        assert [row['exitCode'] for row in exits] == ([1, 0] if user == 'loclab' else [0])
        assert len(executions) == len(exits)
        protocol[user] = dict(start=transfer['start'], end=transfer['end'], first_process=executions[0]['time'],
                              last_process=exits[-1]['time'])
    assert len(set(sessions)) == 2
    assert protocol['locpeer']['first_process'] < protocol['loclab']['first_process'] < protocol['loclab']['last_process'] < protocol['locpeer']['last_process']
    return protocol


def load(candidate, folder):
    return dict(expected={name: (folder / name).read_bytes() for name in ('CONCA.BIN', 'CONCB.BIN')},
        snapshots=json.loads((folder / 'snapshots.json').read_text()),
        catalog=json.loads((folder / 'server-upload-metadata.json').read_text()),
        server_rows=[json.loads(line) for line in (folder / 'server-session.jsonl').read_text().splitlines()],
        peers={user: dict(sent=(folder / user / 'client-wire.bin').read_bytes(),
            received=(folder / user / 'server-wire.bin').read_bytes(),
            events=json.loads((folder / user / 'events.json').read_text())) for user in ('loclab', 'locpeer')})


def main(args):
    candidate = owned(args.candidate)
    assert args.label.replace('-', '').replace('_', '').isalnum()
    folder = ROOT / 'build/bbs-lab/results/enigma' / args.label
    positive = json.loads((folder / 'concurrent-checks.json').read_text())
    assert positive['passed'] and all(positive['checks'].values())
    data = load(candidate, folder)
    protocol = audit(data, candidate)
    cases = []

    def reject(name, mutate):
        damaged = copy.deepcopy(data)
        mutate(damaged)
        try:
            audit(damaged, candidate)
        except (AssertionError, ValueError, KeyError, StopIteration, OSError):
            cases.append(dict(case=name, rejected=True))
        else:
            raise AssertionError('Damaged concurrent evidence passed: ' + name)

    key = next(iter(data['snapshots'][0]['temporary_files']))
    reject('missing-active-peer-after-cancel', lambda d: d['snapshots'][1]['temporary_files'].clear())
    reject('active-peer-inode-replaced', lambda d: d['snapshots'][2]['temporary_files'][key].update(inode=0))
    reject('wrong-active-peer-prefix', lambda d: d['snapshots'][2]['temporary_files'][key].update(sha256='0' * 64))
    reject('empty-initial-partial', lambda d: d['snapshots'][0]['temporary_files'][key].update(bytes=0))
    reject('unrelated-partial-retained', lambda d: d['snapshots'][1]['temporary_files'].update({'enigul-other/CONCA.BIN': {}}))
    reject('canceled-A-installed', lambda d: d['snapshots'][1]['installed'].append('CONCA.BIN'))
    reject('early-B-catalog-entry', lambda d: d['snapshots'][2]['catalog'][1]['entries'].append({}))
    reject('temporary-data-after-completion', lambda d: d['snapshots'][3]['temporary_files'].update({key: {}}))
    reject('wrong-upload-owner', lambda d: d['catalog'][1]['entries'][0]['meta'].update(upload_by_username='loclab'))
    reject('wrong-source-B', lambda d: d['expected'].update({'CONCB.BIN': b'!' + d['expected']['CONCB.BIN'][1:]}))
    reject('same-authenticated-session', lambda d: next(row for row in d['server_rows'] if row.get('msg') == 'User "locpeer" successfully logged in').update(sessionId=next(row['sessionId'] for row in d['server_rows'] if row.get('msg') == 'User "loclab" successfully logged in')))
    reject('missing-achievement-acknowledgments', lambda d: [event.update(label='omitted acknowledgment') for event in d['peers']['locpeer']['events'] if event.get('label') == 'acknowledge achievement pause'])
    def wrong_ack(d):
        peer = d['peers']['locpeer']
        next(event for event in peer['events'] if event.get('label') == 'acknowledge achievement pause')['hex'] = b'X'.hex()
        peer['sent'] = b''.join(bytes.fromhex(event['hex']) for event in peer['events'] if event['direction'] == 'out')
    reject('coherent-wire-wrong-achievement-key', wrong_ack)
    for user in ('loclab', 'locpeer'):
        reject('missing-NFO-' + user, lambda d, user=user: d['peers'][user].update(received=d['peers'][user]['received'].replace(b'NFO | lines', b'XXX | lines')))
        reject('wrong-wire-' + user, lambda d, user=user: d['peers'][user].update(sent=b'!' + d['peers'][user]['sent'][1:]))
        def corrupt_packet(d, user=user):
            peer = d['peers'][user]
            event = next(event for event in reversed(peer['events']) if event.get('label') == 'reference source bytes')
            wire = bytearray.fromhex(event['hex'])
            wire[5] ^= 1
            event['hex'] = bytes(wire).hex()
            peer['sent'] = b''.join(bytes.fromhex(event['hex']) for event in peer['events'] if event['direction'] == 'out')
        reject('coherent-events-corrupt-data-CRC-' + user, corrupt_packet)
    report = dict(passed=True, cases=cases, checker_sha256=sha(Path(__file__)),
        auditor_sha256=sha(ROOT / 'lab/bbs/audit_zmodem.py'), protocol=protocol,
        capture_hashes={str(path.relative_to(folder)): sha(path) for path in folder.rglob('*') if path.is_file() and path.name != 'concurrent-audit-negative-checks.json'},
        scope='Passive real two-session wire/event, ACK/finish ordering, process overlap, source-prefix/inode and catalog checks. Reference peers; no DOS assertion.')
    (folder / 'concurrent-audit-negative-checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Concurrent upload audit:', len(cases), 'corruptions rejected')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--label', required=True)
    main(parser.parse_args())
