#!/usr/bin/env python3
"""Run real linked cursor/pane/parser code against independent logical-screen oracles."""
import hashlib
import itertools
import json
from pathlib import Path
import struct

from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from check_line_edit_live import Live,Abort,ROOT

OUT=ROOT/'build/terminal'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(rows=24,hidden=0,profile=6):
    m=Live()
    m.viewport_callbacks=[]
    def callback(u,at,size,_):
        if at in (m.symbols['viewport_blank_resident'],m.symbols['viewport_unblank_resident']):
            assert u.reg_read(UC_X86_REG_DS)==m.ds,'Viewport hardware callback inherited foreign DS'
            m.viewport_callbacks.append(at)
    m.uc.hook_add(UC_HOOK_CODE,callback)
    m.uc.mem_write(0x449,b'\x03\x50\x00')
    m.uc.mem_write(0x462,b'\0');m.uc.mem_write(0x484,b'\x18')
    fields=dict(reset_ready=1,csi_terminal_id=profile,screen_columns=80,
        screen_video_row_bytes=160,screen_attribute_row_bytes=132,screen_last_column=131,
        csi_row_count=rows,csi_last_row=rows-1,screen_last_row=rows-1,screen_first_row=0,
        erase_cell_count=132*rows,screen_viewport_enabled=1,screen_viewport_active=1,
        screen_viewport_offset=0,screen_viewport_left=52,screen_viewport_right=79,
        ui_flow_suppressed=hidden)
    for name,value in fields.items():m.put(name,value)
    # Logical backing starts consistent with the visible left pane; hidden
    # columns have independent character/attribute patterns.
    shadow=bytearray(8192);video=bytearray(m.uc.mem_read(0xb8000,4000))
    for row in range(rows):
        for col in range(132):struct.pack_into('<H',shadow,2*(row*132+col),0x700|((row+col)%80+33))
        shadow[row*264:row*264+160]=video[row*160:row*160+160]
    address=m.get('erase_shadow_segment')*16+m.get('erase_shadow_offset')
    m.uc.mem_write(address,bytes(shadow));m.receive_irq(b'RX pending')
    return m,address,video,shadow


def pane_reference(video,shadow,rows,active,next_active):
    if next_active==active:return
    old=0 if active else 52;new=0 if next_active else 52
    for row in range(rows):
        at=2*(row*132+old);shadow[at:at+160]=video[row*160:row*160+160]
    for row in range(rows):
        at=2*(row*132+new);video[row*160:row*160+160]=shadow[at:at+160]


def logical(m,address,rows):
    shadow=bytearray(m.uc.mem_read(address,rows*264));video=m.uc.mem_read(0xb8000,4000)
    offset=m.get('screen_viewport_offset')
    for row in range(rows):shadow[(row*132+offset)*2:(row*132+offset)*2+160]=video[row*160:row*160+160]
    return bytes(shadow)


