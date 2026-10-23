#!/usr/bin/env python3
"""Execute linked directory binding validation/lookup with only DOS probes modeled."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
import check_transport as transport
ROOT=transport.ROOT

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    base=ROOT/'build/terminal-directory-keys';transport.BINARY=base/'TERMINAL.EXE';transport.MAP=base/'terminal.map'
    from check_script_launch_live import Script
    class Model(Script):
        def __init__(self):
            super().__init__();self.files=set();self.probes=[];self.handles=set();self.open_errors={};self.close_error=0
            self.install_program_name(entries=b'');self.put('terminal_directory_context_valid',1)
            self.uc.mem_write(self.symbols['terminal_directory_context']+252,bytes(114))
            self.uc.mem_write(self.symbols['terminal_actions_path'],b'OLD.KEY\0'+b'K'*56)
            self.uc.mem_write(self.symbols['terminal_keyboard_path'],b'OLD.KBD\0'+b'B'*56)
            self.put('terminal_option_mask',0);self.port_writes.clear()
        def interrupt(self,u,n,d):
            ax=u.reg_read(UC_X86_REG_AX)
            if n==0x21 and ax==0x3d00:
                at=u.reg_read(UC_X86_REG_DS)*16+u.reg_read(UC_X86_REG_DX)
                name=bytes(u.mem_read(at,64)).split(b'\0',1)[0].decode('ascii');self.probes.append(name)
                error=self.open_errors.get(name,0 if name in self.files else 2)
                self.set_carry(bool(error));u.reg_write(UC_X86_REG_AX,error or 8);self.handles|=set() if error else {8};return
            if n==0x21 and ax>>8==0x3e:
                assert u.reg_read(UC_X86_REG_BX) in self.handles
                self.set_carry(bool(self.close_error));u.reg_write(UC_X86_REG_AX,self.close_error)
                if not self.close_error:self.handles.remove(8)
                return
            return super().interrupt(u,n,d)
        def field(self,at,value):self.uc.mem_write(self.symbols['terminal_directory_context']+252+at,value.ljust(9,b'\0'))
        def state(self):return (self.get('terminal_option_mask'),bytes(self.uc.mem_read(self.symbols['terminal_actions_path'],64)),bytes(self.uc.mem_read(self.symbols['terminal_keyboard_path'],64)))
        def invoke(self,name,args=(),far=False):
            address=self.symbols[name]
            # Select the actual mapped bank segment from the symbol's map record.
            import re
            match=re.search(r'^([0-9a-f]{4}):([0-9a-f]{4})[ *+]+\s*'+re.escape(name)+r'\s*$',(base/'terminal.map').read_text(),re.M|re.I);assert match
            cs=self.base_segment+int(match[1],16)
            target_cs=self.code_segment if far else cs;stop=(target_cs<<4)+self.return_offset
            for reg,val in [(UC_X86_REG_CS,cs),(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_ES,self.ds),(UC_X86_REG_EFLAGS,0x202),(UC_X86_REG_BP,0xbabe)]:self.uc.reg_write(reg,val)
            frame=[self.return_offset]+([target_cs] if far else [])+list(args)
            sp=self.offset('terminal_stack_top')-2*len(frame);self.uc.mem_write(self.data_base+sp,struct.pack('<'+'H'*len(frame),*frame));self.uc.reg_write(UC_X86_REG_SP,sp)
            hits=[]
            def finish(u,at,size,_):
                if at==stop and u.reg_read(UC_X86_REG_CS)==target_cs:hits.append(True);u.emu_stop()
            hook=self.uc.hook_add(UC_HOOK_CODE,finish)
            try:self.uc.emu_start(address,0,count=300000)
            finally:self.uc.hook_del(hook)
            # DosImage's independent near sentinel can stop before our hook.
            assert hits or self.uc.reg_read(UC_X86_REG_CS)==target_cs and self.uc.reg_read(UC_X86_REG_IP)==self.return_offset
            assert self.uc.reg_read(UC_X86_REG_SP)==sp+2*(2 if far else 1)
            return self.uc.reg_read(UC_X86_REG_AX)
    cases=[]
    def done(name,n):cases.append(dict(case=name,inputs=n,passed=True));print(name,n,flush=True)
    allowed=b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-'
    for c in range(256):
        m=Model();stored=bytes([c])+bytes(8);ptr=m.stage_near(stored+b'GAP!'+b'X'*13)
        status=m.invoke('_directory_binding_name',[ptr,0,ptr+13])
        expected=b'' if c in (0,32) else bytes([c]).upper()+b'.KEY' if c in allowed else None
        assert status==int(expected is None),(c,status)
        actual=bytes(m.uc.mem_read(m.data_base+ptr+13,13))
        if expected is None:assert actual==b'X'*13
        else:assert actual==expected+b'\0'+b'X'*(12-len(expected))
        assert not m.probes and not m.port_writes
    done('all-byte-basename-classification-blank-native-test-and-atomic-output',256)
    for name in [b'ABCDEFGH',b'a_b-1',b'CON',b'prn',b'COM9',b'LPT1',b'A.KEY',b'..',b'A/B',b'A B',b'A\\B',b'ABCDEFGHI']:
        for meta in (0,1):
            m=Model();p=m.stage_near(name.ljust(9,b'\0')+b'GAP!'+b'X'*13)
            result=m.invoke('_directory_binding_name',[p,meta,p+13]);assert result==int(name not in (b'ABCDEFGH',b'a_b-1'))
    done('full-eight-byte-uppercase-suffixes-and-devices-paths-extension-refusal',24)
    recipes=[('cwd',{'ACTIONS.KEY','BOARD.KBD'},b'',0,0),('environment',{'D:\\ENV\\ACTIONS.KEY','D:\\ENV\\BOARD.KBD'},b'PCPLUS=D:\\ENV\0',0,0),('cwd-first',{'ACTIONS.KEY','BOARD.KBD','D:\\ENV\\BOARD.KBD'},b'PCPLUS=D:\\ENV\0',0,0),('missing',set(),b'',0,0),('fallback',{'PCPLUS.KBD'},b'',0,0),('env-fallback',{'D:\\ENV\\PCPLUS.KBD'},b'PCPLUS=D:\\ENV\0',0,0),('CLI',set(),b'',4608,0),('key-open-error',set(),b'',0,10),('late-meta-error',{'ACTIONS.KEY'},b'',0,9),('close-error',{'ACTIONS.KEY'},b'',0,10)]
    for label,files,env,flags,want in recipes:
        m=Model();m.files=files;m.install_program_name(entries=env);m.field(0x56,b'actions');m.field(0x5f,b'board');m.put('terminal_option_mask',flags)
        if label=='key-open-error':m.open_errors['ACTIONS.KEY']=5
        if label=='late-meta-error':m.open_errors['BOARD.KBD']=5
        if label=='close-error':m.close_error=6
        before=m.state();assert m.invoke('_terminal_directory_bindings',far=True)==want
        after=m.state();assert not m.port_writes
        if want or label=='CLI':assert after==before
        elif label=='missing':assert after==before
        else:
            has_key='ACTIONS.KEY' in files or 'D:\\ENV\\ACTIONS.KEY' in files
            assert after[0]==(4096 if has_key else 0)|512
            assert after[2].split(b'\0',1)[0]==(b'D:\\ENV\\BOARD.KBD' if label=='environment' else b'PCPLUS.KBD' if label=='fallback' else b'D:\\ENV\\PCPLUS.KBD' if label=='env-fallback' else b'BOARD.KBD')
        if not m.close_error:assert not m.handles
    done('CWD-PCPLUS-fallback-CLI-precedence-and-atomic-failure-publication',len(recipes))
    m=Model();m.field(0x56,b'CON');before=m.state();assert m.invoke('_terminal_directory_bindings',far=True)==8 and m.state()==before and not m.probes
    m=Model();m.put('terminal_directory_context_valid',0);m.field(0x56,b'CON');before=m.state();assert m.invoke('_terminal_directory_bindings',far=True)==0 and m.state()==before and not m.probes
    done('invalid-binding-or-invalid-context-never-opens-resources',2)
    manifest=json.loads((base/'manifest.json').read_text());sources=dict(manifest['sources'])
    for n in ['standalone/check_directory_key_bindings.py','standalone/check_script_launch_live.py','standalone/check_transport.py','standalone/check_process.py','standalone/dos_image.py']:sources[n]=hashlib.sha256((ROOT/n).read_bytes()).hexdigest()
    for n,h in sources.items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h,n
    result=dict(passed=True,inputs=sum(c['inputs'] for c in cases),cases=cases,sources=sources,binary_sha256=manifest['binary_sha256'],scope='Actual linked basename validator and far-bank directory selector. Only DOS readonly open/close errors and filesystem existence modeled; environment resolver and publication execute normally. File format readers and terminal workflows are separately tested in real DOS.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',result['inputs'],'linked inputs')
if __name__=='__main__':main()
