"""Load a source-built 16-bit DOS MZ and Watcom map for bounded CPU replay."""
from pathlib import Path
import re
import struct

from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE
from unicorn.x86_const import (UC_X86_REG_AX, UC_X86_REG_BP, UC_X86_REG_SI,
    UC_X86_REG_DI, UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_SS, UC_X86_REG_SP,
    UC_X86_REG_EFLAGS)


class DosImage:
    def __init__(self, binary, map_path):
        self.image = Path(binary).read_bytes()
        header = struct.unpack_from('<14H', self.image)
        assert self.image[:2] == b'MZ'
        size = (header[2] - 1) * 512 + (header[1] or 512)
        self.base_segment = 0x1000
        self.base = self.base_segment * 16
        self.uc = Uc(UC_ARCH_X86, UC_MODE_16)
        self.uc.mem_map(0, 0x100000)
        self.uc.mem_write(self.base, self.image[header[4] * 16:size])
        for index in range(header[3]):
            off, seg = struct.unpack_from('<HH', self.image, header[12] + index * 4)
            at = self.base + seg * 16 + off
            value = struct.unpack('<H', self.uc.mem_read(at, 2))[0]
            self.uc.mem_write(at, struct.pack('<H', (value + self.base_segment) & 0xffff))
        listing = Path(map_path).read_text()
        code = re.search(r'^_TEXT\s+CODE\s+\S+\s+0000:([0-9a-f]+)\s+([0-9a-f]+)', listing, re.M | re.I)
        assert code, 'Expected one near code segment'
        code_end = int(code[1], 16) + int(code[2], 16)
        # The growing live application can occupy F000. Never let a test
        # return hook silently stop execution in the middle of product code.
        self.return_offset = 0xf000 if code_end <= 0xf000 else 0xfffe
        assert code_end <= self.return_offset, 'No unused near return sentinel'
        group = re.search(r'^DGROUP\s+([0-9a-f]+):([0-9a-f]+)', listing, re.M | re.I)
        assert group
        self.ds = self.base_segment + int(group[1], 16)
        self.data_base = self.ds * 16
        self.symbols = {name: self.base + int(seg, 16) * 16 + int(off, 16)
            for seg, off, name in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$', listing, re.M | re.I)}
        self.fixture_scratch_end = None
        stack = re.search(r'^STACK\s+STACK\s+DGROUP\s+[0-9a-f]+:[0-9a-f]+\s+([0-9a-f]+)', listing, re.M | re.I)
        self.stack_bytes = int(stack[1],16) if stack else None
        self.returned = False
        self.uc.hook_add(UC_HOOK_CODE, self._stop)

    def get(self, name, width=2):
        return int.from_bytes(self.uc.mem_read(self.symbols[name], width), 'little')

    def put(self, name, value, width=2):
        self.uc.mem_write(self.symbols[name], value.to_bytes(width, 'little'))

    def offset(self, name):
        return self.symbols[name] - self.data_base

    def stage_near(self, data):
        # Model caller-owned data inside the unused bottom of the real stack.
        # Beyond STACK is another application segment, never fixture storage.
        assert self.stack_bytes and len(data)<=2049
        pointer=self.offset('terminal_stack_top')-self.stack_bytes+16
        self.fixture_scratch_end=pointer+len(data)
        self.uc.mem_write(self.data_base+pointer,data)
        return pointer

    def _stop(self, uc, address, size, _):
        if self.fixture_scratch_end is not None and uc.reg_read(UC_X86_REG_SS)==self.ds:
            bottom=self.offset('terminal_stack_top')-self.stack_bytes
            assert not bottom<=uc.reg_read(UC_X86_REG_SP)<self.fixture_scratch_end,'Actual stack entered caller fixture'
        if address == self.base + self.return_offset and uc.reg_read(UC_X86_REG_CS)==self.base_segment:
            self.returned = True
            uc.emu_stop()

    def call(self, name, arguments=(), limit=100000):
        uc = self.uc
        for register, value in [(UC_X86_REG_CS,self.base_segment), (UC_X86_REG_DS,self.ds),
            (UC_X86_REG_SS,self.ds), (UC_X86_REG_EFLAGS,0x202),
            (UC_X86_REG_BP,0xbabe), (UC_X86_REG_SI,0x1234), (UC_X86_REG_DI,0x5678)]:
            uc.reg_write(register,value)
        words = [self.return_offset] + list(arguments)
        sp = (self.offset('terminal_stack_top') if 'terminal_stack_top' in self.symbols else 0xe000) - len(words) * 2
        uc.mem_write(self.data_base + sp,struct.pack('<' + 'H' * len(words),*words))
        uc.reg_write(UC_X86_REG_SP,sp)
        self.returned = False
        uc.emu_start(self.symbols[name],0,count=limit)
        assert self.returned,f'{name} failed to return within {limit} instructions'
        assert uc.reg_read(UC_X86_REG_SP) == sp + 2,f'{name} corrupted the stack'
        return uc.reg_read(UC_X86_REG_AX)
