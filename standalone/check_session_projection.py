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
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--session-controls',action='store_true');a=ap.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    variant='terminal-directory-keys-process-bank-session-capture-projection'+('-bound-registers-controls' if a.session_controls else '')
    base=ROOT/'build'/variant;m=json.loads((base/'manifest.json').read_text())
    if a.session_controls:assert m['experimental_session_controls']
    assert m['experimental_session_projection'] and sha(base/'TERMINAL.EXE')==m['binary_sha256']
    model=DosImage(base/'TERMINAL.EXE',base/'terminal.map');u=model.uc;top=model.offset('terminal_stack_top')
    before_at=top-2650;after_at=top-1350;sp=top-2900
    listing=(base/'terminal.map').read_text();match=re.search(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+_terminal_session_project\s*$',listing,re.M|re.I);assert match
    cs=model.base_segment+int(match[1],16);ip=int(match[2],16);target=cs*16+ip
    symbols={n:(model.base_segment+int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
    def prohibited(*args):raise AssertionError('projection attempted interrupt/port IO')
    u.hook_add(UC_HOOK_INTR,prohibited)
    for insn in [UC_X86_INS_IN,UC_X86_INS_OUT]:u.hook_add(UC_HOOK_INSN,prohibited,None,1,0,insn)
    def write(name,data):u.mem_write(model.symbols[name],data)
    baseline=fixture()
    def farcall(name,args=()):
        segment,offset=symbols[name]
        for r,v in {UC_X86_REG_CS:segment,UC_X86_REG_IP:offset,UC_X86_REG_DS:model.ds,
                    UC_X86_REG_SS:model.ds,UC_X86_REG_SP:sp,UC_X86_REG_EFLAGS:0x202}.items():u.reg_write(r,v)
        u.mem_write(model.data_base+sp,struct.pack('<'+'H'*(2+len(args)),model.return_offset,model.code_segment,*args))
        model.returned=False;u.emu_start(segment*16+offset,0,count=200000)
        assert model.returned and u.reg_read(UC_X86_REG_SP)==sp+4,name
        return u.reg_read(UC_X86_REG_AX)
    def mouse(x,y,offer=False):
        raw=bytearray(baseline);struct.pack_into('<HH',raw,0x4e4,x,y)
        previous=bytes(u.mem_read(model.data_base+before_at,1264))
        u.mem_write(model.data_base+before_at,bytes(raw))
        result=farcall('_terminal_mouse_offer_far' if offer else '_terminal_mouse_stage_far',[before_at,1264])
        u.mem_write(model.data_base+before_at,previous)
        return result
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
        if a.session_controls:
            model.put('_terminal_sound_enabled',int(struct.unpack_from('<H',baseline,0x1bc)[0]!=0))
            assert mouse(8,4)==0
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
        if a.session_controls:struct.pack_into('<HH',expected,0x4e4,8,4)
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
    if a.session_controls:
        initialize()
        assert model.get('mouse_present')==model.get('mouse_scale_x')==model.get('mouse_scale_y')==0
        assert invoke()==(0,oracle(baseline,19200))
        cases.append(dict(absent_driver_uses_accepted_mouse_preferences=True,passed=True))
        for raw_sound in [0,1,0x100,0x8000,0xffff]:
            for live_sound in [0,1]:
                for x,y in [(1,999),(999,1),(8,4),(333,777)]:
                    initialize();assert mouse(x,y)==0
                    raw=bytearray(baseline);struct.pack_into('<H',raw,0x1bc,raw_sound)
                    u.mem_write(model.data_base+before_at,bytes(raw));model.put('_terminal_sound_enabled',live_sound)
                    expected=bytearray(oracle(raw,19200))
                    struct.pack_into('<H',expected,0x1bc,(raw_sound or 1) if live_sound else 0)
                    struct.pack_into('<HH',expected,0x4e4,x,y)
                    status,data=invoke();assert status==0 and data==expected,(raw_sound,live_sound,x,y,status)
                    assert bytes(u.mem_read(model.data_base+before_at,1264))==raw
                    cases.append(dict(sound_word=raw_sound,enabled=live_sound,x=x,y=y,passed=True))
        initialize();assert mouse(333,777,offer=True)==16384
        assert invoke()==(0,oracle(baseline,19200))
        farcall('_terminal_mouse_discard_far')
        assert invoke()==(0,oracle(baseline,19200))
        assert mouse(333,777,offer=True)==16384 and farcall('_terminal_mouse_commit_far')==0
        expected=bytearray(oracle(baseline,19200));struct.pack_into('<HH',expected,0x4e4,333,777)
        assert invoke()==(0,bytes(expected))
        cases.append(dict(offer_discard_commit_selected_preferences=True,passed=True))
        for sound in [2,0xffff]:
            initialize();model.put('_terminal_sound_enabled',sound)
            assert invoke()==(9,b'X'*1264)
            cases.append(dict(rejected='sound-control',value=sound,passed=True))
        # The pinned compiler emits two MOV AX,moffs16 / POP BP / RETF paths
        # in this getter. Decode and verify those operands before injecting
        # damaged private settings; no routine is substituted or offset guessed.
        getter=bytes(u.mem_read(model.symbols['_terminal_mouse_selected_scale'],29))
        assert getter.startswith(b'\x55\x89\xe5\x8b\x46\x06')
        selected=[struct.unpack('<H',v)[0] for v in re.findall(b'\xa1(..)\x5d\xcb',getter,re.S)]
        assert len(selected)==2 and selected[1]==selected[0]+2
        for axis in [0,1]:
            initialize()
            assert farcall('_terminal_mouse_selected_scale',[axis])==[8,4][axis]
            address=model.data_base+selected[axis]
            for value in [0,1000,0xffff]:
                u.mem_write(address,struct.pack('<H',value));u.mem_write(model.data_base+after_at,b'X'*1264)
                assert invoke()==(9,b'X'*1264)
                cases.append(dict(rejected='damaged-selected-mouse',axis=axis,value=value,passed=True))
            u.mem_write(address,struct.pack('<H',[8,4][axis]))
    sources=dict(m['sources'])
    for n in ['standalone/check_session_projection.py','standalone/dos_image.py','standalone/check_setup_model.py','standalone/check_startup_import.py','standalone/check_modem_import.py','standalone/terminal_config_fixtures.py']:sources[n]=sha(ROOT/n)
    for n,h in sources.items():assert sha(ROOT/n)==h,n
    report=dict(passed=True,inputs=len(cases),cases=cases,sources=sources,binary_sha256=m['binary_sha256'],
        session_controls=a.session_controls,
        scope='Linked terminal capture policy1 -> explicit group policy -> real far bridges/decoders -> atomic full-image projection. Independent full-image oracle, group/rate cases, invalid data/pointers, and optional accepted mouse/sound controls including offer/discard/commit. Projection itself performs no interrupt/port IO or global mutation. No terminal HOOK routing, returned commit, BBS/hardware acceptance.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',len(cases),'combined terminal projection cases')
if __name__=='__main__':main()
