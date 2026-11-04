#!/usr/bin/env python3
"""Exact Alt-Y native handler/send, sound switch, modem sender and expansion.
Tone, notice rendering, UART and calibrated/BIOS delay calls are modeled services.
"""
import argparse,hashlib,itertools,json,struct,subprocess,sys
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/config'))
from prm import modem_command_events

UNITS=[('answer','reconstruction/local_controls/auto_answer.asm',0x053a,44,'12116c329829b0d5028db647b00ea37ffb9bd3709825d8129c3a5442e76713af'),
       ('sound','reconstruction/program_sound/switch.asm',0x376d,30,'3f985dab01a32a339e5ba599626a8230c301e4a69fd333fe9d463bdf1ad7c9da'),
       ('send','reconstruction/modem_send/send.asm',0x48cc,104,'e007929f4330589b441dd73a6e2c1356e470a269d9a1f1c7dd2650620deb1fbb'),
       ('expand','reconstruction/modem_commands/expand.asm',0x4934,87,'008b9051520b45049c2a7c95767686eb48fa3951da532a8abc18de9ead0f9b43')]

class Native:
    def __init__(self,code,composed=False):
        self.u=u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000)
        self.composed=composed
        for entry,data in code.items():
            if composed or entry in (0x053a,0x376d):u.mem_write(0x10000+entry,data)
        # Real sound-enable switch; tone implementation is a separate boundary.
        u.mem_write(0x17722,b'\xc2\x04\x00')
        u.mem_write(0x131bb,b'\xc3')
        if composed:
            for entry,size in [(0xab0b,2),(0x6b72,2),(0x6b98,2),(0x610,0)]:
                u.mem_write(0x10000+entry,b'\xc2'+struct.pack('<H',size) if size else b'\xc3')
        else:u.mem_write(0x148cc,b'\xc3')
        u.hook_add(UC_HOOK_CODE,self.observe)
    def word(self,address):return struct.unpack('<H',self.u.mem_read(0x50000+address,2))[0]
    def observe(self,u,at,size,_):
        sp=u.reg_read(UC_X86_REG_SP)
        def arg(index=0):return self.word(sp+2+index*2)
        if at==0x148cc:
            self.calls+=1
            assert arg()==0x1c16 and self.word(0x1d68)==50
            assert self.word(0x1d1a)==self.duplex
            if not self.composed:
                for r,v in [(UC_X86_REG_AX,0xbeef),(UC_X86_REG_BX,0x1234),(UC_X86_REG_CX,0x5678),(UC_X86_REG_DX,0x9abc)]:u.reg_write(r,v)
        elif at==0x17722:self.events.append(('tone',arg(),arg(1)))
        elif at==0x131bb:self.events.append(('notice',arg(),arg(1)))
        elif at in (0x1ab0b,0x16b72,0x16b98,0x10610):
            kind={0x1ab0b:'transmit',0x16b72:'character_delay_units',0x16b98:'pause_bios_tick_changes',0x10610:'echo'}[at]
            self.events.append((kind,arg()+1 if at==0x16b98 else arg()))
        elif at==0x1f000:self.returned=True;u.emu_stop()
    def call(self,pace=0,duplex=0,sound=0,payload=b'ATS0=1^M',pause=126,notice=0x1c,direct=False):
        u=self.u;self.duplex=duplex;self.calls=0;self.events=[];self.returned=False
        for address,value in [(0x1d68,pace),(0x1d1a,duplex),(0x1d40,sound),(0x2078,notice)]:u.mem_write(0x50000+address,struct.pack('<H',value))
        u.mem_write(0x51d66,bytes([pause]));u.mem_write(0x51c16,payload+b'\0')
        u.mem_write(0x51c2f,b'ANSWER-OFF-GUARD\0')
        u.mem_write(0x5dffe,struct.pack('<H',0xf000));u.mem_write(0x5df30,b'GUARD!')
        for r,v in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x5000),(UC_X86_REG_SS,0x5000),(UC_X86_REG_SP,0xdffe),
                    (UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0xcafe),(UC_X86_REG_DI,0xabcd),(UC_X86_REG_EFLAGS,0x202)]:u.reg_write(r,v)
        u.emu_start(0x1053a if direct else 0x10553,0,count=10000)
        assert self.returned and self.calls==1 and u.reg_read(UC_X86_REG_SP)==0xe000
        assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==0x5000
        for r,v in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0xcafe),(UC_X86_REG_DI,0xabcd)]:assert u.reg_read(r)==v
        assert self.word(0x1d68)==pace and self.word(0x1d1a)==duplex and self.word(0x1d40)==sound and self.word(0x2078)==notice
        assert bytes(u.mem_read(0x51c16,len(payload)+1))==payload+b'\0'
        assert bytes(u.mem_read(0x51c2f,17))==b'ANSWER-OFF-GUARD\0'
        assert bytes(u.mem_read(0x5df30,6))==b'GUARD!'
        expected=[]
        if not direct:
            if sound:expected.append(('tone',20,440))
            expected.append(('notice',notice,36))
        if self.composed:
            for event in modem_command_events(payload,pause,50):
                if event[0]=='transmit' and event[1] and duplex:expected.append(('echo',event[1]))
                expected.append(event)
        assert self.events==expected,(payload,duplex,pause,sound,self.events,expected)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--original',type=Path);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
    original=a.original.read_bytes() if a.original else None
    if original:
        assert hashlib.sha256(original).hexdigest()=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
        assert struct.unpack_from('<H',original,153936+0x44e0+0x15*2)[0]==0x0553
        assert struct.unpack_from('<H',original,153936+0x2078)[0]==0x1c
        assert original[153936+0x1c:153936+0x1c+15]==b'AUTO ANSWER...\0'
    code={}
    for name,source,entry,size,digest in UNITS:
        binary=out/(name+'.bin');subprocess.run(['nasm','-fbin','-I'+str(ROOT/'reconstruction/uart')+'/',str(ROOT/source),'-o',str(binary)],check=True)
        data=binary.read_bytes();assert len(data)==size and hashlib.sha256(data).hexdigest()==digest,(name,len(data),hashlib.sha256(data).hexdigest())
        if original:assert data==original[0x1200+entry:0x1200+entry+size]
        code[entry]=data
    subprocess.run(['nasm','-fobj','-DAUTO_ANSWER_OMF','-I'+str(ROOT/'reconstruction/uart')+'/',str(ROOT/UNITS[0][1]),'-o',str(out/'answer.obj')],check=True)
    m=Native(code)
    for pace in range(65536):m.call(pace=pace,duplex=pace^0x55aa,sound=pace&1,notice=(pace+0x1c)&65535)
    print('PASS all65536 saved pacing words, exact50 send pacing and restoration',flush=True)
    for sound in range(65536):m.call(sound=sound,direct=False)
    print('PASS all65536 sound-enable words',flush=True)
    count=0;m=Native(code,True)
    variants=[b'',b'ATS0=1^M',b'AT^MATS0=1^M',b'~AT^@^M',b'A^^B^M',b'\xffA^M',b'A^`B',b'^`']
    for duplex,pace,pause,payload,sound in itertools.product((0,1,2,0x7fff,0x8000,0xffff),(0,1,49,50,51,0x7fff,0x8000,0xffff),(0,13,126,255),variants,(0,1)):
        m.call(pace,duplex,sound,payload,pause);count+=1
    for duplex in (0,1,0xffff):m.call(123,duplex,1,b'ATS0=1^M',direct=True)
    print('PASS composed answer/sound/send/expand:',count,'inputs and3 direct sends',flush=True)
    files=[Path(__file__).resolve(),ROOT/'src/config/prm.py',ROOT/'reconstruction/uart/encodings.inc']+[ROOT/u[1] for u in UNITS]
    r=dict(passed=True,new_native_bytes=44,composed_image_bytes=265,original_compared=bool(original),cases=dict(all_saved_pacing_words=65536,all_sound_enable_words=65536,composed=count,direct_send=3),
           sources={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
           scope=__doc__+'44 exact new bytes with30 existing sound-switch bytes (11 error-switch bytes not traversed),104 sender and87 expander. Actual sound WORD conditional, one notice before send,50 native pacing units, saved pacing/duplex/settings/input/stack preserved, ordinary-only echo before wire; pause and FF/NUL semantics. Notice pixels, tone duration/output, UART and delays modeled. No maintained owner/admission/Alt-Y integration, DOS/BBS/SIP/physical acceptance or deployment.')
    (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS original Auto Answer recovery')

if __name__=='__main__':main()
