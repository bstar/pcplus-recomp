#!/usr/bin/env python3
"""Exercise real combined escape/CSI/parser/attribute/cursor instructions."""
import hashlib
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_INTR
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_DX,UC_X86_REG_BP,UC_X86_REG_BX,UC_X86_REG_CX
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1]

class MissingService(Exception):
    pass

class Csi(DosImage):
    def __init__(self):
        super().__init__(ROOT/'build/csi/CSI.EXE',ROOT/'build/csi/csi.map')
        self.positions=[]
        self.rectangles=[]
        self.cursor_shapes=[]
        self.bios_cursor_shape=0x060f
        self.initial_cells=[((i//80)%7+1)*256+(33+i%80) for i in range(2000)]
        self.uc.mem_write(0xb8000,struct.pack("<2000H",*self.initial_cells))
        self.uc.hook_add(UC_HOOK_INTR,self.interrupt)

    def interrupt(self,uc,number,_):
        if number==3:
            raise MissingService(self.get('csi_unimplemented_service'))
        ax=uc.reg_read(UC_X86_REG_AX)
        assert number==0x10,(number,hex(ax))
        if ax>>8==2:
            self.positions.append(uc.reg_read(UC_X86_REG_DX))
            return
        if ax>>8==1:
            self.bios_cursor_shape=uc.reg_read(UC_X86_REG_CX)
            self.cursor_shapes.append(self.bios_cursor_shape)
            # Exercise the recovered BIOS wrapper's explicit BP protection.
            uc.reg_write(UC_X86_REG_BP,0xdead)
            return
        if ax>>8==3:
            uc.reg_write(UC_X86_REG_CX,self.bios_cursor_shape)
            uc.reg_write(UC_X86_REG_DX,self.positions[-1] if self.positions else 0)
            return
        assert ax>>8 in (6,7),(number,hex(ax))
        bx,cx,dx=[uc.reg_read(r) for r in (UC_X86_REG_BX,UC_X86_REG_CX,UC_X86_REG_DX)]
        top,left,bottom,right=cx>>8,cx&255,dx>>8,dx&255
        assert 0<=top<=bottom<25 and 0<=left<=right<80,(top,left,bottom,right)
        self.rectangles.append((ax>>8,ax&255,bx>>8,top,left,bottom,right))
        old=self.video_cells();new=old[:];count=ax&255;delta=count if ax>>8==6 else -count
        for row in range(top,bottom+1):
            for column in range(left,right+1):
                source=row+delta
                new[row*80+column]=old[source*80+column] if count and top<=source<=bottom else ((bx>>8)*256+32)
        uc.mem_write(0xb8000,struct.pack('<2000H',*new))

    def video_cells(self):
        return list(struct.unpack('<2000H',self.uc.mem_read(0xb8000,4000)))

    def sequence(self,data):
        assert len(data)<=2048
        self.uc.mem_write(self.symbols['ansi_input_buffer'],data or b'\0')
        self.put('ansi_input_pointer',self.offset('ansi_input_buffer'))
        self.put('ansi_input_length',len(data))
        self.call('ansi_reset')
        self.call('ansi_escape_entry',limit=200000)
        assert self.uc.reg_read(UC_X86_REG_BP)==0xbabe
        assert self.get('ansi_parameter_canary')==0xa55a
        return self.get('screen_cursor_row'),self.get('screen_cursor_column')


def main():
    cases=[]
    def check(name,operation):
        operation();cases.append({'case':name,'passed':True});print(name,'passed',flush=True)

    def positions():
        c=Csi()
        for data,want in [(b'[10;20H',(9,19)),(b'[2A',(7,19)),(b'[3B',(10,19)),
            (b'[4C',(10,23)),(b'[5D',(10,18)),(b'[12G',(10,11)),(b'[4;7f',(3,6)),
            (b'[H',(0,0)),(b'[999;999H',(24,79)),(b'[0;0H',(0,0))]:
            assert c.sequence(data)==want,(data,want)
            assert c.positions[-1]==want[0]*256+want[1]
            assert c.get('screen_video_offset')==want[0]*160+want[1]*2
            assert c.get('screen_attribute_offset')==want[0]*80+want[1]
    check('real-parser-to-dispatch-to-bios-cursor-and-buffer-offsets',positions)

    def colors():
        c=Csi()
        for data,want in [(b'[31m',4),(b'[1m',12),(b'[5m',140),(b'[7m',200),
            (b'[7m',200),(b'[0m',7),(b'[34;43m',0x61),(b'[22;25m',0x61)]:
            c.sequence(data)
            assert c.get('attributes_current')==want,(data,hex(c.get('attributes_current')),hex(want))
    check('real-sgr-table-and-recovered-attribute-helpers',colors)

    def margins():
        c=Csi()
        c.sequence(b'[5;20r')
        assert (c.get('csi_scroll_top'),c.get('csi_scroll_bottom'))==(4,19)
        assert c.sequence(b'[10;10H')==(9,9)
        c.put('csi_origin_mode',1)
        assert c.sequence(b'[6;18r')==(5,0)
        assert c.get('csi_origin_row')==5 and c.get('csi_origin_bottom')==17
        assert c.sequence(b'[2;10H')==(6,9)
    check('scroll-region-and-shared-origin-state',margins)

    def secondary():
        for terminal,want in [(4,b'\x1b[>1;10;0c'),(5,b'\x1b[>24;10;0c'),(9,b'\x1b[>4c')]:
            c=Csi();c.put('csi_terminal_id',terminal);c.sequence(b'[>0c')
            output=bytes(c.uc.mem_read(c.symbols['csi_output_buffer'],c.get('csi_output_length')))
            assert output==want,(terminal,output,want)
    check('secondary-device-attributes-output-abi',secondary)

    def malformed():
        for data,error in [(b'['+b'0'*32+b'H',1),(b'[65536H',2),
            (b'['+b';'*17+b'H',3),(b'[12',4)]:
            c=Csi();c.sequence(data)
            assert c.get('ansi_parse_error')==error and not c.positions
    check('malformed-input-aborts-before-screen-services',malformed)

    def q():
        c=Csi();assert c.sequence(b'[;4qNEXT')==(0,0)
        assert c.get('ansi_input_position')==4
        assert c.get('csi_receive_calls')==4
    check('maintained-csi-q-does-not-consume-next-payload',q)

    def erase():
        tests=[(b'[2J',lambda r,c:True,7),(b'[J',lambda r,c:r>9 or r==9 and c>=19,7),
            (b'[1J',lambda r,c:r<9 or r==9 and c<=19,7),
            (b'[K',lambda r,c:r==9 and c>=19,7),(b'[1K',lambda r,c:r==9 and c<=19,7),
            (b'[2K',lambda r,c:r==9,7),(b'[4X',lambda r,c:r==9 and 19<=c<=22,0x1e)]
        for data,predicate,attribute in tests:
            c=Csi();c.sequence(b'[10;20H');c.put('attributes_current',0x1e)
            assert c.sequence(data)==(9,19),data
            expected=[attribute*256+32 if predicate(i//80,i%80) else v for i,v in enumerate(c.initial_cells)]
            assert c.video_cells()==expected,data
            assert c.rectangles and c.get('csi_wrap_pending')==0,data
        c=Csi();c.sequence(b'[2J');assert c.sequence(b'[24;80H')==(23,79)
    check('real-csi-j-k-x-through-recovered-erase-to-video-memory',erase)

    def bounded_x():
        for data,count in [(b'[X',1),(b'[0X',1),(b'[1X',1),(b'[61X',61),
                           (b'[62X',61),(b'[999X',61),(b'[65535X',61)]:
            c=Csi();c.sequence(b'[10;20H');c.put('attributes_current',0x1e)
            assert c.sequence(data)==(9,19)
            assert c.rectangles==[(6,0,0x1e,9,19,9,19+count-1)],(data,c.rectangles)
            assert c.video_cells()==[0x1e20 if i//80==9 and 19<=i%80<19+count else v for i,v in enumerate(c.initial_cells)]
        c=Csi();c.sequence(b'[25;80H');c.sequence(b'[65535X')
        assert c.rectangles==[(6,0,7,24,79,24,79)]
        c=Csi();c.put('screen_cursor_column',80);c.sequence(b'[X')
        assert not c.rectangles and c.video_cells()==c.initial_cells
    check('maintained-csi-x-default-and-row-boundary-guards',bounded_x)

    def reports():
        for data,want in [(b'[5n',b'\x1b[0n'),(b'[6n',b'\x1b[10;20R'),
                          (b'[0c',b'\x1b[?62;2c'),(b'Z',b'\x1b[?62;2c')]:
            c=Csi();c.sequence(b'[10;20H');c.sequence(data)
            output=bytes(c.uc.mem_read(c.symbols['csi_output_buffer'],c.get('csi_output_length')))
            assert output==want,(data,output,want)
        c=Csi();c.sequence(b'[10;20H');c.put('csi_report_private_prefix',1);c.sequence(b'[?6n')
        output=bytes(c.uc.mem_read(c.symbols['csi_output_buffer'],c.get('csi_output_length')))
        assert output==b'\x1b[0;10;20R',output
        for ready,want in [(0,b'\x1b[?13n'),(1,b'\x1b[?10n')]:
            c=Csi();c.put('csi_printer_ready',ready);c.sequence(b'[15n')
            output=bytes(c.uc.mem_read(c.symbols['csi_output_buffer'],c.get('csi_output_length')))
            assert output==want,(ready,output,want)
    check('real-primary-attributes-status-and-cursor-report-output',reports)

    def cursor_state():
        live=['ansi_charset_g1_flag_graphics','ansi_charset_g0_flag_graphics',
              'cursor_state_value_cdfc','cursor_state_value_ce04','attributes_current',
              'cursor_state_value_1d20','csi_origin_mode','csi_wrap_pending']
        saved=['cursor_state_saved_cdf0','cursor_state_saved_cdec',
               'cursor_state_saved_cdfc','cursor_state_saved_ce04','cursor_state_saved_1f70',
               'cursor_state_saved_1d20','cursor_state_saved_cdd2','cursor_state_saved_3342']
        for save,restore,full in [(b'7',b'8',True),(b'[s',b'[u',False)]:
            c=Csi();assert c.sequence(b'[10;20H')==(9,19)
            original=[1,1,0x1234,0x5678,0x8c,0x4321,1,1]
            for name,value in zip(live,original):c.put(name,value)
            c.sequence(save)
            assert (c.get('csi_saved_row'),c.get('csi_saved_column'))==(9,19)
            assert [c.get(name) for name in saved]==(original if full else [0]*8)
            # Change cursor with origin disabled before selecting a different state.
            c.put('csi_origin_mode',0)
            assert c.sequence(b'[3;4H')==(2,3)
            current=[0,0,0x2468,0x1357,7,0x1111,0,0]
            for name,value in zip(live,current):c.put(name,value)
            assert c.sequence(restore)==(9,19)
            assert [c.get(name) for name in live]==(original if full else current)
            assert c.positions[-1]==0x0913
            assert c.get('screen_video_offset')==9*160+19*2
            assert c.get('screen_attribute_offset')==9*80+19
            assert c.get('csi_unimplemented_service')==0
    check('real-esc7-8-full-state-and-csi-s-u-position-only-restore',cursor_state)

    def scroll_routes():
        c=Csi();c.sequence(b'[10;20H')
        assert c.sequence(b'D')==(10,19)
        assert c.sequence(b'E')==(11,0)
        assert c.sequence(b'M')==(10,0)
        assert not c.rectangles
        for command,delta,start in [(b'D',1,19),(b'M',-1,4),(b'E',1,19)]:
            c=Csi();c.sequence(b'[5;20r');c.sequence(f'[{start+1};20H'.encode())
            c.put('csi_wrap_pending',1)
            want_column=0 if command==b'E' else 19
            assert c.sequence(command)==(start,want_column)
            expected=c.initial_cells[:]
            for row in range(4,20):
                for column in range(80):
                    source=row+delta
                    expected[row*80+column]=c.initial_cells[source*80+column] if 4<=source<=19 else 0x0720
            assert c.video_cells()==expected,(command,c.rectangles)
            assert c.get('csi_wrap_pending')==0
            assert c.rectangles==[(6 if delta>0 else 7,1,7,4,0,19,79)]
        c=Csi();c.sequence(b'[25;80H');c.call('screen_wrap_forward')
        assert (c.get('screen_cursor_row'),c.get('screen_cursor_column'))==(24,0)
        assert c.get('screen_video_offset')==24*160
        assert c.get('screen_attribute_offset')==24*80
        assert c.rectangles==[(6,1,7,0,0,24,79)]
        assert c.symbols['scroll_skip_attribute_scan']==c.symbols['csi_report_private_prefix']
    check('real-esc-index-nextline-reverseindex-and-bottom-wrap-video',scroll_routes)

    def modes():
        c=Csi();c.sequence(b'[4h');assert c.get('terminal_mode_372c')==1
        c.sequence(b'[?4l');assert c.get('terminal_mode_372c')==1
        c.sequence(b'[4l');assert c.get('terminal_mode_372c')==0
        c.sequence(b'[?7;18;19h')
        assert [c.get(name) for name in ['cursor_state_value_1d20','modes_value_3980','modes_value_3982']]==[1,1,0]
        c.put('csi_wrap_pending',1);c.sequence(b'[?7;18;19l')
        assert [c.get(name) for name in ['cursor_state_value_1d20','modes_value_3980','modes_value_3982','csi_wrap_pending']]==[0,0,1,0]
        c.sequence(b'[5;20r');assert c.sequence(b'[?6h')==(4,0)
        assert (c.get('csi_origin_mode'),c.get('csi_origin_row'),c.get('csi_origin_bottom'))==(1,4,19)
        assert c.sequence(b'[2;10H')==(5,9)
        assert c.sequence(b'[?6l')==(0,0)
        assert (c.get('csi_origin_mode'),c.get('csi_origin_row'),c.get('csi_origin_bottom'))==(0,0,24)
        assert c.get('screen_video_offset')==0 and c.get('screen_attribute_offset')==0
        c.put('csi_report_private_prefix',1);c.sequence(b'[?7h')
        assert c.get('cursor_state_value_1d20')==0
    check('real-parser-mode-state-origin-home-and-private-gates',modes)

    def cursor_key_modes():
        for command,prefix,next_prefix in [(b'[?1h','[','O'),(b'[?1l','O','['),
                                          (b'[1h','[','O'),(b'[1l','O','[')]:
            c=Csi();c.put('terminal_dec_keys',1);c.put('terminal_mode_372c',0x5555)
            entries=[bytes([27,ord(prefix),ch,0])+b'\xa5'*8 for ch in b'ABCD']
            entries += [b'CUSTOM\0'+b'\xa5'*5,bytes([27,ord(prefix),ord('A'),ord('X'),0])+b'\xa5'*7]
            while len(entries)<79:entries.append(b'\0'+b'\xa5'*11)
            entries[-1]=bytes([27,ord(prefix),ord('D'),0])+b'\xa5'*8
            initial=b''.join(entries);c.uc.mem_write(c.symbols['terminal_keymap'],initial)
            c.sequence(command)
            expected=bytearray(initial)
            for index in (0,1,2,3,78):expected[index*12+1]=ord(next_prefix)
            assert bytes(c.uc.mem_read(c.symbols['terminal_keymap'],948))==expected,command
            assert c.get('terminal_mode_372c')==0x5555
        c=Csi();c.put('terminal_dec_keys',0)
        initial=b'\x1b[A\0'+b'\xa5'*944
        c.uc.mem_write(c.symbols['terminal_keymap'],initial);c.sequence(b'[?1h')
        assert bytes(c.uc.mem_read(c.symbols['terminal_keymap'],948))==initial
    check('real-decckm-parser-to-arrow-keymap-rewrite-preserves-custom-bindings',cursor_key_modes)

    def cursor_visibility():
        for flags,visible,hidden in [(0,0x000f,0x200f),(1,0x0e0f,0x2e0f),
                                     (2,0x080f,0x280f),(0xa503,0x080f,0x280f)]:
            c=Csi();c.put('modes_cursor_flags',flags);c.sequence(b'[?25h')
            assert c.get('modes_cursor_flags')==flags|4
            assert c.bios_cursor_shape==visible and c.cursor_shapes==[visible]
            assert c.get('cursor_shape_visibility_state')==1
            c.sequence(b'[?25l')
            assert c.get('modes_cursor_flags')==flags&~4
            assert c.bios_cursor_shape==hidden and c.cursor_shapes==[visible,hidden]
            assert c.get('cursor_shape_visibility_state')==0
        c=Csi();c.put('cursor_shape_visibility_state',2);c.sequence(b'[?25h')
        assert not c.cursor_shapes and c.get('cursor_shape_visibility_state')==2
        c.sequence(b'[?25l');assert c.cursor_shapes==[0x200f]
    check('real-mode25-parser-to-cursor-visibility-and-scanline-BIOS',cursor_visibility)

    def missing_mode_effects():
        for data,address in [(b'[?3h',0x2a6e),(b'[?3l',0x2a6e),(b'[?2l',0x20a4),
                             (b'[12h',0x2fb8)]:
            c=Csi()
            try:c.sequence(data)
            except MissingService as error:assert error.args==(address,),(data,error.args)
            else:raise AssertionError(('Unrecovered mode side effect silently succeeded',data))
            if data==b'[?2l':assert (c.get('csi_previous_terminal_id'),c.get('csi_terminal_id'))==(4,1)
    check('unrecovered-mode-side-effects-fail-explicitly-after-real-state-updates',missing_mode_effects)

    def rendered_state():
        def put_text(c,text):
            for value in text:c.call('render_character',(value,))
        c=Csi();c.sequence(b'[2J');put_text(c,b'Hello')
        c.sequence(b'[31m');put_text(c,b'!')
        assert c.video_cells()[:6]==[0x0700|v for v in b'Hello']+[0x0421]
        assert (c.get('screen_cursor_row'),c.get('screen_cursor_column'))==(0,6)
        c.sequence(b'[6n')
        assert bytes(c.uc.mem_read(c.symbols['csi_output_buffer'],c.get('csi_output_length')))==b'\x1b[1;7R'
        c=Csi();c.sequence(b'[7h');c.sequence(b'[25;80H');c.sequence(b'[31m');put_text(c,b'XY')
        assert c.video_cells()[23*80+79]==0x0458
        assert c.video_cells()[24*80]==0x0459
        assert (c.get('screen_cursor_row'),c.get('screen_cursor_column'))==(24,1)
        c=Csi();c.sequence(b'[7l');c.sequence(b'[25;80H');put_text(c,b'XY')
        assert c.video_cells()[-1]==0x0759 and c.get('screen_cursor_column')==79
        c=Csi();c.sequence(b'[4h')
        try:put_text(c,b'A')
        except MissingService as error:assert error.args==(0xb9f7,)
        else:raise AssertionError('Unrecovered DS372c side effect silently succeeded')
    check('shared-parser-renderer-color-report-wrap-and-scroll-state',rendered_state)

    def missing():
        c=Csi();c.put('screen_cursor_wrap',1);c.put('screen_attribute_checks',1)
        try:c.sequence(b'[K')
        except MissingService as error:assert error.args==(0xd05f,)
        else:raise AssertionError('Unrecovered protected erase silently succeeded')
    check('unrecovered-protected-erase-boundary-fails-explicitly',missing)

    result={'passed':True,'binary_sha256':hashlib.sha256((ROOT/'build/csi/CSI.EXE').read_bytes()).hexdigest(),
        'cases':cases,'scope':'Actual linked escape/parameter/transition/dispatcher/attribute/cursor/report/erase/scroll/save-restore/modes/cursor-shape instructions; explicit BIOS text-video model plus memory input/output, unresolved application services trap. Ordinary text uses recovered renderer/video writers with fixture glyph resources; no live modem or complete application.'}
    (ROOT/'build/csi/csi-results.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
