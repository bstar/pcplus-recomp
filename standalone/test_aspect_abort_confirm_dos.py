#!/usr/bin/env python3
"""Actual DOS declined script abort, active-wait result and live CPR timing."""
import json,socket,struct,sys,types
from pathlib import Path
import test_aspect_keys_dos as keys
from test_aspect_script_window_dos import symbols
from test_aspect_window_query_dos import TracedSocket

ROOT=keys.ROOT
BASE=ROOT/'build/aspect-abort-confirm-dos'
ESC=b'\x1b';QUERY=ESC+b'[6n';REPLY=ESC+b'[1;22R'

def definitions():
    source=('proc main\nwaitfor "LOGIN:" 5\nset duplex full\ntransmit "KEYREADY"\n'
            'waitfor "NEVER" 30\nif waitfor\ntransmit "BADMATCH"\nelse\ntransmit "DECLINED"\nendif\n'
            'waitfor "FRESH" 20\nif waitfor\ntransmit "FRESHOK"\nendif\n'
            'waitfor "END" 30\nif waitfor\ntransmit $D_PWORD\ntransmit "^M"\npause 1\nendif\nendproc\n')
    case=dict(name='abort-No',source=source,profile=4,bios_policy='STANDARD',custom=False,success=True,
        banner=ESC+b'[2J'+ESC+b'[HFIRST BYTE SAFE'+QUERY+ESC+b'[0cLOGIN:',
        keys='p1800 escape p4500 n p1800 d o n e p2500 space p700 r e a d y p700 a-x',
        key_wire=REPLY+b'DECLINEDFRESHOKdone',post=QUERY,post_reply=ESC+b'[1;30R',extra_reply=REPLY,
        screen=[(0,0,'FIRST BYTE SAFE'),(0,21,'FRESHEND')])
    cases=[]
    for name,answer,profile,mode in [('No','n',4,'STANDARD'),('Enter','enter',4,'STANDARD'),('Escape','escape',6,'ENHANCED'),('invalid-extended','f1 p200 x p200 n',4,'ENHANCED')]:
        item=dict(case);item.update(name='abort-'+name,profile=profile,bios_policy=mode,
            keys=case['keys'].replace('p4500 n','p4500 '+answer))
        # Invalid keys delay the final answer; FRESH still arrives afterwards.
        cases.append(item)
    return cases

def confirmation_observer(original):
    parent=symbols(ROOT/'build/terminal/terminal.map')
    def observer(offsets):
        result=original(offsets);out=keys.renderer.OUT;path=out/'observer.asm';text=path.read_text()
        text=text.replace('sample_end:\nowner_table:','confirmation_first_render: dw 0\nconfirmation_render_advanced: dw 0\nconfirmation_seen: dw 0\nconfirmation_ticks: dw 0\nsample_end:\nowner_table:')
        timer='''timer:
 save
 cld
 mov ax,0xb800
 mov es,ax
 mov di,2*(2*80+6)
 mov si,confirmation_title
.confirm_title:
 mov al,[cs:si]
 inc si
 or al,al
 jz .confirm_owner
 cmp al,[es:di]
 jne .confirm_finished
 add di,2
 jmp .confirm_title
.confirm_owner:
 mov ax,[cs:parent_psp]
 or ax,ax
 jz .confirm_finished
 add ax,CONFIRM_CS+0x10
 mov es,ax
 cmp word [es:CONFIRM_ACTIVE],1
 jne .confirm_finished
 inc word [cs:confirmation_ticks]
 mov ax,[es:RENDER_STARTED]
 cmp word [cs:confirmation_seen],0
 jne .confirm_compare
 mov [cs:confirmation_first_render],ax
 mov word [cs:confirmation_seen],1
.confirm_compare:
 cmp ax,[cs:confirmation_first_render]
 je .confirm_finished
 mov word [cs:confirmation_render_advanced],1
.confirm_finished:
'''
        assert parent['terminal_script_confirm_active'][0]==parent['render_started'][0]
        for token,value in [('CONFIRM_CS',parent['terminal_script_confirm_active'][0]),('CONFIRM_ACTIVE',parent['terminal_script_confirm_active'][1]),('RENDER_STARTED',parent['render_started'][1])]:timer=timer.replace(token,str(value))
        assert text.count('timer:\n save\n cld\n')==1
        text=text.replace('timer:\n save\n cld\n',timer)
        text=text.replace('resident_end:\nstart:',"confirmation_title: db ' PCPLUS  //  STOP SCRIPT? ',0\nresident_end:\nstart:")
        path.write_text(text)
        import subprocess
        subprocess.run(['nasm','-fbin',str(path),'-o',str(out/'RENDER.COM')],check=True)
        return ((out/'RENDER.COM').read_bytes(),*result[1:])
    return observer

def main():
    original=keys.adapter;streams={}
    def adapter():
        module=original();run=module.run;events=[]
        module.socket=types.SimpleNamespace(socket=lambda:TracedSocket(socket.socket(),events),timeout=socket.timeout)
        def staged(*args,**kwargs):
            nonlocal events
            events=[]
            streams[args[0]]=events
            kwargs['online_updates']=[(3.0,QUERY),(6.5,b'FRESH')]
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
        results.append(check_case(folder,case,streams[case['case']]))
    result=dict(passed=all(case['passed'] for case in results),cases=results,
        parent_sha256=report['terminal_sha256'],runner_sha256=report['runner_sha256'],
        checker_sha256=keys.renderer.sha(Path(__file__)),
        captures_sha256={str(p.relative_to(folder)):keys.renderer.sha(p) for p in folder.rglob('*') if p.is_file()},scope=__doc__)
    (folder/'confirmation-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['cases']))
    return 0 if result['passed'] else 1

def check_case(folder,case,events):
    wire=b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive')
    assert wire==(folder/case['case']/'serial.bin').read_bytes(),'Each timing stream must belong to exactly this DOS case'
    assert sum(e['kind']=='send' and bytes.fromhex(e['hex']).startswith(b'CONNECT') for e in events)==1
    sent=[e for e in events if e['kind']=='send' and e['hex']==QUERY.hex()]
    assert len(sent)==2
    assert sent,'Preserve a peer failure separately from a product result'
    received=b'';response=None
    for e in events:
        if e['kind']=='receive' and e['time']>=sent[0]['time']:
            received+=bytes.fromhex(e['hex'])
            if REPLY in received:response=e['time'];break
    delay=None if response is None else response-sent[0]['time']
    raw=(folder/case['case']/'RENDER.BIN').read_bytes()
    header=struct.unpack_from('<7H',raw)
    observation=struct.unpack('<4H',raw[-8:])
    checks=dict(functional_wait_wire_screen_and_cleanup=case['passed'],
        actual_child_normal_exit=header[6]==0,query_reply_within_one_second=delay is not None and 0<=delay<=1,
        prompt_seen_with_actual_parent_owner=observation[2]==1,prompt_visible_over_one_second=observation[3]>18,
        actual_render_advances_while_prompt_visible=observation[1]==1)
    result=dict(passed=all(checks.values()),checks=checks,child_exit=header[6],reply_delay_seconds=delay,
        case=case['case'],confirmation_observation=observation)
    return result

if __name__=='__main__':raise SystemExit(main())
