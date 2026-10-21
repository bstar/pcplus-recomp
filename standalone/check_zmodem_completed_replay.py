#!/usr/bin/env python3
"""Linked receiver: queued data after checked EOF and queued closing headers.

Independent peer bytes enter the real UART ISR; no product callback is replaced.
The first recipe mirrors the retained audio02 packet lengths/positions. Native
kernel/UART/BIOS boundaries are modeled; this is not an audio acceptance test.
"""
import argparse,hashlib,json
from collections import deque
from pathlib import Path
import check_transport
from check_carrier_transfer_deadline import SlowCarrier
from check_zmodem import h,offer
from check_zmodem_wire import packet

ROOT=Path(__file__).resolve().parents[1]


def run_case(replay,closing):
    body=bytes((i*73+(i>>8)*19)&255 for i in range(11521))
    m=SlowCarrier(38400,body=body,carrier=115200)
    bulk=b''.join(packet(body[a:b],67,end,0) for a,b,end in [(1024,3072,105),(3072,7168,105),(7168,11521,104)])
    stale=b''.join(h(10,1024,67)+packet(body[1024:1024+n],67,107,0) for n in (4096,2048,1024,512,256,128,128,128)) if replay else b''
    duplicate_close=b''.join(h(7 if i%2==0 else 8) for i in range(8)) if closing else b''
    ready=h(1,0x23002000)
    m.script=deque([(ready,offer('ONE.BIN',len(body))),
        (h(9),h(10,0,67)+packet(body[:1024],67,107,0)),
        (h(3,1024),h(10,1024,67)+bulk+h(11,len(body),67)),
        (ready,stale+h(8)),(h(8),duplicate_close+b'OOAPP')])
    fault=m.run(owner=True)
    leftover=bytearray()
    for _ in range(512):
        value=m.call('uart_receive_byte')
        if value==0xffff:break
        leftover.append(value)
    screen=bytes(m.uc.mem_read(0xb8000,4000))[::2]
    checks={'no_fault':fault==0,'exact_single_file':m.files.get('D:\\RECV\\ONE.BIN')==body,
        'checked_create_and_install_once':sum(r['ah']==0x5b for r in m.fs_calls)==sum(r['ah']==0x56 for r in m.fs_calls)==1,
        'handles_closed':not m.handles,'peer_script_completed':not m.script and not m.pending,
        'confirmed_success_notice':b'RX complete' in screen,'only_application_tail_after_owner':leftover==b'APP'}
    return {'case':f'replay-{replay}-closing-{closing}','passed':all(checks.values()),'checks':checks,
        'fault':fault,'actual_wire_hex':bytes(m.tx).hex(),'remaining_peer_steps':len(m.script),
        'post_owner_bytes_hex':leftover.hex(),'finish_unconfirmed_notice':b'finish unconfirmed' in screen}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--counterexample',action='store_true');a=p.parse_args()
    if a.counterexample:
        check_transport.BINARY=ROOT/'build/terminal/completed-replay-baseline/TERMINAL.EXE'
        check_transport.MAP=ROOT/'build/terminal/completed-replay-baseline/terminal.map'
    rows=[run_case(*v) for v in [(True,False),(False,True),(True,True)]]
    if a.counterexample:assert all(not r['passed'] and r['checks']['exact_single_file'] for r in rows),rows
    else:assert all(r['passed'] for r in rows),rows
    result={'passed':not a.counterexample,'counterexample_reproduced':a.counterexample,'cases':rows,
        'binary_sha256':hashlib.sha256(check_transport.BINARY.read_bytes()).hexdigest(),
        'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'scope':'Actual linked receiver, file owners, UART ISR and bounded owner. Peer requires no replies to already committed in-flight data, full closing-header/OO consumption, one install and intact APP tail. Hardware/kernel and carrier pacing modeled. No real audio/BBS or physical acceptance.'}
    name='zmodem-completed-replay-'+('counterexample' if a.counterexample else 'checks')+'.json'
    (ROOT/'build/terminal'/name).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'passed':result['passed'],'counterexample_reproduced':a.counterexample,'cases':[{k:r[k] for k in ('case','passed','checks')} for r in rows]},indent=2))


if __name__=='__main__':main()
