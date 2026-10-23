#!/usr/bin/env python3
"""Execute the linked session snapshot and check every output byte and rejected context."""
import argparse,hashlib,json,random,struct
from pathlib import Path
from unicorn import UC_HOOK_INTR,UC_HOOK_INSN
from unicorn.x86_const import *
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    base=ROOT/'build/terminal-directory-keys-process-bank-session-capture'
    m=json.loads((base/'manifest.json').read_text());assert m['experimental_session_capture']
    image=DosImage(base/'TERMINAL.EXE',base/'terminal.map');u=image.uc
    def prohibited(*args):raise AssertionError('snapshot attempted interrupt or port IO')
    u.hook_add(UC_HOOK_INTR,prohibited)
    for insn in [UC_X86_INS_IN,UC_X86_INS_OUT]:u.hook_add(UC_HOOK_INSN,prohibited,None,1,0,insn)
    top=image.offset('terminal_stack_top');plan=top-1800;transfer=top-1000;sp=top-2048
    target=image.symbols['terminal_session_capture_far'];cs=target//16;ip=target%16
    # A paragraph-normalized spelling executes the same bank bytes; internal
    # relative control flow and DS-relative state remain original linked code.
    def invoke(p=plan,t=transfer,policy=1,flags=0x202,ds=None,ss=None):
        regs={UC_X86_REG_AX:p,UC_X86_REG_DX:t,UC_X86_REG_BX:policy,UC_X86_REG_CX:0x5678,
              UC_X86_REG_SI:0x1234,UC_X86_REG_DI:0xabcd,UC_X86_REG_BP:0x9876,
              UC_X86_REG_ES:0xb800,UC_X86_REG_DS:image.ds if ds is None else ds,
              UC_X86_REG_SS:image.ds if ss is None else ss,UC_X86_REG_SP:sp,UC_X86_REG_CS:cs,UC_X86_REG_IP:ip,UC_X86_REG_EFLAGS:flags}
        for r,v in regs.items():u.reg_write(r,v)
        u.mem_write(regs[UC_X86_REG_SS]*16+sp,struct.pack('<HH',image.return_offset,image.code_segment))
        image.returned=False;u.emu_start(target,0,count=10000)
        assert image.returned and u.reg_read(UC_X86_REG_SP)==sp+4
        for r in [UC_X86_REG_BX,UC_X86_REG_CX,UC_X86_REG_DX,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_BP,UC_X86_REG_ES,UC_X86_REG_DS,UC_X86_REG_SS]:assert u.reg_read(r)==regs[r],r
        return u.reg_read(UC_X86_REG_AX)
    patches={0:'terminal_port_number',2:'terminal_baud_low',4:'terminal_baud_high',6:'terminal_parity',
        8:'terminal_data_bits',10:'terminal_stop_bits',12:'uart_software_flow',14:'uart_hardware_flow',
        32:'uart_port_rbr',34:'uart_irq_indices',40:'terminal_translation_mode',42:'_clipboard_separator',
        44+366:'terminal_break_delay_units'}
    session={16:'csi_terminal_id',18:'attributes_normal_value',20:'attributes_bold_value',22:'attributes_preset_value',
        24:'attributes_reverse_value',26:'attributes_underline_value',28:'render_autowrap',30:'scroll_enabled',
        38:'terminal_macro_character_delay_units'}
    rnd=random.Random(0x484f4f4b);cases=[]
    for seed in range(32):
        raw=bytes(rnd.randrange(256) for _ in range(628));tr=bytes(rnd.randrange(256) for _ in range(66))
        for name,data in [('terminal_configuration_values',raw[:44]),('terminal_modem_settings',raw[44:412]),('terminal_directory_plan',raw[412:626]),('_terminal_transfer_preferences',tr)]:u.mem_write(image.symbols[name],data)
        values={n:rnd.randrange(65536) for n in set(patches.values())|set(session.values())}
        for n,v in values.items():image.put(n,v)
        pause=rnd.randrange(256);modem_pause=pause^255
        image.put('terminal_macro_pause_character',pause,1);image.put('terminal_modem_pause',modem_pause,1)
        for policy in [0,1]:
            expected=bytearray(raw);expected[626:628]=b'\0\0'
            for at,n in patches.items():struct.pack_into('<H',expected,at,values[n])
            if policy:
                for at,n in session.items():struct.pack_into('<H',expected,at,values[n])
                struct.pack_into('<H',expected,36,pause)
                struct.pack_into('<H',expected,44+14,modem_pause)
            for p,t in [(plan,transfer),(image.offset('terminal_setup_plan'),0)]:
                u.mem_write(image.data_base+p,b'X'*628)
                if t:u.mem_write(image.data_base+t,b'Y'*66)
                before=bytes(u.mem_read(image.data_base,65520))
                assert invoke(p,t,policy)==0
                assert bytes(u.mem_read(image.data_base+p,628))==expected
                if t:assert bytes(u.mem_read(image.data_base+t,66))==tr
                after=bytes(u.mem_read(image.data_base,65520));allowed=set(range(p,p+628))|set(range(sp-32,sp+4))
                if t:allowed.update(range(t,t+66))
                assert all(x==after[i] or i in allowed for i,x in enumerate(before))
                cases.append(dict(seed=seed,policy=policy,setup_destination=not bool(t),passed=True))
    for kw,want in [({'p':0},1),({'p':0xfff0},1),({'p':sp-2},1),({'p':sp},1),({'t':0xfff0},1),
                    ({'p':top-627},1),({'t':top-65},1),({'t':plan+627},1),({'t':plan-65},1),
                    ({'policy':2},1),({'flags':2},2),({'flags':0x602},2),({'ds':image.ds+1},2),({'ds':0xe000,'ss':0xe000},2)]:
        u.mem_write(image.data_base+plan,b'X'*628);u.mem_write(image.data_base+transfer,b'Y'*66)
        before=bytes(u.mem_read(image.data_base,65520));assert invoke(**kw)==want,kw
        after=bytes(u.mem_read(image.data_base,65520))
        assert all(x==after[i] or sp-32<=i<sp+4 for i,x in enumerate(before)),kw
        cases.append(dict(rejected=kw,status=want,passed=True))
    # Adjacent output objects and exact upper stack bound are valid.
    assert invoke(plan,plan+628)==0
    assert invoke(top-628,0)==0
    sources=dict(m['sources'])
    for n in ['standalone/check_session_capture.py','standalone/dos_image.py']:sources[n]=sha(ROOT/n)
    for n,h in sources.items():assert sha(ROOT/n)==h,n
    report=dict(passed=True,inputs=len(cases)+2,cases=cases,sources=sources,binary_sha256=sha(base/'TERMINAL.EXE'),
        scope='Actual linked far snapshot instructions, both policies,128 full-byte outputs and14 rejected geometry/CPU contexts plus two boundaries. No substituted function, IO or hardware access; actual DOS setup workflows are separate.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',report['inputs'],'linked snapshot cases')
if __name__=='__main__':main()
