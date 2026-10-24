#!/usr/bin/env python3
"""Compare the actual wide live repair against the independent native-field oracle."""
import hashlib
import itertools
import json
from pathlib import Path

from check_viewport_live import fixture,pane_reference
from check_attribute_repair import Machine as Reference
from check_line_edit_live import Abort,ROOT
from unicorn.x86_const import *

OUT=ROOT/'build/terminal'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(m,address):
    return [bytes(m.uc.mem_read(m.symbols[name],4096))for name in('screen_attribute_cells','erase_attribute_values')]+[
        bytes(m.uc.mem_read(0xb8000,8000)),bytes(m.uc.mem_read(address,8192)),bytes(m.uc.mem_read(m.symbols['uart_rx_buffer'],4096))]


def main():
    manifest=json.loads((OUT/'manifest.json').read_text())
    assert sha(OUT/'TERMINAL.EXE')==manifest['binary_sha256']
    for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
    cases=0;rejections=0;navigation=0;panes=set()
    for (rows,hidden),profile,pattern,mode in itertools.product([(1,0),(5,0),(24,0),(25,1)],(4,6),range(3),range(5)):
        count=132*rows
        for cursor in sorted({79,min(80,count-1),count-1}):
            m,address,_,_=fixture(rows,hidden,profile);m.position(*divmod(cursor,132));m.put('screen_cursor_wrap',1)
            for name,value in [('attributes_current',0x9c),('attributes_preset_value',0x4e),('attributes_normal_value',0x27),('csi_erase_attribute',0x17)]:
                m.put(name,value,1 if name=='csi_erase_attribute'else 2)
            flags=bytes(0 if pattern==0 else (0x81 if i%79==0 else i%4)if pattern==1 else (0x80 if i in(0,79,80,131,count-1)else i%4)for i in range(count))
            values=bytes((i*31+0x17)&255 for i in range(count))
            m.uc.mem_write(m.symbols['screen_attribute_cells'],flags+b'\x55'*(4096-count))
            m.uc.mem_write(m.symbols['erase_attribute_values'],values+b'\x66'*(4096-count))
            before=snapshot(m,address);active=m.get('screen_viewport_active');panes.add(active)
            oracle=object.__new__(Reference);oracle.cols=132;oracle.rows=rows;oracle.flags=flags;oracle.values=values;oracle.cursor=cursor
            oracle.shadow_offset=0 # Snapshot begins at the application's owned pointer.
            oracle.video=bytearray(before[2]);oracle.shadow=bytearray(before[3])
            expected_values,expected_video,expected_shadow,_=oracle.reference(mode,True,(active,52,79))
            rx_count=m.get('uart_rx_count')
            m.call('erase_repair_attributes',[mode],cleanup=2,limit=2000000)
            after=snapshot(m,address);identity=(rows,hidden,profile,pattern,mode,cursor,active)
            assert after[0]==before[0] and after[1]==bytes(expected_values)+before[1][count:],(identity,'planes')
            assert after[2]==expected_video and after[3]==expected_shadow,(identity,'video/shadow',
                [(i,a,b)for i,(a,b)in enumerate(zip(after[2],expected_video))if a!=b][:8],
                [(i,a,b)for i,(a,b)in enumerate(zip(after[3],expected_shadow))if a!=b][:8])
            assert after[4]==before[4] and m.get('uart_rx_count')==rx_count,(identity,'RX')
            assert(m.get('screen_cursor_row'),m.get('screen_cursor_column'))==divmod(cursor,132)
            for register,value in[(UC_X86_REG_DS,m.ds),(UC_X86_REG_SS,m.ds),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:assert m.uc.reg_read(register)==value,(identity,register)
            assert not m.uc.reg_read(UC_X86_REG_EFLAGS)&0x400
            cases+=1
    # Wide current-cursor admission must reconcile logical and visible offsets.
    mutations=[('screen_cursor_column',132),('screen_attribute_offset',0),('screen_video_offset',0),
        ('screen_visible_column',0),('screen_viewport_offset',0),('screen_viewport_active',1),
        ('erase_shadow_segment',0x6000),('erase_shadow_offset',1),('erase_attribute_values_base',0xff00),
        ('screen_attributes_base',0xff00),('csi_row_count',25),('screen_last_row',24),('terminal_program_active',1)]
    for name,value in mutations:
        m,address,_,_=fixture();m.position(5,120);m.put('screen_cursor_wrap',1);m.put(name,value)
        before=snapshot(m,address)
        try:m.call('erase_repair_attributes',[2],cleanup=2)
        except Abort as problem:assert problem.args==(0x2d98,),(name,problem.args)
        else:raise AssertionError(('Missing wide repair refusal',name))
        assert snapshot(m,address)==before,name;rejections+=1
    assert panes=={0,1}
    for (rows,hidden),profile,direction in itertools.product([(5,0),(24,0),(25,1)],(4,6),(0,1)):
        count=rows*132;step=1 if direction else -1
        for start in (0,51,52,79,80,131,count-1):
            m,address,_,_=fixture(rows,hidden,profile);m.position(*divmod(start,132))
            flags=bytearray(count)
            for i in range(3):flags[(start+step*i)%count]=0x81
            m.uc.mem_write(m.symbols['screen_attribute_cells'],bytes(flags)+b'\x55'*(4096-count))
            before=snapshot(m,address);video=bytearray(before[2][:4000]);shadow=bytearray(before[3])
            target=(start+step*3)%count;row,col=divmod(target,132)
            active=m.get('screen_viewport_active');following=1 if col<52 else 0 if col>79 else active
            pane_reference(video,shadow,rows,active,following)
            result=m.call('screen_adjust_attribute_boundary',[start,direction],cleanup=4,limit=1000000)
            after=snapshot(m,address)
            assert result==1 and (m.get('screen_cursor_row'),m.get('screen_cursor_column'))==(row,col)
            assert after[:2]==before[:2] and after[4]==before[4]
            assert after[2][:4000]==video and after[2][4000:]==before[2][4000:] and after[3]==shadow
            assert m.get('screen_attribute_offset')==target
            assert m.get('screen_viewport_active')==following
            navigation+=1
    result=dict(passed=True,binary_sha256=manifest['binary_sha256'],cases=cases,navigation_cases=navigation,pre_mutation_rejections=rejections,
        checker_sha256=sha(Path(__file__)),oracle_sha256=sha(ROOT/'standalone/check_attribute_repair.py'),
        fixture_sha256=sha(ROOT/'standalone/check_viewport_live.py'),sources=manifest['sources'],original_inputs=[],
        scope='Actual live near/far native field repair at132 logical/80 physical columns with owned pane admission. Independent field oracle, both panes, profiles4/6, supported status/height layouts, all five repair modes, metadata/video/shadow guards, RX and ABI. CPU hardware model and staged wide state; no normal width request, complete scrolling/UI/child/BBS or physical acceptance.')
    (OUT/'attribute-repair-wide-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS wide live repair:',cases,'cases,',navigation,'boundary navigation,',rejections,'pre-mutation refusals')


if __name__=='__main__':main()
