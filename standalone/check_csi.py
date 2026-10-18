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

    def missing():
        c=Csi();c.put('screen_cursor_wrap',1);c.put('screen_attribute_checks',1)
        try:c.sequence(b'[K')
        except MissingService as error:assert error.args==(0xd05f,)
        else:raise AssertionError('Unrecovered protected erase silently succeeded')
    check('unrecovered-protected-erase-boundary-fails-explicitly',missing)

    result={'passed':True,'binary_sha256':hashlib.sha256((ROOT/'build/csi/CSI.EXE').read_bytes()).hexdigest(),
        'cases':cases,'scope':'Actual linked escape/parameter/transition/dispatcher/attribute/cursor/report/erase/save-restore instructions; explicit BIOS text-video model plus memory input/output, unresolved application services trap. No live modem/full renderer.'}
    (ROOT/'build/csi/csi-results.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
