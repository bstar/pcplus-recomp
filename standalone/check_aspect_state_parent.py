#!/usr/bin/env python3
"""Linked cap26 state replies and origin hooks with explicit external boundaries.

CPU replay of source-built DOS instructions; this is not a DOS EXEC test.
"""
import argparse
import inspect
import json
from pathlib import Path
import re
import struct

from unicorn import UC_HOOK_CODE, UC_HOOK_INTR, UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
import check_terminal_query_parent as query
from check_terminal_query_parent import Parent, ROOT, CHILD_DS, CHILD_PSP, sha, WORDS
from dos_image import DosImage

STATE_FIELDS = ('_aspect_fromddir', '_display_rows_mono')
STATE_GETTERS = ('aspect_state_fromddir', 'aspect_state_mono')


class StateParent(Parent):
    def __init__(self, product):
        self.state_entries = []
        self.geometry_stop = None
        self.geometry_done = False
        self.geometry_bios = 0
        super().__init__(product, capability=26)
        self.allowed += [(self.symbols[n], self.symbols[n]+4) for n in STATE_GETTERS]
        self.allowed.append((self.symbols['drows_native_display_geometry'],self.symbols['drows_native_display_geometry']+176))
        self.geometry_segment=0x1000+int(re.search(r'^([0-9a-f]{4}):[0-9a-f]{4}[*+ ]+\s+drows_native_display_geometry\s*$',(product/'terminal.map').read_text(),re.M|re.I)[1],16)

    def code(self, u, address, size, unused):
        if self.geometry_stop is not None and address==self.geometry_stop:
            self.geometry_done=True;u.emu_stop();return
        for name in STATE_GETTERS:
            if address == self.symbols.get(name):
                self.state_entries.append(name)
        super().code(u, address, size, unused)

    def interrupt(self,u,number,unused):
        if self.geometry_stop is not None:
            assert number==0x10 and u.reg_read(UC_X86_REG_AH)==0x0f
            self.geometry_bios+=1;u.reg_write(UC_X86_REG_AX,0x5003);u.reg_write(UC_X86_REG_BH,0)
            return
        super().interrupt(u,number,unused)

    def geometry_probe(self):
        u=self.uc;sp=self.offset('terminal_stack_top')-64
        u.mem_write(self.data_base+sp,struct.pack('<H',0xfffe))
        for reg,value in ((UC_X86_REG_CS,self.geometry_segment),(UC_X86_REG_DS,self.ds),
                          (UC_X86_REG_SS,self.ds),(UC_X86_REG_SP,sp),(UC_X86_REG_EFLAGS,0x202)):
            u.reg_write(reg,value)
        before=bytes(u.mem_read(0xb8000,8000));self.phase='geometry'
        self.geometry_stop=self.geometry_segment*16+0xfffe;self.geometry_done=False;self.geometry_bios=0
        u.emu_start(self.symbols['drows_native_display_geometry'],0,count=1000)
        assert self.geometry_done and self.geometry_bios==1
        assert u.reg_read(UC_X86_REG_SP)==sp+2
        assert bytes(u.mem_read(0xb8000,8000))==before
        self.geometry_stop=None;self.phase='query'

    def write(self, u, access, address, size, value, unused):
        super().write(u, access, address, size, value, unused)
        if self.phase == 'query':
            for name in STATE_FIELDS:
                at = self.symbols[name]
                assert not (address < at+2 and address+size > at), ('query changed state', name)

    def request(self, *args, **kwargs):
        self.state_entries = []
        return super().request(*args, **kwargs)


