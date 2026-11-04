#!/usr/bin/env python3
"""Run linked notice leases and status repaint against canonical row ownership.
Actual parent/UI instructions and video copies execute; UART inputs are modeled.
No physical display timing or complete geometry transition acceptance.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import *
import check_status_live as status
import check_transport as transport
import check_parent_carrier_status as parent
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

class Notice(parent.Poll):
    def show(self,text=b'Carrier lost'):
        pointer=self.offset('_command_menu_script');self.uc.mem_write(self.data_base+pointer,text+b'\0')
        self.near('terminal_connection_notice',si=pointer)
    def video(self):return bytes(self.uc.mem_read(0xb8000,4004))
    def far(self,name):
        u=self.uc;sp=self.offset('terminal_stack_top')-4
        keep={UC_X86_REG_BP:0xbabe,UC_X86_REG_BX:0x2345,UC_X86_REG_CX:0x3456,UC_X86_REG_DX:0x4567,UC_X86_REG_SI:0x5678,UC_X86_REG_DI:0x6789,UC_X86_REG_ES:0x1357}
        for reg,value in {**keep,UC_X86_REG_CS:self.code_segment,UC_X86_REG_DS:self.ds,UC_X86_REG_SS:self.ds,UC_X86_REG_SP:sp,UC_X86_REG_EFLAGS:0x202}.items():u.reg_write(reg,value)
        u.mem_write(self.data_base+sp,struct.pack('<HH',self.return_offset,self.code_segment));self.returned=False
        u.emu_start(self.symbols[name],0,count=500000)
        assert self.returned and u.reg_read(UC_X86_REG_SP)==sp+4
        assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==self.ds
        if name=='terminal_status_notice_refresh':
            for reg,value in keep.items():assert u.reg_read(reg)==value,reg
        return u.reg_read(UC_X86_REG_AX)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
    for mod in (status,transport,parent):mod.BINARY=binary;mod.MAP=binary.parent/'terminal.map'
    manifest=json.loads((binary.parent/'manifest.json').read_text())
    assert manifest['experimental_status_geometry'] and manifest['experimental_screen_pause'] and manifest['experimental_elapsed_view']
    cases=[]
    def done(name):cases.append(dict(case=name,passed=True));print('PASS',name,flush=True)
    m=Notice();m.show();notice=m.video()[3840:3870];assert b'Carrier lost' in notice[::2]
    m.poll();assert m.video()[3840:3870]==notice
    m.near('terminal_connection_notice_restore');assert b'Alt-Z FOR HELP' in m.row()
    assert m.video()[:3840]==b'\xcc'*3840
    done('ordinary-notice-repaint-and-current-underlay-restoration')
    fields={'ui_flow_suppressed':(1,2,0x8000,0xffff),'ui_flow_region_cells':(0,79,81,0xffff),
            'ui_flow_video_base':(0,3838,3842,0xffff),'ui_flow_coordinate_base':(0,0x1700,0x1900,0xffff),
            'screen_columns':(0,40,132,0xffff),'screen_video_row_bytes':(0,80,264,0xffff),
            'text_video_segment':(0,0xb000,0xffff)}
    rejected=0
    for field,values in fields.items():
        for value in values:
            m=Notice();before=m.video();old=m.get(field);m.put(field,value)
            m.put('_redisplay_active',1);m.put('_command_menu_active',1)
            m.show();assert m.video()==before
            assert m.get('_redisplay_active')==m.get('_command_menu_active')==1
            m.put('_redisplay_active',0);m.put('_command_menu_active',0)
            assert m.far('terminal_status_notice_refresh')==3 and m.video()==before
            m.put(field,old);m.near('terminal_connection_notice_restore');assert m.video()==before
            rejected+=1
    done('unsupported-row-never-acquires-notice-or-closes-viewer:'+str(rejected))
    stale=0
    for field,values in fields.items():
        for value in values:
            for service in ('terminal_connection_notice_restore','terminal_status_notice_refresh','terminal_connection_notice'):
                m=Notice();m.show();old=m.get(field)
                # This is already newer terminal output. It must survive stale retirement.
                m.uc.mem_write(0xb8000+3840,b'N\x1f'*80);fresh=m.video();m.put(field,value)
                if service=='terminal_status_notice_refresh':assert m.far(service)==3
                elif service=='terminal_connection_notice':m.show(b'New notice')
                else:m.near(service)
                assert m.video()==fresh,(field,value,service)
                m.put(field,old);m.near('terminal_connection_notice_restore');assert m.video()==fresh
                stale+=1
    done('invalidated-lease-cannot-restore-over-new-terminal-data:'+str(stale))
    m=Notice();before=m.video();m.show(b'First');m.show(b'Second');m.near('terminal_connection_notice_restore');assert m.video()==before
    done('replacement-notice-retains-original-underlay')
    m=Notice();before=m.video();m.show();m.near('terminal_connection_notice_restore');assert m.video()==before
    m.put('ui_flow_suppressed',1);m.uc.mem_write(0xb8000+3840,b'R\x07'*80);fresh=m.video();m.show();m.near('terminal_connection_notice_restore');assert m.video()==fresh
    done('retire-before-exposing-status-row')
    for owner in ('terminal_screen_pause_active','_terminal_elapsed_view_active'):
        m=Notice();m.put(owner,1);before=m.video();m.show();assert m.video()==before
        m.put('ui_flow_suppressed',1);m.put(owner,0);m.far('terminal_pause_notice_flush_far');assert m.video()==before
        m.put('ui_flow_suppressed',0);m.near('terminal_connection_notice_restore');assert m.video()==before
        m=Notice();m.show();m.put(owner,1);m.put('ui_flow_suppressed',1)
        m.uc.mem_write(0xb8000+3840,b'D\x07'*80);fresh=m.video();m.near('terminal_connection_notice_restore');assert m.video()==fresh
        m.put(owner,0);m.far('terminal_pause_notice_flush_far');assert m.video()==fresh
        m.put('ui_flow_suppressed',0);m.near('terminal_connection_notice_restore');assert m.video()==fresh
    done('pause-and-elapsed-deferred-actions-revalidate-current-ownership')
    for source,digest in manifest['sources'].items():assert sha(ROOT/source)==digest,source
    inputs=[Path(__file__).resolve(),ROOT/'standalone/check_parent_carrier_status.py',ROOT/'standalone/check_status_live.py',ROOT/'standalone/check_transport.py',ROOT/'standalone/dos_image.py']
    result=dict(passed=True,cases=cases,parent_sha256=sha(binary),manifest_sha256=sha(binary.parent/'manifest.json'),
                inputs={str(f.relative_to(ROOT)):sha(f) for f in inputs},sources_verified=len(manifest['sources']),scope=__doc__)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
