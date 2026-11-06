#!/usr/bin/env python3
"""Interleave actual native rendering through the caller-owned cursor exchange.

The source-only diagnostic has a memory continuation provider and modeled BIOS.
This is not parent integration, serviced parser ownership or hardware acceptance.
"""
import argparse,json,re,struct,sys
from pathlib import Path
from unicorn.x86_const import *
from check_chat_echo_context import Source,FIELDS
from build_path_session import ROOT,sha

CURSOR=FIELDS[:11]


def state(c):return tuple(c.get(name) for name in CURSOR)


def swap(c,storage,interrupts=True):
    u=c.uc
    listing=c.binary.with_name('input_dispatch.map').read_text()
    match=re.search(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+chat_echo_cursor_swap\s*$',listing,re.M|re.I)
    assert match
    seg,off=c.base_segment+int(match[1],16),int(match[2],16)
    sp=0xe000-4;u.mem_write(c.data_base+sp,struct.pack('<2H',c.return_offset,c.code_segment))
    flags=0x202 if interrupts else 2
    registers={UC_X86_REG_AX:0x1357,UC_X86_REG_BX:0x2468,UC_X86_REG_CX:0x3456,
        UC_X86_REG_DX:0x4567,UC_X86_REG_SI:0x5678,UC_X86_REG_DI:storage&15,
        UC_X86_REG_BP:0x6789,UC_X86_REG_ES:storage//16,UC_X86_REG_DS:c.ds,UC_X86_REG_SS:c.ds}
    for r,v in registers.items():u.reg_write(r,v)
    u.reg_write(UC_X86_REG_EFLAGS,flags);u.reg_write(UC_X86_REG_SP,sp);u.reg_write(UC_X86_REG_CS,seg)
    c.returned=False;u.emu_start(seg*16+off,0,count=100000)
    assert c.returned and u.reg_read(UC_X86_REG_SP)==sp+4
    for r,v in registers.items():assert u.reg_read(r)==v,(r,v,u.reg_read(r))
    assert u.reg_read(UC_X86_REG_EFLAGS)&0x200==flags&0x200


def render(c,data):
    # Complete native parser invocation with explicit fixture-owned continuation
    # bytes. No remote UART/key source is substituted or consumed in this test.
    c.feed(data)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('input','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();binary=a.input.resolve();out=a.output.resolve()
    assert binary.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
    manifest=json.loads(binary.with_name('manifest.json').read_text())
    assert manifest['chat_echo_cursor'] and sha(binary)==manifest['binary_sha256']
    def new(profile,wrap,row,col):
        c=Source(binary);c.binary=binary;c.put('csi_terminal_id',profile);c.put('render_autowrap',wrap);c.position(row,col)
        return c
    sequences=[
        (b'A',b'B',b'C',b'D',b'\tE',b'\rF',b'\nG',b'\x08H',b'\0\x7f\x80\xff'),
        (b'A'*80,b'B',b'C',b'\r\nD'),
        (b'\x1b[1\x08C',b'Z',b'\x1b[D',b'Q'),
        (b'A',b'\x1b[',b'B'), # Memory-provider timeout must still return/restore.
    ]
    cases=[];exchanges=0;operations=0
    for profile in (4,6):
        for wrap in (0,1):
            for number,sequence in enumerate(sequences):
                c=new(profile,wrap,2,79);remote=new(profile,wrap,2,79);local=new(profile,wrap,20,79)
                history=new(profile,wrap,0,0);storage=0x80003
                c.uc.mem_write(storage-16,b'\xa5'*16+struct.pack('<11H',*state(local))+b'\x5a'*16)
                for index,data in enumerate(sequence):
                    # Remote data proceeds in its ordinary native context.
                    remote_data=bytes([ord('a')+index])
                    render(c,remote_data);render(remote,remote_data);render(history,remote_data)
                    assert state(c)==state(remote)
                    outer=state(c);before_history=c.history();pointer=c.get('terminal_history_pointer')
                    swap(c,storage,interrupts=index%2==0);exchanges+=1
                    assert state(c)==state(local)
                    assert c.history()==before_history and c.get('terminal_history_pointer')==pointer
                    render(c,data);render(local,data);render(history,data);operations+=1
                    assert state(c)==state(local)
                    inner=state(c);swap(c,storage,interrupts=index%2==0);exchanges+=1
                    assert state(c)==outer and struct.unpack('<11H',c.uc.mem_read(storage,22))==inner
                    assert c.positions[-1]==(outer[0]<<8)|outer[1]
                    assert c.history()==history.history()
                    assert bytes(c.uc.mem_read(c.video,18*160))==bytes(remote.uc.mem_read(remote.video,18*160))
                    assert bytes(c.uc.mem_read(c.video+20*160,5*160))==bytes(local.uc.mem_read(local.video+20*160,5*160))
                    assert bytes(c.uc.mem_read(storage-16,16))==b'\xa5'*16
                    assert bytes(c.uc.mem_read(storage+22,16))==b'\x5a'*16
                cases.append(dict(profile=profile,autowrap=wrap,sequence=number,passed=True))
    sources=dict(manifest['sources'])
    for mod in tuple(sys.modules.values()):
        q=Path(getattr(mod,'__file__','') or '/').resolve()
        if q.is_relative_to(ROOT/'standalone') and q.suffix=='.py':sources[str(q.relative_to(ROOT))]=sha(q)
    for n,h in sources.items():assert sha(ROOT/n)==h,n
    out.mkdir();(out/'result.json').write_text(json.dumps(dict(passed=True,binary_sha256=sha(binary),cases=cases,
        exchanges=exchanges,local_parser_invocations=operations,register_stack_IF_preserved=True,
        history_remains_shared=True,context_canaries=True,sources=sources,
        scope=__doc__+' Eleven native cursor/cache/deferred words exchanged through actual new8086 assembly. Independent native remote/local instances check both screen regions and all cursor words; a third native instance checks shared interleaved history. Includes high bytes, controls, wrapping, embedded CSI control and memory-provider timeout. Caller supplies coherent plain80-column contexts and owns entire synchronous parser call. No live continuation scheduling, full state isolation, live parent linkage, admission policy, TEXT key binding, BBS or physical acceptance.'),indent=2)+'\n')
    print('PASS',len(cases),'interleaved native-render cases;',exchanges,'cursor exchanges;',operations,'local parser invocations')


if __name__=='__main__':main()
