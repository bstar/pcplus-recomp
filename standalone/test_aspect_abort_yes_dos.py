#!/usr/bin/env python3
"""Actual DOS confirmed abort during WAITFOR/PAUSE, with a live prompt query."""
import inspect,json,socket,struct,sys,types
from pathlib import Path
import test_aspect_keys_dos as keys
from test_aspect_window_query_dos import TracedSocket
from test_aspect_abort_confirm_dos import confirmation_observer

ROOT=keys.ROOT;BASE=ROOT/'build/aspect-abort-yes-dos'
ESC=b'\x1b';QUERY=ESC+b'[6n';REPLY=ESC+b'[1;22R'

def definitions():
    return [dict(name='abort-Yes-'+name,source='proc main\nwaitfor "LOGIN:" 5\nset duplex full\ntransmit "KEYREADY"\n'+command+'\ntransmit "UNREACHABLE"\nendproc\n',
        profile=4,bios_policy='STANDARD',custom=False,success=False,cancel=True,
        banner=ESC+b'[2J'+ESC+b'[HFIRST BYTE SAFE'+QUERY+ESC+b'[0cLOGIN:',
        keys='p1800 escape p4500 y p500 space p700 r e a d y p700 a-x',
        extra_reply=REPLY,screen=[(0,0,'FIRST BYTE SAFE')])
        for name,command in [('WAITFOR','waitfor "NEVER" 30'),('PAUSE','pause 30')]]

def main():
    original=keys.adapter;streams={}
    def adapter():
        module=original();run=module.run;events=[]
        module.socket=types.SimpleNamespace(socket=lambda:TracedSocket(socket.socket(),events),timeout=socket.timeout)
        def staged(*args,**kwargs):
            nonlocal events
            events=[];streams[args[0]]=events;kwargs['online_updates']=[(3.0,QUERY)]
            return run(*args,**kwargs)
        module.run=staged;return module
    keys.OUT=BASE;keys.definitions=definitions
    keys.renderer.observer=confirmation_observer(keys.renderer.observer)
    # Reuse the key fixture's renderer adaptation, ending before its special
    # unsupported-key oracle. Confirmed abort requires13, never that oracle's3.
    source=inspect.getsource(keys.main)
    source=source[:source.index(" folder=scope['OUT'];report=")]
    scope=dict(keys.__dict__,OUT=BASE,definitions=definitions,adapter=adapter)
    exec(compile(source,__file__,'exec'),scope)
    folder=BASE/sys.argv[sys.argv.index('--label')+1]
    try:scope['main']()
    finally:
        for name,events in streams.items():
            if (folder/name).exists():(folder/name/'peer-events.json').write_text(json.dumps(events,indent=2)+'\n')
    report=json.loads((folder/'checks.json').read_text());results=[]
    for case in report['cases']:
        target=folder/case['case'];events=streams[case['case']];wire=(target/'serial.bin').read_bytes()
        assert wire==b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive')
        sent=[e for e in events if e['kind']=='send' and e['hex']==QUERY.hex()];assert len(sent)==1
        received=b'';response=None
        for event in events:
            if event['kind']=='receive' and event['time']>=sent[0]['time']:
                received+=bytes.fromhex(event['hex'])
                if REPLY in received:response=event['time'];break
        delay=None if response is None else response-sent[0]['time']
        raw=(target/'RENDER.BIN').read_bytes();header=struct.unpack_from('<7H',raw);observation=struct.unpack('<4H',raw[-8:])
        expected=b'ATZ\rATDCaseTest:23\r'+ESC+b'[1;16R'+ESC+b'[?62;2cKEYREADY'+REPLY+b' ready+++ATH\r'
        checks=dict(functional_parent_and_hardware_cleanup=case['passed'],actual_child_cancelled_13=header[6]==13,
            exact_whole_wire=wire==expected,unreachable_script_tail_absent=b'UNREACHABLE' not in wire,
            query_reply_within_one_second=delay is not None and 0<=delay<=1,
            actual_prompt_owned_and_visible=observation[2]==1 and observation[3]>18,
            real_render_advances_under_prompt=observation[1]==1)
        results.append(dict(case=case['case'],passed=all(checks.values()),checks=checks,reply_delay_seconds=delay,
            confirmation_observation=observation,whole_wire_sha256=keys.renderer.sha(target/'serial.bin')))
    result=dict(passed=all(case['passed'] for case in results),cases=results,
        parent_sha256=report['terminal_sha256'],runner_sha256=report['runner_sha256'],checker_sha256=keys.renderer.sha(Path(__file__)),
        captures_sha256={str(p.relative_to(folder)):keys.renderer.sha(p) for p in folder.rglob('*') if p.is_file()},scope=__doc__)
    (folder/'confirmation-checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(results))
    return 0 if result['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
