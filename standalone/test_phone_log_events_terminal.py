#!/usr/bin/env python3
"""Observe real terminal event hooks without modifying product memory or replies."""
import argparse
import datetime as dt
import json
from pathlib import Path
import re
import struct
import subprocess
import test_connection_dos as terminal
from modem_fixtures import fixture
from directory_fixtures import directory
from build_phone_log_queue import ROOT, sha

HEADING = b'\r\nNAME                                NUMBER    DATE    ONLINE  OFFLINE  ELAPSED'
OLD_CALL = (b'\r\n' + b'PREVIOUS CALL'.ljust(22) + b' ' + b'5550100'.rjust(20)
            + b' 01/02/95 03:04:05 03:05:06 00:01:01')
assert len(OLD_CALL) == 81
EXISTING_CASES = ('existing-empty', 'existing-records', 'existing-large',
                  'ui-short-retry', 'ui-write-error-retry')
IO_CASES = ('ui-commit-retry', 'ui-rollback-truncate', 'ui-rollback-commit')
PERMISSION_CASES = ('ui-readonly-cancel', 'ui-readonly-retry')


def inspect_record(raw, calls, enabled, name, target):
    meta = struct.unpack_from('<6H', raw)
    life = raw[12:50]
    queue = raw[50:]
    generation = struct.unpack_from('<I', life, 2)[0]
    flags = struct.unpack_from('<4H', life, 6)
    qflags = struct.unpack_from('<9H', queue)
    started, ended, committed = struct.unpack_from('<3I', queue, 18)
    checks = dict(final_kind=meta[0] == 2, startup_ok=meta[5] == 0,
        lifecycle_idle=struct.unpack_from('<H', life)[0] == 0x4c45 and flags == (0, 0, 0, 0),
        generation=generation == calls,
        queue_flags=qflags == (0x514d, 0, enabled, 0, calls * 2, 0, 0, 0, 0),
        queue_generations=(started, ended, committed) == (calls, calls, 0),
        final_status=meta[2] == (512 if calls else 0))
    rows = []
    previous = None
    for index in range(calls * 2):
        at = 106 + index * 140
        count, kind, gen = struct.unpack_from('<HHI', queue, at)
        text = queue[at + 8:at + 8 + count]
        valid = 0 < count < 132 and queue[at + 8 + count] == 0 and kind == index % 2 + 1 and gen == index // 2 + 1
        try:
            if index % 2 == 0:
                prefix = b'\r\n' + name[:22].ljust(22) + b' ' + target.rjust(20) + b' '
                valid &= text.startswith(prefix)
                stamp = dt.datetime.strptime(text[len(prefix):].decode('ascii'), '%m/%d/%y %H:%M:%S ')
                previous = stamp
                if gen == calls:
                    actual = struct.unpack_from('<6H', life, 14)
                    valid &= actual[1:] == (stamp.month, stamp.day, stamp.hour, stamp.minute, stamp.second) and actual[0] % 100 == stamp.year % 100
            else:
                match = re.fullmatch(rb'(\d\d):(\d\d):(\d\d) (\d\d):(\d\d):(\d\d)', text)
                valid &= bool(match)
                if match:
                    h, m, s, elapsed_h, elapsed_m, elapsed_s = map(int, match.groups())
                    elapsed = elapsed_h * 3600 + elapsed_m * 60 + elapsed_s
                    finish = previous + dt.timedelta(seconds=elapsed)
                    valid &= elapsed_m < 60 and elapsed_s < 60 and 0 <= elapsed < 30 and (finish.hour, finish.minute, finish.second) == (h, m, s)
        except (ValueError, UnicodeError, TypeError):
            valid = False
        rows.append(dict(index=index, count=count, kind=kind, generation=gen,
                         text=text.decode('cp437'), valid=bool(valid)))
    checks['exact_event_records'] = all(r['valid'] for r in rows)
    return checks, rows


