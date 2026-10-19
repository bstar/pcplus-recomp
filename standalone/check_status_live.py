#!/usr/bin/env python3
"""Run actual linked parent STATUS staging/drawing; only MSR reads modeled."""
import hashlib
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_INSN, UC_HOOK_INTR
from unicorn.x86_const import *
from dos_image import DosImage

ROOT = Path(__file__).resolve().parents[1]
BINARY = ROOT / 'build/terminal/TERMINAL.EXE'
MAP = BINARY.parent / 'terminal.map'


class Status(DosImage):
    def __init__(self, carrier=0):
        super().__init__(BINARY, MAP)
        self.carrier = carrier
        self.inputs = []
        self.uc.hook_add(UC_HOOK_INSN, self.port, None, 1, 0, UC_X86_INS_IN)
        self.uc.hook_add(UC_HOOK_INTR, self.interrupt)
        for name, value in dict(terminal_program_active=1, terminal_baud_low=38400,
            terminal_baud_high=0, terminal_parity=0, terminal_data_bits=8,
            terminal_stop_bits=1, uart_port_msr=0x3fe).items():
            self.put(name, value)
        self.uc.mem_write(self.symbols['_command_menu_script'], b'C:\\TOOLS\\CHECK.ASX\0')
        self.uc.mem_write(0xb8000, b'\xcc' * 4004)

    def port(self, uc, port, size, user):
        assert port == 0x3fe and size == 1
        self.inputs.append(port)
        return self.carrier

    def interrupt(self, *args):
        raise AssertionError('STATUS must not invoke DOS/BIOS or an interrupt')

    def run(self, duplex=65535):
        uc = self.uc
        target = self.symbols['terminal_status_live']
        memory=json.loads((BINARY.parent/'manifest.json').read_text())['memory_layout']
        segment=self.base_segment+next(s['relative_segment'] for s in memory['code_segments'] if s['name']=='CONFIG_CODE')
        # Return to the existing unused near sentinel using an actual far frame.
        sp = self.offset('terminal_stack_top') - 4
        for reg, value in ((UC_X86_REG_CS, segment), (UC_X86_REG_IP, target-segment*16),
            (UC_X86_REG_DS, self.ds), (UC_X86_REG_SS, self.ds), (UC_X86_REG_SP, sp),
            (UC_X86_REG_BX, duplex), (UC_X86_REG_BP, 0xbabe), (UC_X86_REG_EFLAGS, 0x202)):
            uc.reg_write(reg, value)
        uc.mem_write(self.data_base + sp, struct.pack('<HH', self.return_offset, self.base_segment))
        self.returned = False
        uc.emu_start(target, 0, count=250000)
        assert self.returned
        assert uc.reg_read(UC_X86_REG_SP) == sp + 4 and uc.reg_read(UC_X86_REG_BP) == 0xbabe
        assert uc.reg_read(UC_X86_REG_DS) == uc.reg_read(UC_X86_REG_SS) == self.ds
        assert uc.reg_read(UC_X86_REG_EFLAGS) & 0x600 == 0x200
        return uc.reg_read(UC_X86_REG_AX)

    def row(self):
        return bytes(self.uc.mem_read(0xb8000+3840, 162))[::2]


def main():
    cases = []
    def done(name, machine, expected=0, duplex=65535):
        old = machine.get('modes_value_1d1a')
        assert machine.run(duplex) == expected, name
        assert machine.get('modes_value_1d1a') == old, 'Drawing must not commit a duplex setting'
        if expected:
            assert bytes(machine.uc.mem_read(0xb8000, 4004)) == b'\xcc'*4004
            assert not machine.inputs
        else:
            assert bytes(machine.uc.mem_read(0xb8000, 3840)) == b'\xcc'*3840
        cases.append(dict(name=name, passed=True, result=expected, msr_reads=len(machine.inputs)))
    for index, rate in enumerate((300,1200,2400,4800,9600,19200,38400,57600,115200)):
        for profile, label in ((4,b'VT220'), (6,b'ANSI')):
            m = Status(128)
            m.put('terminal_baud_low',rate & 65535);m.put('terminal_baud_high',rate >> 16)
            m.put('csi_terminal_id',profile)
            done(f'profile-{profile}-rate-{rate}',m)
            row=m.row()
            assert row.startswith(b' CHECK.ASX') and label in row and str(rate).encode() in row and b'ON-LINE ' in row
            assert m.get('reset_data_1b86') == index and m.inputs == [0x3fe]
    for parity, char in enumerate(b'NOEMS'):
        for bits in range(5,9):
            for stop in (1,2):
                m=Status();m.put('terminal_parity',parity);m.put('terminal_data_bits',bits);m.put('terminal_stop_bits',stop)
                done(f'line-{chr(char)}{bits}{stop}',m)
                assert bytes([char,48+bits,48+stop]) in m.row() and b'OFF-LINE' in m.row()
    for parent in (0,1):
        for override in (0,1,255,65535):
            m=Status();m.put('modes_value_1d1a',parent)
            done(f'duplex-{parent}-override-{override}',m,duplex=override)
            assert (b'HDX' if (parent if override==65535 else override) else b'FDX') in m.row()
    for name,value in (('ui_flow_region_cells',79),('ui_flow_video_base',0),
        ('ui_flow_coordinate_base',0),('screen_columns',132),('terminal_tab_wrap',1),
        ('csi_terminal_id',15),('terminal_parity',5),('terminal_data_bits',4),
        ('terminal_data_bits',9),('terminal_stop_bits',0),('terminal_stop_bits',3),
        ('terminal_baud_low',12345),('terminal_baud_high',1)):
        m=Status();m.put(name,value);done(f'reject-{name}-{value}',m,3)
    for value in (256,65534):
        done(f'reject-duplex-{value}',Status(),7,value)
    for label in (b'\0',b'X'*64,b'C:\\THISLABELISTOOLONG.ASX\0'):
        m=Status();m.uc.mem_write(m.symbols['_command_menu_script'],label)
        done('reject-label-'+label.hex(),m,3)
    m=Status();m.put('ui_flow_suppressed',1);done('hidden-status',m)
    assert bytes(m.uc.mem_read(0xb8000,4004))==b'\xcc'*4004 and not m.inputs
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    report=dict(passed=True,binary_sha256=sha(BINARY),checker_sha256=sha(Path(__file__)),
        sources={name:sha(ROOT/name) for name in ('src/terminal/status_live.asm','src/status/status_state.inc')},
        cases=cases,scope='Actual linked parent far STATUS staging and complete native drawing. Authored parent fields and modeled MSR0/128 only; no product instruction skipped, no DOS/BIOS allowed. Covers profiles/rates/line fields, snapshot-only duplex overrides, bounds rejection before video/MSR, label basename and hidden state. Guarded child RPC and physical modem are separate proofs.')
    (BINARY.parent/'status-live-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Live STATUS:',len(cases),'linked cases PASS')


if __name__=='__main__':main()
