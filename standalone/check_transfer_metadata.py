#!/usr/bin/env python3
"""Execute native metadata/CRC/CRT with explicit UART/stat/time/UI boundaries.

Optional --original compares identical synthetic cases against SHA-verified
original instructions. Neither path opens an installed configuration or file.
"""
import argparse
import binascii
import hashlib
import json
import struct
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_AX, UC_X86_REG_SP, UC_X86_REG_IP
from dos_image import DosImage

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/transfer-metadata'
PROOF = json.loads((ROOT / 'reconstruction/transfer_metadata/provenance.json').read_text())
STATES = {name: int(at, 16) for at, name in PROOF['state'].items()}
ENTRIES = dict(send5='metadata_send_ymodem', send3='metadata_send_telink',
               parse5='metadata_parse_ymodem', parse3='metadata_parse_telink',
               end5='metadata_end_ymodem', format='metadata_signed_format')
ADDRESSES = {name: int(at, 16) for at, name in PROOF['boundaries'].items()}


def metadata(name=b'TEST.BIN', fields=b'11521'):
    return (name + b'\0' + fields + b'\0').ljust(128, b'\0')


def signed(value):
    return value if value < 0x80000000 else value - 0x100000000


def base_digits(value, radix):
    out = b''
    while True:
        value, digit = divmod(value, radix)
        out = b'0123456789abcdefghijklmnopqrstuvwxyz'[digit:digit+1] + out
        if not value:
            return out


def cases():
    rows = []
    for size in (0, 1, 65535, 65536, 11521, 0x7fffffff, 0x80000000, 0xffffffff):
        for protocol in (5, 11):
            for name in (b'TEST.BIN', b'C:\\LAB\\mIx.Bin', b'C:NAME'):
                rows.append(dict(kind='send5', size=size, protocol=protocol, name=name))
    for script in ([21, 6], [0xffff, 21, 6], [21, 21, 21], [0xffff]*3):
        rows.append(dict(kind='send5', script=script))
    for kind in ('send5', 'send3'):
        rows += [dict(kind=kind, cancel=1), dict(kind=kind, carrier=0)]
    for name in (b'X', b'FILE.BIN', b'D:\\FILES\\name.dat', b'LONGFILENAME12345'):
        for size in (0, 11521, 0xffffffff):
            rows.append(dict(kind='send3', name=name, size=size))
    rows += [dict(kind='send3', script=[21, 6]), dict(kind='send3', script=[21]*3)]
    for fields in (b'', b'0', b'11521', b'4294967295', b'4294967296', b'-1',
                   b'+42', b'12junk', b' 7', b'\t7', b'123 3314742513 100644'):
        rows.append(dict(kind='parse5', block=metadata(fields=fields)))
    rows += [dict(kind='parse5', block=bytes(128)),
             dict(kind='parse5', block=metadata(b'Z'*65, b'7')),
             dict(kind='parse5', block=b'X'*128)]
    for name in (b'A', b'FILE.BIN', b'1234567890ABCDEF'):
        for size in (0, 0xffffffff):
            rows.append(dict(kind='parse3', block=(struct.pack('<IHH', size, 0x5678, 0xabcd)
                                                  + name.ljust(16, b'\0')).ljust(128, b'\0')))
    rows.append(dict(kind='parse3', block=(struct.pack('<IHH', 7, 0x5678, 0xabcd)
                                          + b'A\0NONZERO-TAIL!!').ljust(128, b'\0')))
    for protocol, script in ((5, [67, 6]), (5, [67, 21]), (5, [0xffff, 0xffff]),
                             (5, [51, 6]), (11, [71]), (11, [0xffff])):
        rows.append(dict(kind='end5', protocol=protocol, script=script))
    for size in (0, 1, 65536, 0x7fffffff, 0x80000000, 0xffffffff):
        for radix in (2, 8, 10, 16, 36):
            rows.append(dict(kind='format', size=size, radix=radix))
    return rows


