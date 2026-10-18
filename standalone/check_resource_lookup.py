#!/usr/bin/env python3
"""Actual linked default lookup, bounded far environment and checked DOS IO."""
import hashlib
import json
from pathlib import Path
import struct
from unicorn import UC_HOOK_MEM_READ
from unicorn.x86_const import UC_X86_REG_AX, UC_X86_REG_DS, UC_X86_REG_DX
from check_translation_live import Translation, ROOT, BINARY

IDENTITY = bytes(range(256))


class Lookup(Translation):
    maximum_stack = 0

    def call(self, name, *args, **kwargs):
        kwargs.setdefault('limit', 6000000)
        result = super().call(name, *args, **kwargs)
        Lookup.maximum_stack = max(Lookup.maximum_stack, getattr(self, 'max_stack', 0))
        return result

    def __init__(self, fault=None, open_error=0):
        super().__init__(fault)
        self.open_error = open_error
        self.env_reads = []
        self.uc.hook_add(UC_HOOK_MEM_READ, self.observe_environment,
                         begin=0x90000, end=0xa000f)
        self.resource_environment([])

    def observe_environment(self, uc, access, address, size, value, data):
        if 0x90000 <= address <= 0xa000f:
            self.env_reads.append((address, size))

    def resource_environment(self, entries, raw=None, paragraphs=0x1000, signature=b'M'):
        raw = raw if raw is not None else b'\0'.join(entries) + b'\0\0'
        assert len(raw) <= 65536
        self.put('process_psp', 0x800)
        self.uc.mem_write(0x802c, struct.pack('<H', 0x9000))
        self.uc.mem_write(0x8fff0, signature + b'\x00\x08' + struct.pack('<H', paragraphs) + bytes(11))
        self.uc.mem_write(0x90000, bytes(65536))
        self.uc.mem_write(0x90000, raw)
        self.env_reads.clear()

    def interrupt(self, uc, number, data):
        if number == 0x21 and uc.reg_read(UC_X86_REG_AX) == 0x3d00 and self.open_error:
            name = self.path(uc.reg_read(UC_X86_REG_DS), uc.reg_read(UC_X86_REG_DX))
            if name == 'PCPLUS.XLT':
                self.xlt_calls.append((0x3d, name, self.open_error, 0))
                uc.reg_write(UC_X86_REG_AX, self.open_error)
                self.set_carry(True)
                return
        super().interrupt(uc, number, data)


