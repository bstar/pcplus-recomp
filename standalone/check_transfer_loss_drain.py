#!/usr/bin/env python3
"""Linked loss cleanup drains binary tail and suppresses flow on lost carrier."""
import argparse
import json
from pathlib import Path
import struct
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_EFLAGS
import check_transport as transport
from check_terminal_transfer_live import LiveTransfer
from check_meta_actions_live import ROOT
from check_meta_actions_live import DAY
import hashlib
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


class Loss(LiveTransfer):
    def __init__(self,tail,hard):
        self.tail=tail;self.dropped=False
        super().__init__(peer=False,after_create='carrier')
        for n,v in {'csi_row_count':24,'csi_last_row':23,'screen_last_row':23,'csi_origin_bottom':23,'erase_cell_count':1920}.items():self.put(n,v)
        self.put('uart_hardware_flow',hard)
    def interrupt(self,u,n,data):
        request=u.reg_read(UC_X86_REG_AX);result=super().interrupt(u,n,data)
        if n==0x21 and request>>8==0x5b and not self.dropped:
            self.dropped=True;self.rx.extend(self.tail)
        return result


class ContinuousLoss(Loss):
    def tick_hook(self,u,address,size,data):
        # One bounded FIFO arrival per foreground clock call. Re-injecting at
        # the same saved IP after IRET would starve that instruction forever.
        clock=self.symbols.get('terminal_clock_ticks')
        if address!=clock and not self.irq_in_service and u.reg_read(UC_X86_REG_EFLAGS)&0x200:
            self.clock_injected=False
        if address==clock and self.get('terminal_transfer_fault')==4 and not getattr(self,'clock_injected',False):
            self.rx.extend(b'Z');self.clock_injected=True
        return super().tick_hook(u,address,size,data)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['baseline','terminal','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
    cases=[]
    for label,path in [('baseline',a.baseline.resolve()),('candidate',a.terminal.resolve())]:
        transport.BINARY=path;transport.MAP=path.parent/'terminal.map'
        for hard in (0,1):
            for tail in [b'\x1b[8;50;80t\x00\xff',bytes(range(256))*4]:
                m=Loss(tail,hard);m.receive()
                assert m.dropped and m.get('terminal_transfer_fault')==4 and m.get('terminal_transfer_cleanup_status')==0
                assert not m.files and not m.handles and not m.get('terminal_quit')
                left=m.get('uart_rx_count')+len(m.rx)
                assert (left==0)==(label=='candidate'),(label,hard,left)
                assert not m.tx,'Lost-carrier cleanup sent bytes in command mode'
                cases.append(dict(image=label,hardware_flow=hard,tail_bytes=len(tail),unretired_bytes=left,first_fault=4,passed=True))
    transport.BINARY=a.terminal.resolve();transport.MAP=a.terminal.resolve().parent/'terminal.map'
    for start in (100,DAY-2):
        for hard in (0,1):
            m=ContinuousLoss(b'\x1b[BINARY',hard);m.tick=start;m.receive()
            assert m.get('terminal_transfer_fault')==4 and m.get('terminal_quit')==1 and m.get('terminal_exit_code')==14
            assert not m.files and not m.handles and not m.tx
            cases.append(dict(case='continuous-tail-bounded-stop',start=start,hardware_flow=hard,first_fault=4,exit_code=14,passed=True))
    for observed in (0,1):
        for carrier in (False,True):
            for cts in (False,True):
                for pending in (0x11,0x13):
                    m=LiveTransfer(peer=False);m.put('transfer_carrier_seen',observed);m.carrier=carrier;m.cts=cts
                    m.put('uart_hardware_flow',1);m.put('uart_software_flow',1);m.put('uart_flow_pending',pending,1)
                    m.tx.clear();m.call('transfer_poll_flow_ready')
                    blocked=bool(observed and not carrier)
                    assert bool(m.uc.reg_read(UC_X86_REG_EFLAGS)&1)==blocked
                    # The existing flow-byte poll uses THRE rather than the
                    # ordinary data writer's CTS/peer-XOFF gate. Preserve it.
                    assert bytes(m.tx)==(bytes([pending]) if not blocked else b'')
                    assert m.get('uart_flow_pending',1)==(0 if not blocked else pending)
                    cases.append(dict(case='physical-flow-predicate',observed=observed,carrier=carrier,CTS=cts,pending=pending,blocked=blocked,passed=True))
    manifest=json.loads((a.terminal.parent/'manifest.json').read_text())
    for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
    sources=['standalone/check_transfer_loss_drain.py','standalone/check_terminal_transfer_live.py','standalone/check_program_actions_live.py','standalone/check_meta_actions_live.py','standalone/check_transport.py']
    r=dict(passed=True,inputs=len(cases),cases=cases,terminal_sha256=sha(a.terminal),baseline_sha256=sha(a.baseline),sources={n:sha(ROOT/n) for n in sources},
        scope=__doc__+' Actual owner/native UART/ISR/storage/cleanup executes; hardware/BIOS/DOS only modeled. No BBS/physical acceptance.')
    (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS transfer loss drain:',len(cases),'linked inputs')


if __name__=='__main__':main()
