#!/usr/bin/env python3
"""Linked manual Init key/menu, UART output lease, admission and connection hooks.
BIOS, DOS and UART registers are modeled; dispatchers/owners are not replaced.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from check_call_timer_live import Clock,configure,ROOT
from check_manual_init_owner_live import snapshot

def stable(m):
    state=list(snapshot(m));state[0].pop('connection_elapsed');return state

def active(m):return m.get('terminal_manual_init_active')
def finish(m):
    for _ in range(500):
        if not active(m):return
        before=len(m.tx);m.poll()
        assert len(m.tx)-before<=1
    raise AssertionError('manual owner remained active')
def ordinary(m,data):
    m.receive_irq(data)
    while m.get('uart_rx_count'):
        value=m.call('uart_receive_byte');m.call('terminal_receive_input',ax=value,limit=1000000)
def prepare(online=False):
    m=Clock()
    if online:m.now=100;m.connect(b'CONNECT\r\n')
    m.tx.clear();return m

def direct(online=False):
    m=prepare(online);before=stable(m);screen=m.text()
    m.key(0x2400);assert active(m) and not m.tx and not m.get('_command_menu_active')
    finish(m)
    assert bytes(m.tx)==b'ATZ\r' and m.get('terminal_manual_init_status')==2
    assert stable(m)==before and m.text()==screen
    m.key(0x2400);finish(m);assert bytes(m.tx)==b'ATZ\rATZ\r'
    return 1

def reference():
    m=prepare();m.key(0x2c00);assert m.get('_command_menu_active')
    m.key(0x2400)
    assert active(m) and not m.get('_command_menu_active') and not m.get('_redisplay_active')
    assert b'P R O C O M M' not in m.text()
    finish(m);assert bytes(m.tx)==b'ATZ\r'
    return 1

def browser():
    m=prepare();m.key(ord('`'));m.key(ord('/'))
    for value in b'Init Modem':m.key(value)
    m.key(13);m.key(27);m.key(13)
    assert active(m) and not m.get('_command_menu_active') and not m.get('_redisplay_active')
    finish(m);assert bytes(m.tx)==b'ATZ\r'
    return 1

def exclusive():
    m=prepare(True);before=stable(m);m.key(0x2400)
    m.key(ord('x'));assert m.get('terminal_deferred_count')==1
    m.key(0x2400);assert m.get('terminal_deferred_count')==1
    ordinary(m,b'OK\r\nName? \x1b[6n')
    assert b'Name?' in m.text() and m.get('terminal_tx_count')>0
    assert m.call('_terminal_auto_allowed')==0
    assert m.get('terminal_deferred_count')==1 and not m.get('terminal_transfer_pending')
    finish(m)
    assert bytes(m.tx)==b'ATZ\r' and not m.get('terminal_deferred_count')
    m.drain();assert bytes(m.tx).startswith(b'ATZ\r\x1b[') and bytes(m.tx).endswith(b'Rx')
    assert stable(m)==before
    return 1

def defer():
    count=0
    fields=('terminal_parser_active','terminal_macro_active','terminal_program_pending',
            'terminal_program_active','terminal_transfer_pending','terminal_transfer_active',
            'terminal_aspect_active','terminal_ansi_wait_active','terminal_snapshot_active',
            'uart_break_hold','terminal_monitor_active','terminal_controller_active',
            'terminal_browser_screen_owned','terminal_editor_screen_owned')
    # Use the actual far local-command admission for states whose own top-level
    # dispatcher intentionally routes elsewhere (ASPECT/monitor/controller).
    from unicorn.x86_const import UC_X86_REG_AX
    for field in fields:
        m=prepare();m.put(field,1,1 if field.endswith('screen_owned') else 2)
        # Generic far harness preserves non-AX, flags except this CF-return API.
        seg,offset=m.entries['terminal_local_control_key'];u=m.uc
        from unicorn.x86_const import UC_X86_REG_CS,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_SP
        sp=m.offset('terminal_stack_top')-4
        u.mem_write(m.data_base+sp,struct.pack('<HH',m.return_offset,m.code_segment))
        for r,v in ((UC_X86_REG_AX,0x2400),(UC_X86_REG_CS,m.base_segment+seg),
                    (UC_X86_REG_DS,m.ds),(UC_X86_REG_SS,m.ds),(UC_X86_REG_SP,sp)):u.reg_write(r,v)
        m.returned=False;u.emu_start(m.symbols['terminal_local_control_key'],0,count=1000000)
        assert m.returned and not active(m) and not m.tx and m.get('terminal_deferred_count')==1,field
        m.put(field,0,1 if field.endswith('screen_owned') else 2)
        m.call('terminal_poll_io',limit=1000000)
        assert active(m) and not m.get('terminal_deferred_count'),field
        finish(m);assert bytes(m.tx)==b'ATZ\r';count+=1
    m=prepare();m.thre=False;m.enqueue(b'PENDING');m.key(0x2400)
    assert not active(m) and m.get('terminal_deferred_count')==1
    m.thre=True
    for _ in range(20):
        m.poll()
        if active(m):break
    assert active(m) and bytes(m.tx)==b'PENDING'
    finish(m);assert bytes(m.tx)==b'PENDINGATZ\r'
    return count+1

def stalls_and_cancel():
    count=0
    for kind in ('thre','cts','xoff'):
        m=prepare(True);m.key(0x2400);before=snapshot(m)
        if kind=='thre':m.thre=False
        if kind=='cts':m.cts=False
        if kind=='xoff':m.put('uart_software_flow',1);m.put('uart_tx_paused',1)
        controls=list(m.controls)
        m.poll(36)
        assert not active(m) and m.get('terminal_manual_init_status')==4 and not m.tx
        assert m.state()==6 and m.get('terminal_call_timer_running') and m.controls==controls
        count+=1
    for partial in (False,True):
        m=prepare(True);m.key(0x2400);m.thre=partial;m.key(27)
        assert not active(m) and m.get('terminal_manual_init_status')==3
        assert bytes(m.tx)==(b'A' if partial else b'')
        assert m.get('connection_resync',1)==int(partial)
        assert m.state()==6 and m.get('terminal_call_timer_running')
        count+=1
    return count

def recording_release():
    m=prepare();m.key(0x1300);m.key(13)
    assert not m.get('_command_menu_active')
    assert m.far('terminal_recording_owned_far')!=0
    m.key(0x2400)
    assert not active(m) and m.get('terminal_deferred_count')==1
    m.key(ord('`')) # The stop/save browser key must remain reachable.
    assert m.get('_command_menu_active') and not active(m)
    m.key(27)
    assert not m.get('_command_menu_active') and not active(m)
    # Stop through the real recorder API, then the retained command can proceed.
    assert m.far('_recording_terminal_stop')==0
    m.call('terminal_poll_io');assert active(m) and not m.get('terminal_deferred_count')
    finish(m);assert bytes(m.tx)==b'ATZ\r'
    return 1

def dialing_escape():
    m=prepare();m.thre=False;m.start()
    assert m.state()==1
    m.key(0x2400)
    assert not active(m) and m.get('terminal_deferred_count')==1
    m.key(27)
    assert m.state()==7 and not active(m) and not m.get('terminal_deferred_count')
    return 1

def carrier_and_actions():
    count=0
    for key,reason in ((0x2300,3),(0x2d00,8)):
        m=prepare(True);m.key(0x2400);m.key(key)
        assert not active(m) and m.get('terminal_manual_init_status')==reason
        assert m.state()==9 and m.get('connection_resync',1)==1
        count+=1
    m=prepare(True);m.key(0x2400);m.poll();assert bytes(m.tx)==b'A'
    m.thre=False # Keep the sender active through the qualified DCD interval.
    m.now=107;m.carrier=False;m.poll(8)
    assert not active(m) and m.get('terminal_manual_init_status')==7 and m.state()==0
    assert m.duration()=='00:00:07' and not m.get('terminal_call_timer_running')
    assert bytes(m.tx)==b'A' and m.get('connection_resync',1)==1
    m.thre=True;m.carrier=True;m.tx.clear();m.now=110;m.connect(b'CONNECT\r\n')
    assert bytes(m.tx)==b'\rATZ\rATDLocal.Example:2323\r'
    assert m.get('terminal_call_timer_epoch')==2
    count+=1
    # Programmatic connection start also cancels a partial raw manual owner.
    m=prepare();m.key(0x2400);m.poll();assert bytes(m.tx)==b'A'
    m.tx.clear();m.connect(b'CONNECT\r\n')
    assert not active(m) and m.get('terminal_manual_init_status')==3
    assert bytes(m.tx)==b'\rATZ\rATDLocal.Example:2323\r'
    return count+1


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();configure(a.terminal)
    assert json.loads((a.terminal.parent/'manifest.json').read_text())['experimental_manual_init']
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
    cases=[]
    for name,fn in [('direct-idle-repeat',direct),('direct-online-repeat',lambda:direct(True)),
                    ('reference-restores-view-before-start',reference),('browser-search-same-owner',browser),
                    ('exclusive-command-CPR-typeahead-and-autostart-guard',exclusive),
                    ('owner-admission-and-queued-output',defer),('flow-stalls-and-Escape',stalls_and_cancel),
                    ('deferred-Init-does-not-starve-recorder-release-keys',recording_release),
                    ('deferred-Init-does-not-starve-dial-cancel',dialing_escape),
                    ('qualified-DCD-hangup-exit-and-redial-resync',carrier_and_actions)]:
        count=fn();cases.append(dict(case=name,inputs=count,passed=True));print(name,count,'PASS',flush=True)
    paths=[Path(__file__).resolve(),ROOT/'src/terminal/manual_init_dispatch.asm',ROOT/'src/terminal/transport.asm',
           ROOT/'src/terminal/local_controls.asm',ROOT/'src/terminal/connection.asm',ROOT/'src/terminal/autostart.asm']
    result=dict(passed=True,cases=cases,terminal_sha256=hashlib.sha256(a.terminal.read_bytes()).hexdigest(),
                sources={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
                scope=__doc__+' Actual root scheduling, FIFO, key/reference/browser admission, native UART/parser, connection/DCD and timer. Hardware/BIOS/DOS models; no actual DOS/BBS/SIP/analog acceptance or deployment.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS manual Init dispatcher:',sum(c['inputs'] for c in cases),'inputs')

if __name__=='__main__':main()