class Linked(DosImage):
    def __init__(self):
        super().__init__(OUT / 'METADATA.EXE', OUT / 'transfer_metadata.map')
        self.unwind = None
        self.uc.hook_add(UC_HOOK_CODE, self.catch_unwind)

    def catch_unwind(self, u, at, size, context):
        if at == self.symbols['metadata_unwind']:
            sp = u.reg_read(UC_X86_REG_SP)
            self.unwind = int.from_bytes(u.mem_read(self.data_base+sp+4, 2), 'little')
            u.emu_stop()

    def configure(self, c):
        script = c.get('script', [6])
        self.put('metadata_protocol', c.get('protocol', 5))
        value = c.get('size', 0x12345678)
        self.put('metadata_size_low', value & 65535)
        self.put('metadata_size_high', value >> 16)
        self.put('metadata_date', 0x5678)
        self.put('metadata_time', 0xabcd)
        self.put('fixture_cancel', c.get('cancel', 0))
        self.put('fixture_carrier', c.get('carrier', 1))
        self.put('metadata_buffer_pointer', self.offset('metadata_input'))
        self.put('fixture_script_count', len(script))
        self.uc.mem_write(self.symbols['fixture_script'], struct.pack('<'+'H'*len(script), *script))
        self.uc.mem_write(self.symbols['fixture_filename'], c.get('name', b'TEST.BIN')+b'\0')
        self.uc.mem_write(self.symbols['metadata_filename'], b'\xa5'*66)
        self.uc.mem_write(self.symbols['metadata_input'], c.get('block', bytes(128)))

    def execute(self, c):
        self.configure(c)
        args = [self.offset('fixture_filename')] if c['kind'].startswith('send') else []
        if c['kind'] == 'format':
            value = c['size']
            args = [value & 65535, value >> 16, self.offset('metadata_input'), c['radix']]
        answer = self.call(ENTRIES[c['kind']], args, limit=1000000)
        # DosImage reports an interrupted call without claiming a return.
        return self.result(c, answer)

    def result(self, c, answer):
        size = self.get('metadata_size_low') | self.get('metadata_size_high') << 16
        return dict(answer=answer if c['kind'].startswith('send') and self.unwind is None else None,
                    wire=bytes(self.uc.mem_read(self.symbols['fixture_wire'], self.get('fixture_wire_count'))).hex(),
                    size=size, date=self.get('metadata_date'), time=self.get('metadata_time'),
                    name=bytes(self.uc.mem_read(self.symbols['metadata_filename'], 66)).hex(),
                    batch_end=self.get('metadata_batch_end'), unwind=self.unwind,
                    formatted=bytes(self.uc.mem_read(self.symbols['metadata_input'], 64)).split(b'\0')[0].hex()
                    if c['kind'] == 'format' else None,
                    stat_calls=self.get('fixture_stat_calls'), display_calls=self.get('fixture_display_calls'),
                    timed_reads=self.get('fixture_timeout_calls'), flushes=self.get('fixture_flush_calls'),
                    delays=self.get('fixture_delay_calls'))


