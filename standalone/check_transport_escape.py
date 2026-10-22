#!/usr/bin/env python3
"""Execute real transport cancellation against a modeled standard BIOS ring."""
import argparse,json,shutil,struct
from pathlib import Path
from unicorn.x86_const import *
from check_aspect_render_client import Client,q,sha
ROOT=q.ROOT


class Keys(Client):
    def _interrupt(self,u,number,data):
        if number==0x16:
            function=u.reg_read(UC_X86_REG_AX)>>8
            if function in (0,1,16,17):
                head,tail=struct.unpack('<2H',u.mem_read(0x41a,4))
                if head==tail:
                    assert function in (1,17)
                    u.reg_write(UC_X86_REG_EFLAGS,u.reg_read(UC_X86_REG_EFLAGS)|0x40);return
                value=struct.unpack('<H',u.mem_read(0x400+head,2))[0]
                if function in (0,16):u.mem_write(0x41a,struct.pack('<H',0x1e if head==0x3c else head+2))
                u.reg_write(UC_X86_REG_AX,value);u.reg_write(UC_X86_REG_EFLAGS,u.reg_read(UC_X86_REG_EFLAGS)&~0x40);return
        return super()._interrupt(u,number,data)

    def queue(self,words,start=0):
        head=0x1e+2*start;tail=0x1e+2*((start+len(words))%16)
        self.uc.mem_write(0x41a,struct.pack('<2H',head,tail));self.uc.mem_write(0x480,struct.pack('<2H',0x1e,0x3e))
        for i,word in enumerate(words):self.uc.mem_write(0x41e+2*((start+i)%16),struct.pack('<H',word))

    def queued(self):
        head,tail=struct.unpack('<2H',self.uc.mem_read(0x41a,4));result=[]
        while head!=tail:
            result.append(struct.unpack('<H',self.uc.mem_read(0x400+head,2))[0]);head=0x1e if head==0x3c else head+2
            assert len(result)<=15
        return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--expect-gap',action='store_true');a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    rows=[]
    for mode in (0,16):
      for start in (0,14,15):
        m=Keys();assert m.open()==0;m.call('_runtime_when_reset');m.put('_runtime_keyboard_mode',mode)
        m.queue([0x1071,0x011b,0x1372],start);before=bytes(m.uc.mem_read(0x400,256))
        answer=m.call('_runtime_when_transport_poll')
        assert answer==int(not a.expect_gap) and m.get('_runtime_error')==(0 if a.expect_gap else 13)
        assert m.queued()==([0x1071,0x011b,0x1372] if a.expect_gap else [0x1071,0x1372])
        if a.expect_gap:assert bytes(m.uc.mem_read(0x400,256))==before
        rows.append(dict(mode=mode,head_slot=start,passed=True,remaining=m.queued()))
    manifest=json.loads((q.BINARY.parent/'manifest.json').read_text());assert sha(q.BINARY)==manifest['binary_sha256']
    inputs={**manifest['sources'],str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)),'standalone/check_aspect_render_client.py':sha(ROOT/'standalone/check_aspect_render_client.py')}
    for name,digest in inputs.items():
        assert sha(ROOT/name)==digest;target=out/'inputs'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    result=dict(passed=True,gap_reproduced=a.expect_gap,compatibility_accepted=not a.expect_gap,cases=rows,runner_sha256=sha(q.BINARY),inputs=inputs,
        scope=__doc__+' Real native peek/read wrappers and transport service execute; BIOS INT16 and UART/kernel boundaries modeled. Baseline leaves Escape behind ordinary q; fixed owner removes only Escape, retaining q/r and wrap order. Actual DOS and nonstandard BIOS queues require separate evidence.')
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows),gap=a.expect_gap)))


if __name__=='__main__':main()
