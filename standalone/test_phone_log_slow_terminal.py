#!/usr/bin/env python3
"""Actual DOS delayed log writes, bounded in-flight bytes and paced ANSI traffic."""
import argparse,json,re,struct,subprocess
from pathlib import Path
import test_connection_dos as terminal
from build_phone_log_queue import ROOT,sha
from modem_fixtures import fixture
from test_phone_log_events_terminal import HEADING,OLD_CALL,inspect_disk_record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terminal',type=Path,required=True)
    parser.add_argument('--label',required=True)
    parser.add_argument('--case',choices=['soft-9','both-36','none-36'])
    args=parser.parse_args();assert re.fullmatch('[a-z0-9-]+',args.label)
    parent=args.terminal.resolve();manifest=json.loads((parent/'manifest.json').read_text())
    assert manifest['experimental_phone_log_controls']
    binary=parent/'TERMINAL.EXE';assert sha(binary)==manifest['binary_sha256'];terminal.BINARY=binary
    symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(
        r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',(parent/'terminal.map').read_text(),re.M|re.I)}
    defines=dict(IRQ_VECTOR=12,ISR_SEGMENT=symbols['uart_receive_interrupt'][0],ISR_OFFSET=symbols['uart_receive_interrupt'][1],
        DATA_SEGMENT=symbols['_terminal_phone_log_event_status'][0],EVENT_STATUS_OFFSET=symbols['_terminal_phone_log_event_status'][1],
        EPOCH_OFFSET=symbols['_terminal_phone_log_event_epoch'][1],LIFECYCLE_OFFSET=symbols['_phone_log_lifecycle_store'][1],
        QUEUE_SEGMENT=symbols['_phone_log_queue_store'][0],QUEUE_OFFSET=symbols['_phone_log_queue_store'][1],
        CONNECTION_STATE_OFFSET=symbols['connection_state'][1],CONNECTION_STATUS_OFFSET=symbols['connection_status'][1],
        STARTUP_STATUS_OFFSET=symbols['_terminal_phone_log_startup_status'][1],
        DISK_ATTEMPTS_OFFSET=symbols['_terminal_phone_log_disk_attempts'][1],DISK_STATUS_OFFSET=symbols['_terminal_phone_log_disk_status'][1],
        CONTROL_ACK_OFFSET=symbols['_terminal_phone_log_retry_acks'][1])
    slow_defines=dict(HARDWARE_ACTIVE_OFFSET=symbols['hardware_active'][1],RX_COUNT_OFFSET=symbols['uart_rx_count'][1],
                      RX_DROPPED_OFFSET=symbols['uart_rx_dropped'][1])
    assert all(symbols[n][0]==defines['DATA_SEGMENT'] for n in ('hardware_active','uart_rx_count','uart_rx_dropped'))
    output=ROOT/'build/phone-log-slow-terminal'/args.label;assert not output.exists();output.mkdir(parents=True)
    observer=output/'PLWATCH.COM'
    subprocess.run(['nasm','-fbin',*[f'-D{k}={v}' for k,v in defines.items()],str(ROOT/'standalone/phone_log_events_watch.asm'),'-o',str(observer)],check=True)
    sources=dict(manifest['sources'])
    for name in ['standalone/test_phone_log_slow_terminal.py','standalone/phone_log_slow_write.asm','standalone/phone_log_events_watch.asm',
                 'standalone/test_connection_dos.py','standalone/test_phone_log_events_terminal.py','standalone/modem_fixtures.py',
                 'standalone/directory_fixtures.py','standalone/directory_test_support.py','standalone/terminal_config_fixtures.py','standalone/test_terminal.py']:
        sources[name]=sha(ROOT/name)
    chunks=[];replies=[];last_rows={}
    for frame in range(3):
        for row in range(2,18):
            text=(f'FRAME {frame:02d} ROW {row:02d} '.encode()+bytes(65+(frame+row+i)%26 for i in range(79)))[:79]
            chunks.append(f'\x1b[{row};1H'.encode()+text+b'\x1b[6n')
            replies.append(f'\x1b[{row};80R'.encode());last_rows[row]=text
    expected_screen=bytearray(b' '*1920);expected_screen[:15]=b'FIRST BYTE SAFE'
    for row,text in last_rows.items():expected_screen[(row-1)*80:(row-1)*80+79]=text
    results=[];artifacts={}
    for name,ticks,soft,hard in [('soft-9',9,1,0),('both-36',36,1,1),('none-36',36,0,0)]:
        if args.case and name!=args.case:continue
        helper=output/(name+'.com')
        subprocess.run(['nasm','-fbin',f'-DDELAY_TICKS={ticks}',*[f'-D{k}={v}' for k,v in slow_defines.items()],
                        str(ROOT/'standalone/phone_log_slow_write.asm'),'-o',str(helper)],check=True)
        folder=ROOT/'build/connection-dos'/(args.label+'-'+name);assert not folder.exists();folder.mkdir(parents=True)
        seed=HEADING+OLD_CALL;(folder/'PCPLUS.FON').write_bytes(seed)
        settings=bytearray(fixture(timeout=5));struct.pack_into('<HH',settings,0x4e4,8,4)
        struct.pack_into('<H',settings,0x1e6,1);struct.pack_into('<HH',settings,0x198,soft,hard)
        inflight=b''.join(chunks[:4]) if soft else b''
        scheduled=chunks[4:] if soft else chunks
        native=terminal.run(args.label+'-'+name,'success','p900 enter p11000 w o r k enter p700 a-x',
            prm=bytes(settings),files={'PLWATCH.COM':observer.read_bytes(),'SLOWLOG.COM':helper.read_bytes()},
            observer='PLWATCH',auxiliary=('SLOWLOG',),working_drive='d',cpu='8086',timeout=22,
            flow_updates=tuple((.3+i*.07,chunk) for i,chunk in enumerate(scheduled)),flow_inflight=inflight)
        captured=(folder/'PLSTATE.BIN').read_bytes();assert len(captured)==9798
        header=struct.unpack_from('<10H',captured);final=captured[20+(header[2]-1)*722:20+header[2]*722]
        data=(folder/'PCPLUS.FON').read_bytes()
        checks,records=inspect_disk_record(final,1,1,b'MODEM',b'CaseTest:23',HEADING+data[len(seed):])
        delay=struct.unpack('<16H',(folder/'SLOW.BIN').read_bytes())
        attempts,status,acks=struct.unpack_from('<3H',final,716)
        flow=json.loads((folder/'flow-state.json').read_text())
        wire=(folder/'serial.bin').read_bytes();clean=wire.replace(b'\x11',b'').replace(b'\x13',b'')
        samples=[captured[20+i*722:20+(i+1)*722] for i in range(header[2])]
        online=[struct.unpack_from('<I',sample,76)[0] for sample in samples if struct.unpack_from('<H',sample,18)[0]==1]
        checks.update(native_terminal=native['passed'],existing_prefix_preserved=data.startswith(seed) and len(data)==len(seed)+81,
            delayed_real_write=delay[0:3]==(0x534c,1,ticks) and delay[3]>=ticks and delay[10]==64 and not(delay[11]&1),
            interrupts_enabled=bool(delay[4]&0x200) and bool(delay[14]&0x200),
            no_receive_drops=delay[8]==delay[9]==0,real_parent_DS=delay[15]==header[5],
            intended_UART_ownership=delay[5]==int(bool(soft)),
            in_flight_received_during_write=delay[7]>delay[6] if soft else delay[7]==0,
            RTS_low_during_BOTH=not(delay[13]&2) if hard else True,
            exact_ANSI_glyphs=(folder/'SCREEN.BIN').read_bytes()[:3840:2]==expected_screen,
            exact_ANSI_attributes=(folder/'SCREEN.BIN').read_bytes()[1:3840:2]==bytes([7])*1920,
            exact_every_cursor_reply_and_keyboard=clean==b'ATZ\rATDCaseTest:23\r\x1b[1;16R\x1b[?1;2c'+b''.join(replies)+b'work\r+++ATH\r',
            all_sent_bytes_exact=(folder/'flow-payload.bin').read_bytes()==b''.join(chunks),
            bounded_burst_sent_during_pause=any(s['kind']=='bounded-inflight' and s['paused'] for s in flow['sends'])==bool(soft),
            independent_pause_intervals=all(not [e for e in flow['events'] if e['at']<=s['at']]
                or [e for e in flow['events'] if e['at']<=s['at']][-1]['byte']==0x11
                for s in flow['sends'] if s['kind']=='scheduled'),
            balanced_flow=wire.count(b'\x13')==wire.count(b'\x11') and (wire.count(b'\x13')>=1)==bool(soft),
            no_automatic_retries=(attempts,status,acks)==(2,0,0),
            observed_commit_policy=any(n>=1 for n in online) if soft else bool(online) and all(n==0 for n in online),
            observer_final=header[0]==0x4c45 and header[3]==1 and header[9]==0)
        results.append(dict(case=name,passed=all(checks.values()),checks=checks,native=native,slow_snapshot=list(delay),
                            observer_header=list(header),records=records,flow=flow))
        artifacts.update({str(p.relative_to(ROOT)):sha(p) for p in folder.rglob('*') if p.is_file()})
        print(name,'PASS' if results[-1]['passed'] else 'FAIL',flush=True)
    checks=dict(all_cases=bool(results) and all(r['passed'] for r in results),sources_unchanged=all(sha(ROOT/n)==h for n,h in sources.items()),
                binary_unchanged=sha(binary)==manifest['binary_sha256'])
    report=dict(passed=all(checks.values()),checks=checks,cases=results,sources=sources,artifacts=artifacts,terminal_sha256=sha(binary),
                original_inputs=[],scope=__doc__+' Real DOS write delayed by an active fixture; no product RAM patches or synthesized terminal replies. '
                'Paced synthetic serial peer, bounded in-flight burst and selected final screen; not physical RTS, arbitrary disk latency, every ANSI frame or file-transfer acceptance.')
    (output/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':report['passed'],'failed':[{k:v for k,v in r['checks'].items() if not v} for r in results if not r['passed']]}))
    assert report['passed']

if __name__=='__main__':main()
