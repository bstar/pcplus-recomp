#!/usr/bin/env python3
"""Linked 8086 policy parser and standard BIOS ring cancellation ownership."""
import argparse,json,struct
from pathlib import Path
from unicorn.x86_const import *
from check_transport_escape import Keys,q,sha


class Clock(Keys):
    step=1
    def _code(self,u,address,size,data):
        if address==self.symbols['_aspect_serial_ticks']:self.tick+=self.step-1
        return super()._code(u,address,size,data)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(q.ROOT/'build') and not out.exists()
    m=Keys();rows=[]
    def configure(text):
        if text is None:return m.call('_runtime_serial_wait_configure',[0])
        m.uc.mem_write(m.data_base+0xb100,text+b'\0')
        return m.call('_runtime_serial_wait_configure',[0xb100])
    assert configure(None)==0 and m.get('_runtime_serial_tx_wait_ticks')==540
    for value in range(1,3601):
        assert configure(str(value).encode())==0
        assert m.get('_runtime_serial_tx_wait_ticks')==value*18
    for text in (b'0001',b'0030',b'0999'):
        assert configure(text)==0 and m.get('_runtime_serial_tx_wait_ticks')==int(text)*18
    bad=[b'',b'0',b'0000',b'3601',b'9999',b'10000',b'00001',b'-1',b'+1',b' 1',b'1 ',b'1s',b'1.0',b'\xff']
    previous=m.get('_runtime_serial_tx_wait_ticks')
    for text in bad:
        assert configure(text)==1 and m.get('_runtime_serial_tx_wait_ticks')==previous
    assert configure(None)==0 and m.get('_runtime_serial_tx_wait_ticks')==540
    assert not m.writes and not m.requests
    rows.append(dict(case='all-seconds-range-and-invalid-nondestructive-parser',inputs=3600+len(bad)+5,passed=True))
    count=0
    for seconds in (1,30,3600):
      for initial in (50,1573030):
        for step in (1,97,997):
          if seconds==3600 and step==1:continue
          clock=Clock();assert clock.open()==0;clock.queue([])
          clock.put('uart_tx_paused',1);clock.put('_runtime_serial_tx_wait_ticks',seconds*18)
          clock.tick=initial;clock.step=step;before=bytes(clock.tx)
          assert clock.call('_runtime_serial_send',[65],limit=10000000)==14
          assert clock.get('_runtime_serial_error')==7 and bytes(clock.tx)==before
          elapsed=clock.tick-initial
          assert seconds*18<=elapsed<=seconds*18+step*3,(seconds,initial,step,elapsed)
          count+=1
    clock=Clock();assert clock.open()==0;clock.queue([]);before=bytes(clock.tx)
    assert clock.call('_runtime_serial_send',[65])==0 and bytes(clock.tx)==before+b'A'
    clock.put('_runtime_error',11);before=bytes(clock.tx)
    assert clock.call('_runtime_serial_send',[66])==11 and bytes(clock.tx)==before
    rows.append(dict(case='native-send-deadline-midnight-no-leak-single-byte-first-error',inputs=count+2,passed=True))
    count=0
    for start in range(16):
      for length in range(16):
        for escape in range(-1,length):
          words=[(0x1000+i*256)+(0 if i%2 else 0xe0) for i in range(length)]
          if escape>=0:words[escape]=0x011b
          expected=words[:]
          if escape>=0:expected.pop(escape)
          for flags in (2,0x202,0x402,0x602):
            m.queue(words,start)
            before=bytes(m.uc.mem_read(0x400,256))
            answer=m.call('_runtime_keyboard_cancel_pending',eflags=flags,bx=0x1234,cx=0x2345,dx=0x3456,si=0x4567,di=0x5678,bp=0x6789,es=0x7890)
            assert answer==int(escape>=0) and m.queued()==expected
            assert m.uc.reg_read(UC_X86_REG_EFLAGS)&0x600==flags&0x600
            for register,value in [(UC_X86_REG_BX,0x1234),(UC_X86_REG_CX,0x2345),(UC_X86_REG_DX,0x3456),(UC_X86_REG_SI,0x4567),(UC_X86_REG_DI,0x5678),(UC_X86_REG_BP,0x6789),(UC_X86_REG_ES,0x7890),(UC_X86_REG_DS,m.ds),(UC_X86_REG_SS,m.ds)]:
                assert m.uc.reg_read(register)==value
            after=bytes(m.uc.mem_read(0x400,256));allowed={0x1c,0x1d} if escape>=0 else set()
            if escape>=0:
                for i in range(escape,length-1):
                    offset=0x1e+2*((start+i)%16);allowed.update((offset,offset+1))
            assert all(x==y or i in allowed for i,(x,y) in enumerate(zip(before,after)))
            count+=1
    rows.append(dict(case='every-ring-head-length-position-wrap-and-IF-DF-preservation',inputs=count,passed=True))
    count=0
    for head,tail,low,high in [(0x1f,0x24,0x1e,0x3e),(0x1e,0x25,0x1e,0x3e),(0x1c,0x24,0x1e,0x3e),(0x1e,0x3e,0x1e,0x3e),(0x1e,0x24,0x20,0x40),(0x1e,0x24,0,0x3e),(0xffff,0,0,0)]:
        m.queue([0x1071,0x011b,0x1372]);m.uc.mem_write(0x41a,struct.pack('<2H',head,tail));m.uc.mem_write(0x480,struct.pack('<2H',low,high))
        before=bytes(m.uc.mem_read(0x400,256));assert m.call('_runtime_keyboard_cancel_pending')==0
        assert bytes(m.uc.mem_read(0x400,256))==before;count+=1
    m.queue([0x1071,0x011b,0x1372],15);m.uc.mem_write(0x480,b'\0'*4)
    assert m.call('_runtime_keyboard_cancel_pending')==1 and m.queued()==[0x1071,0x1372]
    m.queue([0x011b,0x011b,0x1071],15)
    assert m.call('_runtime_keyboard_cancel_pending')==1 and m.queued()==[0x011b,0x1071]
    rows.append(dict(case='invalid-layout-untouched-legacy-bounds-first-Escape-only',inputs=count+2,passed=True))
    out.mkdir(parents=True)
    result=dict(passed=True,cases=rows,runner_sha256=sha(q.BINARY),test_sha256=sha(Path(__file__)),scope=__doc__+' Native linked code executes; BIOS/UART/kernel boundaries modeled. Standard IBM queue only; actual DOS stalls and nonstandard BIOS behavior are separate.')
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
