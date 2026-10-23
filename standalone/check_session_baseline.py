#!/usr/bin/env python3
"""Execute retained baseline ownership, damage rejection and bound projection."""
import argparse,hashlib,json,re,struct
from pathlib import Path
from unicorn import UC_HOOK_INTR,UC_HOOK_INSN
from unicorn.x86_const import *
from dos_image import DosImage
from check_setup_model import image
from check_startup_import import terminal_expected
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    base=ROOT/'build/terminal-directory-keys-process-bank-session-capture-projection-bound';m=json.loads((base/'manifest.json').read_text())
    assert m['experimental_session_baseline'] and sha(base/'TERMINAL.EXE')==m['binary_sha256']
    model=DosImage(base/'TERMINAL.EXE',base/'terminal.map');u=model.uc
    listing=(base/'terminal.map').read_text();symbols={n:(model.base_segment+int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
    top=model.offset('terminal_stack_top');source=top-2700;dest=top-1400;sp=top-3000
    store=model.symbols['terminal_baseline_storage'];data=model.symbols['terminal_baseline_image']
    kernel={'payload':None,'position':0,'opened':False}
    def prohibited(*args):raise AssertionError('baseline API attempted interrupt/port IO')
    def interrupt(uc,n,unused):
        if n!=0x21 or kernel['payload'] is None:prohibited()
        ah=uc.reg_read(UC_X86_REG_AX)>>8
        address=uc.reg_read(UC_X86_REG_DS)*16+uc.reg_read(UC_X86_REG_DX)
        if ah==0x3d:
            assert bytes(uc.mem_read(address,9))==b'TEST.PRM\0' and not kernel['opened']
            kernel['opened']=True;kernel['position']=0;result=8
        elif ah==0x3f:
            assert kernel['opened'] and uc.reg_read(UC_X86_REG_BX)==8
            count=uc.reg_read(UC_X86_REG_CX);data_bytes=kernel['payload'][kernel['position']:kernel['position']+count]
            if data_bytes:uc.mem_write(address,data_bytes)
            kernel['position']+=len(data_bytes);result=len(data_bytes)
        elif ah==0x3e:
            assert kernel['opened'] and uc.reg_read(UC_X86_REG_BX)==8
            kernel['opened']=False;result=0
        else:prohibited()
        uc.reg_write(UC_X86_REG_AX,result);uc.reg_write(UC_X86_REG_EFLAGS,uc.reg_read(UC_X86_REG_EFLAGS)&~1)
    u.hook_add(UC_HOOK_INTR,interrupt)
    for op in [UC_X86_INS_IN,UC_X86_INS_OUT]:u.hook_add(UC_HOOK_INSN,prohibited,None,1,0,op)
    def call(name,args=(),flags=0x202,ds=None,ss=None):
        cs,ip=symbols[name]
        registers={UC_X86_REG_CS:cs,UC_X86_REG_IP:ip,UC_X86_REG_DS:model.ds if ds is None else ds,
            UC_X86_REG_SS:model.ds if ss is None else ss,UC_X86_REG_ES:0xb800,UC_X86_REG_SP:sp,
            UC_X86_REG_BP:0xbabe,UC_X86_REG_SI:0x1234,UC_X86_REG_DI:0x5678,
            UC_X86_REG_BX:0x1122,UC_X86_REG_CX:0x3344,UC_X86_REG_DX:0x5566,UC_X86_REG_EFLAGS:flags}
        for r,v in registers.items():u.reg_write(r,v)
        u.mem_write(registers[UC_X86_REG_SS]*16+sp,struct.pack('<'+'H'*(2+len(args)),model.return_offset,model.code_segment,*args))
        before=bytes(u.mem_read(model.data_base,top-8192));model.returned=False
        u.emu_start(cs*16+ip,0,count=200000);assert model.returned and u.reg_read(UC_X86_REG_SP)==sp+4
        preserved=[UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI]
        if name.startswith('_hook_baseline_'):preserved += [UC_X86_REG_ES,UC_X86_REG_BX,UC_X86_REG_CX,UC_X86_REG_DX]
        for r in preserved:assert u.reg_read(r)==registers[r],(name,r)
        assert bytes(u.mem_read(model.data_base,top-8192))==before,'active globals changed'
        return u.reg_read(UC_X86_REG_AX)
    def output():return bytes(u.mem_read(model.data_base+dest,1264))
    def sentinel():u.mem_write(model.data_base+dest,b'X'*1264)
    def sealed(raw,generation,kind):
        h=0xb41d^generation^kind
        for value in struct.unpack('<632H',raw):h=((h<<1)|(h>>15))&65535;h^=value
        return struct.pack('<4H',0xb451,generation,kind,h)+raw
    cases=[]
    def done(name,n):cases.append(dict(case=name,inputs=n,passed=True));print(name,n,flush=True)
    sentinel();assert call('_hook_baseline_copy',[dest])==3 and output()==b'X'*1264
    assert call('_terminal_session_project_bound',[dest])==8 and output()==b'X'*1264
    done('missing-store-and-bound-output-atomic',2)
    raw=image();u.mem_write(model.data_base+source,raw)
    for generation in range(1,33):
        current=bytearray(raw);current[0x480]=generation;current=bytes(current)
        u.mem_write(model.data_base+source,current);sentinel()
        assert call('_hook_baseline_publish',[source,1 if generation==1 else 2])==0
        assert bytes(u.mem_read(store,1272))==sealed(current,generation,1 if generation==1 else 2)
        assert call('_hook_baseline_copy',[dest])==0 and output()==current
        assert bytes(u.mem_read(model.data_base+source,1264))==current
    done('complete-image-publication-generation-kind-seal-and-exact-copy',32)
    original=bytes(u.mem_read(store,1272))
    for offset in range(1264):
        u.mem_write(data+offset,bytes([current[offset]^1]));sentinel()
        assert call('_hook_baseline_copy',[dest])==4 and output()==b'X'*1264,offset
        u.mem_write(data+offset,current[offset:offset+1])
    done('every-image-byte-single-bit-damage-rejected-before-output',1264)
    for offset,value,want in [(0,0,3),(2,0,4),(2,33,4),(4,0,4),(4,3,4),(4,1,4),(6,0,4)]:
        u.mem_write(store,original);u.mem_write(store+offset,struct.pack('<H',value));sentinel()
        assert call('_hook_baseline_copy',[dest])==want and output()==b'X'*1264,(offset,value)
        assert call('_terminal_session_project_bound',[dest])==8 and output()==b'X'*1264
    u.mem_write(store,original);done('header-damage-and-bound-refusal',7)
    for name,args in [('_hook_baseline_publish',[source,1]),('_hook_baseline_copy',[dest]),('_hook_baseline_invalidate',[])]:
        for ctx in [dict(flags=2),dict(flags=0x602),dict(ds=model.ds+1),dict(ds=0xe000,ss=0xe000)]:
            sentinel();assert call(name,args,**ctx)==2
            assert bytes(u.mem_read(store,1272))==original and output()==b'X'*1264
    done('IF0-DF1-foreign-DS-and-foreign-DGROUP-context',12)
    for pointer,kind in [(0,1),(0xfff0,1),(source,0),(source,3)]:
        assert call('_hook_baseline_publish',[pointer,kind])==1 and bytes(u.mem_read(store,1272))==original
    for pointer in [0,0xfff0]:assert call('_hook_baseline_copy',[pointer])==1 and bytes(u.mem_read(store,1272))==original
    done('argument-refusal-retains-previous-image',6)
    assert call('_hook_baseline_invalidate')==0
    sentinel();assert call('_hook_baseline_copy',[dest])==3 and output()==b'X'*1264
    u.mem_write(model.symbols['terminal_baseline_generation'],b'\xff\xff')
    u.mem_write(model.data_base+source,raw);assert call('_hook_baseline_publish',[source,1])==0
    assert bytes(u.mem_read(store,1272))==sealed(raw,1,1)
    done('invalidation-and-nonzero-generation-wrap',2)
    # Populate actual session values, then prove bound projection reads the
    # retained bytes rather than the caller's now-different source buffer.
    serial=struct.unpack('<22H',terminal_expected(raw))
    names=['terminal_port_number','terminal_baud_low','terminal_baud_high','terminal_parity','terminal_data_bits','terminal_stop_bits',
        'uart_software_flow','uart_hardware_flow','csi_terminal_id','attributes_normal_value','attributes_bold_value','attributes_preset_value',
        'attributes_reverse_value','attributes_underline_value','render_autowrap','scroll_enabled','uart_port_rbr','uart_irq_indices',
        'terminal_macro_pause_character','terminal_macro_character_delay_units','terminal_translation_mode','_clipboard_separator']
    for n,v in zip(names,serial):model.put(n,v,1 if n=='terminal_macro_pause_character' else 2)
    model.put('terminal_option_mask',16);model.put('terminal_directory_mode',0);model.put('terminal_directory_context_valid',0)
    model.put('terminal_break_delay_units',350)
    u.mem_write(model.symbols['_terminal_transfer_preferences'],struct.pack('<H',0)+b'.\0'.ljust(64,b'\0'))
    u.mem_write(model.data_base+source,b'Z'*1264);sentinel()
    expected=bytearray(raw);struct.pack_into('<H',expected,0x1a4,350)
    assert call('_terminal_session_project_bound',[dest])==0 and output()==expected
    assert bytes(u.mem_read(store,1272))==sealed(raw,1,1)
    done('bound-projection-keeps-accepted-baseline-and-uses-current-BREAK',1)
    for name,args,want in [('_terminal_preferences_read_far',[0]*5,6),('_terminal_directory_preferences_read_far',[0]*10,1)]:
        u.mem_write(model.data_base+source,raw);assert call('_hook_baseline_publish',[source,1])==0
        assert call(name,args)==want
        sentinel();assert call('_hook_baseline_copy',[dest])==3 and output()==b'X'*1264
    for short in [False,True]:
        u.mem_write(model.data_base+source,raw);assert call('_hook_baseline_publish',[source,1])==0
        broken=bytearray(raw);struct.pack_into('<H',broken,0x194,7)
        kernel['payload']=bytes(broken[:-1] if short else broken)
        path=top-2800;s=top-2736;t=top-2650;io=top-2580
        u.mem_write(model.data_base+path,b'TEST.PRM\0');u.mem_write(model.data_base+s,b'S'*44);u.mem_write(model.data_base+t,b'T'*66)
        assert call('_terminal_preferences_read_far',[path,s,0,t,io])==(1 if short else 4)
        assert not kernel['opened'];kernel['payload']=None
        assert bytes(u.mem_read(model.data_base+s,44))==b'S'*44 and bytes(u.mem_read(model.data_base+t,66))==b'T'*66
        sentinel();assert call('_hook_baseline_copy',[dest])==3 and output()==b'X'*1264
    done('invalid-arguments-bad-profile-and-short-import-invalidate-without-publishing',4)
    sources=dict(m['sources'])
    for n in ['standalone/check_session_baseline.py','standalone/dos_image.py','standalone/check_setup_model.py','standalone/check_startup_import.py','standalone/check_modem_import.py','standalone/terminal_config_fixtures.py']:sources[n]=sha(ROOT/n)
    for n,h in sources.items():assert sha(ROOT/n)==h,n
    report=dict(passed=True,inputs=sum(r['inputs'] for r in cases),cases=cases,sources=sources,binary_sha256=m['binary_sha256'],
        scope='Actual linked far baseline store, seal, atomic refusal/copy, bound projection and failed import invalidation. Only three DOS filesystem interrupts are modeled for two malformed import cases; no product routine substituted. Single-bit-per-byte detection is not cryptographic integrity. Successful startup/live setup separately exercised in DOS.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',report['inputs'],'linked baseline cases')
if __name__=='__main__':main()
