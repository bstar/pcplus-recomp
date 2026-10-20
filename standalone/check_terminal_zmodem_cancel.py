#!/usr/bin/env python3
"""Production foreground Escape cleanup with real UART/IRQ and file owners."""
import hashlib,json
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_AX
from check_terminal_zmodem_live import LiveZmodem,ROOT,BINARY


class Canceled(LiveZmodem):
    def __init__(self,mode,sending=False):
        self.cancel_mode=mode;self.injected=False;self.cancel_tick=None;self.late=0;self.jumped=False
        super().__init__(source=bytes(range(256))*16,sending=sending)
    def output_port(self,u,port,size,value,data):
        result=super().output_port(u,port,size,value,data)
        if self.direction and not self.injected and len(self.tx)>1600:
            self.injected=True;self.script_enabled=False;self.strict=False
            self.keys.append(0x011b)
        return result
    def interrupt(self,u,n,data):
        write=n==0x21 and u.reg_read(UC_X86_REG_AX)>>8==0x40
        result=super().interrupt(u,n,data)
        if write and not self.injected and any(len(v)>0 for k,v in self.files.items() if k.endswith('PCRX.$$$')):
            self.injected=True;self.script_enabled=False;self.strict=False
            self.keys.append(0x011b)
        return result
    def tick_hook(self,u,address,size,data):
        super().tick_hook(u,address,size,data)
        if self.injected and self.get('terminal_transfer_fault')==2:
            if self.cancel_tick is None:self.cancel_tick=self.tick
            elapsed=(self.tick-self.cancel_tick)%0x1800b0
            if self.cancel_mode=='clock-jump' and not self.jumped and elapsed>=4:
                self.tick=(self.tick+65536)%0x1800b0;self.jumped=True
            wanted=elapsed if self.cancel_mode=='continuous' else (2 if elapsed>=6 else 1 if elapsed>=4 else 0) if self.cancel_mode=='late' else 0
            if wanted>self.late:
                self.rx.extend(b'\x1b[999z\x00\xff');self.late=wanted


def main():
    cases=[]
    for mode,sending in [('quiet',False),('late',False),('continuous',False),('quiet',True),('clock-jump',False)]:
        m=Canceled(mode,sending);assert m.run(owner=True)==2
        assert m.injected and m.cancel_tick is not None
        assert b'\x18'*8+b'\x08'*10 in bytes(m.tx)
        assert not m.handles
        if sending:assert {k:bytes(v) for k,v in m.files.items()}=={'SEND.BIN':m.source}
        else:assert not m.files
        assert m.get('terminal_transfer_cleanup_status')==0
        elapsed=(m.tick-m.cancel_tick)%0x1800b0
        if mode=='clock-jump':
            assert elapsed>=65536 and m.get('terminal_quit')==1 and m.get('terminal_exit_code')==14
        elif mode=='continuous':
            assert elapsed<=190,(mode,elapsed)
            assert elapsed>=180 and m.get('terminal_quit')==1 and m.get('terminal_exit_code')==14
        else:
            assert elapsed<=190,(mode,elapsed)
            assert not m.rx and m.get('uart_rx_count')==0 and m.get('terminal_quit')==0
        assert b'canceled' in bytes(m.uc.mem_read(0xb8000,4000))[::2]
        cases.append(dict(case=mode+'-upload' if sending else mode,passed=True,elapsed_modeled_ticks=elapsed,late_bursts=m.late))
    report=dict(passed=True,cases=cases,binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope='Actual linked foreground owner, ZMODEM engine, storage, UART ISR and cancel writer; BIOS clock/keyboard/ports and DOS filesystem boundaries modeled. Late input and endless-input deadline checked; real BBS cancellation is separate.')
    (ROOT/'build/terminal/zmodem-cancel-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Passed',len(cases),'foreground cancellation cases')


if __name__=='__main__':main()