def verify(c, got):
    kind = c['kind']
    wire = bytes.fromhex(got['wire'])
    if c.get('cancel') or c.get('carrier') == 0:
        assert got['unwind'] == (7 if c.get('cancel') else 15) and not wire
        return
    if kind == 'send5':
        name = c.get('name', b'TEST.BIN')
        name = name.rsplit(b'\\', 1)[-1] if b'\\' in name else name.rsplit(b':', 1)[-1]
        body = metadata(name, str(signed(c.get('size', 0x12345678))).encode())
        frame = b'\x01\0\xff' + body + binascii.crc_hqx(body, 0).to_bytes(2, 'big')
        script = c.get('script', [6])
        attempts = 1 if c.get('protocol', 5) == 11 else min(next((i+1 for i, x in enumerate(script) if x == 6), 3), 3)
        assert wire == frame * attempts
        assert got['answer'] == int(c.get('protocol', 5) == 11 or 6 in script[:3])
        assert got['timed_reads'] == (0 if c.get('protocol', 5) == 11 else attempts)
    elif kind == 'send3':
        name = c.get('name', b'TEST.BIN')
        name = name.rsplit(b'\\', 1)[-1] if b'\\' in name else name.rsplit(b':', 1)[-1]
        body = struct.pack('<IHH', c.get('size', 0x12345678), 0x5678, 0xabcd)
        body += name.ljust(16, b' ') + b'\0PROCOMM PLUS    ' + bytes(87)
        frame = b'\x16\0\xff'+body+bytes([sum(body)&255])
        script = c.get('script', [6])
        attempts = min(next((i+1 for i, x in enumerate(script) if x == 6), 3), 3)
        assert wire == frame*attempts and got['timed_reads'] == attempts
        assert got['answer'] == int(6 in script[:3])
    elif kind == 'end5':
        assert wire == b'\x01\0\xff'+bytes(130)
        assert got['timed_reads'] == (1 if c.get('protocol') == 11 else 2)
        assert got['flushes'] == 1, 'Original empty-header retry defect unexpectedly disappeared'
    elif kind == 'format':
        value, radix = c['size'], c['radix']
        expected = str(signed(value)).encode() if radix == 10 else base_digits(value, radix)
        assert bytes.fromhex(got['formatted']) == expected
    elif kind == 'parse3':
        assert got['size'] == int.from_bytes(c['block'][:4], 'little')
        assert (got['date'], got['time']) == (0x5678, 0xabcd)
        expected_name = c['block'][8:24].split(b'\0', 1)[0].ljust(16, b'\0')
        assert bytes.fromhex(got['name'])[:16] == expected_name
        assert got['display_calls'] == 1
    elif c['block'][0] == 0:
        assert got['batch_end'] == 1 and got['size'] == 0x12345678
    elif c['block'] == b'X'*128:
        assert bytes.fromhex(got['name']) == b'X'*65+b'\0'
        assert got['size'] == 0x12345678
    else:
        fields = c['block'].split(b'\0', 2)[1]
        if not fields:
            expected = 0x12345678
        else:
            import re
            token = fields.split(b' ', 1)[0].lstrip(b'\t')
            match = re.match(rb'([+-]?)([0-9]+)', token)
            expected = (int(match[0]) if match else 0) & 0xffffffff
        assert got['size'] == expected, (fields, got)


