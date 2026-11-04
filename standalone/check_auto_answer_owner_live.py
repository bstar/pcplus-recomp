#!/usr/bin/env python3
"""Typed answer-on component: linked UART, native echo renderer and reentrancy guard.
No Alt-Y/configured command selection, sound or notice UI is bound by this suite.
"""
import argparse,hashlib,itertools,json
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_AX
from check_call_timer_live import Clock,configure,ROOT
from check_manual_init_owner_live import invoke,begin,poll,finish
from check_manual_init_dispatch_live import stable
from prm import modem_command_events

class Echo(Clock):
    def __init__(self,online=False,duplex=0):
        super().__init__()
        if online:self.now=100;self.connect(b'CONNECT\r\n')
        self.put('modes_value_1d1a',duplex);self.tx.clear();self.echoes=[];self.echo_wire=[]
        self.uc.hook_add(UC_HOOK_CODE,self.observe_echo)
    def observe_echo(self,u,address,size,_):
        if address==self.symbols['terminal_key_echo_far']:
            value=u.reg_read(UC_X86_REG_AX)&255
            self.echoes.append(value);self.echo_wire.append(bytes(self.tx))
            assert self.tx and self.tx[-1]==value,'echo before physical acceptance'

def answer(m,command=b'ATS0=1^M',marker=126,budget=200):
    assert len(command)<25
    source=m.stage_near(command+b'\0')
    return invoke(m,'begin',ax=budget,si=source,cx=len(command)+1,dx=0x4500|marker,answer=True)


def exact():
    count=0
    for online,duplex,marker,command in itertools.product((False,True),(0,1,2,0x7fff,0x8000,0xffff),(0,13,126,255),
                                                        (b'',b'ATS0=1^M',b'A~B^@C^M',b'A^^B^M',b'A^`IGNORED')):
        m=Echo(online,duplex);before=stable(m)
        status=answer(m,command,marker);assert status in (1,2)
        assert m.get('terminal_manual_command_kind')==1 and not m.echoes and not m.tx
        assert finish(m)==2
        wire=[v for kind,v in modem_command_events(command,marker,1) if kind=='transmit']
        assert list(m.tx)==wire
        expected=[v for v in wire if v] if duplex else []
        assert m.echoes==expected,(command,marker,duplex,m.echoes,expected)
        assert stable(m)==before
        count+=1
    return count


def copied_echo():
    m=Echo(duplex=1);assert answer(m)==1
    m.put('modes_value_1d1a',0)
    assert finish(m)==2 and m.echoes==list(b'ATS0=1\r')
    assert m.get('modes_value_1d1a')==0 # never restore a setting borrowed by the owner
    m.tx.clear();m.echoes.clear();assert answer(m)==1
    m.put('modes_value_1d1a',1)
    assert finish(m)==2 and not m.echoes and m.get('modes_value_1d1a')==1
    return 2


def shared_owner():
    m=Echo(duplex=1);assert answer(m)==1
    assert begin(m,b'WRONG^M')==6 and m.get('terminal_manual_command_kind')==1
    assert answer(m,b'WRONG^M')==6
    assert finish(m)==2 and bytes(m.tx)==b'ATS0=1\r'
    m.tx.clear();m.echoes.clear();assert begin(m)==1
    assert m.get('terminal_manual_command_kind')==0
    assert answer(m)==6
    assert finish(m)==2 and bytes(m.tx)==b'ATZ\r' and not m.echoes
    source=m.stage_near(b'A'*25+b'\0')
    assert invoke(m,'begin',ax=200,si=source,cx=26,dx=126,answer=True)==5
    assert m.get('terminal_manual_command_kind')==0
    return 3


def stalls():
    count=0
    for kind in ('grant','thre','cts','xoff'):
        m=Echo(duplex=1);assert answer(m)==1
        if kind=='thre':m.thre=False
        if kind=='cts':m.cts=False
        if kind=='xoff':m.put('uart_software_flow',1);m.put('uart_tx_paused',1)
        for _ in range(20):assert poll(m,1,grant=int(kind!='grant'))==1
        assert not m.tx and not m.echoes
        if kind=='thre':m.thre=True
        if kind=='cts':m.cts=True
        if kind=='xoff':m.put('uart_tx_paused',0)
        assert finish(m)==2 and bytes(m.tx)==b'ATS0=1\r' and m.echoes==list(b'ATS0=1\r')
        count+=1
    m=Echo(duplex=1);assert answer(m)==1
    assert poll(m)==1 and m.echoes==[65]
    m.thre=False
    assert poll(m,1)==1 and poll(m,36)==4
    assert bytes(m.tx)==b'A' and m.echoes==[65] and not m.get('terminal_manual_init_active')
    return count+1