def main():
    cases = []
    def done(name, count=1):
        cases.append(dict(case=name, inputs=count, passed=True))
        print(name, 'passed', count, flush=True)
    def rejected(model, status=6):
        before = b'\xa5'*256
        model.uc.mem_write(model.symbols['terminal_translation_table'], before)
        assert model.load(None, selected=False, prm_mode=1) == 12
        assert model.get('terminal_translation_status') == status
        assert not model.get('terminal_translation_enabled')
        assert bytes(model.uc.mem_read(model.symbols['terminal_translation_table'], 256)) == before

    for directory, expected in [(b'D:\\CFG', 'D:\\CFG\\PCPLUS.XLT'),
                                (b'D:\\CFG\\', 'D:\\CFG\\PCPLUS.XLT'),
                                (b'D:', 'D:\\PCPLUS.XLT'),
                                (b'..\\CFG', '..\\CFG\\PCPLUS.XLT')]:
        m = Lookup();m.resource_environment([b'IGNORED=VALUE', b'PCPLUS='+directory])
        m.files[expected] = bytearray(IDENTITY)
        assert m.load(None, selected=False, prm_mode=1) == 0
        assert [c[1] for c in m.xlt_calls if c[0] == 0x3d] == ['PCPLUS.XLT', expected]
        assert m.env_reads and m.far_seen and not m.xlt_handles
    done('current-open-miss-then-one-PCPLUS-directory-native-separator-rules', 4)

    for entries in [[], [b'PCPLUS='], [b'pcplus=D:\\CFG'], [b'PCPLUSX=D:\\CFG'],
                    [b'PCPLUS=', b'PCPLUS=D:\\CFG']]:
        m = Lookup();m.resource_environment(entries);rejected(m, 2)
        assert len(m.xlt_calls) == 1
    done('absent-empty-case-sensitive-name-and-first-duplicate-selection', 5)
    m = Lookup();m.resource_environment([b'PCPLUS=D:\\FIRST', b'PCPLUS=D:\\SECOND'])
    m.files['D:\\FIRST\\PCPLUS.XLT'] = bytearray(IDENTITY)
    assert not m.load(None, selected=False, prm_mode=1)
    assert m.xlt_calls[-1][1] == 'D:\\FIRST\\PCPLUS.XLT'
    done('first-nonempty-duplicate-directory-wins')

    for size in range(1, 65):
        m = Lookup();m.resource_environment([b'PCPLUS='+b'A'*size])
        name = 'A'*size+'\\PCPLUS.XLT'
        if size <= 49:
            m.files[name] = bytearray(IDENTITY)
            assert not m.load(None, selected=False, prm_mode=1), size
        else:
            rejected(m)
            assert len(m.xlt_calls) == 1
    done('every-relative-directory-length1-through64-canonical63-byte-path-limit', 64)

    for value in [b'"D:\\CFG"', b'D:\\A B', b'D:\\CFG;C:\\OTHER', b'D:\\*', b'D:\\?',
                  b'D:\\<', b'D:\\>', b'D:\\|', b'D:\\=', b'D:\x01', b'D:\xff']:
        m = Lookup();m.resource_environment([b'PCPLUS='+value]);rejected(m)
        assert len(m.xlt_calls) == 1
    done('invalid-directory-characters-never-open-fallback', 11)

    for raw, paragraphs, signature in [(b'A'*16, 1, b'M'),
             (b'PCPLUS=D:\\CFG\0XY', 1, b'M'), (b'\0A', 1, b'M'),
             (b'\0\0', 0, b'M'), (b'\0\0', 0x8000, b'M'), (b'\0\0', 1, b'X')]:
        m = Lookup();m.resource_environment([], raw=raw, paragraphs=paragraphs, signature=signature)
        rejected(m)
        if paragraphs==1:assert all(a+s<=0x90010 for a,s in m.env_reads)
    done('MCB-shape-extent-and-complete-double-NUL-environment-validation', 6)

    # A match does not excuse a malformed remainder or wrapping16-bit indexing.
    m = Lookup();m.resource_environment([], raw=b'PCPLUS=D:\\CFG\0'+b'A'*(65536-14))
    rejected(m)
    assert m.env_reads[-1][0] == 0x9ffff
    m = Lookup();m.resource_environment([], raw=b'PAD='+b'A'*65505+b'\0PCPLUS=D:\\CFG\0\0')
    m.files['D:\\CFG\\PCPLUS.XLT'] = bytearray(IDENTITY)
    assert not m.load(None, selected=False, prm_mode=1)
    assert all(a+s<=0xa0000 for a,s in m.env_reads)
    done('full64KiB-environment-scan-validates-trailing-data-without-offset-wrap', 2)

    for psp in (0, 65535):
        m = Lookup();m.put('process_psp', psp);rejected(m)
        assert len(m.xlt_calls)==1 and not m.env_reads
    m = Lookup();m.uc.mem_write(0x802c, bytes(2));rejected(m, 2)
    assert not m.env_reads
    m = Lookup();m.put('process_psp', m.ds+(m.offset('terminal_stack_top')-256)//16);rejected(m)
    m = Lookup();segment=m.ds+(m.offset('terminal_stack_top')-512)//16
    m.uc.mem_write(0x802c, struct.pack('<H', segment))
    m.uc.mem_write((segment-1)*16, b'M\0\0\x40\0'+bytes(11));rejected(m)
    done('missing-PSP-invalid-physical-extent-no-environment-and-stack-alias-rejection', 5)

    for bad in range(6):
        m = Lookup();destination=m.offset('terminal_translation_table');result=m.offset('terminal_translation_io')
        m.uc.mem_write(m.data_base+destination, b'\xa5'*256);m.uc.mem_write(m.data_base+result, b'\xcc'*8)
        actual_dest,actual_result=destination,result
        if bad==0:actual_dest=0
        if bad==1:actual_dest=0xff01
        if bad==2:actual_result=0xfffc
        if bad==3:actual_result=destination
        if bad==4:actual_result=destination+250
        if bad==5:actual_dest=result
        assert m.call('_xlt_dos_read_default', [0x800,actual_dest,actual_result])==1
        assert not m.xlt_calls and not m.env_reads
        assert bytes(m.uc.mem_read(m.data_base+destination, 256))==b'\xa5'*256
        assert bytes(m.uc.mem_read(m.data_base+result, 8))==b'\xcc'*8
    done('default-loader-null-wrap-and-overlap-arguments-reject-before-IO', 6)

    for error in (2, 3, 5):
        m = Lookup(open_error=error);m.resource_environment([b'PCPLUS=D:\\CFG'])
        m.files['D:\\CFG\\PCPLUS.XLT'] = bytearray(IDENTITY)
        if error in (2, 3):assert not m.load(None, selected=False, prm_mode=1)
        else:
            rejected(m, 2);assert not m.env_reads and len(m.xlt_calls)==1
    done('only-open-errors2-and3-enable-fallback-access-denied-stops', 3)
    for fault, blob, expected in [(None, b'', 4), (None, bytes(255), 4),
                                 (None, bytes(257), 4), ('read', IDENTITY, 3),
                                 ('probe', IDENTITY, 3), ('close', IDENTITY, 5)]:
        m = Lookup(fault);m.files['PCPLUS.XLT'] = bytearray(blob)
        m.resource_environment([b'PCPLUS=D:\\CFG']);m.files['D:\\CFG\\PCPLUS.XLT'] = bytearray(IDENTITY)
        rejected(m, expected);assert not m.env_reads
        assert [c[1] for c in m.xlt_calls if c[0]==0x3d] == ['PCPLUS.XLT']
    done('damaged-current-table-read-probe-or-close-error-never-hidden-by-fallback', 6)

    for mode in (0, 2):
        m = Lookup();m.resource_environment([], raw=b'A'*16, paragraphs=1)
        assert not m.load(None, selected=False, prm_mode=mode) and not m.env_reads and not m.xlt_calls
    m = Lookup();m.resource_environment([], raw=b'A'*16, paragraphs=1)
    assert not m.load(IDENTITY) and not m.env_reads
    m = Lookup();m.resource_environment([], raw=b'A'*16, paragraphs=1)
    assert not m.load(IDENTITY, selected=False, prm_mode=1) and not m.env_reads
    done('explicit-X-identity-sevenbit-and-valid-current-table-ignore-environment', 4)
    assert Lookup.maximum_stack < 1536
    result = dict(passed=True, inputs=sum(c['inputs'] for c in cases), cases=cases,
                  maximum_stack_bytes=Lookup.maximum_stack,
                  binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
                  sources={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in [Path(__file__).resolve(), ROOT/'src/config/resource_path.c',
                                     ROOT/'src/config/resource_path.h', ROOT/'src/translation/xlt_default.c',
                                     ROOT/'src/translation/xlt_default.h',
                                     ROOT/'src/translation/xlt_live.c',ROOT/'src/translation/xlt_live.h',
                                     ROOT/'src/terminal/translation.asm']},
                  scope='Actual linked startup selector, cdecl/far adapters, bounded PSP/MCB environment parser and checked DOS reader. Only DOS IO and BIOS/UART modeled. Current-file error precedence, no fallback for explicit /X or modes0/2, destination preservation and64KiB environment bounds. Actual DOS environment/import tests remain separate.')
    (ROOT/'build/terminal/resource-lookup-checks.json').write_text(json.dumps(result, indent=2)+'\n')
    print('Resource lookup passed:', result['inputs'])


if __name__ == '__main__':
    main()
