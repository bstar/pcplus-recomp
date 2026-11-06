#!/usr/bin/env python3
"""Compose loaded Chat timing with real parent UART/queue/IRQ/history/recording code.

MZ loading, BIOS time, DOS filesystem and UART hardware are modeled. No product
routine is skipped or patched. Parent main/foreground TEXT keys are not entered.
"""
import argparse,json,re,struct,sys
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
import check_transport as transport
from check_chat_text_transport import TextTransport,recorded
from build_path_session import ROOT,sha


class Composed(TextTransport):
    def attach(self,path):
        self.frozen=self.symbols['redisplay_snapshot'];assert not self.frozen%16
        self.segment=self.frozen//16+1;self.state_at=self.frozen+12288;self.req=self.frozen+13200
        self.uc.mem_write(self.frozen,b'\xa5'*63000)
        raw=path.read_bytes();h=struct.unpack_from('<14H',raw);image=bytearray(raw[h[4]*16:])
        for i in range(h[3]):
            off,seg=struct.unpack_from('<2H',raw,h[12]+i*4);at=seg*16+off
            struct.pack_into('<H',image,at,(struct.unpack_from('<H',image,at)[0]+self.segment)&65535)
        self.uc.mem_write(self.segment*16,bytes(image));self.code_before=bytes(image)
        self.mod={n:(self.segment+int(s,16),int(o,16)) for s,o,n in re.findall(
            r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',path.with_name('PCCHAT.MAP').read_text(),re.M|re.I)}
        self.uc.mem_write(self.state_at,bytes(448));self.uc.mem_write(self.req,bytes(50))
        self.advance_ticks=False;self.tick=100;self.set_tick(100);self.units=[];self.measured=0
        at=lambda n:self.mod[n][0]*16+self.mod[n][1]
        self.uc.hook_add(UC_HOOK_CODE,self.unit,None,at('_chat_timing_one'),at('_chat_timing_one'))
        self.uc.hook_add(UC_HOOK_CODE,self.complete,None,at('chat_timing_complete'),at('chat_timing_complete'))
    def set_tick(self,value):self.tick=value;self.uc.mem_write(0x46c,struct.pack('<I',value))
    def unit(self,u,at,size,user):
        self.units.append(struct.unpack('<H',u.mem_read(self.ds*16+u.reg_read(UC_X86_REG_SP)+4,2))[0])
    def complete(self,u,at,size,user):
        if self.timing()[0]==2:
            self.measured+=1
            if self.measured==55:self.set_tick(self.tick+1)
    def timing(self):return struct.unpack('<4HI3H',self.uc.mem_read(self.state_at+430,18))
    def word(self,offset,value):self.uc.mem_write(self.req+offset,struct.pack('<H',value))
    def pointer(self,offset,linear):self.uc.mem_write(self.req+offset,struct.pack('<2H',linear&15,linear//16))
    def product_sink(self,name):
        seg,off=self.entries[name];self.uc.mem_write(self.req+18,struct.pack('<2H',off,self.base_segment+seg))
    def farcall(self,seg,off,args):
        u=self.uc;words=[self.return_offset,self.code_segment,*args]
        sp=self.offset('terminal_stack_top')-len(words)*2
        u.mem_write(self.data_base+sp,struct.pack('<'+'H'*len(words),*words))
        guards=((UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_BP,0xbabe),
                (UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678))
        for reg,value in (*guards,(UC_X86_REG_CS,seg),(UC_X86_REG_SP,sp),(UC_X86_REG_EFLAGS,0x202)):
            u.reg_write(reg,value)
        self.returned=False;u.emu_start(seg*16+off,0,count=40000000)
        assert self.returned and u.reg_read(UC_X86_REG_SP)==sp+4
        for reg,value in guards:assert u.reg_read(reg)==value,reg
        return u.reg_read(UC_X86_REG_AX)
    def operation(self,op):
        self.word(2,op);return self.farcall(*self.mod['_chat_module_dispatch'],[13200,self.frozen//16])
    def byte_word(self,at):return struct.unpack('<H',self.uc.mem_read(at,2))[0]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('terminal','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve()
    assert binary.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
    manifest=json.loads(binary.with_name('manifest.json').read_text());assert manifest['experimental_chat_timing']
    assert sha(binary)==manifest['binary_sha256'] and manifest['chat_loader']['module']['api_version']==0x103
    transport.BINARY=binary;transport.MAP=binary.with_name('terminal.map')
    m=Composed();m.initialize();assert m.begin_recording()==0;m.put('_redisplay_active',2)
    module=binary.parent/'chat-module/PCCHAT.OVL';m.attach(module);m.word(0,0x103)
    m.pointer(6,m.state_at);m.pointer(10,m.symbols['redisplay_view'])
    for off,value in [(26,4000),(28,25),(30,0x17),(32,0x71),(34,0x17),(36,1),(38,0),(40,1),(44,1)]:m.word(off,value)
    assert m.operation(1)==1;m.word(42,ord('L'));assert m.operation(2)==3
    m.record(0,b'A~^@B',kind=0);source=m.symbols['terminal_action_definitions']+2
    m.pointer(22,source);m.word(48,52);m.word(32,126);m.word(46,3)
    assert m.operation(8)==1;m.uc.mem_write(source,b'X'*52) # Expanded source is owned.
    m.product_sink('_terminal_chat_text_tx_sink');m.pointer(22,0);m.word(46,32)
    m.put('uart_hardware_flow',1);m.cts=False;record_before=m.state()
    m.call('terminal_poll_serial');assert m.operation(9)==0
    m.set_tick(101);assert m.operation(9)==1
    assert not m.tx and m.timing()[0]==3 and m.timing()[5]==0 and m.state()==record_before
    m.enqueue(b'Q');m.call('terminal_poll_serial');assert m.operation(9)==1 and not m.tx
    m.cts=True;m.call('terminal_poll_serial');assert bytes(m.tx)==b'Q' and m.operation(9)==1
    assert m.timing()[5]==0 and m.state()==record_before # Queue delivery is not TEXT pacing.
    m.call('terminal_poll_serial');assert m.operation(9)==2
    assert bytes(m.tx)==b'QA' and m.timing()[5:]==(6,3,2)
    assert m.operation(9)==1 and m.timing()[-1]==1
    assert m.operation(9)==2 and m.timing()[5:]==(5,9,10)
    pause=m.tick;wire_before=bytes(m.tx);key_calls=m.keyboard_calls
    m.receive_irq(b'\0\x80\xff')
    m.uc.mem_write(m.frozen+14500,bytes(range(256)));m.pointer(14,m.frozen+14500)
    m.product_sink('_terminal_chat_sink')
    for _ in range(3):
        value=m.call('uart_receive_byte');m.word(48,value);assert m.operation(3)==1
        assert m.operation(4)==(0 if value==0 else 2)
    frame=m.symbols['redisplay_view']+18*160
    assert bytes(m.uc.mem_read(frame,4))==b'\x80\x17\xff\x17'
    assert bytes(m.tx)==wire_before and m.keyboard_calls==key_calls
    m.word(42,ord('Z'));assert m.operation(2)==0 and m.byte_word(m.state_at+10)==1
    m.product_sink('_terminal_chat_text_tx_sink')
    for n in range(10):
        m.set_tick(pause+n);m.call('terminal_poll_serial');assert m.operation(9)==1 and bytes(m.tx)==wire_before
    m.set_tick(pause+10);m.call('terminal_poll_serial');assert m.operation(9)==3
    assert bytes(m.tx)==b'QA\0' and m.timing()[5]==0 # FF->NUL skips pacing; grant consumed.
    m.call('terminal_poll_serial');assert m.operation(9)==2 and bytes(m.tx)==b'QA\0B'
    assert m.operation(9)==1;assert m.operation(9)==1
    assert m.byte_word(m.state_at+362)==0 and m.byte_word(m.state_at+10)==1
    assert m.units==[512]*61 #55calibration chunks and3units for each ordinary byte.
    assert recorded(m)==b'A\0B' # Ordinary reply/RX are not user transmissions.
    seg,off=m.entries['_chat_module_image_valid']
    assert m.farcall(m.base_segment+seg,off,[m.segment])==1
    assert bytes(m.uc.mem_read(m.segment*16,len(m.code_before)))==m.code_before
    assert bytes(m.uc.mem_read(m.state_at+448,32))==b'\xa5'*32
    assert m.operation(5)==0 and m.timing()==(0,0,0,0,0,0,0,0)
    sources=dict(manifest['sources'])
    for mod in tuple(sys.modules.values()):
        q=Path(getattr(mod,'__file__','') or '/').resolve()
        if q.is_relative_to(ROOT/'standalone') and q.suffix=='.py':sources[str(q.relative_to(ROOT))]=sha(q)
    for n,h in sources.items():assert sha(ROOT/n)==h,n
    out.mkdir();(out/'result.json').write_text(json.dumps(dict(passed=True,binary_sha256=sha(binary),module_sha256=sha(module),
        sources=sources,wire_hex=bytes(m.tx).hex(),recorded_user_hex='410042',native_unit_calls=len(m.units),
        scope=__doc__+' Actual module uses physical parent TX sink, native UART try-write, ordinary reply priority and real recorder, then native history/log for raw RX during pending pause. CTS rejection cannot start pacing; a physical grant is consumed only on success; FF->NUL has no pacing. Same pending local line/canaries/image CRC/abort. Time edge is modeled at completed calibration chunks; echo disabled by explicit test input. Separate actualDOS test covers loader/lifetimes/real BIOS clock. No original echo rendering, foreground shortcut or BBS/physical acceptance.'),indent=2)+'\n')
    print('PASS actual Chat module to parent UART/timing/history/recorder; CTS/queue priority, pause and RX coexist')


if __name__=='__main__':main()
