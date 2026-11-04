#!/usr/bin/env python3
"""Linked send-only manual Init owner; real expander/UART, modeled BIOS/hardware.

This deliberately does not claim dispatcher admission, Alt-J binding or physical
acceptance. The harness supplies the explicit output grant and cancellation.
"""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from unicorn.x86_const import *
from check_call_timer_live import Clock, configure

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src/config'))
from prm import expand_modem_command, modem_command_events
DAY = 0x1800b0


def invoke(m, operation, *, ax=0, si=0x5678, cx=0x3456, dx=0x4567):
    name = 'terminal_manual_init_' + operation + '_far'
    segment, offset = m.entries[name]
    regs = {UC_X86_REG_BX: 0x2345, UC_X86_REG_CX: cx, UC_X86_REG_DX: dx,
            UC_X86_REG_SI: si, UC_X86_REG_DI: 0x6789, UC_X86_REG_BP: 0xbabe,
            UC_X86_REG_ES: 0xb800}
    sp = m.offset('terminal_stack_top') - 4
    m.uc.mem_write(m.data_base + sp, struct.pack('<HH', m.return_offset, m.code_segment))
    for register, value in {**regs, UC_X86_REG_AX: ax,
            UC_X86_REG_CS: m.base_segment + segment, UC_X86_REG_IP: offset,
            UC_X86_REG_DS: m.ds, UC_X86_REG_SS: m.ds,
            UC_X86_REG_SP: sp, UC_X86_REG_EFLAGS: 0x246}.items():
        m.uc.reg_write(register, value)
    m.returned = False
    m.uc.emu_start(m.symbols[name], 0, count=1000000)
    assert m.returned and m.uc.reg_read(UC_X86_REG_SP) == sp + 4, name
    assert m.uc.reg_read(UC_X86_REG_DS) == m.uc.reg_read(UC_X86_REG_SS) == m.ds
    assert all(m.uc.reg_read(r) == v for r, v in regs.items()), name
    assert m.uc.reg_read(UC_X86_REG_EFLAGS) == 0x246, name
    return m.uc.reg_read(UC_X86_REG_AX)


def begin(m, command=b'ATZ^M', marker=126, budget=200):
    pointer = m.stage_near(command + b'\0')
    return invoke(m, 'begin', ax=budget, si=pointer, cx=len(command) + 1, dx=0x4500 | marker)


def poll(m, ticks=0, grant=1):
    m.tick = (m.tick + ticks) % DAY
    before = len(m.tx)
    status = invoke(m, 'poll', ax=grant)
    assert len(m.tx) - before <= 1
    return status


def finish(m):
    for _ in range(500):
        status = poll(m, 1)
        if status != 1:
            return status
    raise AssertionError('owner did not terminate')


def snapshot(m):
    fields = ('connection_state', 'connection_status', 'connection_elapsed',
              'terminal_call_timer_valid', 'terminal_call_timer_running',
              'terminal_call_timer_epoch', 'elapsed_start_seconds',
              'modes_value_1d1a', 'uart_hardware_flow', 'uart_software_flow')
    return ({n: bytes(m.uc.mem_read(m.symbols[n], 4 if n in
             ('connection_elapsed', 'elapsed_start_seconds') else 2)) for n in fields},
            bytes(m.uc.mem_read(m.symbols['terminal_modem_settings'], 368)),
            m.mcr, m.lcr, list(m.controls), m.duration())


def wire_cases():
    commands = (b'', b'ATZ^M', b'AT^MATE0^M', b'~AT~~Z^M', b'^@A^M',
                b'^^^A^M', b'A^`IGNORED', b'^`', b'^M^J', b'A' * 46)
    count = 0
    for online in (False, True):
        m = Clock()
        if online:
            m.now = 123; m.connect(b'CONNECT\r\n')
        m.tx.clear()
        for marker in (0, 13, 126, 255):
            for command in commands:
                before = snapshot(m); text = bytes(m.uc.mem_read(0xb8000, 4000))
                m.tx.clear()
                expanded = expand_modem_command(command)
                assert begin(m, command, marker) == (2 if not expanded or not expanded[0] else 1)
                assert finish(m) == 2
                expected = bytes(value for event, value in modem_command_events(command, marker, 1)
                                 if event == 'transmit')
                assert bytes(m.tx) == expected, (command, marker, bytes(m.tx), expected)
                assert m.get('terminal_manual_init_accepted') == len(expected)
                assert snapshot(m) == before
                assert bytes(m.uc.mem_read(0xb8000, 4000)) == text, 'local echo'
                pointer = m.offset('terminal_stack_top') - m.stack_bytes + 16
                assert bytes(m.uc.mem_read(m.data_base + pointer, len(command)+1)) == command+b'\0'
                count += 1
    return count