def inspect_disk_record(raw, calls, enabled, name, target, data, max_elapsed=30):
    meta = struct.unpack_from('<6H', raw)
    life, queue = raw[12:50], raw[50:]
    checks = dict(final_kind=meta[0] == 2, startup_ok=meta[5] == 0,
        lifecycle_idle=struct.unpack_from('<H', life)[0] == 0x4c45 and struct.unpack_from('<4H', life, 6) == (0, 0, 0, 0),
        generation=struct.unpack_from('<I', life, 2)[0] == calls,
        queue_flags=struct.unpack_from('<9H', queue) == (0x514d, 0, enabled, calls * 2 % 4, 0, 0, 0, 0, 0),
        queue_generations=struct.unpack_from('<3I', queue, 18) == (calls, calls, calls * 2),
        final_status=meta[2] == 0)
    heading = b'\r\nNAME                                NUMBER    DATE    ONLINE  OFFLINE  ELAPSED'
    prefix = b'\r\n' + name[:22].ljust(22) + b' ' + target.rjust(20) + b' '
    rows = []
    checks['heading_and_size'] = (data.startswith(heading) and data.count(heading) == 1 and len(data) == len(heading) + calls * 81) if calls else data is None
    if calls and data is not None:
        for i in range(calls):
            start = data[len(heading) + i * 81:len(heading) + i * 81 + 64]
            end = data[len(heading) + i * 81 + 64:len(heading) + (i + 1) * 81]
            valid = start.startswith(prefix)
            try:
                stamp = dt.datetime.strptime(start[len(prefix):].decode('ascii'), '%m/%d/%y %H:%M:%S ')
                match = re.fullmatch(rb'(\d\d):(\d\d):(\d\d) (\d\d):(\d\d):(\d\d)', end)
                valid &= bool(match)
                if match:
                    h, m, sec, eh, em, es = map(int, match.groups())
                    elapsed = eh * 3600 + em * 60 + es
                    finish = stamp + dt.timedelta(seconds=elapsed)
                    valid &= em < 60 and es < 60 and elapsed < max_elapsed and (finish.hour, finish.minute, finish.second) == (h, m, sec)
                if i == calls - 1:
                    captured = struct.unpack_from('<6H', life, 14)
                    valid &= captured[0] % 100 == stamp.year % 100 and captured[1:] == (stamp.month, stamp.day, stamp.hour, stamp.minute, stamp.second)
            except (ValueError, UnicodeError):
                valid = False
            rows.append(dict(generation=i + 1, start=start.decode('cp437'), end=end.decode('cp437'), valid=bool(valid)))
    checks['exact_event_records'] = len(rows) == calls and all(r['valid'] for r in rows)
    return checks, rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terminal', type=Path, required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--existing', action='store_true', help='Run the separate existing-file/rollback application matrix')
    parser.add_argument('--preexisting', action='store_true', help='Seed the existing matrix before application startup')
    parser.add_argument('--io-failures', action='store_true', help='Run commit and rollback-failure application cases')
    parser.add_argument('--permissions', action='store_true', help='Change real DOS read-only attributes after startup')
    parser.add_argument('--case', choices=['success', 'hangup', 'busy', 'silence', 'redial', 'disabled', 'direct', 'capacity', 'soft', 'both', 'none', 'fs-failure', 'program', 'ui-ready', 'ui-retry', 'ui-cancel', 'ui-unrepaired', 'ui-recovery', 'ui-disabled', *EXISTING_CASES, *IO_CASES, *PERMISSION_CASES])
    args = parser.parse_args()
    assert re.fullmatch('[a-z0-9-]+', args.label)
    parent = args.terminal.resolve()
    manifest = json.loads((parent / 'manifest.json').read_text())
    assert manifest['experimental_phone_log_events']
    disk = bool(manifest.get('experimental_phone_log_disk'))
    controls=bool(manifest.get('experimental_phone_log_controls'))
    assert not args.existing or controls
    assert not args.preexisting or args.existing
    assert not args.io_failures or controls and not args.existing
    assert not args.permissions or controls and not args.existing and not args.io_failures
    binary = parent / 'TERMINAL.EXE'
    assert sha(binary) == manifest['binary_sha256']
    terminal.BINARY = binary
    symbols = {n: (int(s, 16), int(o, 16)) for s, o, n in re.findall(
        r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$', (parent / 'terminal.map').read_text(), re.M | re.I)}
    defines = dict(IRQ_VECTOR=12, ISR_SEGMENT=symbols['uart_receive_interrupt'][0],
        ISR_OFFSET=symbols['uart_receive_interrupt'][1], DATA_SEGMENT=symbols['_terminal_phone_log_event_status'][0],
        EVENT_STATUS_OFFSET=symbols['_terminal_phone_log_event_status'][1], EPOCH_OFFSET=symbols['_terminal_phone_log_event_epoch'][1],
        LIFECYCLE_OFFSET=symbols['_phone_log_lifecycle_store'][1], QUEUE_SEGMENT=symbols['_phone_log_queue_store'][0],
        QUEUE_OFFSET=symbols['_phone_log_queue_store'][1], CONNECTION_STATE_OFFSET=symbols['connection_state'][1],
        CONNECTION_STATUS_OFFSET=symbols['connection_status'][1], STARTUP_STATUS_OFFSET=symbols['_terminal_phone_log_startup_status'][1])
    if disk:
        defines.update(DISK_ATTEMPTS_OFFSET=symbols['_terminal_phone_log_disk_attempts'][1],
                       DISK_STATUS_OFFSET=symbols['_terminal_phone_log_disk_status'][1])
    if controls:defines['CONTROL_ACK_OFFSET']=symbols['_terminal_phone_log_retry_acks'][1]
    record_bytes = 722 if controls else 720 if disk else 716
    output = ROOT / 'build/phone-log-events-terminal' / args.label
    assert not output.exists()
    output.mkdir(parents=True)
    observer = output / 'PLWATCH.COM'
    subprocess.run(['nasm', '-fbin', *[f'-D{k}={v}' for k, v in defines.items()],
        str(ROOT / 'standalone/phone_log_events_watch.asm'), '-o', str(observer)], check=True)
    if disk:
        child=output/'CHILD.COM'
        subprocess.run(['nasm','-fbin',str(ROOT/'standalone/program_handoff_child.asm'),'-o',str(child)],check=True)
    if controls:
        close_fault=output/'CLOSEFLT.COM'
        subprocess.run(['nasm','-fbin',str(ROOT/'standalone/phone_log_close_fault.asm'),'-o',str(close_fault)],check=True)
    if args.existing or args.io_failures:
        for suffix, options in (('SHORT', ['RETURN_ERROR=0']), ('WRERR', ['RETURN_ERROR=1']),
                ('COMMIT', ['WRITE_FULL=1', 'FAIL_FIRST_COMMIT=1']),
                ('RBTRUNC', ['FAIL_TRUNCATE=1']), ('RBCOMMIT', ['FAIL_FIRST_COMMIT=1'])):
            subprocess.run(['nasm', '-fbin', *['-D'+o for o in options],
                str(ROOT/'standalone/phone_log_write_fault.asm'), '-o', str(output/(suffix+'.COM'))], check=True)
    if args.permissions:
        for stem,source in [('ATTRLOCK','phone_log_attributes.asm'),('ATTRCLR','phone_log_clear_attributes.asm')]:
            subprocess.run(['nasm','-fbin',str(ROOT/'standalone'/source),'-o',str(output/(stem+'.COM'))],check=True)
    sources = dict(manifest['sources'])
    if controls:sources['standalone/phone_log_close_fault.asm']=sha(ROOT/'standalone/phone_log_close_fault.asm')
    if args.existing or args.io_failures:sources['standalone/phone_log_write_fault.asm']=sha(ROOT/'standalone/phone_log_write_fault.asm')
    if args.permissions:
        for source in ('phone_log_attributes.asm','phone_log_clear_attributes.asm'):
            sources['standalone/'+source]=sha(ROOT/'standalone'/source)
    if disk:sources['standalone/program_handoff_child.asm']=sha(ROOT/'standalone/program_handoff_child.asm')
    for name in ('standalone/test_phone_log_events_terminal.py', 'standalone/phone_log_events_watch.asm',
        'standalone/test_connection_dos.py', 'standalone/modem_fixtures.py', 'standalone/directory_fixtures.py',
        'standalone/terminal_config_fixtures.py', 'standalone/directory_test_support.py', 'standalone/test_terminal.py'):
        sources[name] = sha(ROOT / name)
    cases = [('success', 'success', 'p3500 a-x', 1, 1),
        ('hangup', 'hangup', 'p3000 a-h p2200 a-x', 1, 1),
        ('busy', 'busy', 'p4000 a-x', 1, 0),
        ('silence', 'silence', 'p4500 a-x', 1, 0),
        ('redial', 'redial', 'p3500 a-d p3500 a-x', 1, 1),
        ('disabled', 'success', 'p3500 a-x', 0, 0),
        ('direct', 'direct', 'p3500 a-x', 1, 1),
        ('capacity', 'direct', 'p2000 a-h p300 a-d p500 a-h p300 a-d p500 a-x', 1, 2)]
    if disk:
        cases += [(n, 'success', 'p3500 a-x', 1, 1) for n in ('soft', 'both', 'none', 'fs-failure')]
        cases += [('program','success','p2500 a-1 p1500 space p700 r e a d y p800 a-x',1,1)]
    if controls:
        cases += [('ui-ready','success','p2000 a-z l p700 r p700 escape p300 escape p900 a-x',1,1),
            ('ui-retry','success','p2000 f i x enter p500 a-z l p700 r p700 y p900 escape p300 escape p1100 a-x',1,1),
            ('ui-cancel','success','p2000 a-z l p700 r p700 n p700 escape p300 escape p900 a-x',1,1),
            ('ui-unrepaired','success','p2000 a-z l p700 r p700 y p900 escape p300 escape p900 a-x',1,1),
            ('ui-recovery','success','p2000 a-1 p800 a-z l p700 r p700 y p700 escape p300 escape p900 a-x',1,1),
            ('ui-disabled','success','p2000 a-z l p700 r p700 escape p300 escape p900 a-x',0,0)]
    if args.existing:
        cases = [(name, 'success',
            'p2000 f i x enter p500 a-z l p700 r p700 y p900 escape p300 escape p1100 a-x'
            if name.startswith('ui-') else 'p3500 a-x', 1, 1) for name in EXISTING_CASES]
    if args.io_failures:
        cases = [(name, 'success',
            'p2000 f i x enter p500 a-z l p700 r p700 y p900 escape p300 escape p1100 a-x'
            if name=='ui-commit-retry' else
            'p2000 a-1 p800 a-z l p700 r p700 y p700 escape p300 escape p900 a-x',
            1, 1) for name in IO_CASES]
    if args.permissions:
        cases=[('ui-readonly-cancel','success','p2000 a-z l p700 r p700 n p700 escape p300 escape p900 a-x',1,1),
               ('ui-readonly-retry','success','p2000 a-1 p500 space p700 f i x enter p500 a-z l p700 r p700 y p900 escape p300 escape p1100 a-x',1,1)]
    assert not args.case or any(row[0] == args.case for row in cases)
    results, artifacts = [], {}
    for name, mode, keys, enabled, calls in cases:
        if disk and name == 'capacity':calls=3
        if args.case and args.case != name:
            continue
        settings = bytearray(fixture(timeout=2 if mode == 'silence' else 5))
        struct.pack_into('<HH', settings, 0x4e4, 8, 4)
        struct.pack_into('<H', settings, 0x1e6, enabled)
        if name in ('soft', 'both', 'none', 'fs-failure'):
            struct.pack_into('<HH', settings, 0x198, int(name != 'none'), int(name == 'both'))
        selected = directory(direct=1) if mode == 'direct' else None
        options = dict(directory=selected, arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1', accounting_delta=calls) if selected else {}
        case = args.label + '-' + name
        folder = ROOT / 'build/connection-dos' / case
        assert not folder.exists()
        seed = None
        retry_case = name in ('ui-retry', 'ui-short-retry', 'ui-write-error-retry', 'ui-commit-retry', 'ui-readonly-retry')
        recovery_case = name in ('ui-recovery', 'ui-rollback-truncate', 'ui-rollback-commit')
        if name in EXISTING_CASES or name in IO_CASES or name in PERMISSION_CASES:
            seed = b'' if name == 'existing-empty' else HEADING + OLD_CALL * (900 if name in ('existing-large', 'ui-write-error-retry', *IO_CASES) else 1)
            def seed_existing(owned):
                assert owned == folder and not (owned/'PCPLUS.FON').exists()
                (owned/'PCPLUS.FON').write_bytes(seed)
            if args.preexisting or args.io_failures or args.permissions:
                folder.mkdir(parents=True)
                seed_existing(folder)
                def verify_startup_preserved(owned):
                    assert owned==folder and (owned/'PCPLUS.FON').read_bytes()==seed
                options['dial_action']=verify_startup_preserved
            else:
                options['dial_action'] = seed_existing
            if retry_case:
                def verify_rollback(owned):
                    assert owned == folder and (owned/'PCPLUS.FON').read_bytes() == seed
                options['online_actions'] = ((b'fix\r', verify_rollback),)
        if name in ('fs-failure','ui-retry','ui-cancel','ui-unrepaired'):
            def namespace_fault(owned):
                assert owned == folder and not (owned/'PCPLUS.FON').exists()
                (owned/'PCPLUS.FON').mkdir()
                (owned/'PCPLUS.FON'/'KEEP.BIN').write_bytes(b'OWNED NAMESPACE FAULT')
            options['dial_action'] = namespace_fault
        if name == 'ui-retry':
            def repair_namespace(owned):
                assert owned==folder and (owned/'PCPLUS.FON').is_dir()
                assert (owned/'PCPLUS.FON'/'KEEP.BIN').read_bytes()==b'OWNED NAMESPACE FAULT'
                (owned/'PCPLUS.FON'/'KEEP.BIN').unlink();(owned/'PCPLUS.FON').rmdir()
            options['online_actions']=((b'fix\r',repair_namespace),)
        files={'PLWATCH.COM':observer.read_bytes()}
        if args.permissions:
            files['ATTRLOCK.COM']=(output/'ATTRLOCK.COM').read_bytes();options['auxiliary']=('ATTRLOCK',)
        if name == 'program' or recovery_case or name=='ui-readonly-retry':
            keymap=bytearray(540)
            for i in range(10):struct.pack_into('<H',keymap,i*54,3)
            command=b'D:\\CHILD.COM /OWNED'
            if name=='ui-readonly-retry':command=b'D:\\ATTRCLR.COM'
            struct.pack_into('<H',keymap,0,1);keymap[2:2+len(command)]=command
            files.update({'CHILD.COM':child.read_bytes(),'TEST.KEY':bytes(keymap)})
            if name=='ui-readonly-retry':files['ATTRCLR.COM']=(output/'ATTRCLR.COM').read_bytes()
            options['arguments']='@D:\\TEST.PRM /D:CaseTest:23 /T:D:\\TEST.KEY'
        if name=='ui-recovery':
            files['CLOSEFLT.COM']=close_fault.read_bytes();options['auxiliary']=('CLOSEFLT',)
        if name in ('ui-short-retry', 'ui-write-error-retry', *IO_CASES):
            helper = {'ui-short-retry':'SHORT', 'ui-write-error-retry':'WRERR',
                      'ui-commit-retry':'COMMIT', 'ui-rollback-truncate':'RBTRUNC',
                      'ui-rollback-commit':'RBCOMMIT'}[name]
            files[helper+'.COM'] = (output/(helper+'.COM')).read_bytes()
            options['auxiliary'] = (helper,)
        expected_exit = 12 if (calls and not disk) or recovery_case or name in ('fs-failure','ui-cancel','ui-unrepaired','ui-readonly-cancel') else 0
        native = terminal.run(case, mode, 'p900 enter ' + keys, prm=bytes(settings),
            files=files, observer='PLWATCH', working_drive='d',
            expected=expected_exit, cpu='8086', **options)
        captured = (folder / 'PLSTATE.BIN').read_bytes()
        assert len(captured) == 20+8*record_bytes+(2 if disk else 0)+(4000 if controls else 0)
        header = struct.unpack_from('<10H', captured)
        final = captured[20 + (header[2] - 1) * record_bytes:20 + header[2] * record_bytes]
        identity, number = (b'LAB NODE 001', b'') if selected else (b'MODEM', b'CaseTest:23')
        if disk:
            ui_flags=struct.unpack_from('<H',captured,20+8*record_bytes)[0]
            acks=struct.unpack_from('<H',final,720)[0] if controls else 0
            attempts, disk_status = struct.unpack_from('<2H', final, 716)
            samples=[captured[20+i*record_bytes:20+(i+1)*record_bytes] for i in range(header[2])]
            if recovery_case:
                meta=struct.unpack_from('<6H',final);life=final[12:50];queue=final[50:716]
                start_count=struct.unpack_from('<H',queue,106)[0]
                original_start=queue[114:114+start_count]
                heading=b'\r\nNAME                                NUMBER    DATE    ONLINE  OFFLINE  ELAPSED'
                checks=dict(final_kind=meta[0]==2,actual_recovery=meta[2]==8 and disk_status==8,
                    no_blind_retry=attempts==1 and acks==0,
                    queue_recovery_preserved=struct.unpack_from('<9H',queue)==(0x514d,0,1,0,1,1,1,1,9 if name=='ui-recovery' else 7),
                    original_generation_preserved=struct.unpack_from('<3I',queue,18)==(1,0,0),
                    retained_END=struct.unpack_from('<I',life,2)[0]==1 and struct.unpack_from('<4H',life,6)==(1,1,0,8),
                    partial_file_exact=(folder/'PCPLUS.FON').read_bytes()==(
                        heading+original_start if name=='ui-recovery' else seed+original_start[:7] if name=='ui-rollback-truncate' else seed),
                    uncertain_handle_blocks_child=not (folder/'HANDOFF.BIN').exists() and not (folder/'HANDARG.BIN').exists())
                if name=='ui-recovery':
                    fault=struct.unpack('<6H',(folder/'CLOSE.BIN').read_bytes())
                    checks['real_close_then_error']=fault[0]==0x4346 and fault[1:3]==(1,1) and not (fault[4]&1)
                else:
                    fault=struct.unpack('<9H',(folder/'WRITE.BIN').read_bytes())
                    checks['real_partial_write_then_failed_rollback']=fault[:4]==(0x5746,1,64,7) and not (fault[4]&1) and fault[5:]==(0xffff,1,1,int(name=='ui-rollback-commit'))
                rows=[]
            elif name in ('fs-failure','ui-cancel','ui-unrepaired','ui-readonly-cancel'):
                checks, rows = inspect_record(final, calls, enabled, identity, number)
                checks.update(queue_flags=struct.unpack_from('<9H',final,50)==(0x514d,0,1,0,2,0,1,0,4),
                    final_status=struct.unpack_from('<H',final,4)[0]==9,
                    bounded_failed_polls=attempts==(2 if name=='ui-unrepaired' else 1) and disk_status==9,
                    namespace_preserved=(folder/'PCPLUS.FON').read_bytes()==seed if name=='ui-readonly-cancel' else
                        (folder/'PCPLUS.FON').is_dir() and (folder/'PCPLUS.FON'/'KEEP.BIN').read_bytes()==b'OWNED NAMESPACE FAULT')
            else:
                data=(folder/'PCPLUS.FON').read_bytes() if (folder/'PCPLUS.FON').is_file() else None
                normalized = HEADING + data[len(seed):] if seed else data
                checks, rows = inspect_disk_record(final, calls, enabled, identity, number, normalized)
                checks['one_poll_per_record']=attempts==calls*2+int(retry_case) and disk_status==0
                if seed is not None:
                    checks.update(existing_prefix_preserved=data.startswith(seed),
                        exact_physical_append=len(data)==len(seed or HEADING)+calls*81,
                        heading_not_duplicated=data.count(HEADING)==1)
                if name in ('ui-short-retry', 'ui-write-error-retry', 'ui-commit-retry'):
                    fault = struct.unpack('<9H', (folder/'WRITE.BIN').read_bytes())
                    before_ack = [r for r in samples if struct.unpack_from('<H', r, 720)[0] == 0
                                  and struct.unpack_from('<2H', r, 716) == (1, 9)]
                    checks.update(first_data_write_observed=fault[0]==0x5746 and fault[1:4]==(1,64,64 if name=='ui-commit-retry' else 7) and not (fault[4]&1),
                        rollback_truncate_and_commit=fault[6:]==(3,1,4 if name=='ui-commit-retry' else 3),
                        rollback_verified_before_retry=native['checks'].get('owned_online_actions_run') is True,
                        original_timestamp_not_replaced=bool(before_ack) and all(r[26:38]==final[26:38] for r in before_ack),
                        retained_START_saved_exactly=bool(before_ack) and all(
                            struct.unpack_from('<HHI', r, 156)==(64,1,1) and data[len(seed):len(seed)+64]==r[164:228]
                            for r in before_ack))
                online_commits=[struct.unpack_from('<I',r,76)[0] for r in samples if struct.unpack_from('<H',r,18)[0]==1]
                if calls and name not in ('capacity','none'):
                    checks['foreground_append_while_online']=any(n>=1 for n in online_commits)
                if name == 'none':checks['online_NONE_deferred']=bool(online_commits) and all(n==0 for n in online_commits)
            if name in ('soft','both','fs-failure'):
                wire=(folder/'serial.bin').read_bytes()
                checks['software_pause_resumed']=wire.count(b'\x13')>=1 and wire.count(b'\x13')==wire.count(b'\x11')
        else:
            checks, rows = inspect_record(final, calls, enabled, identity, number)
        screen = (folder / 'SCREEN.BIN').read_bytes()[::2]
        checks.update(normal_terminal=native['passed'], observer_final=header[0] == 0x4c45 and header[1] > 0 and 0 < header[2] <= 8 and header[3] == 1,
            actual_live_segments=header[4] > 0 and header[5] != header[6],
            actual_exit=header[9] == expected_exit,
            expected_log_files=set(p.relative_to(folder).as_posix() for p in folder.rglob('*.FON')) == ({'PCPLUS.FON'} if calls and disk else set()),
            unsaved_notice=(b'Call log pending; records were not saved.' in screen) == bool(expected_exit==12))
        if name == 'program':
            handoff=(folder/'HANDOFF.BIN').read_bytes() if (folder/'HANDOFF.BIN').exists() else b''
            before=(folder/'BEFORE.BIN').read_bytes()
            checks.update(child_with_released_UART=len(handoff)==10 and handoff[:4]==before[16:20] and handoff[5]==0 and handoff[6]&3==1,
                child_arguments=(folder/'HANDARG.BIN').is_file() and (folder/'HANDARG.BIN').read_bytes()==b'\x07 /OWNED\r',
                child_returned_to_same_call=b'ready' in (folder/'serial.bin').read_bytes())
        if name in ('fs-failure','ui-cancel','ui-unrepaired'):
            checks['retry_notice_observed']=bool(ui_flags&1)
        if args.permissions:
            attr=struct.unpack('<8H',(folder/'ATTR.BIN').read_bytes())
            checks.update(real_readonly_change=attr[:2]==(0x414c,0) and attr[2]>=2 and attr[3]==1
                and not(attr[4]&1) and attr[5]&1==1 and attr[6]==0,
                final_access_observed=bool(attr[7]&1)==(name=='ui-readonly-cancel'),
                retry_notice_observed=bool(ui_flags&1))
            if name=='ui-readonly-retry':
                cleared=struct.unpack('<3H',(folder/'CLEAR.BIN').read_bytes())
                before_ack=[r for r in samples if struct.unpack_from('<H',r,720)[0]==0
                            and struct.unpack_from('<2H',r,716)==(1,9)]
                checks.update(real_DOS_child_cleared_readonly=cleared[0]==0x4143 and cleared[1]&1==1 and not(cleared[2]&1),
                    original_file_verified_before_ack=native['checks'].get('owned_online_actions_run') is True,
                    original_timestamp_not_replaced=bool(before_ack) and all(r[26:38]==final[26:38] for r in before_ack),
                    retained_START_saved_exactly=bool(before_ack) and all(
                        struct.unpack_from('<HHI',r,156)==(64,1,1) and data[len(seed):len(seed)+64]==r[164:228]
                        for r in before_ack))
        if controls:
            checks['explicit_retry_acks']=acks==int(retry_case or name=='ui-unrepaired')
        if name.startswith('ui-'):
            frame=captured[-4000:]
            (folder/'CONTROL.BIN').write_bytes(frame)
            chars=frame[::2]
            checks.update(actual_control_pane=bool(ui_flags&2) and b'Telephone call log' in chars,
                fixed_destination_visible=(b'D:\\PCPLUS.FON' in chars)==(name!='ui-disabled'),
                local_menu_keys_not_sent=(folder/'serial.bin').read_bytes().replace(b'\x11',b'').replace(b'\x13',b'')==b'ATZ\rATDCaseTest:23\r\x1b[1;16R\x1b[?1;2c'+(b'fix\r' if retry_case else b'')+b'+++ATH\r')
            if name=='ui-disabled':checks['disabled_retry_refused']=b'Logging is disabled' in chars and not (ui_flags&4) and not (ui_flags&8)
            if name=='ui-ready':checks['healthy_retry_refused']=bool(ui_flags&32) and not (ui_flags&4)
            if name in ('ui-cancel','ui-readonly-cancel'):checks['confirmation_cancelled']=bool(ui_flags&4) and bool(ui_flags&16) and not (ui_flags&8)
            if retry_case or name=='ui-unrepaired':
                checks['confirmed_ack_visible']=bool(ui_flags&4) and bool(ui_flags&8)
                checks['ack_enqueued_no_disk_IO']=any(struct.unpack_from('<H',r,720)[0]==1 and struct.unpack_from('<H',r,716)[0]==1 for r in samples)
            if recovery_case:checks['recovery_retry_refused']=bool(ui_flags&64) and not (ui_flags&4) and not (ui_flags&8)
            if retry_case:checks['repaired_original_timestamp_saved']=all(r['valid'] for r in rows)
        if name == 'capacity':
            checks['capacity_refusal_visible'] = (b'Call log blocked' in screen) == (not disk)
        results.append(dict(case=name, passed=all(checks.values()), checks=checks,
            observer_header=header, final_metadata=list(struct.unpack_from('<6H', final)), records=rows, native=native))
        artifacts.update({str(p.relative_to(ROOT)): sha(p) for p in folder.rglob('*') if p.is_file()})
        print(name, 'PASS' if results[-1]['passed'] else 'FAIL', flush=True)
    checks = dict(all_cases=bool(results) and all(r['passed'] for r in results), sources_unchanged=all(sha(ROOT / n) == d for n, d in sources.items()),
        binary_unchanged=sha(binary) == manifest['binary_sha256'])
    result = dict(passed=all(checks.values()), disk_scheduling=disk, checks=checks, cases=results, sources=sources,
        existing_files_before_startup=bool(args.preexisting or args.io_failures or args.permissions), io_failure_matrix=args.io_failures,
        permissions_matrix=args.permissions,
        terminal_sha256=sha(binary), observer_defines=defines, artifacts=artifacts, original_inputs=[],
        scope=__doc__ + ' Stable passive observer snapshots at parent INT21/4C before deallocation; no synthesized terminal replies. The separate uncertain-close fixture performs a real DOS close then explicitly changes its returned error/CF, without patching product variables or executable bytes. '
        + ('Permissions fixtures change and query real DOS attributes; a real DOS child clears read-only before confirmed retry. No synthetic filesystem return for permission cases. ' if args.permissions else '')
        + ('The separate existing-file matrix includes real seven-byte writes, short-count/error returns, real rollback and confirmed retry; owned serial callbacks inspect the physical file before acknowledgement. ' if args.existing else '')
        + ('Checked log persistence with foreground/shutdown composition. ' if disk else 'RAM events only: nonempty logs deliberately fail shutdown with error12 until a disk scheduler is added. ')
        + 'These cases do not prove physical DCD, failed-hangup continuity, child-clock ownership, power-loss durability or sustained transport.')
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=result['passed'], checks=checks, failed=[r for r in results if not r['passed']]), indent=2))
    assert result['passed']


if __name__ == '__main__':
    main()