def cancellation():
    count=0
    for reason,partial in itertools.product((3,7,8),(False,True)):
        m=Echo(duplex=1);assert answer(m)==1
        if partial:assert poll(m)==1
        assert invoke(m,'cancel',ax=reason)==reason
        assert poll(m,20)==reason
        assert bytes(m.tx)==(b'A' if partial else b'') and m.echoes==([65] if partial else [])
        assert not m.get('terminal_manual_init_active')
        count+=1
    return count


def echo_reentrancy(cancel=False):
    m=Echo(duplex=1);m.advance_ticks=True
    assert answer(m,b'^[A^M',budget=500)==1
    if cancel:m.keys.append(27)
    status=poll(m)
    assert m.echoes==[27] and bytes(m.tx)==b'\x1b'
    assert not m.get('terminal_parser_active')
    if cancel:
        assert status==3 and not m.get('terminal_manual_init_active')
        # A new command proves that the recursive renderer guard was released.
        m.advance_ticks=False;m.tx.clear();m.echoes.clear();assert answer(m)==1
        assert finish(m)==2 and m.echoes==list(b'ATS0=1\r')
    else:
        assert status==1 and m.get('terminal_manual_init_active')
        assert finish(m)==2 and bytes(m.tx)==b'\x1bA\r' and m.echoes==[27,65,13]
    return 1


def automatic_retirement():
    count=0
    for key,reason in ((27,3),(0x2300,3),(0x2d00,8)):
        m=Echo(online=True,duplex=1);assert answer(m)==1
        m.key(key) # The ordinary root dispatcher, not a supplied cancel API.
        assert not m.get('terminal_manual_init_active') and m.get('terminal_manual_init_status')==reason
        assert bytes(m.tx)==b'A' and m.echoes==[65]
        assert m.get('connection_resync',1)==1
        assert m.get('terminal_manual_command_kind')==1
        count+=1
    m=Echo(online=True,duplex=1);assert answer(m)==1
    m.poll();assert bytes(m.tx)==b'A' and m.echoes==[65]
    m.thre=False;m.carrier=False;m.now=107;m.poll(8)
    assert not m.get('terminal_manual_init_active') and m.get('terminal_manual_init_status')==7
    assert m.state()==0 and m.duration()=='00:00:07'
    assert bytes(m.tx)==b'A' and m.echoes==[65]
    m.thre=True;m.carrier=True;m.tx.clear();m.now=110;m.connect(b'CONNECT\r\n')
    assert bytes(m.tx)==b'\rATZ\rATDLocal.Example:2323\r'
    assert m.echoes==[65] and m.get('terminal_call_timer_epoch')==2
    return count+1


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    configure(a.terminal);manifest=json.loads((a.terminal.parent/'manifest.json').read_text());assert manifest['experimental_auto_answer_owner']
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False);cases=[]
    for name,fn in [('captured-duplex-wire-and-ordinary-only-echo',exact),('concurrent-duplex-is-not-borrowed-or-restored',copied_echo),
                    ('typed-identity-shared-lease-and-capacity',shared_owner),('stalls-do-not-duplicate-echo',stalls),
                    ('cancel-loss-exit-no-extra-echo',cancellation),('native-ANSI-echo-does-not-reenter-UART-owner',echo_reentrancy),
                    ('Escape-during-native-echo-releases-guard',lambda:echo_reentrancy(True)),
                    ('root-cancel-hangup-exit-qualified-loss-and-redial',automatic_retirement)]:
        count=fn();cases.append(dict(case=name,passed=True,inputs=count));print(name,count,'PASS',flush=True)
    paths=[Path(__file__).resolve(),ROOT/'src/terminal/manual_init.asm',ROOT/'src/terminal/key_dispatch.asm']
    report=dict(passed=True,cases=cases,terminal_sha256=hashlib.sha256(a.terminal.read_bytes()).hexdigest(),
                sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
                scope=__doc__+' Actual linked bounded owner/expander/UART/IRQ and native terminal echo/ANSI/keyboard paths; no product callback replaced. BIOS/DOS/ports modeled. Capture-on-begin duplex and echo-after-physical-acceptance are maintained changes. No actual DOS/BBS/SIP/physical or configured Alt-Y/UI acceptance or deployment.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS typed answer owner:',sum(c['inputs'] for c in cases),'inputs')

if __name__=='__main__':main()
