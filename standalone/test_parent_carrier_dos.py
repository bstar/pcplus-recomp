#!/usr/bin/env python3
"""Passive parent-state observations around a real modem drop inside ASPECT."""
import argparse,json,re,shutil,struct,subprocess
from pathlib import Path
import test_aspect_abort_carrier_dos as carrier
import test_aspect_renderer_dos as renderer
import test_aspect_script_window_dos as window
from directory_fixtures import directory,prm
ROOT=carrier.ROOT;sha=carrier.sha
FIELDS=['parent_seen_in_child','parent_menu_sampled','parent_menu_state','parent_menu_status',
        'parent_loss_seen_after','parent_OFF_LINE_seen_after','parent_status_samples']


def observer(out):
    compiled,_=carrier.observer(out,ROOT)
    parent=window.symbols(ROOT/'build/terminal/terminal.map')
    # This internal byte follows the exported enabled byte in the owned source.
    source=(ROOT/'src/terminal/connection.asm').read_text()
    assert re.search(r'connection_enabled: db 0\s+connection_carrier_seen: db 0',source)
    path=out/'observer.asm';text=path.read_text()
    assert text.count('sample_end:\nowner_table:')==1
    text=text.replace('sample_end:\nowner_table:',''.join(n+': dw 0\n' for n in FIELDS)+'sample_end:\nowner_table:')
    timer='''timer:
 save
 cld
 cmp word [cs:exec_seen],1
 jne .parent_carrier_done
 mov ax,[cs:parent_ds]
 or ax,ax
 jz .parent_carrier_done
 mov es,ax
 cmp word [cs:exec_done],0
 jne .parent_return
 xor ax,ax
 mov al,[es:CARRIER_SEEN]
 or ax,ax
 jz .parent_carrier_done
 mov [cs:parent_seen_in_child],ax
 jmp .parent_carrier_done
.parent_return:
 ; Only sample the live parent's ordinary stack, not DOS after process exit.
 mov dx,ss
 mov ax,es
 cmp ax,dx
 jne .parent_carrier_done
 inc word [cs:parent_status_samples]
 cmp word [es:CONNECTION_STATE],0
 jne .parent_menu
 cmp word [es:CONNECTION_STATUS],6
 jne .parent_menu
 mov word [cs:parent_loss_seen_after],1
.parent_menu:
 cmp word [es:MENU_ACTIVE],0
 je .parent_status
 mov word [cs:parent_menu_sampled],1
 mov ax,[es:CONNECTION_STATE]
 mov [cs:parent_menu_state],ax
 mov ax,[es:CONNECTION_STATUS]
 mov [cs:parent_menu_status],ax
.parent_status:
 mov ax,0xb800
 mov es,ax
 mov si,parent_offline
 mov di,3840+71*2
 mov cx,8
.parent_status_compare:
 mov al,[cs:si]
 cmp al,[es:di]
 jne .parent_carrier_done
 inc si
 add di,2
 loop .parent_status_compare
 mov word [cs:parent_OFF_LINE_seen_after],1
.parent_carrier_done:
'''
    for token,value in [('CARRIER_SEEN',parent['connection_enabled'][1]+1),('CONNECTION_STATE',parent['connection_state'][1]),('CONNECTION_STATUS',parent['connection_status'][1]),('MENU_ACTIVE',parent['_command_menu_active'][1])]:
        timer=timer.replace(token,str(value))
    assert text.count('timer:\n save\n cld\n')==1;text=text.replace('timer:\n save\n cld\n',timer)
    text=text.replace('resident_end:\nstart:',"parent_offline: db 'OFF-LINE'\nresident_end:\nstart:")
    path.write_text(text);subprocess.run(['nasm','-fbin',str(path),'-o',str(out/'RENDER.COM')],check=True)
    return (out/'RENDER.COM').read_bytes()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True);p.add_argument('--expect-gap',action='store_true');a=p.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+',a.label)
    out=ROOT/'build/parent-carrier-dos'/a.label;out.mkdir(parents=True,exist_ok=False)
    inputs={}
    for d,leaf in [('terminal','TERMINAL.EXE'),('aspect-runner','ASPECT.EXE')]:
        base=ROOT/'build'/d;m=json.loads((base/'manifest.json').read_text());assert m['binary_sha256']==sha(base/leaf)
        inputs.update(m['sources'])
        for f in [base/leaf,base/'manifest.json',*base.glob('*.map')]:inputs[str(f.relative_to(ROOT))]=sha(f)
        shutil.copy2(base/leaf,out/leaf)
    for f in [Path(__file__),Path(carrier.__file__),Path(renderer.__file__),Path(window.__file__),ROOT/'standalone/test_aspect_abort_confirm_dos.py']:
        inputs[str(f.relative_to(ROOT))]=sha(f)
    for name,digest in inputs.items():
        assert sha(ROOT/name)==digest;target=out/'inputs'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    compiled=observer(out);events=[];peer=carrier.adapter(out,events);folder=out/'CALL-No';folder.mkdir()
    peer.BINARY=out/'TERMINAL.EXE'
    payload=bytearray(directory(profile=4));payload[302:311]=b'LOGIN\0\0\0\0'
    settings=bytearray(prm());settings[0x79:0x79+25]=b'ATH^M'.ljust(25,b'\0')
    script=carrier.source('CALL');files={'LOGIN.ASP':script.encode(),'LOGIN.ASX':renderer.compile_source(script),'RENDER.COM':compiled,'ASPECT.EXE':(out/'ASPECT.EXE').read_bytes()}
    try:
        r=peer.run('CALL-No','success','p2200 escape p5000 n p1900 a-z p800 escape p400 a-x',
            directory=bytes(payload),prm=bytes(settings),profile=4,files=files,
            arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /A:NETWORK',working_drive='d',observer='RENDER',
            banner=carrier.ESC+b'[2J'+carrier.ESC+b'[HFIRST BYTE SAFE'+carrier.QUERY+carrier.ESC+b'[0cLOGIN:')
    finally:(folder/'peer-events.json').write_text(json.dumps(events,indent=2)+'\n')
    raw=(folder/'RENDER.BIN').read_bytes();values=struct.unpack('<7H',raw[-14:]);state=dict(zip(FIELDS,values));header=struct.unpack_from('<7H',raw)
    expected=carrier.ESC+b'[1;16R'+carrier.ESC+b'[?62;2cKEYREADY'+carrier.ESC+b'[1;22R'
    assert r['passed'] and (folder/'serial.bin').read_bytes()==expected
    assert header[:4]==(0x524e,1,1,1) and header[6]==0
    assert raw[14:34]==raw[34:54] and raw[54:470]==raw[470:886]
    assert (folder/'DCD.OK').read_bytes()==b'FRAME37' and (folder/'MAIN.OK').read_bytes()==b'DECLINED'
    assert state['parent_menu_sampled']==1 and state['parent_status_samples']>18
    checks=dict(carrier_seen_at_connect=bool(state['parent_seen_in_child']),
                parent_detects_loss=state['parent_loss_seen_after']==1,
                menu_sees_offline_session=(state['parent_menu_state'],state['parent_menu_status'])==(0,6),
                status_refreshes_OFF_LINE=state['parent_OFF_LINE_seen_after']==1,
                final_status_OFF_LINE=b'OFF-LINE' in (folder/'SCREEN.BIN').read_bytes()[3840:4000:2])
    passed=all(not value for value in checks.values()) if a.expect_gap else all(checks.values())
    result=dict(passed=passed,gap_reproduced=a.expect_gap,compatibility_accepted=passed and not a.expect_gap,
                observations=state,checks=checks,inputs=inputs,parent_sha256=sha(out/'TERMINAL.EXE'),runner_sha256=sha(out/'ASPECT.EXE'),
                checker_sha256=sha(Path(__file__)),captures={str(f.relative_to(out)):sha(f) for f in out.rglob('*') if f.is_file()},scope=__doc__)
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['observations']));assert passed,checks


if __name__=='__main__':main()