def main():
    manifest=json.loads((OUT/'manifest.json').read_text())
    assert sha(OUT/'TERMINAL.EXE')==manifest['binary_sha256']
    for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
    transitions=0;rendered=0;rejections=0
    layouts=[(1,0),(5,0),(24,0),(24,1),(25,1)]
    for (rows,hidden),profile in itertools.product(layouts,(4,6)):
        m,address,video,shadow=fixture(rows,hidden,profile)
        rx=bytes(m.uc.mem_read(m.symbols['uart_rx_buffer'],4096));count=m.get('uart_rx_count')
        active=1
        for row,col in [(0,131),(rows-1,0),(0,79),(rows//2,80),(rows-1,52),(0,51),(0,120),(rows-1,10)]:
            following=1 if col<52 else 0 if col>79 else active
            pane_reference(video,shadow,rows,active,following);active=following
            m.position(row,col)
            assert m.get('screen_viewport_active')==active
            assert m.get('screen_viewport_offset')==(0 if active else 52)
            visible=col-(0 if active else 52)
            assert m.get('screen_visible_column')==visible
            assert m.get('screen_video_offset')==row*160+visible*2
            assert m.get('screen_attribute_offset')==row*132+col
            assert bytes(m.uc.mem_read(0xb8000,4000))==video
            assert bytes(m.uc.mem_read(address,8192))==shadow
            assert bytes(m.uc.mem_read(m.symbols['uart_rx_buffer'],4096))==rx and m.get('uart_rx_count')==count
            for register,value in [(UC_X86_REG_DS,m.ds),(UC_X86_REG_SS,m.ds),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0xb800)]:
                assert m.uc.reg_read(register)==value,(register,value)
            assert not m.uc.reg_read(UC_X86_REG_EFLAGS)&0x400
            transitions+=1
        # Discard only the fixture's initial unread bytes before supplying a
        # declared printable/parser stream through the actual UART IRQ reader.
        while m.get('uart_rx_count'):m.call('ansi_next_byte')
        expected=bytearray(logical(m,address,rows))
        for row,col,char in [(0,0,b'A'),(rows-1,131,b'Z'),(rows//2,80,b'R'),(0,51,b'L'),(rows-1,79,b'Q')]:
            m.feed(b'\x1b['+str(row+1).encode()+b';'+str(col+1).encode()+b'H'+char)
            struct.pack_into('<H',expected,2*(row*132+col),0x700|char[0])
            assert logical(m,address,rows)==expected,(rows,hidden,profile,row,col,'print')
            rendered+=1
        row=rows-1
        m.feed(b'\x1b['+str(row+1).encode()+b';1H\x1b[2K')
        expected[row*264:(row+1)*264]=b' \x07'*132
        assert logical(m,address,rows)==expected,(rows,hidden,profile,'erase')
        if rows<=24:assert bytes(m.uc.mem_read(0xb8000+3840,160))==video[3840:4000]
        assert m.viewport_callbacks
        rendered+=1
    mutations=[('screen_columns',79),('screen_video_row_bytes',264),('screen_attribute_row_bytes',80),
        ('screen_last_column',79),('screen_viewport_enabled',0),('screen_viewport_active',2),
        ('screen_viewport_offset',52),('screen_viewport_left',51),('screen_viewport_right',80),
        ('csi_row_count',0),('csi_row_count',26),('csi_last_row',22),('screen_last_row',24),
        ('screen_first_row',24),('erase_cell_count',1),('screen_attributes_base',0xff00),
        ('erase_attribute_values_base',0xff00),('erase_shadow_segment',0x6000),('erase_shadow_offset',1),
        ('text_video_segment',0xb000),('text_cga_status_port',0x3da),('reset_ready',0),('csi_terminal_id',14),
        ('ui_flow_region_cells',132),('ui_flow_video_base',0),('ui_flow_coordinate_base',0),('connection_state',2)]
    mutations += [(name,1)for name in ['terminal_program_active','terminal_program_pending','terminal_macro_active',
        'terminal_monitor_active','terminal_snapshot_active','terminal_screen_print_active','terminal_controller_active',
        'terminal_ansi_wait_active','terminal_transfer_active','terminal_transfer_pending','_redisplay_active','_command_menu_active']]
    mutations += [('BDA-mode',7),('BDA-columns',132),('BDA-page',1),('BDA-rows',42),('FLAGS',0x2),('FLAGS',0x602),('status-overlap',25)]
    for (name,value),(entry,error) in itertools.product(mutations,[('terminal_viewport_admit',None),('screen_viewport_enter',0x482a),('screen_viewport_leave',0x4850),('screen_viewport_refresh',0x2fb8)]):
        m,address,video,shadow=fixture()
        if name.startswith('BDA-'):
            at,width={'BDA-mode':(0x449,1),'BDA-columns':(0x44a,2),'BDA-page':(0x462,1),'BDA-rows':(0x484,1)}[name]
            m.uc.mem_write(at,value.to_bytes(width,'little'))
        elif name=='FLAGS':
            entry_at=m.symbols['terminal_viewport_admit_far']
            bridge=bytes(m.uc.mem_read(entry_at,3));assert bridge[0]==0xe8
            admit_at=entry_at+3+struct.unpack_from('<h',bridge,1)[0]
            def flags(u,at,size,_):
                if at==admit_at:u.reg_write(UC_X86_REG_EFLAGS,value)
            m.uc.hook_add(UC_HOOK_CODE,flags)
        elif name=='status-overlap':
            for field,v in dict(csi_row_count=25,csi_last_row=24,screen_last_row=24,erase_cell_count=3300).items():m.put(field,v)
        else:m.put(name,value)
        rx=bytes(m.uc.mem_read(m.symbols['uart_rx_buffer'],4096));count=m.get('uart_rx_count')
        try:m.call(entry,limit=1000000)
        except Abort as problem:assert error and problem.args==(error,),(name,entry,problem.args)
        else:assert error is None and m.uc.reg_read(UC_X86_REG_EFLAGS)&1,(name,entry)
        assert bytes(m.uc.mem_read(0xb8000,4000))==video and bytes(m.uc.mem_read(address,8192))==shadow,(name,entry)
        assert bytes(m.uc.mem_read(m.symbols['uart_rx_buffer'],4096))==rx and m.get('uart_rx_count')==count
        rejections+=1
    # A redundant native restore would discard visible edits from a stale
    # shadow pane. Live callers must request a transition from the other pane.
    for entry,active,error in [('screen_viewport_enter',1,0x482a),('screen_viewport_leave',0,0x4850)]:
        m,address,video,shadow=fixture()
        m.put('screen_viewport_active',active);m.put('screen_viewport_offset',0 if active else 52)
        try:m.call(entry)
        except Abort as problem:assert problem.args==(error,)
        else:raise AssertionError('Redundant pane restore admitted')
        assert bytes(m.uc.mem_read(0xb8000,4000))==video and bytes(m.uc.mem_read(address,8192))==shadow
        assert not m.viewport_callbacks
        rejections+=1
    m=Live();m.call('terminal_sink_427f');m.call('screen_viewport_refresh')
    try:m.call('screen_viewport_refresh')
    except Abort as problem:assert problem.args==(0x2fb8,)
    else:raise AssertionError('Capture refresh token was not consumed')
    report=dict(passed=True,binary_sha256=manifest['binary_sha256'],cursor_transitions=transitions,
        parser_output_erase_cases=rendered,pre_copy_rejections=rejections,capture_refresh_separate=True,hardware_callbacks_owned_DS=True,
        checker_sha256=sha(Path(__file__)),sources=manifest['sources'],original_inputs=[],
        scope='Actual linked recovered viewport/cursor plus live static-shadow admission and real UART/parser/output/erase at132 logical columns over80 physical columns. Restricted heights, visible/hidden status, profiles4/6, pane overlap and receive preservation; unsupported ownership/geometry/FLAGS refuses before copy. BIOS/UART hardware model; no enabled peer width request, general132 field repair/UI/child/BBS or physical acceptance.')
    (OUT/'viewport-live-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS live viewport:',transitions,'cursor transitions,',rendered,'parser output/erase,',rejections,'pre-copy rejections')


if __name__=='__main__':main()