def pacing():
    m = Clock(); assert begin(m, b'A~B^@C^M') == 1
    assert poll(m) == 1 and bytes(m.tx) == b'A'
    assert poll(m) == 1 and bytes(m.tx) == b'A'
    assert poll(m, 1) == 1 and bytes(m.tx) == b'A' # pause begins
    assert poll(m, 9) == 1 and bytes(m.tx) == b'A'
    assert poll(m, 1) == 1 and bytes(m.tx) == b'AB'
    assert poll(m) == 1 and bytes(m.tx) == b'AB'
    assert poll(m, 1) == 1 and bytes(m.tx) == b'AB\0'
    assert poll(m) == 1 and bytes(m.tx) == b'AB\0C' # no FF pacing
    assert poll(m, 1) == 1 and bytes(m.tx) == b'AB\0C\r'
    assert poll(m, 1) == 2 and not m.get('terminal_manual_init_needs_resync')
    return 1


def admission():
    count = 0
    m = Clock(); pointer = m.stage_near(b'ATZ^M\0')
    for budget, cap, data in ((0,6,b'ATZ^M\0'), (200,0,b'\0'), (200,48,b'\0'),
                             (200,3,b'ABC'), (200,2,b'^\0')):
        m.uc.mem_write(m.data_base+pointer,data)
        assert invoke(m,'begin',ax=budget,si=pointer,cx=cap,dx=126) == 5
        assert not m.get('terminal_manual_init_active') and not m.tx
        count += 1
    for state in (1,2,5,7,9,10):
        m.put('connection_state',state)
        assert begin(m) == 6 and not m.tx and not m.get('terminal_manual_init_active')
        assert m.get('connection_state') == state
        count += 1
    m.put('connection_state',0)
    assert invoke(m,'begin',ax=200,si=0xfffe,cx=6,dx=126) == 5
    assert not m.tx and not m.get('terminal_manual_init_active')
    count += 1
    m.put('connection_state',0);m.call('terminal_enqueue_al',ax=65)
    assert begin(m) == 6 and m.get('terminal_tx_count') == 1 and not m.tx
    m.put('terminal_tx_count',0)
    assert begin(m) == 1
    assert begin(m,b'CHANGED^M') == 6
    assert poll(m,grant=2) == 5 and m.get('terminal_manual_init_active')
    assert finish(m) == 2 and bytes(m.tx) == b'ATZ\r'
    return count + 3


def stalls():
    count=0
    for kind in ('grant', 'thre', 'cts', 'xoff'):
        m=Clock();assert begin(m) == 1
        if kind=='thre':m.thre=False
        if kind=='cts':m.cts=False
        if kind=='xoff':m.put('uart_software_flow',1);m.put('uart_tx_paused',1)
        before=snapshot(m)
        assert poll(m,35,grant=int(kind!='grant'))==1
        assert poll(m,1,grant=int(kind!='grant'))==4
        assert not m.tx and not m.get('terminal_manual_init_active')
        assert not m.get('terminal_manual_init_needs_resync') and snapshot(m)==before
        count+=1
    for tick in (65530, DAY-5):
        m=Clock();m.tick=tick;assert begin(m,b'~A',budget=10)==1
        assert poll(m)==1 and poll(m,9)==1 and not m.tx
        assert poll(m,1)==4 and not m.tx
        count+=1
    m=Clock();assert begin(m,b'A'*40,budget=5)==1
    assert poll(m)==1
    for _ in range(4):assert poll(m,1)==1
    assert poll(m,1)==4 and len(m.tx)==5 and m.get('terminal_manual_init_needs_resync')
    return count+1


def cancellation():
    count=0
    for reason in (3,7,8):
        for sent in (0,1,2):
            m=Clock();assert begin(m,b'A^M')==1
            for _ in range(sent):poll(m,1)
            before=snapshot(m);wire=bytes(m.tx)
            assert invoke(m,'cancel',ax=reason)==reason
            assert not m.get('terminal_manual_init_active')
            assert m.get('terminal_manual_init_needs_resync')==int(sent==1)
            assert invoke(m,'cancel',ax=8)==reason and poll(m,10)==reason
            assert bytes(m.tx)==wire and snapshot(m)==before
            count+=1
    m=Clock();assert begin(m)==1
    assert invoke(m,'cancel',ax=4)==5 and m.get('terminal_manual_init_active')
    assert finish(m)==2
    # Physical partial-line debt survives empty commands and clears on an actual CR.
    assert begin(m,b'A')==1 and finish(m)==2 and m.get('terminal_manual_init_needs_resync')
    assert begin(m,b'')==2 and m.get('terminal_manual_init_needs_resync')
    assert begin(m,b'^M')==1 and finish(m)==2 and not m.get('terminal_manual_init_needs_resync')
    return count+2


