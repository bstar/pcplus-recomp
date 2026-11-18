#!/usr/bin/env python3
"""Source-only compact OMF link/CPU measurement; no application connection IO."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import subprocess

from unicorn.x86_const import *
from unicorn import UC_HOOK_MEM_WRITE

ROOT=Path(__file__).resolve().parents[1]
DRIVER=ROOT/'standalone/fixtures/aspect_connection_omf_driver.asm'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


class Pointer(int):
    """An actual compact near pointer, distinct from an original logical offset."""
    def __add__(self,n):return Pointer(int(self)+int(n))
    def __radd__(self,n):return Pointer(int(n)+int(self))
    def __sub__(self,n):return Pointer(int(self)-int(n))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();out=args.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    native=load(ROOT/'standalone/check_aspect_connection_native.py','connection_native_model')
    prov=json.loads((ROOT/'reconstruction/aspect_connection_commands/provenance.json').read_text())
    sources={Path(__file__).resolve(),DRIVER,Path(native.__file__),ROOT/prov['source'],
             ROOT/'reconstruction/aspect_connection_commands/provenance.json',ROOT/'reconstruction/uart/encodings.inc'}
    spans=[]
    for name,old,extent,allocation in re.findall(r'^SPAN (\w+),(0x[0-9a-f]+),(\d+)(?:,(\d+))?$',DRIVER.read_text(),re.M):
        spans.append(dict(name=name,original=int(old,16),extent=int(extent),bytes=int(allocation or extent)))
    original_symbols={name:int(value,16) for name,value in prov['data_bindings'].items()}
    original_symbols.update({r['OMF_symbol']:int(r['original_near'],16) for r in prov['call_bindings'].values()})
    images=[];objects=[];texts=[];adaptations=[]
    def prepare(name,source,defines=(),selected=None,unit_macro=None):
        source=ROOT/source;sources.add(source);text=source.read_text()
        original_symbols.update({n:int(v,16) for n,v in re.findall(r'^%define (\w+) (0x[0-9a-f]+)\s*$',text,re.M)})
        if selected is not None:
            text=text.replace('%define '+unit_macro+' 0','%define '+unit_macro+' 999')
            text=re.sub(r'%if '+unit_macro+r'=0 \|\| '+unit_macro+r'=(\d+)',
                        lambda m:'%if '+str(int(int(m[1]) in selected)),text)
        staged=out/(name+'-input.asm');staged.write_text(text)
        processed=subprocess.check_output(['nasm','-E','-I'+str(ROOT/'reconstruction/uart')+'/',
            *['-D'+v for v in defines],str(staged)],text=True)
        processed=re.sub(r'^%line.*\n','',processed,flags=re.M)
        processed=re.sub(r'^\[(global|extern) (.*)\]$',r'\1 \2',processed,flags=re.M)
        labels=set(re.findall(r'^(\w+):',processed,re.M))
        body=re.sub(r'^(?:extern|global) .*\n','',processed,flags=re.M)
        filtered=[]
        for line in processed.splitlines():
            m=re.match(r'(extern|global) (.*)',line)
            if m:
                names=[n.strip() for n in m[2].split(',')]
                names=[n for n in names if (n in labels if m[1]=='global' else re.search(r'\b'+re.escape(n)+r'\b',body))]
                if not names:continue
                line=m[1]+' '+','.join(names)
            filtered.append(line)
        staged=out/(name+'.asm');staged.write_text('\n'.join(filtered)+'\n');texts.append(staged.read_text())
        obj=out/(name+'.obj');subprocess.run(['nasm','-fobj',str(staged),'-o',str(obj)],check=True);objects.append(obj)
        adaptations.append(dict(source=str(source.relative_to(ROOT)),selected_units=selected,
            generated_sha256=sha(staged),rule='Select existing conditional units; preprocess macros; omit undefined globals and unused extern declarations. No instruction substitution.'))
    prepare('connection',prov['source'])
    prepare('strings','src/aspect/string_operands.asm',selected=[1,4,5,6],unit_macro='ASPECT_STRING_UNIT')
    prepare('operands','src/aspect/numeric_operands.asm',selected=[1,4],unit_macro='ASPECT_OPERANDS_UNIT')
    prepare('conversion','src/aspect/conversion_services.asm',selected=[3,5],unit_macro='ASPECT_CONVERSION_SERVICES_UNIT')
    for name,source,defines in [('upper','reconstruction/directory_dial/uppercase.asm',['DIRECTORY_DIAL_OMF']),
                                ('length','reconstruction/directory_dial/length.asm',['DIRECTORY_DIAL_OMF']),
                                ('matcher','reconstruction/modem_responses/match.asm',['MODEM_RESPONSES_OMF']),
                                ('attempt','reconstruction/modem_responses/attempt.asm',['MODEM_RESPONSES_OMF'])]:
        prepare(name,source,defines)
    exported=set();external=set()
    for text in texts:
        for kind,names in re.findall(r'^(global|extern) (.*)$',text,re.M):
            (exported if kind=='global' else external).update(n.strip() for n in names.split(','))
    entry_symbols={int(r['entry'],16):r['symbol'] for r in prov['units']}
    entry_symbols.update({0xdf04:'aspect_string_read',0xe0e4:'aspect_string_option_flag',0x9286:'aspect_string_far_copy',
        0x76b0:'aspect_string_get_ds',0xe0f1:'aspect_operand_next_token',0x8e6c:'aspect_conversion_itoa',
        0xa5e8:'aspect_conversion_format_long',0x9128:'directory_dial_upper_original',0x8d18:'directory_dial_length_original',
        0x4a1d:'modem_response_match_original',0xe8ad:'modem_dial_attempt_original'})
    code_imports=set(re.findall(r'\b(?:call|jmp)\s+(?:(?:near|far|short)\s+)?(\w+)', '\n'.join(texts)))
    callbacks=[];aliases=[];data=[]
    cleanup={0xda83:2,0xe2a9:2,0x780e:2,0x4056:6,0x6bf0:6,0x6e66:4}
    for name in sorted(external-exported):
        assert name in original_symbols,('unknown import',name)
        old=original_symbols[name]
        span=next((s for s in spans if s['original']<=old<s['original']+s['extent']),None)
        if old in entry_symbols:
            aliases.extend(['global '+name,name+': jmp near '+entry_symbols[old],'extern '+entry_symbols[old]])
        elif span and name not in code_imports:
            data.extend(['global '+name,name+' equ '+span['name']+'+'+str(old-span['original'])])
        else:
            index=len(callbacks);callbacks.append(dict(name=name,original=old,cleanup=cleanup.get(old,0),index=index))
            aliases.extend(['global '+name,name+':',' mov ax,'+str(index),' push ax',' call far controlled_parent_gate',' add sp,2',
                            ' ret '+str(cleanup[old]) if cleanup.get(old,0) else ' ret'])
    (out/'connection_callbacks.inc').write_text('\n'.join(aliases)+'\n')
    (out/'connection_data_bindings.inc').write_text('\n'.join(data)+'\n')
    driver_obj=out/'driver.obj';subprocess.run(['nasm','-fobj','-I'+str(out)+'/',str(DRIVER),'-o',str(driver_obj)],check=True)
    exe=out/'CONNOMF.EXE';mapping=out/'CONNOMF.MAP'
    subprocess.run(['wlink','system','dos','option','quiet','option','start=connection_probe_start',
        'option','map='+str(mapping),'name',str(exe),'file',','.join(str(x) for x in [driver_obj,*objects])],check=True)
    # Public symbol map resolves both code offsets and DGROUP-relative aliases.
    symbols={}
    for seg,offset,name in re.findall(r'^\s*([0-9a-fA-F]{4}):([0-9a-fA-F]{4})[+*]?\s+([\w]+)\s*$',mapping.read_text(),re.M):
        symbols[name]=(int(seg,16),int(offset,16))
    assert 'private_stack_end' in symbols, mapping.read_text()
    image=exe.read_bytes();header=struct.unpack_from('<14H',image)
    assert image[:2]==b'MZ';loadseg=0x1000;loadbase=loadseg*16;payload=bytearray(image[header[4]*16:])
    file_image_bytes=(header[2]-1)*512+(header[1] or 512)-header[4]*16
    footprint=((file_image_bytes+15)//16+header[5])*16
    for i in range(header[3]):
        off,seg=struct.unpack_from('<HH',image,header[12]+4*i);pos=seg*16+off
        struct.pack_into('<H',payload,pos,(struct.unpack_from('<H',payload,pos)[0]+loadseg)&65535)
    code_seg=symbols['connection_probe_start'][0];data_seg=symbols['private_data_header'][0]
    codebase=loadbase+code_seg*16;database=loadbase+data_seg*16
    def address(name):
        seg,offset=symbols[name];return seg*16+offset
    def near_data(name):return address(name)-data_seg*16
    def near_code(name):return address(name)-code_seg*16
    for s in spans:s['offset']=near_data(s['name'])
    for name,old in prov['data_bindings'].items():
        original=int(old,16);span=next(s for s in spans if s['original']<=original<s['original']+s['extent'])
        assert near_data(name)==span['offset']+original-span['original'],('data alias',name)
    code_maps=[]
    def flat(name,source,defines,start,symbol):
        path=out/(name+'.bin');subprocess.run(['nasm','-fbin','-I'+str(ROOT/'reconstruction/uart')+'/',
            *['-D'+d for d in defines],str(ROOT/source),'-o',str(path)],check=True)
        code=path.read_bytes();images.append((name,start,code));code_maps.append((near_code(symbol),near_code(symbol)+len(code),start,name))
    for row in prov['units']:
        flat(row['name'],prov['source'],['ASPECT_CONNECTION_FLAT','ASPECT_CONNECTION_UNIT='+str(row['unit'])],int(row['entry'],16),row['symbol'])
    for name,source,defines,start,_ in native.HELPERS:flat(name,source,defines,start,entry_symbols[start])
    code_maps.append((near_code('aspect_operand_frame_plus'),near_code('aspect_operand_frame_plus')+18,0xd19e,'frame_helpers'))
    # Native aliases are short linked jumps, not controlled callback substitutes.
    alias_maps={near_code(n):original_symbols[n] for n in external-exported if original_symbols[n] in entry_symbols}
    native.CODE=codebase;native.DATA=database
    private_ss=(database>>4);stack_top=near_data('private_stack_end');stack_base=near_data('private_stack_base')
    stop=near_code('connection_probe_stop');parent=0x70000;cases=[];all_hits=set();highwater=[];far_calls=0
    class Linked(native.Machine):
        def offset(self,at):
            if isinstance(at,Pointer):return int(at)
            s=next((s for s in spans if s['original']<=at<s['original']+s['extent']),None)
            assert s is not None,('unmapped logical data',hex(at))
            return s['offset']+at-s['original']
        def put(self,at,value):self.u.mem_write(database+self.offset(at),struct.pack('<H',value&65535))
        def get(self,at):return struct.unpack('<H',self.u.mem_read(database+self.offset(at),2))[0]
        def write(self,at,value):self.u.mem_write(database+self.offset(at),bytes(value))
        def text(self,at):return bytes(self.u.mem_read(database+self.offset(at),256)).split(b'\0',1)[0]
        def __init__(self):
            self.in_parent=False;self.current_callback=None;self.minimum_sp=stack_top;self.callback_count=0;self.linked_hits=set();self.trace=[]
            super().__init__([],[])
            self.ranges=[(start,start+len(code),name,code) for name,start,code in images]
            self.hangup=(0,bytes());self.hangup_active=False
            # Load actual linked code and initialized DATA, preserving authored
            # inputs already placed in the separately linked private BSS.
            code_length=address('private_data_header')-code_seg*16
            self.u.mem_write(codebase,bytes(payload[code_seg*16:code_seg*16+code_length]))
            self.u.mem_write(database+near_data('private_data_header'),bytes(payload[address('private_data_header'):address('private_data_header')+16]))
            self.put(0x4b02,self.offset(0x5200))
            for i in range(2):
                self.put(0xdb82+i*4,self.offset(0xf100+i*81));self.put(0xdb84+i*4,private_ss)
                self.write(0xf100+i*81,b'OLD\0'+bytes(77))
            self.u.mem_write(database+near_data('private_stack_guard_low'),b'L'*16)
            self.u.mem_write(database+near_data('private_stack_guard_high'),b'H'*16)
            self.u.mem_write(parent+0xfe0,b'P'*16);self.u.mem_write(parent+0x1000,b'Q'*16)
            def memory_guard(u,access,at,width,value,unused):
                assert loadbase<=at and at+width<=loadbase+footprint or parent+0xfe0<=at and at+width<=parent+0x1010,('CPU memory outside context',hex(at),width,self.trace)
            self.u.hook_add(UC_HOOK_MEM_WRITE,memory_guard)
        def arg(self,n=0):
            if self.in_parent:
                sp=struct.unpack('<H',self.u.mem_read(codebase+near_code('gate_saved_sp'),2))[0]+10
            else:sp=self.u.reg_read(UC_X86_REG_SP)+2
            return Pointer(struct.unpack('<H',self.u.mem_read(database+sp+2*n,2))[0])
        def read(self,count):
            at,n=self.get(0x5200),self.get(0x5202);assert count<=n
            value=bytes(self.u.mem_read(database+at,count));self.put(0x5200,at+count);self.put(0x5202,n-count);return value
        def ret(self,value=0,cleanup=0):
            self.u.reg_write(UC_X86_REG_AX,value&65535)
            if self.in_parent:
                assert cleanup==self.current_callback['cleanup'],('callback RETn',self.current_callback,cleanup)
                self.u.reg_write(UC_X86_REG_IP,near_code('controlled_parent_return'));return
            sp=self.u.reg_read(UC_X86_REG_SP)
            self.u.reg_write(UC_X86_REG_IP,struct.unpack('<H',self.u.mem_read(database+sp,2))[0])
            self.u.reg_write(UC_X86_REG_SP,sp+2+cleanup)
        def hook(self,u,absolute,size,_):
            ip=absolute-codebase
            self.trace.append((hex(ip),hex(u.reg_read(UC_X86_REG_SP)),hex(u.reg_read(UC_X86_REG_SS))))
            self.trace=self.trace[-20:]
            if u.reg_read(UC_X86_REG_SS)==private_ss and ip!=near_code('controlled_private_restore_sp'):
                sp=u.reg_read(UC_X86_REG_SP);self.minimum_sp=min(self.minimum_sp,sp)
                assert stack_base<=sp<=stack_top,('private stack bounds',hex(sp))
            if ip==stop:u.emu_stop();return
            if ip==near_code('controlled_parent_dispatch'):
                assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==0x7000
                assert u.reg_read(UC_X86_REG_SP)==0x1000
                sp=struct.unpack('<H',u.mem_read(codebase+near_code('gate_saved_sp'),2))[0]
                index=struct.unpack('<H',u.mem_read(database+sp+6,2))[0]
                self.current_callback=callbacks[index];self.in_parent=True;self.callback_count+=1
                logical=self.current_callback['original']
                # Pointer-bearing C read callback validates the relocated FILE.
                if logical==0x845a:
                    dest,width,count,stream=(self.arg(i) for i in range(4))
                    assert width==1 and stream==self.offset(0x5200)
                    self.write(dest,self.read(count));self.ret(count)
                elif logical==0xda83:
                    self.event('builtin',self.arg());self.ret(self.offset(0x5150),2)
                else:native.Machine.hook(self,self.u,codebase+logical,size,None)
                return
            if ip==near_code('controlled_parent_return'):self.in_parent=False;return
            if ip in alias_maps:return
            for start,end,logical,name in code_maps:
                if start<=ip<end:
                    self.linked_hits.add(name)
                    native.Machine.hook(self,self.u,codebase+logical+ip-start,size,None);return
            # Only actual generated gate/stub code may execute otherwise.
            assert 0<=ip<near_code('aspect_connection_dial'),('unexpected code',hex(ip),self.trace,self.events)
        def run(self,entry,wire=b'',args=(),cleanup=0,flags=0x202):
            self.write(0x5300,wire);self.put(0x5200,self.offset(0x5300));self.put(0x5202,len(wire))
            sp=stack_top-32;frame=struct.pack('<'+'H'*(len(args)+1),stop,*args)
            self.u.mem_write(database+sp,frame+b'CANARY')
            code_before=bytearray(self.u.mem_read(codebase,address('private_data_header')-code_seg*16))
            for reg,value in [(UC_X86_REG_CS,codebase>>4),(UC_X86_REG_DS,private_ss),(UC_X86_REG_SS,private_ss),
                (UC_X86_REG_ES,0x1234),(UC_X86_REG_SP,sp),(UC_X86_REG_BP,0x1357),
                (UC_X86_REG_SI,0x2468),(UC_X86_REG_DI,0x369c),(UC_X86_REG_EFLAGS,flags)]:self.u.reg_write(reg,value)
            self.u.emu_start(codebase+near_code(entry),codebase+0x10000,count=3000000)
            assert not self.invalid and self.u.reg_read(UC_X86_REG_IP)==stop
            code_after=bytearray(self.u.mem_read(codebase,len(code_before)))
            for name,width in [('gate_saved_ss',2),('gate_saved_sp',2),('gate_busy',1)]:
                at=near_code(name);code_before[at:at+width]=bytes(width);code_after[at:at+width]=bytes(width)
            self.abi=dict(near_return_stack=self.u.reg_read(UC_X86_REG_SP)==sp+2+cleanup,
                BP_SI_DI=all(self.u.reg_read(reg)==value for reg,value in [(UC_X86_REG_BP,0x1357),(UC_X86_REG_SI,0x2468),(UC_X86_REG_DI,0x369c)]),
                frame_canary=bytes(self.u.mem_read(database+sp,len(frame)+6))==frame+b'CANARY',
                private_DS_SS=self.u.reg_read(UC_X86_REG_DS)==self.u.reg_read(UC_X86_REG_SS)==private_ss,
                IF_DF=self.u.reg_read(UC_X86_REG_EFLAGS)&0x600==flags&0x200,
                private_stack_guards=bytes(self.u.mem_read(database+near_data('private_stack_guard_low'),16))==b'L'*16 and bytes(self.u.mem_read(database+near_data('private_stack_guard_high'),16))==b'H'*16,
                parent_stack_guards=bytes(self.u.mem_read(parent+0xfe0,16))==b'P'*16 and bytes(self.u.mem_read(parent+0x1000,16))==b'Q'*16,
                far_gate_retired=self.u.mem_read(codebase+near_code('gate_busy'),1)==b'\0',
                code_immutable_except_gateway_cache=code_before==code_after,CPU_writes_within_guarded_contexts=True,
                linked_initialized_DATA=bytes(self.u.mem_read(database+near_data('private_data_header'),16))==b'CONNOMF\0'+struct.pack('<4H',1,0,0,0))
            return self.u.reg_read(UC_X86_REG_AX)
    def done(name,m,checks):
        nonlocal far_calls
        checks.update(m.abi);assert all(checks.values()),(name,checks,m.events)
        all_hits.update(m.linked_hits);highwater.append(stack_top-m.minimum_sp);far_calls+=m.callback_count
        cases.append(dict(case=name,checks=checks,events=m.events,observations=m.observations,private_stack_highwater=highwater[-1],controlled_far_calls=m.callback_count))
    for cmd in ('dial','redial'):
        for selected in (-1,0,1,200):
            m=Linked();m.selected=selected;m.current_record=m.record(True,True);m.write(0xe650,m.current_record);m.string(0xd13a,b'1,200')
            wire=(b'\x64\0' if cmd=='dial' else b'')+b'\1\x8c\0'
            m.run('aspect_connection_'+cmd,wire)
            done(cmd+'/'+str(selected),m,dict(result=m.text(0xf100)==str(selected).encode(),FAILURE=m.get(0xd124)==int(selected<0),
                 adoption=m.engine_flags==[6 if selected>=0 else 0],global_flush=m.get(0xdd86)==0))
    for selected in (-1,0):
        for kind,second,label in [('absent',b'\0',b'MANUAL DIAL'),('global',b'\1\x8c\0',b'OLD'),
                                 ('literal',b'\1'+native.literal(b'LABEL'),b'LABEL'),('builtin',b'\1\x6e\x08',b'BUILTIN')]:
            m=Linked();m.model_loop=selected;m.string(0xd13a,b'5550123');m.run('aspect_connection_mdial',b'\x64\0'+second)
            done('mdial/'+str(selected)+'/'+kind,m,dict(label=m.text(0xe650)==label,number=m.text(0xe669)==b'5550123',
                no_adoption=m.engine_flags==[0] and not any(e[0] in ('KEY','META','reset','persist') for e in m.events),FAILURE=m.get(0xd124)==int(selected<0)))
    for cmd in ('dial','redial','mdial'):
        for mode in ('connect','escape','exhausted','direct'):
            if cmd=='mdial' and mode=='direct':continue
            m=Linked();m.model_selection=False;m.expanded=0 if cmd=='mdial' else 200 if cmd=='dial' else 1
            record=bytearray(m.record(True,True,mode=='direct'));record[104]=2;m.current_record=bytes(record);m.write(0xe650,record)
            m.string(0xd13a,b'5550123' if cmd=='mdial' else str(m.expanded).encode());m.string(0x70b4,str(m.expanded).encode());m.write(0x70ba,b'\0')
            if mode=='escape':m.keys=[27]
            if mode=='exhausted':m.response=b'BUSY';m.retry_result=0
            m.run('aspect_connection_'+cmd,(b'\x64\0' if cmd!='redial' else b'')+b'\1\x8c\0')
            success=mode in ('connect','direct');names=[e[0] for e in m.events]
            done('complete/'+cmd+'/'+mode,m,dict(FAILURE=m.get(0xd124)==int(not success),
                published=m.text(0xf100)==(b'OLD' if cmd=='mdial' else str(m.expanded if success else -1).encode()),
                global_pending=bool(m.get(0xdd86))==(cmd=='mdial'),native_engine='dial-engine' in m.linked_hits,
                native_loop='dial-loop' in m.linked_hits,native_attempt=mode=='direct' or 'attempt' in m.linked_hits,
                banner=mode!='connect' or m.rx==b'BANNER',adoption=names.count('KEY')==names.count('META')==int(success and cmd!='mdial')))
    for blocked in (False,True):
        for before,after in [(0,0),(1,0),(1,1)]:
            for dtr in (0,1):
                m=Linked();m.put(0x1d78,int(blocked));m.put(0x3986,int(blocked));m.put(0x1d72,dtr);m.carriers=[before,after]
                m.run('aspect_connection_hangup');names=[e[0] for e in m.events]
                done(f'hangup/{blocked}/{before}/{after}/{dtr}',m,dict(FAILURE=m.get(0xd124)==(0x1234 if blocked else after),
                    status=names[-1]=='status',DTR=names.count('driver')==int(not blocked and bool(dtr)),
                    send=names.count('send')==int(not blocked and bool(before)),gate_no_effects=not blocked or names==['status']))
    # A second command in the same allocation retains list bytes and flags.
    # The one successful slot is already consumed, so empty REDIAL exhausts.
    # This deliberately says nothing about unload/reload persistence.
    m=Linked();m.model_selection=False;m.expanded=200;m.string(0xd13a,b'200')
    m.run('aspect_connection_dial',b'\x64\0\1\x8c\0')
    first=m.text(0xf100);slots=bytes(m.u.mem_read(database+m.offset(0x70b4),105))
    m.sent=0;m.run('aspect_connection_redial',b'\1\x8c\0')
    done('same_allocation/consumed_list_REDIAL',m,dict(first_selected=first==b'200',
        retained_slots=slots==bytes(m.u.mem_read(database+m.offset(0x70b4),105)),
        exhausted_result=m.text(0xf100)==b'-1' and m.get(0xd124)==1,
        no_new_attempt=m.sent==0,flushed=m.get(0xdd86)==0))
    # MZ's memory contract includes its BSS/stack minimum allocation and loader
    # relocation table; no absent bytes are silently omitted from capacity.
    result=dict(passed=True,case_count=len(cases),checks=sum(len(c['checks']) for c in cases),cases=cases,
        code_bytes=address('private_data_header')-code_seg*16,initialized_data_bytes=16,
        bss_bytes=sum(s['bytes'] for s in spans),private_stack_bytes=4096,stack_guard_bytes=32,
        allocated_image_bytes=footprint,allocated_image_paragraphs=(footprint+15)//16,
        allocation_padding_bytes=footprint-(address('private_data_header')-code_seg*16+16+sum(s['bytes'] for s in spans)+4128),
        fits_8192=footprint<=8192,fits_16384=footprint<=16384,fits_32768=footprint<=32768,
        mz_relocations=header[3],fixup_table_bytes=header[3]*4,mz_header_bytes=header[4]*16,
        image_plus_retained_header_bytes=footprint+header[4]*16,
        minimum_DOS_process_bytes_with_PSP=footprint+256,
        mz_file_bytes=len(image),mz_payload_bytes=file_image_bytes,mz_minalloc_paragraphs=header[5],
        measured_private_stack_highwater=max(highwater),controlled_far_calls=far_calls,executed_units=sorted(all_hits),
        data_spans=spans,verified_native_data_aliases=len(prov['data_bindings']),symbolic_imports=len(external-exported),callbacks=callbacks,source_adaptations=adaptations,
        executable_sha256=sha(exe),map_sha256=sha(mapping),sources={str(s.relative_to(ROOT)):sha(s) for s in sorted(sources)},
        original_inputs=[],scope='Actual linked symbolic OMF code executes with compact private DS=SS and a full4096-byte private stack. Controlled FAR gateway switches to a separate guarded synthetic parent DS=SS/stack then restores the private context. Representative matrix, not the frozen241-case native matrix. CPU writes and executed code are bounded; no CPU-read bounds claim. No DOS/process loader, real parent API, UART/ASIO/IRQ, filesystem/UI, persistent REDIAL state across unloads, application integration or release qualification. Same-allocation REDIAL retention is checked separately. Fixture wire/global buffers and opaque UI resource tokens are included; real native UI strings/code remain external. Stack high-water is observed for this matrix, not a worst-case proof. MZ minimum image allocation excludes PSP and its consumed nonresident relocation/header bytes; both additional sizes are reported. Actual DOS maxalloc policy is not modeled.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('CONNECTION_OMF',len(cases),'cases',result['checks'],'checks',footprint,'bytes',max(highwater),'stack highwater')


if __name__=='__main__':main()