class Hooks(DosImage):
    """Execute selected linked caller bodies, never replace their origin writes."""
    def __init__(self, product):
        super().__init__(product/'TERMINAL.EXE', product/'terminal.map')
        listing = (product/'terminal.map').read_text()
        self.entries = {n: (self.base_segment+int(s,16), int(o,16))
                        for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$', listing, re.M|re.I)}
        self.groups = {n: (self.base+int(s,16)*16+int(o,16), int(length,16))
                       for n,s,o,length in re.findall(r'^(\w+_GROUP)\s+([0-9a-f]{4}):([0-9a-f]{4})\s+([0-9a-f]+)\s*$', listing, re.M|re.I)}
        self.allowed = []
        self.models = {}
        self.trace = []
        self.model_events = []
        self.stop = None
        self.done = False
        self.geometry = False
        self.bios_calls = 0
        self.origin_writes = []
        self.origin = self.symbols['_aspect_fromddir']
        self.uc.hook_add(UC_HOOK_CODE, self.code)
        self.uc.hook_add(UC_HOOK_INTR, self.interrupt)
        self.uc.hook_add(UC_HOOK_MEM_WRITE, self.write)

    def span(self, first, last):
        return self.symbols[first], self.symbols[last]

    def group(self, name):
        begin, size = self.groups[name]
        return begin, begin+size

    def return_model(self, value, far):
        u = self.uc
        sp = u.reg_read(UC_X86_REG_SP)
        at = u.reg_read(UC_X86_REG_SS)*16+sp
        frame = struct.unpack('<2H' if far else '<H', u.mem_read(at, 4 if far else 2))
        u.reg_write(UC_X86_REG_AX, value)
        if far:u.reg_write(UC_X86_REG_CS, frame[1])
        u.reg_write(UC_X86_REG_IP, frame[0])
        u.reg_write(UC_X86_REG_SP, sp+(4 if far else 2))

    def code(self, u, address, size, unused):
        if address == self.stop:
            self.done = True;u.emu_stop();return
        if address in self.models:
            name, value, far = self.models[address]
            self.trace.append((name, value, self.get('_aspect_fromddir')))
            self.model_events.append(name)
            self.return_model(value, far);return
        assert any(begin <= address < end for begin,end in self.allowed), ('unmodeled external code', hex(address))
        assert bytes(u.mem_read(address,1))[0] not in (0xe4,0xe5,0xe6,0xe7,0xec,0xed,0xee,0xef,0x6c,0x6d,0x6e,0x6f), ('unexpected port IO',hex(address))
        assert u.reg_read(UC_X86_REG_DS) == u.reg_read(UC_X86_REG_SS) == self.ds

    def interrupt(self, u, number, unused):
        assert self.geometry and number == 0x10 and u.reg_read(UC_X86_REG_AH) == 0x0f, ('unexpected interrupt', number)
        self.bios_calls += 1
        u.reg_write(UC_X86_REG_AX, 0x5003)
        u.reg_write(UC_X86_REG_BH, 0)

    def write(self, u, access, address, size, value, unused):
        if address < self.origin+2 and address+size > self.origin:
            assert address == self.origin and size == 2, ('partial/overlapping origin write', address, size)
            self.origin_writes.append(value)

    def model(self, name, value=0, far=False):
        if name in self.symbols:self.models[self.symbols[name]] = (name,value,far)

    def invoke(self, name, arguments=(), far=False, ax=0, limit=100000):
        u = self.uc
        segment, offset = self.entries[name]
        sentinel = 0xfffe
        self.stop = segment*16+sentinel
        words = [sentinel]+([segment] if far else [])+list(arguments)
        sp = self.offset('terminal_stack_top')-64-len(words)*2
        frame = struct.pack('<'+'H'*len(words), *words)
        u.mem_write(self.data_base+sp, frame+b'CANARY')
        for reg,value in ((UC_X86_REG_CS,segment),(UC_X86_REG_DS,self.ds),
                          (UC_X86_REG_SS,self.ds),(UC_X86_REG_SP,sp),
                          (UC_X86_REG_AX,ax),(UC_X86_REG_EFLAGS,0x202)):
            u.reg_write(reg,value)
        self.done=False;self.returned=False;self.trace=[];self.origin_writes=[]
        neighbors = [(self.origin-2,bytes(u.mem_read(self.origin-2,2))),
                     (self.origin+2,bytes(u.mem_read(self.origin+2,2)))]
        u.emu_start(self.symbols[name], 0, count=limit)
        assert self.done or self.returned, ('no function return', name)
        assert u.reg_read(UC_X86_REG_SP) == sp+(4 if far else 2), name
        assert u.reg_read(UC_X86_REG_DS) == u.reg_read(UC_X86_REG_SS) == self.ds
        assert bytes(u.mem_read(self.data_base+sp,len(frame)+6)) == frame+b'CANARY'
        assert all(bytes(u.mem_read(at,2))==value for at,value in neighbors), 'origin neighbor changed'
        return u.reg_read(UC_X86_REG_AX)


def lifecycle(product):
    cases=[]
    # Startup /E /N and startup chooser execute the same validated directory
    # entry prefix. Only the chooser's actual UI/file result is modeled.
    for mask,entry,choice,want,status in ((0,0,1,0x73a9,0),(128,1,1,0x73a9,8),
            (64,1,1,0x73a9,8),(64|16|32,1,1,0x73a9,8),
            (64|16|128,1,1,0,0),(64|16|128,200,1,0,0),
            (64|16,0,1,0,1),(64|16,0,0,0,0),(64|16,0,2,0,8)):
        m=Hooks(product);m.put('_aspect_fromddir',0x73a9)
        m.put('terminal_option_mask',mask);m.put('terminal_directory_entry',entry)
        m.allowed=[m.span('terminal_select_directory','terminal_load_configuration')]
        m.model('terminal_directory_choose',choice)
        assert m.invoke('terminal_select_directory')==status
        assert m.get('_aspect_fromddir')==want
        assert m.origin_writes==([0] if want==0 else [])
        assert len(m.trace)==int(bool(mask&64 and mask&16 and not mask&32 and not entry))
        cases.append(dict(case='startup-directory-reset',mask=mask,entry=entry,chooser=choice,passed=True))
    for name in (b'\0',b' ',b'LOGIN\0',b'TEST.ASP\0',b'\t\0'):
        for entry in (1,37,200,0x8000,0xffff):
            for refusal in (0,7):
                m=Hooks(product);m.put('_aspect_fromddir',0x6b2d)
                m.put('terminal_directory_context_valid',1)
                m.uc.mem_write(m.symbols['terminal_directory_context'],struct.pack('<H',entry))
                m.uc.mem_write(m.symbols['terminal_directory_context']+252+0x34,name)
                m.allowed=[m.span('terminal_directory_script_connected','terminal_script_start')]
                m.model('terminal_script_start',refusal)
                m.model('_directory_adopt_script_name',0,far=True)
                m.invoke('terminal_directory_script_connected')
                active=name[:1] not in (b'\0',b' ')
                assert m.get('_aspect_fromddir')==(entry if active else 0x6b2d)
                assert m.origin_writes==([entry] if active else [])
                launches=[x for x in m.trace if x[0]=='terminal_script_start']
                assert len(launches)==int(active)
                if active:assert launches[0][2]==entry
                cases.append(dict(case='automatic-entry-before-load',name_hex=name.hex(),entry=entry,loader_result=refusal,passed=True))
    for owner in ('terminal_program_active','terminal_program_pending','_command_menu_active','_redisplay_active'):
        m=Hooks(product);m.put('_aspect_fromddir',37);m.put('terminal_directory_context_valid',1);m.put(owner,1)
        m.allowed=[m.span('terminal_directory_script_connected','terminal_script_start')]
        m.invoke('terminal_directory_script_connected')
        assert m.get('_aspect_fromddir')==37 and not m.origin_writes and not m.trace
        cases.append(dict(case='busy-auto-preserves-origin',owner=owner,passed=True))
    m=Hooks(product);m.put('_aspect_fromddir',37)
    m.allowed=[m.span('terminal_directory_script_connected','terminal_script_start')]
    m.invoke('terminal_directory_script_connected')
    assert m.get('_aspect_fromddir')==37 and not m.origin_writes
    cases.append(dict(case='no-directory-context-preserves-origin',passed=True))
    return cases


def manual(product):
    cases=[]
    for entry in ('AltF5','menu-script'):
        m=Hooks(product);m.put('_aspect_fromddir',200)
        m.allowed=[m.group('REFERENCE_GROUP')]
        for name,far in (('_recording_terminal_inspect',True),('_recording_terminal_initialize',True),
                         ('_command_reference_prepare',True),('_command_reference_event',True),
                         ('_command_reference_unavailable',False)):
            m.model(name,0,far)
        frame=(0,0x8800)
        m.uc.mem_write(0x88000-2,b'AB'+bytes(4000)+b'CD')
        assert m.invoke('_command_menu_event',[0,0x6c00 if entry=='AltF5' else 0,*frame],far=True)==1
        if entry=='menu-script':
            assert m.get('_aspect_fromddir')==200 and not m.origin_writes
            assert m.invoke('_command_menu_event',[1,ord('A'),*frame],far=True)==1
        assert m.get('_aspect_fromddir')==0 and m.origin_writes==[0]
        # Cancel returns through the actual two-level menu/reference state.
        for _ in range(2):m.invoke('_command_menu_event',[1,27,*frame],far=True)
        assert m.get('_command_menu_active')==0 and m.get('_aspect_fromddir')==0
        assert not m.origin_writes
        assert bytes(m.uc.mem_read(0x88000-2,2))==b'AB' and bytes(m.uc.mem_read(0x88000+4000,2))==b'CD'
        cases.append(dict(case='manual-prompt-clear-and-cancel',entry=entry,modeled_boundaries=sorted(set(m.model_events)),passed=True))
    # The recorder's published ABI pins claimed at+156 (foreground.c static
    # assertion). Only inspect's pointer is modeled; the linked record_blocked
    # predicate and both manual-entry branches execute without substitution.
    assert 'offsetof(recording_file,claimed)==156' in (ROOT/'src/recording/foreground.c').read_text()
    for entry in ('AltF5','menu-script'):
        m=Hooks(product);m.put('_aspect_fromddir',200)
        m.allowed=[m.group('REFERENCE_GROUP')]
        for name,far in (('_recording_terminal_initialize',True),('_command_reference_prepare',True),
                         ('_command_reference_event',True),('_command_reference_unavailable',False)):
            m.model(name,0,far)
        m.model('_recording_terminal_inspect',m.offset('_recording_terminal_owner'),far=True)
        owner=m.symbols['_recording_terminal_owner']
        m.uc.mem_write(owner,bytes(326));m.uc.mem_write(owner+136,b'\1\0');m.uc.mem_write(owner+156,b'\1\0')
        frame=(0,0x8800);m.uc.mem_write(0x88000-2,b'AB'+bytes(4000)+b'CD')
        assert m.invoke('_command_menu_event',[0,0x6c00 if entry=='AltF5' else 0,*frame],far=True)==1
        if entry=='menu-script':assert m.invoke('_command_menu_event',[1,ord('A'),*frame],far=True)==1
        assert m.get('_aspect_fromddir')==200 and not m.origin_writes
        for _ in range(2):m.invoke('_command_menu_event',[1,27,*frame],far=True)
        assert m.get('_aspect_fromddir')==200 and not m.origin_writes and not m.get('_command_menu_active')
        assert bytes(m.uc.mem_read(0x88000-2,2))==b'AB' and bytes(m.uc.mem_read(0x88000+4000,2))==b'CD'
        cases.append(dict(case='recording-blocked-manual-keeps-origin',entry=entry,modeled_boundaries=sorted(set(m.model_events)),passed=True))
    for owner in ('terminal_program_active','terminal_program_pending'):
        m=Hooks(product);m.put('_aspect_fromddir',200);m.put(owner,1)
        m.allowed=[m.group('CONFIG_GROUP'),m.span('terminal_redisplay_key','terminal_redisplay_before')]
        if 'terminal_gateway_key_far' in m.symbols:
            m.allowed.append(m.span('terminal_gateway_key_far','_gateway_video_ready'))
        m.model('_command_reference_unavailable',0,far=True)
        m.invoke('terminal_redisplay_key',ax=0x6c00)
        assert m.get('_aspect_fromddir')==200 and not m.origin_writes
        assert m.uc.reg_read(UC_X86_REG_EFLAGS)&1
        cases.append(dict(case='busy-manual-key-keeps-origin-before-dialog',owner=owner,modeled_boundaries=sorted(set(m.model_events)),passed=True))
    return cases


def macros(product):
    cases=[]
    for origin in (0,1,37,200,0xffff):
        for payload in (b'\0',b'TEST.ASX\0',b'X'*52):
            for load_result in (0,7):
                m=Hooks(product);m.put('_aspect_fromddir',origin)
                m.allowed=[m.span('terminal_macro_start','terminal_macro_poll'),m.group('CONFIG_GROUP')]
                m.model('_meta_front_exec_allowed',1,far=True)
                m.model('terminal_script_start',load_result)
                m.uc.mem_write(m.symbols['terminal_action_definitions'],b'\0\0'+payload.ljust(52,b'\0'))
                result=m.invoke('terminal_macro_start',ax=0)
                launches=[x for x in m.trace if x[0]=='terminal_script_start']
                valid=payload==b'TEST.ASX\0'
                assert len(launches)==int(valid)
                assert result==(3 if (payload==b'X'*52 or valid and load_result) else 0)
                assert m.get('_aspect_fromddir')==origin and not m.origin_writes
                if valid:
                    assert bytes(m.uc.mem_read(m.symbols['_command_menu_script'],9))==b'TEST.ASX\0'
                    assert launches[0][2]==origin
                cases.append(dict(case='KEY-kind0-retains-origin',origin=origin,payload_hex=payload.hex(),loader_result=load_result,modeled_boundaries=sorted(set(m.model_events)),passed=True))
    return cases


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--product',type=Path,required=True)
    p.add_argument('--child',type=Path)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();product=a.product.resolve();out=a.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    manifest=json.loads((product/'manifest.json').read_text())
    assert manifest['binary_sha256']==sha(product/'TERMINAL.EXE') and manifest['experimental_state_builtins_parent']
    sources={n:sha(ROOT/n) for n in manifest['sources']}
    assert sources==manifest['sources'],'stale application source'
    listing=(product/'terminal.map').read_text()
    match=re.search(r'^([0-9a-f]{4}):[0-9a-f]{4}[*+ ]+\s+render_body\s*$',listing,re.M|re.I);assert match
    Parent._aspect_segment=0x1000+int(match[1],16)
    cases=[];m=StateParent(product)
    assert m.get('_aspect_fromddir')==0
    # Actual physical producer and actual getter on the same linked instance.
    for port in (0x3b4,0x3d4,0x12b4,0x12d4,0xffb4):
        m=StateParent(product);m.put('_aspect_fromddir',37);m.put('_display_rows_mono',0xa55a)
        m.put('_display_rows_legacy',0);m.put('_display_rows_snow',0)
        m.uc.mem_write(0x460,b'\x0f\x06');m.uc.mem_write(0x463,struct.pack('<H',port));m.uc.mem_write(0x484,b'\x18')
        m.geometry_probe();want=int(port&255==0xb4)
        assert m.get('_display_rows_mono')==want and m.get('_aspect_fromddir')==37
        m.uc.mem_write(0x463,b'\xd4\x03' if want else b'\xb4\x03')
        m.put('attributes_monochrome',1-want)
        assert m.request(29,10)==0xf000|want and m.request(29,0x10a)==0xf000
        assert m.geometry_bios==1 and m.get('_display_rows_mono')==want
        cases.append(dict(case='native-mono-producer-then-cached-getter',CRT_port=port,value=want,passed=True))
    for index,field in enumerate(STATE_FIELDS,9):
        for value in WORDS:
            m.put(field,value);other=STATE_FIELDS[10-index];m.put(other,0x6b3d)
            # A getter reads the retained physical flag, not a fresh BDA test.
            m.uc.mem_write(0x463,b'\xb4\x03' if value==0 else b'\xd4\x03')
            before={n:bytes(m.uc.mem_read(m.symbols[n]-2,6)) for n in STATE_FIELDS}
            for high in (0,1):
                assert m.request(29,index|(high<<8))==0xf000|((value>>(high*8))&255)
                assert m.state_entries==[STATE_GETTERS[index-9]] and not m.getters
                assert sum(n=='actual-client-auth' for n,_ in m.events)==1
                assert ('pure-admission-model',index|(high<<8)) in m.events
                assert all(bytes(m.uc.mem_read(m.symbols[n]-2,6))==data for n,data in before.items())
            cases.append(dict(case='tagged-state-word',index=index,value=value,passed=True))
    for payload in (11,255,267,511,512,0x8000,0xffff):
        assert m.request(29,payload)==7 and not m.state_entries
        cases.append(dict(case='invalid-selector',payload=payload,passed=True))
    for owner in ('render_program_owned','render_snapshot_owned','terminal_script_window_active','terminal_script_confirm_active','terminal_script_field_active'):
        m=StateParent(product);m.put(owner,1)
        for index in (9,10):assert m.request(29,index)==10 and not m.state_entries
        cases.append(dict(case='owner-refusal',owner=owner,passed=True))
    for control in ('inactive-program','wrong-kind','detached','wrong-PSP','bad-token','bad-client-version','bad-parent-version','returned-UART'):
        m=StateParent(product)
        if control=='inactive-program':m.put('terminal_program_active',0)
        elif control=='wrong-kind':m.put('terminal_program_kind',3)
        elif control=='detached':m.put('render_attached',0)
        elif control=='wrong-PSP':m.current_psp=CHILD_PSP+1
        elif control=='bad-token':m.client_words[2]^=1;m.publish_client()
        elif control=='bad-client-version':m.client_words[1]=25;m.publish_client()
        elif control=='bad-parent-version':m.put('_script_render_version',25)
        elif control=='returned-UART':m.uc.mem_write(m.symbols['_script_handoff']+22,b'\1\0')
        expected=14 if control=='returned-UART' else 10
        for index in (9,10):assert m.request(29,index)==expected and not m.state_entries
        cases.append(dict(case=control,result=expected,passed=True))
    for status in (3,7,10,14):
        m=StateParent(product);m.admit_result=status
        for index in (9,10):assert m.request(29,index)==status and not m.state_entries
        cases.append(dict(case='controlled-admission-refusal',status=status,passed=True))
    m=StateParent(product);assert m.request(29,9)&0xff00==0xf000
    m.client_words[2]^=1;m.publish_client()
    assert m.request(29,0x109)==10 and not m.state_entries
    cases.append(dict(case='high-byte-reauthentication',passed=True))
    cases+=lifecycle(product);cases+=manual(product);cases+=macros(product)
    handshake=[]
    if a.child:
        helper=inspect.getsource(query.child_handshake)
        old='(0, 12, 20, 21, 22, 23, 24, 25, 255, 65535)';assert helper.count(old)==1
        helper=helper.replace(old,'(0, 12, 20, 21, 22, 23, 24, 25, 26, 255, 65535)')
        scope=dict(query.__dict__);exec(compile(helper,str(out/'child_handshake_adapter.py'),'exec'),scope)
        (out/'child_handshake_adapter.py').write_text(helper)
        handshake=scope['child_handshake'](a.child,capability=26)
        assert any(c['version']==26 and c['reached_controlled_absent_backend'] for c in handshake)
    relevant=['standalone/check_aspect_state_parent.py','standalone/check_terminal_query_parent.py','standalone/dos_image.py']
    sources.update({n:sha(ROOT/n) for n in relevant})
    unknowns=['Real DOS EXEC/startup and full child EXECUTE origin retention are separate integration gates.',
              'Pure renderer admission, DOS62 PSP, BIOS0F geometry input, chooser UI and downstream script loading are controlled boundaries.']
    for flag,label in (('experimental_directory_view','Interactive directory-view event0'),('experimental_directory_adopt','Adopted compiled automatic-script path')):
        if not manifest.get(flag):unknowns.append(label+' is unlinked in this product and is not executed.')
    report=dict(passed=True,cases=cases,handshake_cases=handshake,unknowns=unknowns,original_inputs=[],
                parent_sha256=manifest['binary_sha256'],parent_manifest_sha256=sha(product/'manifest.json'),
                child_sha256=sha(a.child/'ASPECT.EXE') if a.child else None,sources=sources,
                scope=__doc__+' Actual cap26 prepare/BEGIN/client validation and parent bridge, state getter routing and tagged responses with source WORD/canary/ABI preservation. Actual startup directory clear, legacy automatic full-entry assignment before modeled loader failure/success, manual C prompt clear/cancel and busy-key refusal, KEY-kind0 dispatch/name staging without origin reset, and recovered physical mono producer followed by actual cached getter RPC. No unexpected interrupts, port IO or external paths permitted; modeled boundaries are named. Unlinked hooks and full DOS/physical/BBS/ASPECT acceptance remain explicit unknowns.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS linked cap26 state parent',len(cases),'cases;',len(handshake),'child handshake cases')


if __name__=='__main__':main()
