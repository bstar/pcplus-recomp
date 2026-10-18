#!/usr/bin/env python3
"""Compare preserved original parser instructions with the linked source module.

Timed receive/unreceive and control-character presentation are fixture callbacks.
Original decimal conversion, parameter reader and transition helper run unchanged.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys

from unicorn import UC_HOOK_CODE
from unicorn.x86_const import (UC_X86_REG_AX, UC_X86_REG_BP, UC_X86_REG_CS,
    UC_X86_REG_IP, UC_X86_REG_SP, UC_X86_REG_EFLAGS)
from check_ansi_freeze import load_image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'standalone'))
from check_ansi import Parser, BINARY


class Original:
    def __init__(self,data):
        self.image=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes()
        assert hashlib.sha256(self.image).hexdigest()=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
        self.uc=load_image(self.image)
        self.ds_base=0x1fb70
        self.data=data
        self.position=0
        self.controls=[]
        self.returned=False
        self.uc.mem_write(self.ds_base+0xcb3c,b'\0'*34)
        for off in [0xcd38,0xceac,0xcee2]:
            self.uc.mem_write(self.ds_base+off,b'\0\0')
        self.uc.hook_add(UC_HOOK_CODE,self._hook)

    def word(self,off):
        return int.from_bytes(self.uc.mem_read(self.ds_base+off,2),'little')

    def _return_callback(self,value=None):
        uc=self.uc
        sp=uc.reg_read(UC_X86_REG_SP)
        target=self.word(sp)
        uc.reg_write(UC_X86_REG_SP,sp+2)
        if value is not None:
            uc.reg_write(UC_X86_REG_AX,value)
        uc.reg_write(UC_X86_REG_IP,target)

    def _hook(self,uc,address,size,_):
        if address==0x1fff0:
            self.returned=True
            uc.emu_stop()
        elif address==0x15ca0:
            value=self.data[self.position] if self.position<len(self.data) else 0xffff
            if value!=0xffff:
                self.position+=1
            self._return_callback(value)
        elif address==0x1abde:
            assert self.position
            self.position-=1
            self._return_callback()
        elif address==0x10610:
            self.controls.append(self.word(uc.reg_read(UC_X86_REG_SP)+2))
            self._return_callback()

    def call(self,address):
        self.uc.reg_write(UC_X86_REG_CS,0x1000)
        self.uc.reg_write(UC_X86_REG_SP,0xf29e)
        self.uc.reg_write(UC_X86_REG_BP,0xbabe)
        self.uc.reg_write(UC_X86_REG_EFLAGS,0x202)
        self.uc.mem_write(self.ds_base+0xf29e,struct.pack('<H',0xfff0))
        self.returned=False
        self.uc.emu_start(address,0,count=100000)
        assert self.returned,f'Original parser did not return at {address:x}'
        return self.uc.reg_read(UC_X86_REG_AX)

    def sequence(self):
        for _ in range(32):
            token=self.call(0x1e3f2)
            bp=self.uc.reg_read(UC_X86_REG_BP)
            if token==ord('A') or (token==ord('S') and self.call(0x1e4a2)==ord('L')):
                count=self.word(0xcb5c)
                return {'token':chr(token),'command':self.word(0xcd38),
                    'parameters':[self.word(0xcb3c+n*2) for n in range(min(count,16))],
                    'private':self.word(0xceac),'secondary':self.word(0xcee2),
                    'count':count,'saved_bp':bp}
        raise AssertionError('Original parser failed to terminate')


def main():
    cases=[]
    vectors=[b'12;34H',b';4q',b'm',b'0m',b'1;;3m',b'65535H',b'?25h',b'>0c',
             b'1\0\x7f\x082H',b'12\x1b[H',b'0'*31+b'H']
    for data in vectors:
        baseline=Original(data);old=baseline.sequence()
        current=Parser(data);new=current.sequence()
        for key in ['token','command','parameters','private','secondary']:
            assert old[key]==new[key],(data,key,old,new)
        assert old['saved_bp']==0xbabe
        assert new['error']==0
        assert baseline.controls==([8] if b'\x08' in data else [])
        cases.append({'input_hex':data.hex(),'behavior_matched':True})
    differences=[]
    for data,error,reason in [(b'0'*32+b'H',1,'32-digit stack-frame overwrite'),
        (b';'*17+b'H',3,'17th parameter overwrites count'),
        (b'65536H',2,'word overflow wraps the original numeric value'),
        (b'12',4,'timeout after partial parameter')]:
        old=Original(data).sequence();new=Parser(data).sequence()
        assert new['token']=='A' and new['error']==error
        if error==1:
            assert old['saved_bp']!=0xbabe
        elif error==3:
            assert old['count']==1
        elif error==2:
            assert old['parameters']==[0]
        elif error==4:
            assert old['token']=='S' and old['command']==0xffff and old['parameters']==[12]
        differences.append({'reason':reason,'original':old,'maintained':new})
    result={'passed':True,'matched_cases':cases,'intentional_differences':differences,
        'original_sha256':hashlib.sha256(Original(b'').image).hexdigest(),
        'linked_parser_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        'scope':'Original and source-linked parameter/decimal/transition instructions in Unicorn; receive and control presentation are fixture callbacks, no live BBS.'}
    (ROOT/'reconstruction/build/ansi-comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':
    main()
