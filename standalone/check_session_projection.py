#!/usr/bin/env python3
"""Execute terminal capture -> group policy -> banked PRM projection end to end."""
import argparse,hashlib,json,re,struct
from pathlib import Path
from unicorn import UC_HOOK_INTR,UC_HOOK_INSN
from unicorn.x86_const import *
from dos_image import DosImage
from check_setup_model import image as fixture
from check_startup_import import terminal_expected
from check_modem_import import expected as modem_expected
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    base=ROOT/'build/terminal-directory-keys-process-bank-session-capture-projection';m=json.loads((base/'manifest.json').read_text())
    assert m['experimental_session_projection'] and sha(base/'TERMINAL.EXE')==m['binary_sha256']
    model=DosImage(base/'TERMINAL.EXE',base/'terminal.map');u=model.uc;top=model.offset('terminal_stack_top')
    before_at=top-2650;after_at=top-1350;sp=top-2900
    listing=(base/'terminal.map').read_text();match=re.search(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+_terminal_session_project\s*$',listing,re.M|re.I);assert match
    cs=model.base_segment+int(match[1],16);ip=int(match[2],16);target=cs*16+ip
    def prohibited(*args):raise AssertionError('projection attempted interrupt/port IO')
    u.hook_add(UC_HOOK_INTR,prohibited)
    for insn in [UC_X86_INS_IN,UC_X86_INS_OUT]:u.hook_add(UC_HOOK_INSN,prohibited,None,1,0,insn)
    def write(name,data):u.mem_write(model.symbols[name],data)
    baseline=fixture()
    actual={'terminal_port_number':2,'terminal_baud_low':19200,'terminal_baud_high':0,'terminal_parity':2,
        'terminal_data_bits':7,'terminal_stop_bits':2,'uart_software_flow':1,'uart_hardware_flow':0,
        'uart_port_rbr':0x2f8,'uart_irq_indices':3,'terminal_translation_mode':2,'_clipboard_separator':32,
        'csi_terminal_id':6,'attributes_normal_value':0x1e,'attributes_bold_value':15,'attributes_preset_value':3,
        'attributes_reverse_value':0x70,'attributes_underline_value':1,'render_autowrap':0,'scroll_enabled':0,
        'terminal_macro_character_delay_units':30,'terminal_break_delay_units':350}
    def initialize(mode=0,direct=0,rate=19200):
        write('terminal_configuration_values',terminal_expected(baseline));write('terminal_modem_settings',modem_expected(baseline))
        directory=bytearray(214)
        if mode==64:struct.pack_into('<HH',directory,0,3,direct)
        write('terminal_directory_plan',bytes(directory))
        model.put('terminal_option_mask',mode);model.put('terminal_directory_mode',direct)
        model.put('terminal_directory_context_valid',int(mode==64))
        for n,v in actual.items():model.put(n,v)
        model.put('terminal_baud_low',rate&65535);model.put('terminal_baud_high',rate>>16)
        model.put('terminal_macro_pause_character',126,1);model.put('terminal_modem_pause',126,1)
        write('_terminal_transfer_preferences',struct.pack('<H',1)+b'D:\\FILES\0'.ljust(64,b'\0'))
        u.mem_write(model.data_base+before_at,baseline);u.mem_write(model.data_base+after_at,b'X'*1264)
    def invoke(source=before_at,dest=after_at):
        regs={UC_X86_REG_CS:cs,UC_X86_REG_IP:ip,UC_X86_REG_DS:model.ds,UC_X86_REG_SS:model.ds,
              UC_X86_REG_ES:0xb800,UC_X86_REG_BP:0xbabe,UC_X86_REG_SI:0x1234,UC_X86_REG_DI:0x5678,
              UC_X86_REG_EFLAGS:0x202,UC_X86_REG_SP:sp}
        for r,v in regs.items():u.reg_write(r,v)
        u.mem_write(model.data_base+sp,struct.pack('<4H',model.return_offset,model.code_segment,source,dest))
        old=bytes(u.mem_read(model.data_base,65520));model.returned=False
        u.emu_start(target,0,count=200000)
        assert model.returned and u.reg_read(UC_X86_REG_SP)==sp+4
        for r in [UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI]:assert u.reg_read(r)==regs[r],r
        new=bytes(u.mem_read(model.data_base,65520))
        assert old[:top-8192]==new[:top-8192],'active globals mutated'
        return u.reg_read(UC_X86_REG_AX),bytes(u.mem_read(model.data_base+after_at,1264))
    def oracle(raw,rate):
        expected=bytearray(raw);rates=[300,1200,2400,4800,9600,19200,38400,57600,115200]
        words={0:1,2:rates.index(rate),4:2,6:2,8:7,0x176:0x2f8,0x186:3,0x198:1,0x19a:0,
            0x194:6,0x19c:0,0x19e:0,0x1ae:0x1e,0x1b0:15,0x1b2:3,0x1b4:0x70,0x1b6:1,
            0x1e0:2,0x4ea:32,0x1e4:30,0x1a4:350,0x42c:1}
        for at,v in words.items():struct.pack_into('<H',expected,at,v)
        expected[0x1e2]=126;expected[0x31c:0x325]=b'D:\\FILES\0'
        return expected
    cases=[]
    for mode,direct in [(0,0),(32,0),(64,0),(64,1)]:
        for rate in [300,1200,2400,4800,9600,19200,38400,57600,115200]:
            initialize(mode,direct,rate);status,data=invoke();assert status==0,(mode,direct,rate,status)
            assert data==oracle(baseline,rate),(mode,direct,rate)
            assert bytes(u.mem_read(model.data_base+before_at,1264))==baseline
            cases.append(dict(mode=mode,direct=direct,rate=rate,passed=True))
    for mode,direct in [(0,0),(64,1)]:
        initialize(mode,direct);raw=bytearray(baseline);raw[0xa:0x174]=bytes([255])*(0x174-0xa)
        u.mem_write(model.data_base+before_at,bytes(raw));write('terminal_modem_settings',bytes(368));model.put('terminal_modem_pause',0,1)
        status,data=invoke();assert status==0 and data==oracle(raw,19200)
        cases.append(dict(inactive_corrupt_baseline=mode,passed=True))
    for label,mode,direct,changes,want in [
        ('CLI-and-directory',96,0,{},7),('directory-no-context',64,0,{'terminal_directory_context_valid':0},7),
        ('directory-wrong-mode',64,0,{'terminal_directory_mode':1},7),('serial-stale-context',0,0,{'terminal_directory_context_valid':1},7),
        ('MODEM-invalid-mode',32,1,{},7),('invalid-mode',0,2,{},7),
        ('active-pause-conflict',32,0,{'terminal_modem_pause':33},4),
        ('active-delay-conflict',32,0,{'terminal_macro_character_delay_units':31},4),
        ('unsupported-rate',0,0,{'terminal_baud_low':14400},2),('invalid-serial',0,0,{'terminal_data_bits':9},2)]:
        initialize(mode,direct)
        for n,v in changes.items():model.put(n,v,1 if n=='terminal_modem_pause' else 2)
        status,data=invoke();assert status==want and data==b'X'*1264,(label,status)
        cases.append(dict(rejected=label,status=want,passed=True))
    initialize(32);broken_modem=bytearray(368);struct.pack_into('<H',broken_modem,12,30)
    write('terminal_modem_settings',bytes(broken_modem));status,data=invoke();assert status==3 and data==b'X'*1264
    cases.append(dict(rejected='zero-active-modem',status=3,passed=True))
    for source,dest in [(0,after_at),(before_at,0),(before_at,before_at),(0xfff0,after_at),(before_at,0xfff0)]:
        initialize();status,data=invoke(source,dest);assert status==1 and data==b'X'*1264
        cases.append(dict(rejected='pointer',source=source,dest=dest,passed=True))
    sources=dict(m['sources'])
    for n in ['standalone/check_session_projection.py','standalone/dos_image.py','standalone/check_setup_model.py','standalone/check_startup_import.py','standalone/check_modem_import.py','standalone/terminal_config_fixtures.py']:sources[n]=sha(ROOT/n)
    for n,h in sources.items():assert sha(ROOT/n)==h,n
    report=dict(passed=True,inputs=len(cases),cases=cases,sources=sources,binary_sha256=m['binary_sha256'],
        scope='Linked terminal capture policy1 -> explicit group policy -> real far bridges/decoders -> atomic full-image projection. Independent byte oracle across36 supported group/rate combinations, inactive bad baselines, rejected policies/shared fields/invalid active data/pointers. No interrupt/port IO or global mutation. No baseline loading, terminal HOOK routing, returned commit, BBS/hardware acceptance.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',len(cases),'combined terminal projection cases')
if __name__=='__main__':main()
