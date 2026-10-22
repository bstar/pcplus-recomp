#!/usr/bin/env python3
"""Execute native yes/no plus the linked child owner against a modeled scalar parent.

No parser or replacement yes/no policy is modeled here; actual DOS prompt/query
checks separately constrain the parent frame and terminal implementation.
"""
import json
from pathlib import Path
from unicorn.x86_const import *
import check_aspect_render_client as client

class Keyboard(client.Client):
    def __init__(self,keys=(),drain_before_answer=False,close_on_read=False):
        self.keys=list(keys);self.reads=[];self.bells=0
        self.drain_before_answer=drain_before_answer;self.close_on_read=close_on_read
        super().__init__();self.words[-1]=12;self.publish()

    def _code(self,u,address,size,extra):
        super()._code(u,address,size,extra)
        if self.close_on_read and address==self.symbols['_runtime_abort_read_key']:
            self.put('_aspect_serial_active',0);self.close_on_read=False

    def _interrupt(self,u,number,extra):
        if number==0x16:
            function=u.reg_read(UC_X86_REG_AX)>>8
            assert function in (0,1,16,17)
            available=bool(self.keys) and not (self.drain_before_answer and self.reads and self.get('uart_rx_count'))
            if function in (1,17):
                flags=u.reg_read(UC_X86_REG_EFLAGS)
                u.reg_write(UC_X86_REG_EFLAGS,flags&~0x40 if available else flags|0x40)
                if available:u.reg_write(UC_X86_REG_AX,self.keys[0])
            else:
                assert available;value=self.keys.pop(0);self.reads.append(value);u.reg_write(UC_X86_REG_AX,value)
            return
        if number==0x10:
            assert u.reg_read(UC_X86_REG_AX)==0x0e07
            self.bells+=1;return
        return super()._interrupt(u,number,extra)

def main():
    cases=[]
    for name,answer,decision in [('No',0x316e,1),('Escape',0x011b,1),('Enter',0x1c0d,None),('Yes',0x1579,2)]:
        m=Keyboard([0x011b,answer]);assert m.open()==0
        m.call('_runtime_receive_reset');m.requests.clear()
        assert m.call('_runtime_when_cancel_poll',limit=1000000)==1
        assert m.get('_runtime_error')==(13 if decision==2 else 0)
        expected=[(12,0),(12,1)]+([] if decision is None else [(12,decision)])+[(12,3)]
        assert m.requests==expected,(name,m.requests)
        assert m.reads==[0x011b,answer] and m.get('_runtime_abort_last_key')==(answer&255)
        assert m.get('_runtime_when_last_key')==27
        assert m.uc.reg_read(UC_X86_REG_SP)==0xdfc0
        assert m.uc.reg_read(UC_X86_REG_DS)==m.uc.reg_read(UC_X86_REG_SS)==m.ds
        cases.append(dict(name=name,passed=True))
    m=Keyboard([0x011b,0x4800,0x2d78,0x314e]);assert m.open()==0
    m.call('_runtime_receive_reset');m.requests.clear()
    assert m.call('_runtime_when_cancel_poll',limit=1000000)==1 and not m.get('_runtime_error')
    assert m.bells==2 and m.reads==[0x011b,0x4800,0x2d78,0x314e]
    cases.append(dict(name='extended-and-invalid-keys-ring-and-continue-native-reader',passed=True))
    m=Keyboard([0x011b,0x316e],drain_before_answer=True);assert m.open()==0
    m.call('_runtime_receive_reset');m.call('_runtime_receive_begin',[1]);m.receive_irq(b'A'*90);m.requests.clear()
    assert m.call('_runtime_when_cancel_poll',limit=3000000)==1 and not m.get('_runtime_error')
    assert not m.get('uart_rx_count') and m.requests.count((1,65))==90
    assert m.requests[0:2]==[(12,0),(12,1)] and m.requests[-2:]==[(12,1),(12,3)]
    cases.append(dict(name='modal-native-receive-does-not-overrun-suspended-RGET-destination',passed=True))
    m=Keyboard([0x011b],close_on_read=True);assert m.open()==0;m.requests.clear()
    assert m.call('_runtime_when_cancel_poll',limit=1000000)==1 and m.get('_runtime_error')==14
    assert m.requests==[(12,0),(12,1),(12,3)]
    cases.append(dict(name='UART-loss-retires-parent-frame-with-original-error',passed=True))
    m=Keyboard();assert m.open()==0;m.requests.clear()
    assert m.call('_runtime_when_confirm_abort')==1 and m.get('_runtime_error')==10 and not m.requests
    cases.append(dict(name='reject-confirmation-outside-native-service-before-parent-call',passed=True))
    m=Keyboard();assert m.open()==0;m.requests.clear()
    for operation in (1,2,4):assert m.call('_aspect_render_confirm',[operation])==10
    assert m.call('_aspect_render_confirm',[5])==7 and not m.requests
    assert m.call('_aspect_render_confirm',[0])==0
    assert m.call('_aspect_render_confirm',[0])==10
    assert m.call('_aspect_render_key',[65])==10
    assert m.call('_aspect_serial_close')==0
    assert m.call('_aspect_render_confirm',[3])==0
    cases.append(dict(name='scalar-owner-guards-nesting-keys-and-post-UART-retirement',passed=True))
    out=client.q.ROOT/'build/aspect-abort-owner';out.mkdir(exist_ok=True)
    report=dict(passed=True,cases=cases,runner_sha256=client.sha(client.q.BINARY),
        checker_sha256=client.sha(Path(__file__)),modeled_endpoint_sha256=client.sha(Path(client.__file__)),scope=__doc__)
    (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Abort owner',len(cases),'linked groups PASS')

if __name__=='__main__':main()
