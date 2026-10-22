#!/usr/bin/env python3
"""Actual DOS native confirmation under9114 paced ANSI bytes and44 CPRs."""
import json,socket,struct,sys,types
from pathlib import Path
import test_aspect_keys_dos as keys
import test_aspect_window_pressure_dos as pressure
from test_aspect_window_query_dos import TracedSocket
from test_aspect_abort_confirm_dos import confirmation_observer

ROOT=keys.ROOT;BASE=ROOT/'build/aspect-abort-pressure-dos'

def definitions():
    case=pressure.definitions()[0]
    case['name']='abort-pressure'
    case['source']=case['source'].replace('waitfor "END" 30','waitfor "NEVER" 30\nif waitfor\ntransmit "BADMATCH"\nelse\ntransmit "DECLINED"\nendif\nwaitfor "END" 30',1)
    case['keys']='p1800 escape p7500 n p300 d o n e p2500 space p700 r e a d y p700 a-x'
    case['key_wire']=b''.join(p['reply'] for p in pressure.packets())+b'DECLINEDdone'
    return [case]

def main():
    original=keys.adapter;events=[];workload=pressure.packets()
    def adapter():
        module=original();run=module.run
        module.socket=types.SimpleNamespace(socket=lambda:TracedSocket(socket.socket(),events),timeout=socket.timeout)
        def staged(*args,**kwargs):
            kwargs['online_updates']=[(p['scheduled'],p['payload']) for p in workload]
            return run(*args,**kwargs)
        module.run=staged;return module
    keys.OUT=BASE;keys.definitions=definitions;keys.adapter=adapter
    keys.renderer.observer=confirmation_observer(keys.renderer.observer)
    folder=BASE/sys.argv[sys.argv.index('--label')+1]
    try:keys.main()
    finally:
        if folder.exists():(folder/'peer-events.json').write_text(json.dumps(events,indent=2)+'\n')
    report=json.loads((folder/'checks.json').read_text());case=report['cases'][0];target=folder/case['case']
    wire=(target/'serial.bin').read_bytes();assert wire==b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive')
    screen=(target/'SCREEN.BIN').read_bytes();raw=(target/'RENDER.BIN').read_bytes();observation=struct.unpack('<4H',raw[-8:])
    cells=[];colors=[];delays=[];completions=[];declined=None;received=b''
    for event in events:
        if event['kind']=='receive':
            received+=bytes.fromhex(event['hex'])
            if declined is None and b'DECLINED' in received:declined=event['time']
    for packet in workload:
        at=2*((packet['row']-1)*80+packet['column']-1)
        cells.append(screen[at:at+64:2]==packet['text']);colors.append(screen[at+1:at+64:2]==bytes([4,2]*16))
        sent=[e for e in events if e['kind']=='send' and e['hex']==packet['payload'].hex()];assert len(sent)==1
        received=b'';completion=None
        for event in events:
            if event['kind']=='receive' and event['time']>=sent[0]['time']:
                received+=bytes.fromhex(event['hex'])
                if packet['reply'] in received:completion=event['time'];break
        completions.append(completion)
        delays.append(None if completion is None else completion-sent[0]['time'])
    checks=dict(functional_wire_wait_screen_and_cleanup=report['passed'],
        actual_owned_prompt=observation[2]==1 and observation[3]>72,render_advances_under_prompt=observation[1]==1,
        all1408_characters=all(cells),all1408_attributes=all(colors),all44_replies_before_decline=declined is not None and all(t is not None and t<declined for t in completions),
        all44_replies_within_one_second=all(d is not None and 0<=d<=1 for d in delays))
    result=dict(passed=all(checks.values()),checks=checks,payload_bytes=sum(len(p['payload']) for p in workload),
        packet_reply_delay_seconds=delays,confirmation_observation=observation,
        parent_sha256=report['terminal_sha256'],runner_sha256=report['runner_sha256'],checker_sha256=keys.renderer.sha(Path(__file__)),
        reused_workload_sha256=keys.renderer.sha(Path(pressure.__file__)),
        captures_sha256={str(p.relative_to(folder)):keys.renderer.sha(p) for p in folder.rglob('*') if p.is_file()},scope=__doc__+' Transparent emulated UART; no actual CTS/RTS/XOFF/XON or physical acceptance.')
    (folder/'confirmation-checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(checks))
    return 0 if result['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