def copied_plan():
    m=Clock();assert begin(m)==1
    pointer=m.offset('terminal_stack_top')-m.stack_bytes+16
    m.uc.mem_write(m.data_base+pointer,b'XXXXX\0')
    assert finish(m)==2 and bytes(m.tx)==b'ATZ\r'
    return 1


def receive_and_queue():
    m=Clock();m.now=100;m.connect(b'CONNECT\r\n');m.tx.clear()
    before=snapshot(m);assert begin(m)==1
    # Actual ISR/parser; owner itself has no reply classifier or ACK state.
    m.receive_irq(b'OK\r\nName? \x1b[6n')
    while m.get('uart_rx_count'):
        value=m.call('uart_receive_byte')
        m.call('terminal_receive_input',ax=value,limit=1000000)
    assert b'Name?' in m.text() and m.get('terminal_tx_count')>0
    if 'terminal_manual_init_key_far' in m.symbols:
        assert b'ATZ\r'.startswith(bytes(m.tx)) # Integrated parser polls service the owner.
    else:
        assert not m.tx
    assert finish(m)==2 and bytes(m.tx)==b'ATZ\r'
    assert snapshot(m)==before
    m.drain()
    assert bytes(m.tx).startswith(b'ATZ\r\x1b[') and bytes(m.tx).endswith(b'R')
    return 1


def subsequent_connection():
    m=Clock();assert begin(m)==1 and finish(m)==2
    assert bytes(m.tx)==b'ATZ\r' and not m.get('terminal_call_timer_epoch')
    m.tx.clear();m.now=50;m.connect(b'CONNECT\r\n')
    assert bytes(m.tx)==b'ATZ\rATDLocal.Example:2323\r'
    assert m.get('terminal_call_timer_epoch')==1
    m.now=57;m.carrier=False;m.poll(8)
    assert m.state()==0 and m.duration()=='00:00:07'
    m.carrier=True;m.tx.clear();m.now=60;m.connect(b'CONNECT\r\n')
    assert m.get('terminal_call_timer_epoch')==2 and m.get('terminal_manual_init_status')==2
    return 1


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--terminal',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    configure(a.terminal)
    manifest=json.loads((a.terminal.parent/'manifest.json').read_text())
    assert manifest['experimental_manual_init_owner']
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
    cases=[]
    for name,function in (('native-command-wire-idle-and-connected',wire_cases),
                          ('ordinary-pause-and-FF-pacing',pacing),
                          ('bounded-validation-and-busy-refusals',admission),
                          ('flow-stalls-budget-and-clock-wrap',stalls),
                          ('cancel-loss-exit-and-partial-line-debt',cancellation),
                          ('private-copy-of-expanded-input',copied_plan),
                          ('real-receive-parser-and-deferred-CPR',receive_and_queue),
                          ('subsequent-dial-carrier-loss-and-redial',subsequent_connection)):
        count=function();cases.append(dict(case=name,inputs=count,passed=True));print(name,count,'PASS',flush=True)
    paths=[Path(__file__).resolve(),ROOT/'src/terminal/manual_init.asm',
           ROOT/'src/terminal/modem_abi.inc',ROOT/'src/terminal/transport.asm',
           ROOT/'reconstruction/modem_commands/bounded.asm',ROOT/'src/config/prm.py']
    result=dict(passed=True,cases=cases,binary_sha256=hashlib.sha256(a.terminal.read_bytes()).hexdigest(),
                sources={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
                scope=__doc__+' Actual linked far owner, native bounded expander, UART/IRQ, receive parser and connected call timer. BIOS/DOS/ports modeled. Output grant and loss/exit cancellation explicitly supplied by harness. No dispatcher exclusion, automatic DCD cancellation, Alt-J/menu binding, native calibrated timing equivalence, DOS/BBS/analog acceptance or deployment.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS manual initialization owner:',sum(c['inputs'] for c in cases),'inputs')

if __name__=='__main__':main()