def original_runner(path):
    from check_directory_dial_original import Original, DATA, EXPECTED
    image = path.read_bytes()
    assert hashlib.sha256(image).hexdigest() == EXPECTED
    overlays = [o for o in json.loads((ROOT/'analysis/pcplus-overlays/manifest.json').read_text())['overlays'] if o['id'] == 21]

    class Native(Original):
        def __init__(self, c):
            super().__init__(image, overlays)
            self.c = c; self.script = list(c.get('script', [6])); self.wire = bytearray(); self.unwind = None
            self.counts = dict(stat_calls=0, display_calls=0, timed_reads=0, flushes=0, delays=0)
            self.uc.mem_write(DATA+0x39fc, image[0x25950+0x39fc:0x25950+0x3bfc])
            self.uc.mem_write(DATA+0x7920, b'PROCOMM PLUS    \0')
            value = c.get('size', 0x12345678)
            for at, value in ((0x3996, c.get('protocol', 5)), (0x39c0, 0x5000), (0x9006, value&65535), (0x9008, value>>16), (0xcd76, 0x5678), (0xcd3a, 0xabcd)):
                self.put(at, value)
            self.uc.mem_write(DATA+0x5000, c.get('block', bytes(128)))
            self.uc.mem_write(DATA+0x6000, c.get('name', b'TEST.BIN')+b'\0')
            self.uc.mem_write(DATA+0xcb68, b'\xa5'*66)

        def hook(self, u, at, size, context):
            if at == self.stop:
                u.emu_stop(); return
            address = at-0x10000
            if address not in (0xab0b, 0xaad9, 0x3f4b, 0x4861, 0x3b56, 0xee10, 0x9065, 0x6b72, 0xabca):
                return
            sp = u.reg_read(UC_X86_REG_SP)
            ret, arg, error = struct.unpack('<3H', u.mem_read(DATA+sp, 6))
            cleanup = 0; answer = u.reg_read(UC_X86_REG_AX)
            if address == 0x9065:
                self.unwind = error; u.emu_stop(); return
            if address == 0xab0b:
                self.wire.append(arg&255); answer=arg; cleanup=2
            elif address == 0xaad9:
                self.counts['timed_reads'] += 1; answer=self.script.pop(0) if self.script else 65535; cleanup=2
            elif address == 0x3f4b: answer=self.c.get('cancel', 0)
            elif address == 0x4861: answer=self.c.get('carrier', 1)
            elif address == 0x3b56: self.counts['stat_calls'] += 1; answer=0
            elif address == 0xee10: self.counts['display_calls'] += 1
            elif address == 0x6b72: self.counts['delays'] += 1; cleanup=2
            elif address == 0xabca: self.counts['flushes'] += 1; self.put(0x8e20, 0)
            u.reg_write(UC_X86_REG_AX, answer); u.reg_write(UC_X86_REG_SP, sp+2+cleanup); u.reg_write(UC_X86_REG_IP, ret)

        def execute(self):
            c = self.c
            args = [0x6000] if c['kind'].startswith('send') else []
            if c['kind'] == 'format': args=[c['size']&65535, c['size']>>16, 0x5000, c['radix']]
            self.stop=0x1f800
            self.uc.reg_write(UC_X86_REG_SP, 0xd000)
            self.uc.mem_write(DATA+0xd000, struct.pack('<'+'H'*(len(args)+1), 0xf800, *args))
            self.uc.emu_start(0x10000+ADDRESSES[ENTRIES[c['kind']]], 0x20000, count=1000000)
            assert self.unwind is not None or self.uc.reg_read(UC_X86_REG_IP) == 0xf800
            return dict(answer=self.uc.reg_read(UC_X86_REG_AX) if c['kind'].startswith('send') and self.unwind is None else None,
                        wire=bytes(self.wire).hex(), size=self.get(0x9006)|(self.get(0x9008)<<16), date=self.get(0xcd76), time=self.get(0xcd3a),
                        name=bytes(self.uc.mem_read(DATA+0xcb68, 66)).hex(), batch_end=self.get(0xcb56), unwind=self.unwind,
                        formatted=self.string(0x5000, 64).hex() if c['kind']=='format' else None, **self.counts)
    return Native


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original', type=Path)
    args = p.parse_args()
    native = original_runner(args.original) if args.original else None
    results = []
    for i, c in enumerate(cases()):
        model = Linked()
        try:
            got = model.execute(c)
        except AssertionError:
            if model.unwind is None:
                raise
            got = model.result(c, None)
        verify(c, got)
        if native:
            actual = native(c).execute()
            assert actual == got, (i, c, actual, got)
        results.append(dict(index=i, kind=c['kind'], result=got))
    report = dict(passed=True, binary_sha256=hashlib.sha256((OUT/'METADATA.EXE').read_bytes()).hexdigest(),
                  cases=len(results), original_comparisons=len(results) if native else 0, results=results,
                  scope='Actual native metadata, basename, decimal conversion, CRC and flush instructions; declared memory UART/stat/timing/UI/nonlocal-unwind boundaries. Original defects retained. No complete batch owner, live UART, real filesystem or YMODEM interoperability claim.')
    (OUT/('checks-original.json' if native else 'checks.json')).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='results'}, indent=2))


if __name__ == '__main__':
    main()
