#!/usr/bin/env python3
"""Observe real native DCD/WHEN service while the native abort reader owns keys.

Only BIOS/UART and the scalar parent endpoint are modeled. No callback replaces
carrier detection, native WHEN triggering, its transmitter or the yes/no body.
"""
import argparse,json,shutil,struct
from pathlib import Path
from unicorn.x86_const import *
import check_aspect_abort_owner as owner

ROOT=owner.client.q.ROOT
sha=owner.client.sha


class Carrier(owner.Keyboard):
    def __init__(self,keys,armed=True):
        self.entered=False;self.idles=0;self.retired=False;self.at_retire=None;self.carrier_reads=[]
        super().__init__([0x011b,*keys,0x1051])
        self.armed=armed

    def _code(self,u,address,size,extra):
        super()._code(u,address,size,extra)
        if address==self.symbols['_runtime_abort_read_key'] and not self.entered:
            self.entered=True;self.registers[0x3fe]=0x1f # DCD down; CTS stays up.
        if address==self.symbols['_aspect_render_confirm']:
            sp=u.reg_read(UC_X86_REG_SP)
            operation=struct.unpack('<H',u.mem_read(self.data_base+sp+2,2))[0]
            if operation==4:self.idles+=1
        if address==self.symbols['_runtime_abort_ui_end']:
            self.at_retire=dict(tx=bytes(self.tx).hex(),armed=self.get('_runtime_when_disconnect_armed'),
                               reads=len(self.carrier_reads),idles=self.idles)
            self.retired=True

    def _input(self,u,port,size,extra):
        value=super()._input(u,port,size,extra)
        if port==0x3fe:
            self.carrier_reads.append(dict(value=value,prompt=self.entered and not self.retired,idles=self.idles))
            self.registers[port]&=0xf0
        return value

    def _interrupt(self,u,number,extra):
        if number==0x16 and self.entered and len(self.reads)==1 and self.idles<4:
            function=u.reg_read(UC_X86_REG_AX)>>8
            if function in (1,17):
                u.reg_write(UC_X86_REG_EFLAGS,u.reg_read(UC_X86_REG_EFLAGS)|0x40)
                return
        return super()._interrupt(u,number,extra)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expect-gap',action='store_true')
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    out=args.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    binary=owner.client.q.BINARY
    manifest=json.loads((binary.parent/'manifest.json').read_text())
    assert sha(binary)==manifest['binary_sha256']
    for name,digest in manifest['sources'].items():
        assert sha(ROOT/name)==digest,name
        target=out/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    for path in [Path(__file__),Path(owner.__file__),Path(owner.client.__file__),binary,binary.parent/'ASPECT.map',binary.parent/'manifest.json']:
        target=out/'inputs'/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
    rows=[]
    for name,keys,yes,armed in [
        ('No',[0x316e],False,True),('Yes',[0x1579],True,True),('Enter',[0x1c0d],False,True),
        ('Escape',[0x011b],False,True),('invalid-extended-No',[0x4800,0x2d78,0x314e],False,True),
        ('unarmed-No',[0x316e],False,False)]:
        m=Carrier(keys,armed);assert m.open()==0;m.call('_runtime_receive_reset')
        address=m.symbols['_runtime_when_records']+3*86
        record=bytearray(86);record[0]=0x32;record[42:47]=b'DROP\0';m.uc.mem_write(address,bytes(record))
        m.put('_runtime_when_disconnect_armed',int(armed));m.requests.clear();m.tx.clear()
        assert m.call('_runtime_when_cancel_poll',limit=4000000)==1
        assert m.at_retire is not None and m.at_retire['idles']>=4
        assert m.get('_runtime_error')==(13 if yes else 0)
        assert m.reads==[0x011b,*keys] and m.keys==[0x1051]
        assert m.get('_runtime_when_last_key')==27
        assert m.requests[0:2]==[(12,0),(12,1)] and m.requests[-1]==(12,3)
        assert not any(op==8 for op,_ in m.requests)
        assert m.uc.reg_read(UC_X86_REG_SP)==0xdfc0
        assert m.uc.reg_read(UC_X86_REG_DS)==m.uc.reg_read(UC_X86_REG_SS)==m.ds
        expected=b'DROP' if armed and not args.expect_gap else b''
        assert bytes.fromhex(m.at_retire['tx'])==expected,(name,m.at_retire)
        assert m.at_retire['armed']==int(armed and args.expect_gap),(name,m.at_retire)
        assert bool([r for r in m.carrier_reads if r['prompt']])==bool(armed and not args.expect_gap)
        if not yes:
            # Normal polling after No must dispatch a previously missed event
            # once; a fixed product must neither repeat it nor steal queuedQ.
            m.put('_runtime_when_keyboard_disabled',1)
            assert m.call('_runtime_when_poll',limit=1000000)==0
            assert m.call('_runtime_when_poll',limit=1000000)==0
            assert bytes(m.tx)==(b'DROP' if armed else b'') and not m.get('_runtime_when_disconnect_armed')
            assert m.keys==[0x1051]
        rows.append(dict(case=name,passed=True,at_retire=m.at_retire,carrier_reads=m.carrier_reads,
                         keys_read=m.reads,keys_retained=m.keys,bells=m.bells))
    for first_error in (0,11):
        class Closed(Carrier):
            def _code(self,u,address,size,extra):
                super()._code(u,address,size,extra)
                if address==self.symbols['_runtime_abort_read_key']:
                    self.put('_aspect_serial_active',0)
                    if first_error:self.put('_runtime_error',first_error)
        m=Closed([]);assert m.open()==0;m.call('_runtime_receive_reset')
        m.put('_runtime_when_disconnect_armed',1);m.requests.clear()
        assert m.call('_runtime_when_cancel_poll',limit=1000000)==1
        assert m.get('_runtime_error')==(first_error or 14)
        assert m.at_retire['armed']==1 and not m.at_retire['tx']
        assert m.requests==[(12,0),(12,1),(12,3)]
        assert not [r for r in m.carrier_reads if r['prompt']]
        assert m.reads==[0x011b] and m.keys==[0x1051]
        rows.append(dict(case='closed-UART-first-error-'+str(first_error),passed=True,
                         error=m.get('_runtime_error'),at_retire=m.at_retire,carrier_reads=m.carrier_reads))
    result=dict(passed=True,gap_reproduced=args.expect_gap,compatibility_accepted=not args.expect_gap,cases=rows,
                runner_sha256=sha(binary),checker_sha256=sha(Path(__file__)),
                frozen_files={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()},
                scope=__doc__+' The same DCD drop occurs only after prompt ownership. A baseline gap means no MSR service/event before answer, not a compatibility pass. No physical modem or actual DOS claim.')
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,gap_reproduced=args.expect_gap,cases=len(rows))))


if __name__=='__main__':main()
