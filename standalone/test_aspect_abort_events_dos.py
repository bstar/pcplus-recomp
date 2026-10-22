#!/usr/bin/env python3
"""Actual DOS confirmation with native WHEN TX/CALL and a suspended RGET."""
import json,socket,struct,sys,types
from pathlib import Path
import test_aspect_keys_dos as keys
from test_aspect_window_query_dos import TracedSocket
from test_aspect_abort_confirm_dos import confirmation_observer

ROOT=keys.ROOT;BASE=ROOT/'build/aspect-abort-events-dos'
ESC=b'\x1b';QUERY=ESC+b'[6n';REPLY=ESC+b'[1;26R'

def definitions():
    cases=[]
    for name,register,wait,after,helper,before,following,marker in [
        ('WHEN-TX','when 0 "WAKE" transmit "EVENT"','waitfor "NEVER" 30','transmit "DECLINED"','',b'EVENT',b'DECLINED',b'WAKE'),
        ('WHEN-CALL','when 0 "WAKE" call worker','waitfor "NEVER" 30','transmit "DECLINED"',
         'proc worker\ninteger local_value\nlocal_value=37\nif local_value == 37\ntransmit "FRAME"\nelse\ntransmit "BADFRAME"\nendif\nendproc\n',b'',b'FRAMEDECLINED',b'WAKE'),
        ('RGET','','rget buffer 80 30','strcmp buffer ""\nif success\ntransmit "RGETEMPTY"\nelse\ntransmit "BADBUFFER"\nendif','',b'',b'RGETEMPTY',b'DATA')]:
        source=('string buffer\nproc main\nwaitfor "LOGIN:" 5\nset duplex full\ntransmit "KEYREADY"\n'+register+'\n'+wait+'\n'+after+
            '\nwaitfor "FRESH" 20\nif waitfor\ntransmit "FRESHOK"\nendif\nwaitfor "END" 30\nif waitfor\ntransmit $D_PWORD\ntransmit "^M"\npause 1\nendif\nendproc\n'+helper)
        cases.append(dict(name='abort-'+name,source=source,profile=4,bios_policy='STANDARD',custom=False,success=True,
            banner=ESC+b'[2J'+ESC+b'[HFIRST BYTE SAFE'+QUERY+ESC+b'[0cLOGIN:',
            keys='p1800 escape p4500 n p1800 d o n e p2500 space p700 r e a d y p700 a-x',
            key_wire=before+REPLY+following+b'FRESHOKdone',post=QUERY,post_reply=ESC+b'[1;34R',extra_reply=REPLY,
            screen=[(0,0,'FIRST BYTE SAFE'),(0,21,marker.decode()+'FRESHEND')],marker=marker))
    return cases

def main():
    original=keys.adapter;streams={};specs={c['name']:c for c in definitions()}
    def adapter():
        module=original();run=module.run;events=[]
        module.socket=types.SimpleNamespace(socket=lambda:TracedSocket(socket.socket(),events),timeout=socket.timeout)
        def staged(*args,**kwargs):
            nonlocal events
            events=[];streams[args[0]]=events
            kwargs['online_updates']=[(3.0,specs[args[0]]['marker']+QUERY),(6.5,b'FRESH')]
            return run(*args,**kwargs)
        module.run=staged;return module
    keys.OUT=BASE;keys.definitions=definitions;keys.adapter=adapter
    keys.renderer.observer=confirmation_observer(keys.renderer.observer)
    folder=BASE/sys.argv[sys.argv.index('--label')+1]
    try:keys.main()
    finally:
        for name,events in streams.items():
            if (folder/name).exists():(folder/name/'peer-events.json').write_text(json.dumps(events,indent=2)+'\n')
    report=json.loads((folder/'checks.json').read_text());results=[]
    for case in report['cases']:
        target=folder/case['case'];events=streams[case['case']];wire=(target/'serial.bin').read_bytes()
        assert wire==b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive')
        packet=specs[case['case']]['marker']+QUERY
        sent=[e for e in events if e['kind']=='send' and e['hex']==packet.hex()];assert len(sent)==1
        received=b'';response=None
        for event in events:
            if event['kind']=='receive' and event['time']>=sent[0]['time']:
                received+=bytes.fromhex(event['hex'])
                if REPLY in received:response=event['time'];break
        delay=None if response is None else response-sent[0]['time']
        observation=struct.unpack('<4H',(target/'RENDER.BIN').read_bytes()[-8:])
        checks=dict(functional_WHEN_or_RGET_wire_screen_and_cleanup=case['passed'],
            query_reply_within_one_second=delay is not None and 0<=delay<=1,
            actual_prompt_owned_and_visible=observation[2]==1 and observation[3]>18,
            real_render_advances_under_prompt=observation[1]==1)
        results.append(dict(case=case['case'],passed=all(checks.values()),checks=checks,reply_delay_seconds=delay,confirmation_observation=observation))
    result=dict(passed=all(case['passed'] for case in results),cases=results,
        parent_sha256=report['terminal_sha256'],runner_sha256=report['runner_sha256'],checker_sha256=keys.renderer.sha(Path(__file__)),
        captures_sha256={str(p.relative_to(folder)):keys.renderer.sha(p) for p in folder.rglob('*') if p.is_file()},scope=__doc__)
    (folder/'confirmation-checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(results))
    return 0 if result['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
