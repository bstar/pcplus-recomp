#!/usr/bin/env python3
"""Execute actual parent connection/status/notice code with modeled modem inputs."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import *
from check_status_live import Status,ROOT,BINARY,MAP
from check_connection import Connection
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


class Poll(Status):
    def __init__(self,carrier=0):
        super().__init__(carrier)
        self.put('terminal_program_active',0);self.put('reset_ready',1)
        self.uc.mem_write(self.symbols['_command_menu_script'],b'\0')
        self.clock(100)

    def clock(self,value):self.uc.mem_write(0x46c,struct.pack('<I',value))

    def near(self,name,si=0):
        u=self.uc;sp=self.offset('terminal_stack_top')-2
        for reg,value in [(UC_X86_REG_CS,self.code_segment),(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),
                          (UC_X86_REG_SP,sp),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,si),(UC_X86_REG_EFLAGS,0x202)]:
            u.reg_write(reg,value)
        u.mem_write(self.data_base+sp,struct.pack('<H',self.return_offset));self.returned=False
        u.emu_start(self.symbols[name],0,count=250000)
        assert self.returned and u.reg_read(UC_X86_REG_SP)==sp+2
        assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==self.ds

    def poll(self,flags=0x202):
        memory=json.loads((BINARY.parent/'manifest.json').read_text())['memory_layout']
        segment=self.base_segment+next(c['relative_segment'] for c in memory['code_segments'] if c['name']=='CONFIG_CODE')
        sp=self.offset('terminal_stack_top')-4;u=self.uc
        kept=dict(BX=0x2345,CX=0x3456,DX=0x4567,SI=0x5678,DI=0x6789,BP=0xbabe,ES=0x1357)
        for name,value in dict(CS=segment,DS=self.ds,SS=self.ds,SP=sp,EFLAGS=flags,AX=0x1234,**kept).items():
            u.reg_write(globals()['UC_X86_REG_'+name],value)
        u.mem_write(self.data_base+sp,struct.pack('<HH',self.return_offset,self.base_segment));self.returned=False
        u.emu_start(self.symbols['terminal_status_poll'],0,count=500000);assert self.returned
        assert u.reg_read(UC_X86_REG_AX)==0 and u.reg_read(UC_X86_REG_SP)==sp+4
        assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==self.ds
        assert u.reg_read(UC_X86_REG_EFLAGS)&0x600==flags&0x600
        for name,value in kept.items():assert u.reg_read(globals()['UC_X86_REG_'+name])==value,name


def main():
    global BINARY,MAP
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--mouse',action='store_true');a=p.parse_args()
    if a.mouse:
        import check_status_live as status,check_transport as transport
        BINARY=ROOT/'build/terminal-mouse/TERMINAL.EXE';MAP=BINARY.parent/'terminal.map'
        status.BINARY=transport.BINARY=BINARY;status.MAP=transport.MAP=MAP
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    rows=[]
    def done(name):rows.append(dict(case=name,passed=True))
    for direct in (False,True):
        for initial in (False,True):
            m=Connection();m.carrier=initial
            if direct:
                m.put('terminal_directory_mode',1);m.start();assert m.state()==6
            else:m.connect()
            seen=m.uc.mem_read(m.symbols['connection_enabled']+1,1)[0]
            assert bool(seen)==initial
            m.carrier=False;m.poll()
            assert (m.state(),m.get('connection_status'))==((0,6) if initial else (6,1))
            if not initial:
                m.carrier=True;m.poll();m.carrier=False;m.poll();assert (m.state(),m.get('connection_status'))==(0,6)
            done('connect-snapshot-direct%d-initialDCD%d'%(direct,initial))
    for carrier in (0,128):
        for flags in (0x202,0x602):
            m=Poll(carrier);m.poll(flags)
            assert b'Alt-Z FOR HELP' in m.row() and (b'ON-LINE' if carrier else b'OFF-LINE') in m.row()
            assert bytes(m.uc.mem_read(0xb8000,3840))==b'\xcc'*3840
            assert len(m.inputs)==2
            m.poll(flags);assert len(m.inputs)==2
            m.clock(101);m.poll(flags);assert len(m.inputs)==3
            m.carrier=128-carrier;m.clock(102);m.poll(flags);assert len(m.inputs)==5
            assert (b'OFF-LINE' if carrier else b'ON-LINE') in m.row()
            done('unlabelled-ordinary-status-carrier%d-flags%x'%(carrier,flags))
    owners=['terminal_program_active','terminal_program_pending','terminal_aspect_active','terminal_parser_active',
            'terminal_ansi_wait_active','terminal_monitor_active','terminal_snapshot_active','terminal_screen_print_active',
            'terminal_controller_active','terminal_transfer_active','terminal_transfer_pending','_redisplay_active',
            '_command_menu_active','ui_flow_suppressed','terminal_tab_wrap']
    for name in owners:
        m=Poll(128);m.put(name,1);m.poll()
        assert not m.inputs and bytes(m.uc.mem_read(0xb8000,4004))==b'\xcc'*4004
        assert m.get('status_parent_valid')==0
        m.put(name,0);m.poll();assert b'ON-LINE' in m.row()
        done('defer-owner-'+name)
    for name,value in [('screen_columns',79),('ui_flow_region_cells',79),('ui_flow_video_base',0),('ui_flow_coordinate_base',0),('csi_terminal_id',15),('reset_ready',0)]:
        m=Poll();old=m.get(name);m.put(name,value);m.poll()
        assert not m.inputs and bytes(m.uc.mem_read(0xb8000,4004))==b'\xcc'*4004
        m.put(name,old);m.poll();assert b'OFF-LINE' in m.row()
        done('defer-layout-'+name)
    m=Poll();m.put('terminal_baud_low',123);m.poll()
    assert m.get('status_parent_valid')==0 and len(m.inputs)==1 and bytes(m.uc.mem_read(0xb8000,4004))==b'\xcc'*4004
    m.put('terminal_baud_low',38400);m.clock(101);m.poll();assert b'OFF-LINE' in m.row()
    done('unsupported-setting-retries-next-tick-with-same-carrier')
    m=Poll();m.poll();assert m.get('status_parent_valid')==1
    # The ordinary sampler sees low both before and after a script. The script
    # draws high STATUS in between; that explicit draw must invalidate its cache.
    m.carrier=128;m.put('terminal_program_active',1);m.uc.mem_write(m.symbols['_command_menu_script'],b'CHILD.ASX\0')
    assert m.run()==0 and b'ON-LINE' in m.row() and m.get('status_parent_valid')==0
    m.carrier=0;m.put('terminal_program_active',0);m.clock(101);m.poll()
    assert b'OFF-LINE' in m.row() and m.get('status_parent_valid')==1
    done('low-high-script-draw-low-invalidates-ordinary-sampler')
    m=Poll();pointer=m.offset('_command_menu_script');m.uc.mem_write(m.data_base+pointer,b'Carrier lost\0')
    m.near('terminal_connection_notice',si=pointer)
    notice=bytes(m.uc.mem_read(0xb8000+3840,30));assert b'Carrier lost' in notice[::2]
    m.poll();assert bytes(m.uc.mem_read(0xb8000+3840,30))==notice and b'OFF-LINE' in m.row()
    m.near('terminal_connection_notice_restore')
    assert b'Alt-Z FOR HELP' in m.row() and b'OFF-LINE' in m.row()
    assert bytes(m.uc.mem_read(0xb8000,3840))==b'\xcc'*3840
    done('notice-survives-repaint-and-restores-new-underlay')
    manifest=json.loads((BINARY.parent/'manifest.json').read_text())
    for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
    inputs={name:sha(ROOT/name) for name in ('standalone/check_parent_carrier_status.py','standalone/check_status_live.py','standalone/check_connection.py','standalone/check_transport.py','standalone/dos_image.py')}
    result=dict(passed=True,cases=rows,parent_sha256=sha(BINARY),manifest_sha256=sha(BINARY.parent/'manifest.json'),
                checker_sha256=sha(Path(__file__)),inputs=inputs,scope=__doc__+' Real near/far code, DS=SS stack copies, register/IF/DF retention and video bytes execute. Modem/BDA inputs are modeled. No actual DOS or physical timing claim.')
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,groups=len(rows))))


if __name__=='__main__':main()
