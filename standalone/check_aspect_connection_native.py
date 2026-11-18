#!/usr/bin/env python3
"""Isolated native connection-command CPU proof; no application UART ownership.

Actual recovered wrappers, engine/adoption, selection/manual/attempt bodies,
string readers/writeback, signed decimal formatter and response matcher execute.
UI, sender, clock, keyboard, directory file/cache, reset and KEY/META calls are
controlled boundaries. No DOS/BIOS/ports, analysis EXE or live service executes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess

from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE, UC_HOOK_INTR, UC_HOOK_INSN
from unicorn import __version__ as UNICORN_VERSION
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[1]
# Keep the modeled stack clear of native matcher cursors at 8F58h..8F6Dh.
CODE, DATA, STOP, STACK = 0x10000, 0x40000, 0x200, 0xc000
ORIGINAL = '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
TRANSFORM = bytes.fromhex('b3350bc747291dfb1f7f055917')
HELPERS = [
 ('strings','src/aspect/string_operands.asm',['ASPECT_STRING_FLAT','ASPECT_STRING_UNIT=1'],0xdf04,16),
 ('optional','src/aspect/string_operands.asm',['ASPECT_STRING_FLAT','ASPECT_STRING_UNIT=4'],0xe0e4,16),
 ('farcopy','src/aspect/string_operands.asm',['ASPECT_STRING_FLAT','ASPECT_STRING_UNIT=5'],0x9286,0),
 ('getds','src/aspect/string_operands.asm',['ASPECT_STRING_FLAT','ASPECT_STRING_UNIT=6'],0x76b0,0),
 ('token','src/aspect/numeric_operands.asm',['ASPECT_OPERANDS_FLAT','ASPECT_OPERANDS_UNIT=4'],0xe0f1,16),
 ('itoa','src/aspect/conversion_services.asm',['ASPECT_CONVERSION_SERVICES_FLAT','ASPECT_CONVERSION_SERVICES_UNIT=3'],0x8e6c,0),
 ('decimal','src/aspect/conversion_services.asm',['ASPECT_CONVERSION_SERVICES_FLAT','ASPECT_CONVERSION_SERVICES_UNIT=5'],0xa5e8,0),
 ('upper','reconstruction/directory_dial/uppercase.asm',[],0x9128,0),
 ('strlen','reconstruction/directory_dial/length.asm',[],0x8d18,0),
 ('matcher','reconstruction/modem_responses/match.asm',[],0x4a1d,0),
 ('attempt','reconstruction/modem_responses/attempt.asm',[],0xe8ad,5)]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def literal(text):
    # Authored valid literal fixture: native decoder consumes encoded stride3.
    delta = TRANSFORM
    return b'\xaa'+bytes([(len(text)+0xb3)&255, len(text)+3])+bytes(
        (b+(-delta[((i+1)*3)%13] if ((i+1)*3)%13&1 else delta[((i+1)*3)%13]))&255
        for i,b in enumerate(text))


class Machine:
    def __init__(self, images, units):
        self.u = Uc(UC_ARCH_X86, UC_MODE_16)
        self.u.mem_map(0, 0x100000)
        self.units = units
        self.ranges = []
        for name,start,code in images:
            if name == 'hangup':
                self.hangup = (start,code)
                continue  # Original overlay18 aliases part of overlay5.
            self.u.mem_write(CODE+start,code)
            self.ranges.append((start,start+len(code),name,code))
        self.events = []
        self.engine_flags = []
        self.observations = []
        self.abi = {}
        self.hits = set()
        self.selected = 1
        self.model_selection = True
        self.model_loop = None
        self.expanded = 1
        self.retry_result = 27
        self.keys = []
        self.carriers = [0]
        self.response = b'CONNECTBANNER'
        self.rx = b''
        self.sent = 0
        self.clock = 0
        self.invalid = False
        self.current_record = self.record()
        self.token_at = None
        self.u.hook_add(UC_HOOK_CODE,self.hook)
        self.u.hook_add(UC_HOOK_INTR,lambda u,n,x: self.forbidden(('interrupt',n)))
        self.u.hook_add(UC_HOOK_INSN,lambda *args:self.forbidden('port IN'),None,1,0,UC_X86_INS_IN)
        self.u.hook_add(UC_HOOK_INSN,lambda *args:self.forbidden('port OUT'),None,1,0,UC_X86_INS_OUT)
        self.put(0x4b02,0x5200)
        self.put(0xe38c,0)
        self.put(0xe106,0)
        self.put(0xdd86,0)
        self.write(0x7748,TRANSFORM)
        self.write(0xe650,self.current_record)
        for i in range(15):
            self.write(0x70b4+i*7,b'\0'*6+b'\1')
        for at,text in [(0x4942,b''),(0x69e4,b'MANUAL DIAL'),(0x711d,b' ,;'),(0x7121,b' ,;'),
                        (0x7125,b'0'),(0x1bcb,b'ATDT'),(0x1be4,b'^M'),(0x1bfd,b'HANG'),
                        (0x5100,b'11/18/26'),(0x5150,b'BUILTIN')]:
            self.string(at,text)
        for at,val in [(0x7a74,25),(0x1b9a,1),(0x1b8e,3),(0x1b90,1),(0x1d18,6),
                       (0x1b84,0),(0x1b86,5),(0x1b88,1),(0x1b8a,1),(0x1b8c,8),
                       (0x1d1a,1),(0x1d68,7),(0xd124,0x1234)]:
            self.put(at,val)
        for i in range(11):
            self.write(0x1c48+i*16,bytes(16))
        self.string(0x1c48,b'CONNECT')
        self.string(0x1c48+8*16,b'BUSY')
        for i in range(2):
            self.put(0xdb82+i*4,0x100)
            self.put(0xdb84+i*4,0x6000+i*0x100)
            self.u.mem_write((0x6000+i*0x100)*16+0x100,b'OLD\0'+bytes(77))

    @staticmethod
    def record(meta=False,key=False,direct=False):
        r = bytearray(114)
        r[:6] = b'ENTRY\0'
        r[25:33] = b'5550123\0'
        struct.pack_into('<H',r,46,3)
        r[48:52] = bytes([2,8,1,1])
        r[72:75] = bytes([4,4,int(direct)])
        if key:r[86:90] = b'KEY\0'
        if meta:r[95:100] = b'META\0'
        return bytes(r)

    def forbidden(self,what):
        raise AssertionError(('forbidden external execution',what))

    def put(self,at,value):
        self.u.mem_write(DATA+(at&65535),struct.pack('<H',value&65535))

    def get(self,at):
        return struct.unpack('<H',self.u.mem_read(DATA+(at&65535),2))[0]

    def write(self,at,value):
        self.u.mem_write(DATA+at,bytes(value))

    def text(self,at):
        return bytes(self.u.mem_read(DATA+at,256)).split(b'\0',1)[0]

    def string(self,at,value):
        self.write(at,value+b'\0')

    def arg(self,n=0):
        return self.get(self.u.reg_read(UC_X86_REG_SP)+2+2*n)

    def ret(self,value=0,cleanup=0):
        sp = self.u.reg_read(UC_X86_REG_SP)
        self.u.reg_write(UC_X86_REG_AX,value&65535)
        self.u.reg_write(UC_X86_REG_IP,self.get(sp))
        self.u.reg_write(UC_X86_REG_SP,sp+2+cleanup)

    def event(self,name,*values):
        self.events.append((name,*[x.decode('ascii') if isinstance(x,bytes) else x for x in values]))

    def read(self,count):
        at,n = self.get(0x5200),self.get(0x5202)
        assert count<=n,('authored byte stream truncated',count,n)
        value = bytes(self.u.mem_read(DATA+at,count))
        self.put(0x5200,at+count);self.put(0x5202,n-count)
        return value

    def hook(self,u,address,size,_):
        ip = address-CODE
        if ip == STOP:
            u.emu_stop();return
        if ip == 0xe203:
            self.engine_flags.append(u.reg_read(UC_X86_REG_AX))
        if ip == 0xe1f2:
            self.observations.append(('before_failure',self.get(0xd124)))
        if ip == 0xe0a4:
            self.observations.append(('output_flush',int(bool(self.get(0xdd86))),self.get(0xd124)))
        if ip == 0xe423 and self.model_selection:
            self.event('selection_boundary',self.text(self.arg()))
            self.ret(self.selected);return
        if ip == 0xe5e3 and self.model_loop is not None:
            self.event('loop_boundary',self.text(0xe650),self.text(0xe669))
            self.ret(self.model_loop);return
        thunks = {0xce1f:0xdf04,0xce2b:0xdf0b,0xcd5f:0xe0e4,0xcd47:0xe0a4,
                  0xcdb3:0xe182,0xcfe7:0xe423,0xcff3:0xe556}
        if ip in thunks:
            u.reg_write(UC_X86_REG_IP,thunks[ip]);return
        for start,end,name,code in self.ranges:
            if start<=ip<end:
                self.hits.add(name)
                return
        if self.hangup[0]<=ip<self.hangup[0]+len(self.hangup[1]) and self.hangup_active:
            self.hits.add('hangup');return
        if ip == 0x4cb4:
            self.ret(self.read(1)[0]);return
        if ip == 0x845a:
            dest,width,count,stream = (self.arg(i) for i in range(4))
            assert width == 1 and stream == 0x5200
            self.write(dest,self.read(count));self.ret(count);return
        if ip == 0xda83:
            self.event('builtin',self.arg());self.ret(0x5150,2);return
        if ip in (0x4f90,0x4efb):
            self.invalid=True;u.emu_stop();return
        if ip == 0x8268:
            dest,src=self.arg(),self.arg(1)
            self.string(dest,self.text(src));self.ret(dest);return
        if ip == 0x9888:
            dest,src,count=(self.arg(i) for i in range(3));value=self.text(src)[:count]
            self.write(dest,value+bytes(count-len(value)));self.ret(dest);return
        if ip == 0x97bc:
            at = self.arg()
            if at:self.token_at=at
            assert self.text(self.arg(1)) == b' ,;'
            at=self.token_at
            while self.u.mem_read(DATA+at,1)[0] in b' ,;':at+=1
            if not self.u.mem_read(DATA+at,1)[0]:self.ret(0);return
            end=at
            while self.u.mem_read(DATA+end,1)[0] not in b'\0 ,;':end+=1
            if self.u.mem_read(DATA+end,1)[0]:self.write(end,b'\0');self.token_at=end+1
            else:self.token_at=end
            self.ret(at);return
        if ip == 0xec49:
            for i in range(15):self.write(0x70b4+i*7,b'\0');self.write(0x70ba+i*7,b'\1')
            self.event('clear_selection');self.ret();return
        if ip == 0xec61:
            slot,dest=self.arg(),self.arg(1)
            self.event('expand_selection',slot,self.expanded)
            self.string(dest,b'5550123');self.ret(self.expanded);return
        if ip == 0xddb6:
            self.event('load_record',self.arg())
            if self.arg():self.write(0xe650,self.current_record)
            self.ret();return
        if ip == 0x36d4:self.event('date');self.ret(0x5100);return
        if ip in (0xdd94,0xdd28):
            self.event('store_cache' if ip==0xdd94 else 'persist',self.arg(),*([] if ip==0xdd94 else [self.arg(1)]))
            self.ret();return
        if ip in (0x20a4,0xbae7,0x0cd2):
            self.event({0x20a4:'reset',0xbae7:'KEY',0x0cd2:'META'}[ip],*([self.arg()] if ip==0x20a4 else []))
            self.ret();return
        if ip == 0xaa5c:
            value=self.carriers.pop(0) if len(self.carriers)>1 else self.carriers[0]
            self.event('carrier',value);self.ret(value);return
        if ip == 0xabca:
            self.event('rx_flush');self.rx=b'';self.put(0x8e20,0);self.ret();return
        if ip == 0x48cc:
            self.event('send',self.text(self.arg()),self.get(0x1d68),self.get(0x1d1a))
            self.sent+=1
            if self.sent==3:self.rx=self.response;self.put(0x8e20,len(self.rx))
            self.ret();return
        if ip == 0xaad9:
            assert self.arg()==1 and self.rx
            value,self.rx=self.rx[0],self.rx[1:];self.put(0x8e20,len(self.rx));self.ret(value);return
        if ip == 0x3323:
            self.clock+=1;self.ret(self.clock);return
        if ip == 0x6530:self.ret(bool(self.keys));return
        if ip in (0x7878,0x64fe):
            assert self.keys;value=self.keys.pop(0);self.event('key',value);self.ret(value);return
        if ip == 0xeb89:self.event('retry_pause',self.retry_result);self.ret(self.retry_result);return
        if ip == 0xec0e:self.event('abort_modem');self.ret();return
        if ip in (0x3fc7,0x4015):
            self.event('save_screen' if ip==0x3fc7 else 'restore_screen')
            if ip==0x3fc7:u.reg_write(UC_X86_REG_DX,0x1234)
            self.ret(0x5678);return
        services={0x6e5a:'hide',0x6dca:'show',0xde19:'layout25',0xdfcd:'layout43',0xe2a9:'log',
                  0x3a7:'configure',0xadba:'close_port',0x2fb8:'status',0x6b5a:'cursor_push',
                  0x6b42:'cursor_pop',0x31bb:'message',0x82a8:'driver',0x6bb6:'delay',
                  0xeaed:'prepare_attempt',0x3616:'connected',0xac27:'autobaud',
                  0x4056:'frame',0x780e:'choices',0x498b:'time_text',0x6bf0:'draw',
                  0x75e8:'printf',0x6e66:'cursor',0xda4e:'directory_page'}
        if ip in services:
            name=services[ip]
            values=[self.arg()] if name in ('log','driver','prepare_attempt') else []
            if name=='configure':values=[self.get(at) for at in (0x1b84,0x1b86,0x1b88,0x1b8a,0x1b8c,0x1d1a)]
            self.event(name,*values)
            self.ret(0,{'log':2,'choices':2,'frame':6,'draw':6,'cursor':4}.get(name,0));return
        raise AssertionError(('unmodeled native target',hex(ip),self.events[-8:]))

    def run(self,entry,wire=b'',args=(),cleanup=0,flags=0x202):
        self.hangup_active = entry in (0xe759,0x445)
        if self.hangup_active:
            self.u.mem_write(CODE+self.hangup[0],self.hangup[1])
            self.ranges=[r for r in self.ranges if r[2]!='dial-loop']
        self.write(0x5300,wire)
        self.put(0x5200,0x5300);self.put(0x5202,len(wire))
        frame=struct.pack('<'+'H'*(len(args)+1),STOP,*args)
        self.write(STACK,frame+b'CANARY')
        for reg,value in [(UC_X86_REG_CS,CODE>>4),(UC_X86_REG_DS,DATA>>4),
            (UC_X86_REG_SS,DATA>>4),(UC_X86_REG_ES,0x1234),(UC_X86_REG_SP,STACK),
            (UC_X86_REG_BP,0x1357),(UC_X86_REG_SI,0x2468),(UC_X86_REG_DI,0x369c),
            (UC_X86_REG_EFLAGS,flags)]:self.u.reg_write(reg,value)
        self.u.emu_start(CODE+entry,CODE+STOP,count=3000000)
        if not self.invalid:
            assert self.u.reg_read(UC_X86_REG_IP)==STOP,('execution budget',hex(entry),self.events[-8:])
            self.abi=dict(near_return_stack=self.u.reg_read(UC_X86_REG_SP)==STACK+2+cleanup,
                BP_preserved=self.u.reg_read(UC_X86_REG_BP)==0x1357,
                SI_DI_preserved=self.u.reg_read(UC_X86_REG_SI)==0x2468 and self.u.reg_read(UC_X86_REG_DI)==0x369c,
                caller_frame_canary=bytes(self.u.mem_read(DATA+STACK,len(frame)+6))==frame+b'CANARY',
                IF_preserved_DF_clear=self.u.reg_read(UC_X86_REG_EFLAGS)&0x600 == flags&0x200)
            assert all(self.abi.values()),self.abi
        assert self.u.reg_read(UC_X86_REG_DS)==self.u.reg_read(UC_X86_REG_SS)==DATA>>4
        self.abi['DS_SS_contract']=True
        return self.u.reg_read(UC_X86_REG_AX)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--original',type=Path)
    args=parser.parse_args();out=args.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    prov=json.loads((ROOT/'reconstruction/aspect_connection_commands/provenance.json').read_text())
    original=args.original.read_bytes() if args.original else None
    if original is not None:assert hashlib.sha256(original).hexdigest()==ORIGINAL
    sources={Path(__file__).resolve(),ROOT/prov['source'],ROOT/'reconstruction/aspect_connection_commands/provenance.json',ROOT/'reconstruction/uart/encodings.inc'}
    images=[];units=[]
    def assemble(name,source,defines,start,offset=None,digest=None):
        path=out/(name+'.bin');sources.add(ROOT/source)
        subprocess.run(['nasm','-fbin','-I'+str(ROOT/'reconstruction/uart')+'/',
            *['-D'+x for x in defines],str(ROOT/source),'-o',str(path)],check=True)
        code=path.read_bytes()
        if digest:assert hashlib.sha256(code).hexdigest()==digest,name
        if original is not None:assert code==original[offset:offset+len(code)],name
        images.append((name,start,code));return dict(name=name,bytes=len(code),sha256=sha(path),entry=hex(start))
    for row in prov['units']:
        units.append(assemble(row['name'],prov['source'],['ASPECT_CONNECTION_FLAT','ASPECT_CONNECTION_UNIT='+str(row['unit'])],
            int(row['entry'],16),row['source_file_offset'],row['sha256']))
    reused=[]
    for name,source,defines,start,overlay in HELPERS:
        offset=(0x1200 if not overlay else 109184-0xd0d0 if overlay==16 else 68016-0xe530)+start
        # Overlay5's native attempt is already source-recovered and range-bound.
        if name=='attempt':offset=prov['reused_attempt']['source_file_offset']
        reused.append(assemble(name,source,defines,start,offset,
            prov['reused_attempt']['sha256'] if name=='attempt' else None))
    subprocess.run(['nasm','-fobj','-I'+str(ROOT/'reconstruction/uart')+'/',str(ROOT/prov['source']),'-o',str(out/'connection.obj')],check=True)
    subprocess.run(['nasm','-fobj','-DMODEM_RESPONSES_OMF','-I'+str(ROOT/'reconstruction/uart')+'/',str(ROOT/'reconstruction/modem_responses/attempt.asm'),'-o',str(out/'attempt.obj')],check=True)
    cases=[];coverage=set()
    def done(name,m,checks):
        checks.update(m.abi)
        assert all(checks.values()),(name,checks,m.events)
        coverage.update(m.hits);cases.append(dict(case=name,checks=checks,events=m.events,observations=m.observations))
    # Actual string readers + engine/result/adoption, with only selected result
    # modeled at the list boundary. Global outputs use real far copy/writeback.
    for entry,cmd in [(0x567e,'dial'),(0x568d,'redial')]:
        for selected in (-1,0,1,200):
            for destination in ('none','bank','global'):
                for meta,key in [(False,False),(True,False),(False,True),(True,True)]:
                    m=Machine(images,units);m.selected=selected;m.current_record=m.record(meta,key)
                    m.write(0xe650,m.current_record);m.string(0xd13a,b'1,200');m.string(0xd13a+81,b'OLD')
                    wire=(b'\x64\0' if cmd=='dial' else b'')+(b'\0' if destination=='none' else b'\1'+(b'\x64\1' if destination=='bank' else b'\x8c\0'))
                    value=m.run(entry,wire)
                    target=m.text(0xd13a+81) if destination=='bank' else bytes(m.u.mem_read(0x60100,81)).split(b'\0')[0]
                    expected_flags=(2*key+4*meta) if selected>=0 else 0
                    names=[e[0] for e in m.events]
                    checks=dict(failure=m.get(0xd124)==int(selected<0),engine_flags=m.engine_flags==[expected_flags],
                        optional_output=destination=='none' or target==str(selected).encode(),
                        output_flush=m.get(0xdd86)==0,wire_consumed=m.get(0x5202)==0,
                        selected_index_forwarded=any(e==('selection_boundary','1,200' if cmd=='dial' else '') for e in m.events),
                        accounting=(names.count('persist')==int(selected>0) and names.count('date')==int(selected>0)),
                        accounting_contents=selected<=0 or (m.get(0xe696)==1 and m.text(0xe68d)==b'11/18/26'),
                        adopted_fields=selected<0 or (m.get(0x1d18)==4 and m.get(0x3996)==4),
                        output_after_FAILURE=m.observations[-1:]==[('output_flush',int(destination=='global'),int(selected<0))] if destination!='none' else not any(o[0]=='output_flush' for o in m.observations),
                        no_automatic_script=all(n not in ('execute','auto_script') for n in names),
                        reset=names.count('reset')==int(selected>=0),
                        load_key=names.count('KEY')==int(selected>=0 and key),
                        load_meta=names.count('META')==int(selected>=0 and meta))
                    if 'KEY' in names and 'META' in names:checks['adoption_order']=names.index('reset')<names.index('KEY')<names.index('META')
                    if selected>0:checks['accounting_before_reset']=names.index('load_record')<names.index('date')<names.index('store_cache')<names.index('persist')<names.index('reset')<names.index('show')
                    done(f'{cmd}/{selected}/{destination}/{int(meta)}/{int(key)}',m,checks)
    for selected in (-1,0):
        for kind in ('absent','bank','global','literal','builtin'):
            m=Machine(images,units);m.model_loop=selected;m.string(0xd13a,b'5550123');m.string(0xd13a+81,b'LABEL')
            second={'absent':b'\0','bank':b'\1\x64\1','global':b'\1\x8c\0','literal':b'\1'+literal(b'LABEL'),'builtin':b'\1\x6e\x08'}[kind]
            value=m.run(0x5685,b'\x64\0'+second)
            label={'absent':b'MANUAL DIAL','bank':b'LABEL','global':b'OLD','literal':b'LABEL','builtin':b'BUILTIN'}[kind]
            done(f'mdial/{selected}/{kind}',m,dict(failure=m.get(0xd124)==int(selected<0),no_adoption=value==0 and not any(e[0] in ('reset','KEY','META','persist') for e in m.events),
                manual_record=m.text(0xe650)==label and m.text(0xe669)==b'5550123',
                global_input_preserved=bytes(m.u.mem_read(0x60100,4))==b'OLD\0',
                manual_MODEM=m.u.mem_read(DATA+0xe69a,1)==b'\0',wire_consumed=m.get(0x5202)==0,
                global_pending_not_flushed=bool(m.get(0xdd86))==(kind=='global')))
    for text in (b'1,200',b'a1; b2',b'',b'1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16'):
        m=Machine(images,units);m.model_selection=False;m.model_loop=200;m.string(0x5500,text)
        m.write(0x70b4,b'OLD\0\0\0\0')
        value=m.run(0xe423,args=(0x5500,))
        expected=[t for t in re.split(b'[ ,;]+',text.upper()) if t][:15]
        done('selection/'+text.decode(),m,dict(loop_result=value==200,
            tokens=all(m.text(0x70b4+i*7)==t[:5] and m.u.mem_read(DATA+0x70ba+i*7,1)==b'\0' for i,t in enumerate(expected)),
            empty_retains=bool(text) or m.text(0x70b4)==b'OLD'))
    # Actual complete loop + actual native attempt + response matcher. Only
    # UART read/send, clocks, UI and input sources are modeled explicit peers.
    for mode in ('connect','busy','escape','space','delete','direct','invalid-selection','timeout','exhausted'):
        m=Machine(images,units);m.model_selection=False;m.model_loop=None
        m.current_record=m.record(direct=mode=='direct');m.write(0xe650,m.current_record)
        m.string(0x70b4,b'1');m.write(0x70ba,b'\0');m.string(0x5500,b'1')
        m.expanded=201 if mode=='invalid-selection' else 1
        m.response=b'BUSY' if mode in ('busy','exhausted') else b'' if mode=='timeout' else b'CONNECTBANNER'
        if mode=='exhausted':m.retry_result=0
        if mode in ('escape','space','delete'):m.keys=[{'escape':27,'space':32,'delete':0x5300}[mode]]
        value=m.run(0xe423,args=(0x5500,))
        names=[e[0] for e in m.events]
        success=mode in ('connect','direct')
        checks=dict(result=value==(1 if success else 65535),configuration_before_attempt='configure' not in names or mode=='direct' or names.index('configure')<names.index('send'),
            no_attempt_for_DIRECT=mode!='direct' or m.sent==0,
            banner_retained=mode!='connect' or m.rx==b'BANNER',
            escape_not_script_abort=not m.invalid,
            screen_restored=names.count('restore_screen')==1)
        if mode=='space':checks['space_retry']=('retry_pause',27) in m.events
        if mode=='escape':checks['escape_aborts_modem']=('abort_modem',) in m.events
        done('actual_loop/'+mode,m,checks)
    # Combine entry, operand decode, complete native loop/attempt, publication
    # and real far writeback. Retry delay's zero result allows the native cycle
    # counter itself to exhaust, rather than modeling an exhausted result.
    for cmd,entry in [('dial',0x567e),('redial',0x568d),('mdial',0x5685)]:
        for mode in ('connect','escape','exhausted','direct'):
            if cmd=='mdial' and mode=='direct':continue
            m=Machine(images,units);m.model_selection=False
            m.expanded=0 if cmd=='mdial' else 200 if cmd=='dial' else 1
            r=bytearray(m.record(meta=True,key=True,direct=mode=='direct'));r[104]=2
            m.current_record=bytes(r);m.write(0xe650,m.current_record)
            m.string(0xd13a,b'5550123' if cmd=='mdial' else str(m.expanded).encode())
            m.string(0x70b4,str(m.expanded).encode());m.write(0x70ba,b'\0')
            wire=(b'\x64\0' if cmd!='redial' else b'')+b'\1\x8c\0'
            if mode=='escape':m.keys=[27]
            if mode=='exhausted':m.response=b'BUSY';m.retry_result=0
            try:m.run(entry,wire)
            except Exception as exc:raise AssertionError(('complete command',cmd,mode,m.events)) from exc
            names=[e[0] for e in m.events];success=mode in ('connect','direct')
            target=bytes(m.u.mem_read(0x60100,81)).split(b'\0')[0]
            expected_flags=6 if success and cmd!='mdial' else 0
            checks=dict(complete_native_path={'dial-engine','dial-loop','shared','strings'}.issubset(m.hits),
                native_attempt_or_DIRECT=(mode=='direct' or {'attempt','matcher'}.issubset(m.hits)) if mode!='escape' else 'attempt' in m.hits,
                native_cycle_exhausted=mode!='exhausted' or (m.retry_result==0 and names.count('retry_pause')==1),
                failure=m.get(0xd124)==int(not success),engine_flags=m.engine_flags==[expected_flags],
                output_or_input=target==(b'OLD' if cmd=='mdial' else str(m.expanded if success else -1).encode()),
                global_pending=bool(m.get(0xdd86))==(cmd=='mdial'),
                KEY_META=names.count('KEY')==names.count('META')==int(bool(expected_flags)),
                no_key_meta_on_failure=success or not any(n in names for n in ('KEY','META','persist')),
                retained_banner=mode!='connect' or m.rx==b'BANNER',
                line_applied_before_attempt=names.index('configure')<names.index('send') if mode!='direct' else m.sent==0,
                port_change=cmd=='mdial' or (m.get(0x1b84)==1 and names.index('close_port')<names.index('configure')),
                returned_not_fatal=not m.invalid,
                flush_after_FAILURE=cmd=='mdial' or m.observations[-1:]==[('output_flush',1,int(not success))])
            done('complete_command/'+cmd+'/'+mode,m,checks)
    for gate in (0,1,65535):
        for other in (0,1,65535):
            for before,after in [(0,0),(1,0),(1,1)]:
                for dtr in (0,1):
                    for flags in (2,0x202):
                        m=Machine(images,units);m.put(0x1d78,gate);m.put(0x3986,other);m.put(0x1d72,dtr)
                        m.put(0xd124,0x1234);m.carriers=[before,after];value=m.run(0xe759,flags=flags)
                        blocked=bool(gate and other);names=[e[0] for e in m.events]
                        done(f'hangup/{gate}/{other}/{before}/{after}/{dtr}/{flags}',m,
                            dict(blocked_retains_FAILURE=m.get(0xd124)==(0x1234 if blocked else int(bool(after))),
                                 status_tailcall=names[-1]=='status',
                                 no_effects_when_blocked=not blocked or names==['status'],
                                 command=names.count('send')==int(not blocked and bool(before)),
                                 reconfigure=names.count('configure')==int(not blocked),
                                 rx_flush=names.count('rx_flush')==int(not blocked),
                                 restored_pacing=m.get(0x1d68)==7,
                                 cursor_pair=blocked or names.index('cursor_push')<names.index('message')<names.index('configure')<names.index('rx_flush')<names.index('cursor_pop')<names.index('status'),
                                 DTR_control=names.count('driver')==int(not blocked and bool(dtr)),
                                 send_before_reconfigure='send' not in names or names.index('send')<names.index('configure'),
                                 send_pacing=all(e[2:]==(30,1) for e in m.events if e[0]=='send')))
    for entry,wire in [(0x567e,b'\x63'),(0x568d,b'\1\x63'),(0x5685,b'\x64\0\1\x63')]:
        m=Machine(images,units);m.string(0xd13a,b'1');m.run(entry,wire)
        done('invalid_operand/'+hex(entry),m,dict(actual_invalid=m.invalid,no_engine_effects=not m.events,failure_unchanged=m.get(0xd124)==0x1234))
    identities={str(p.relative_to(ROOT)):sha(p) for p in sorted(sources)}
    result=dict(passed=True,cases=cases,case_count=len(cases),checks=sum(len(c['checks']) for c in cases),
        original_compared=original is not None,original_sha256=ORIGINAL if original is not None else None,
        original_inputs=[str(args.original)] if args.original else [],native_units=units,reused_helpers=reused,
        new_native_bytes=sum(x['bytes'] for x in units),connection_family_bytes=sum(x['bytes'] for x in units)+prov['reused_attempt']['bytes'],
        executed_units=sorted(coverage),sources=identities,
        tools=dict(unicorn=UNICORN_VERSION,nasm=subprocess.check_output(['nasm','-v'],text=True).strip()),
        scope=__doc__+' Near DS=SS/RETn/stack/canary/BP/SI/DI and IF/DF checks apply at every completed entry; ordinary FLAGS and command AX are volatile. Engine AX contains adoption bits before callbacks. Original overlay18 HANGUP aliases overlay5 and is loaded as a separately selected context, not an emulated loader. Selected-result boundary cases are separate from complete-loop/command cases. Abort routines, retry delay, expansion/record/cache/file services and KEY/META/reset callbacks remain modeled; invalid operands stop at the native failure-handler boundary. No application build selection, private settings, physical UART, ASIO handoff, parent lifecycle, actual DOS/executable integration or full-language qualification.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('CONNECTION_NATIVE',len(cases),'cases',result['checks'],'checks',result['connection_family_bytes'],'native bytes',True)


if __name__=='__main__':
    main()
