#!/usr/bin/env python3
"""Exercise linked parameter-reader instructions, including hostile input bounds."""
import hashlib
import json
from pathlib import Path
import random
import struct

from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_BP, UC_X86_REG_SI, UC_X86_REG_DI
from dos_image import DosImage

ROOT = Path(__file__).resolve().parents[1]
BINARY = ROOT / 'build/ansi/PARSER.EXE'
MAP = ROOT / 'build/ansi/parser.map'


class Parser(DosImage):
    def __init__(self, data, chunks=()):
        super().__init__(BINARY,MAP)
        assert len(data) + sum(map(len,chunks)) <= 2048
        self.buffer = bytearray(data)
        self.chunks = list(chunks)
        self.put('ansi_input_pointer',self.offset('ansi_input_buffer'))
        self.put('ansi_input_length',len(data))
        self.uc.mem_write(self.symbols['ansi_input_buffer'],bytes(data) or b'\0')
        self.call('ansi_reset')
        self.uc.hook_add(UC_HOOK_CODE,self._supply_chunk)

    def _supply_chunk(self,uc,address,size,_):
        if address == self.symbols['ansi_next_byte'] and self.chunks and self.get('ansi_input_position') == len(self.buffer):
            part = self.chunks.pop(0)
            self.buffer.extend(part)
            self.uc.mem_write(self.symbols['ansi_input_buffer'],bytes(self.buffer))
            self.put('ansi_input_length',len(self.buffer))

    def step(self):
        token = self.call('ansi_read_parameter')
        assert self.uc.reg_read(UC_X86_REG_BP) == 0xbabe,'BP frame overwritten'
        assert self.uc.reg_read(UC_X86_REG_SI) == 0x1234,'SI not preserved'
        assert self.uc.reg_read(UC_X86_REG_DI) == 0x5678,'DI not preserved'
        assert self.get('ansi_parameter_canary') == 0xa55a,'parameter array overwritten'
        count = self.get('ansi_parameter_count')
        assert count <= 16,'parameter count exceeded capacity'
        parameters = list(struct.unpack('<' + 'H' * count,self.uc.mem_read(self.symbols['ansi_parameters'],count * 2))) if count else []
        return {'token': chr(token), 'command':self.get('ansi_command'),
                'parameters':parameters,'error':self.get('ansi_parse_error'),
                'private':self.get('ansi_private'),'secondary':self.get('ansi_secondary')}

    def sequence(self):
        for _ in range(32):
            state = self.step()
            if state['token'] == 'A':
                return state
            if state['token'] == 'S' and self.call('ansi_parameter_transition') == ord('L'):
                return state
        raise AssertionError('Parameter parse did not terminate')


def run():
    cases = []

    def check(name,operation):
        operation()
        cases.append({'case':name,'passed':True})
        print(name,'passed',flush=True)

    def ordinary():
        for data,parameters,command in [(b'12;34H',[12,34],'H'),(b';4q',[0,4],'q'),
            (b'm',[],'m'),(b'0m',[0],'m'),(b'1;;3m',[1,0,3],'m'),(b'65535H',[65535],'H')]:
            p=Parser(data); state=p.sequence()
            assert state == {'token':'S','command':ord(command),'parameters':parameters,
                             'error':0,'private':0,'secondary':0},(data,state)
    check('ordinary-empty-and-word-sized-parameters',ordinary)

    def prefixes():
        for data,private,secondary in [(b'?25h',1,0),(b'>0c',0,1)]:
            p=Parser(data);first=p.step()
            assert first['token']=='D' and not first['parameters']
            last=p.sequence()
            assert last['private']==private and last['secondary']==secondary and last['error']==0
            assert last['parameters']==([25] if private else [0])
    check('private-and-secondary-prefixes',prefixes)

    def controls():
        p=Parser(b'1\x00\x7f\x082H');state=p.sequence()
        assert state['parameters']==[12] and state['command']==ord('H')
        assert p.get('ansi_control_count')==1 and p.get('ansi_last_control')==8
        p=Parser(b'12\x1b[H');state=p.step()
        assert state['token']=='A' and state['error']==0 and not state['parameters']
        assert p.get('ansi_input_position')==2,'ESC not put back for the outer parser'
    check('embedded-controls-and-escape-putback',controls)

    def split():
        p=Parser(b'1',chunks=[b'2;',b'3',b'4H']);state=p.sequence()
        assert state['parameters']==[12,34] and state['error']==0 and not p.chunks
    check('input-provider-fragment-boundaries',split)

    def bounds():
        for data,error in [(b'0'*32+b'H',1),(b'1'*1024+b'H',1),
            (b'65536H',2),(b'9999999999H',2),(b'12',4),(b'',4)]:
            p=Parser(data);state=p.sequence()
            assert state['token']=='A' and state['error']==error,(data[:40],state)
            assert not state['parameters']
        p=Parser(b'0'*31+b'H');state=p.sequence()
        assert state['parameters']==[0] and state['error']==0
        p=Parser(b';'*16+b'H');state=p.sequence()
        assert state['parameters']==[0]*16 and state['error']==0
        p=Parser(b';'*17+b'H');state=p.sequence()
        assert state['token']=='A' and state['error']==3 and state['parameters']==[0]*16
        p=Parser(b';'.join([b'1']*16)+b'H');state=p.sequence()
        assert state['parameters']==[1]*16 and state['error']==0
        p=Parser(b';'.join([b'1']*17)+b'H');state=p.sequence()
        assert state['token']=='A' and state['error']==3 and state['parameters']==[1]*16
    check('digit-value-parameter-and-timeout-bounds',bounds)

    def numeric_vectors():
        randomizer=random.Random(0x201)
        values=[0,1,9,10,99,100,32767,32768,65534,65535]
        values += [randomizer.randrange(65536) for _ in range(60)]
        for value in values:
            p=Parser(str(value).encode()+b'm');state=p.sequence()
            assert state['parameters']==[value] and state['error']==0
    check('unsigned-decimal-regression-vectors',numeric_vectors)

    result={'passed':True,'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),
            'cases':cases,'scope':'Actual linked parameter-reader/decimal/fixture-host code in Unicorn; no original executable or live modem.'}
    (ROOT/'build/ansi/parameter-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    run()
