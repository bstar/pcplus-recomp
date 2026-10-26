#!/usr/bin/env python3
"""Independent proposal vectors, pure linked execution and real DOS8086 replay."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
from unicorn import UC_HOOK_CODE, UC_HOOK_INTR, UC_HOOK_INSN
from unicorn.x86_const import (UC_X86_INS_IN, UC_X86_INS_OUT, UC_X86_REG_BP,
    UC_X86_REG_SI, UC_X86_REG_DI, UC_X86_REG_DS, UC_X86_REG_SS,
    UC_X86_REG_ES, UC_X86_REG_SP)
from dos_image import DosImage
from check_setup_model import image
from check_directory_live import record, serial_expected, plan_expected, text, word
from check_startup_import import terminal_expected
from check_modem_import import expected as modem_expected
from test_terminal import SAMPLER

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT/'build/directory-selection'
PROPOSAL = 1190
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def python_sources():
    """Bind the local import closure, including helpers only used indirectly."""
    pending = ['standalone/test_directory_selection.py']
    found = set()
    while pending:
        name = pending.pop()
        if name in found:
            continue
        found.add(name)
        for node in ast.walk(ast.parse((ROOT/name).read_text())):
            modules = ([a.name for a in node.names] if isinstance(node, ast.Import)
                       else [node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
            for module in modules:
                for folder in ('standalone', 'src/directory'):
                    path = folder+'/'+module.replace('.', '/')+'.py'
                    if (ROOT/path).is_file() and path not in found:
                        pending.append(path)
    return sorted(found)


def changes(active, candidate):
    # Independent field spans in the628-byte contract. These vectors keep modem
    # strings identical or clear them for DIRECT; no after-NUL string oracle here.
    flag = 0
    for bit, spans in [(1, [(0, 2), (32, 4)]), (2, [(2, 4)]),
                       (4, [(6, 6)]), (8, [(12, 4)]), (16, [(16, 2)]),
                       (32, [(18, 14)]), (64, [(36, 4)]),
                       (128, [(44, 366)]), (256, [(412, 214)]),
                       (512, [(410, 2)]), (1024, [(414, 2), (447, 64)]),
                       (2048, [(40, 2)]), (4096, [(42, 2)])]:
        if any(active[at:at+n] != candidate[at:at+n] for at, n in spans):
            flag |= bit
    return flag


def vectors():
    base = word(word(word(image(), 0, 2), 2, 5), 0x188, 5)
    active = terminal_expected(base)+modem_expected(base)+bytes(216)
    header = bytes((i*17+11) & 255 for i in range(250))
    records = []
    for entry in range(1, 201):
        raw = text(text(record(), 0, 25, f'NODE {entry:03}'.encode()),
                   25, 21, f'555{entry:03}'.encode())
        raw = text(raw, 0x4b, 11, b'SECRET')
        raw = bytearray(raw)
        raw[24] = 0xfe  # bounded name's opaque suffix remains exact
        raw[0x69:0x72] = bytes((entry+i) & 255 for i in range(9))
        records.append(bytes(raw))
    values = []

    def add(name, *, entry=1, first=1, count=None, prm=base, selected=None,
            raw_header=header, codes=0, mask=0, current=active,
            prm_path=b'C:\\PCPLUS\\PCPLUS.PRM', directory_path=b'C:\\PCPLUS\\PCPLUS.DIR',
            error=None, target=None):
        count = min(10, 201-first) if count is None and 1 <= first <= 200 else count or 0
        rows = records[first-1:first-1+min(count, 10)] if 1 <= first <= 200 else []
        rows += [bytes(114)]*(10-len(rows))
        if selected is not None and 0 <= entry-first < 10:
            rows[entry-first] = selected
        page = struct.pack('<2H', first, count)+raw_header+b''.join(rows)
        assert len(page) == 1394
        pp, dp = prm_path.ljust(64, b'\0'), directory_path.ljust(64, b'\0')
        assert len(pp) == len(dp) == 64
        if error:
            returned, result = error
            expected = b'\xcc'*PROPOSAL
        else:
            raw = rows[entry-first]
            serial = bytearray(serial_expected(prm, raw))
            for bit, spans in [(1, [(0, 2), (32, 4)]), (2, [(2, 4)]),
                               (4, [(6, 6)]), (8, [(12, 4)])]:
                if mask & bit:
                    for at, n in spans:
                        serial[at:at+n] = current[at:at+n]
            modem = modem_expected(prm) if not raw[0x4a] else bytes(366)+prm[0x1a4:0x1a6]
            if target is None:
                target = raw[25:46].split(b'\0')[0] if not raw[0x4a] else b''
            plan = plan_expected(entry, raw, codes, target)
            candidate = bytes(serial)+modem+plan
            candidate += struct.pack('<H', changes(current, candidate))
            context = struct.pack('<H', entry)+raw_header+raw+struct.pack('<H', codes)+pp+dp
            download = prm[0x31c:0x35c].split(b'\0')[0] or b'.'
            transfer = struct.pack('<H', int(any(prm[0x42c:0x42e])))+download.ljust(64, b'\0')
            expected = context+candidate+transfer
            assert len(expected) == PROPOSAL
            returned, result = 0, (0, 0, 0)
        params = struct.pack('<7H', entry, codes, mask, returned, *result)
        raw_vector = prm+page+current+pp+dp+params+expected
        assert len(raw_vector) == 4618
        values.append((name, raw_vector))

    for entry in range(1, 201):
        add(f'entry-{entry}', entry=entry, first=(entry-1)//10*10+1)
    for first in (197, 200):
        add(f'partial-page-{first}', first=first, entry=200)
    for mask in range(16):
        prm = word(word(base, 0x198, 1), 0x19a, 0)
        selected = bytearray(records[0])
        selected[0x68] = 1
        struct.pack_into('<H', selected, 0x2e, 8)
        selected[0x30:0x33] = bytes([1, 8, 1])
        add(f'CLI-mask-{mask}', mask=mask, prm=prm, selected=bytes(selected))
    for codes in (0, 1):
        for code in range(10):
            h = bytearray(250)
            prefix = f'{code},'.encode()
            h[code*25:code*25+len(prefix)] = prefix
            target = bytes([65+code])+b'55'
            add(f'code-{codes}-{code}', raw_header=bytes(h), codes=codes,
                selected=text(records[0], 25, 21, target),
                target=prefix+b'55' if codes else target)
    selected = text(text(text(records[0], 0x34, 9, b'GO'), 0x56, 9, b'CUSTOM'), 0x5f, 9, b'MACROS')
    add('binding-syntax-and-private-password-retained', selected=selected)
    add('paths-max63-exact', prm_path=b'P'*63, directory_path=b'D'*63)
    prm = text(word(base, 0x42c, 0xffff), 0x31c, 64, b'C:\\DOWNLOAD')
    add('transfer-prefix-and-nonzero-auto', prm=prm)
    direct = bytearray(records[0]); direct[0x4a] = 1; direct[25:46] = bytes(21)
    prm = bytearray(base); prm[0x18:0x47] = b'X'*47
    add('DIRECT-skips-unusable-modem-strings', prm=bytes(prm), selected=bytes(direct))
    for first, count, entry in [(0, 10, 1), (201, 1, 201), (1, 0, 1),
                                 (191, 11, 191), (200, 10, 200),
                                 (11, 10, 10), (11, 10, 21), (1, 10, 0), (191, 10, 65535)]:
        add(f'bad-page-{first}-{count}-{entry}', first=first, count=count, entry=entry, error=(2, (2, 0, 0)))
    for codes, mask in [(2, 0), (65535, 0), (0, 16), (0, 65535)]:
        add(f'bad-policy-{codes}-{mask}', codes=codes, mask=mask, error=(1, (1, 0, 0)))
    for which in ('prm_path', 'directory_path'):
        for path in (b'', b'X'*64):
            add(f'bad-{which}-{len(path)}', **{which: path}, error=(1, (0xdddd,)*3))
    for at, value in [(0, 4), (2, 9), (4, 5), (6, 0), (8, 6), (0x198, 2),
                       (0x19a, 2), (0x194, 5), (0x1ae, 256), (0x188, 2)]:
        add(f'bad-global-before-overrides-{at}', prm=word(base, at, value), mask=15,
            error=(3, (3, 4, 4)))
    for at, value, detail in [(0x68, 5, 4), (0x30, 5, 4), (0x49, 5, 4),
                              (0x4a, 2, 9), (0x33, 1, 10)]:
        selected = bytearray(records[0]); selected[at] = value
        add(f'bad-record-{at}', selected=bytes(selected), mask=15, error=(3, (3, 4, detail)))
    for at, size, detail in [(0, 25, 6), (25, 21, 6), (0x4b, 11, 6),
                              (0x34, 9, 6), (0x56, 9, 6), (0x5f, 9, 6)]:
        selected = bytearray(records[0]); selected[at:at+size] = b'X'*size
        add(f'unterminated-record-{at}', selected=bytes(selected), error=(3, (3, 4, detail)))
    for at in (0x34, 0x56, 0x5f):
        add(f'unsupported-binding-{at}', selected=text(records[0], at, 9, b'BAD.EXE'), error=(3, (3, 4, 7)))
    add('empty-modem-target', selected=text(records[0], 25, 21, b''), error=(3, (3, 4, 8)))
    for at, size, detail in [(0x18, 47, 5), (0xc4, 16, 5)]:
        prm = bytearray(base); prm[at:at+size] = b'X'*size
        add(f'unterminated-modem-{at}', prm=bytes(prm), error=(3, (3, 4, detail)))
    for value in (0, 2, 65535):
        current = bytearray(active); struct.pack_into('<H', current, 34, value)
        add(f'invalid-active-IRQ-{value}', current=bytes(current), error=(3, (3, 5, 0)))
    for path in (b'..\\BAD', b'CON', b'\\\\SERVER\\SHARE', b'C:\\TOOLONG99', b'X'*64):
        prm = bytearray(base); prm[0x31c:0x35c] = path.ljust(64, b'\0')
        add('invalid-transfer-'+path.decode(), prm=bytes(prm), error=(4, (4, 2, 0)))
    return values


class Model(DosImage):
    def __init__(self):
        super().__init__(BUILD/'SELECT.EXE', BUILD/'SELECTION.map')
        self.start = self.offset('_selection_input')
        self.result = self.offset('_selection_result')
        self.maximum_stack = 0
        self.uc.hook_add(UC_HOOK_CODE, self.stack)
        self.uc.hook_add(UC_HOOK_INTR, self.forbid)
        for ins in (UC_X86_INS_IN, UC_X86_INS_OUT):
            self.uc.hook_add(UC_HOOK_INSN, self.forbid, None, 1, 0, ins)

    def stack(self, uc, address, size, user):
        assert uc.reg_read(UC_X86_REG_SS) == self.ds
        used = 0xe000-uc.reg_read(UC_X86_REG_SP)
        self.maximum_stack = max(used, self.maximum_stack)
        assert 0 <= used <= 8192, 'exceeded application8KiB stack budget'

    def forbid(self, *args):
        raise AssertionError('pure selection attempted DOS/BIOS/UART IO')

    def prepare(self, vector):
        self.uc.mem_write(self.data_base+self.start, vector)
        self.uc.mem_write(0x80000, b'\xa5'*16+vector[1264:2658]+b'\xa5'*16)
        self.uc.mem_write(0x90000, b'\xcc'*(PROPOSAL+32))
        self.uc.mem_write(self.data_base+self.result, b'\xdd'*6)
        self.uc.reg_write(UC_X86_REG_ES, self.ds)
        entry, codes, mask = struct.unpack_from('<3H', vector, 3414)
        return [self.start, 16, 0x8000, entry, codes, mask, self.start+2658,
                self.start+3286, self.start+3350, 16, 0x9000, self.result]

    def invoke(self, args):
        status = self.call('_directory_selection_stage', args, limit=2000000)
        for reg, value in [(UC_X86_REG_BP, 0xbabe), (UC_X86_REG_SI, 0x1234),
                           (UC_X86_REG_DI, 0x5678), (UC_X86_REG_DS, self.ds),
                           (UC_X86_REG_SS, self.ds)]:
            assert self.uc.reg_read(reg) == value, (reg, self.uc.reg_read(reg), value)
        assert bytes(self.uc.mem_read(self.data_base+0xe000-len(args)*2, len(args)*2)) == struct.pack('<12H', *args)
        return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    manifest = json.loads((BUILD/'manifest.json').read_text())
    assert not manifest['original_inputs'] and sha(BUILD/'SELECT.EXE') == manifest['binary_sha256']
    for name, digest in manifest['sources'].items():
        assert sha(ROOT/name) == digest, name
    cases = vectors()
    model = Model()
    for name, vector in cases:
        try:
            arguments = model.prepare(vector)
            assert model.invoke(arguments) == struct.unpack_from('<H', vector, 3420)[0]
            assert bytes(model.uc.mem_read(model.data_base+model.result, 6)) == vector[3422:3428]
            assert bytes(model.uc.mem_read(0x90010, PROPOSAL)) == vector[3428:]
            assert bytes(model.uc.mem_read(model.data_base+model.start, len(vector))) == vector
            assert bytes(model.uc.mem_read(0x80000, 1426)) == b'\xa5'*16+vector[1264:2658]+b'\xa5'*16
            assert bytes(model.uc.mem_read(0x90000, 16)) == bytes(model.uc.mem_read(0x90010+PROPOSAL, 16)) == b'\xcc'*16
        except Exception as exc:
            raise AssertionError(name) from exc
    # Malformed extents, exact/partial aliases and alternative physical far
    # spellings must reject before touching any caller storage, including result.
    invalid = []
    for index, value in [(0, 0), (0, 0xfc00), (1, 0xffff), (2, 0xffff),
                         (6, 0), (6, 0xff00), (7, 0), (7, 0xffff),
                         (8, 0), (8, 0xffff), (9, 0xffff), (10, 0xffff),
                         (11, 0), (11, 0xffff)]:
        invalid.append((str((index, value)), {index: value}))
    standard = model.prepare(cases[0][1])
    for region in (0, 6, 7, 8, 11):
        for delta in (0, 1):
            invalid.append((f'far-output-alias-near-{region}-{delta}',
                            {9: standard[region]+delta, 10: model.ds}))
            invalid.append((f'far-page-alias-near-{region}-{delta}',
                            {1: standard[region]+delta, 2: model.ds}))
    invalid += [('physical-far-alias', {9: 0, 10: 0x8001}),
                ('partial-far-alias', {9: 17, 10: 0x8000}),
                ('near-image-active-alias', {6: standard[0]}),
                ('near-result-image-alias', {11: standard[0]}),
                ('near-path-alias', {8: standard[7]})]
    for name, changes_ in invalid:
        arguments = model.prepare(cases[0][1])
        for index, value in changes_.items():
            arguments[index] = value
        memory = bytes(model.uc.mem_read(0, 0x100000))
        assert model.invoke(arguments) == 1, name
        # Stack writes/temporary frames are permitted; all caller regions stay exact.
        for start, size in [(model.data_base+model.start, 4618),
                            (model.data_base+model.result, 6), (0x80000, 1426),
                            (0x90000, PROPOSAL+32)]:
            assert bytes(model.uc.mem_read(start, size)) == memory[start:start+size], name
    print(f'Linked {len(cases)} golden vectors, {len(invalid)} invalid extents/aliases; stack {model.maximum_stack}/8192', flush=True)
    out.mkdir(parents=True)
    (out/'CASES.BIN').write_bytes(b''.join(v for _, v in cases))
    shutil.copyfile(BUILD/'SELECT.EXE', out/'SELECT.EXE')
    (out/'sampler.asm').write_text(SAMPLER)
    subprocess.run(['nasm', '-fbin', str(out/'sampler.asm'), '-o', str(out/'SNAP.COM')], check=True)
    config = f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 12000
[mixer]
nosound=true
[serial]
serial1=disabled
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{out}"
mount d "{out}"
c:
SNAP B
SELECT >RESULT.TXT
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto capture
:failed
echo FAIL>FAIL.TXT
:capture
SNAP A
exit
'''
    (out/'dosbox.conf').write_text(config)
    with (out/'dosbox.log').open('w') as log:
        run = subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(out/'dosbox.conf')],
            env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'),
            stdout=log, stderr=log, timeout=180)
    assert run.returncode == 0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(), (out/'RESULT.TXT').read_text()
    count, checks = struct.unpack('<2H', (out/'RESULT.BIN').read_bytes())
    assert count == len(cases) and checks == count*21
    assert (out/'CASES.BIN').read_bytes() == b''.join(v for _, v in cases)
    before, after = (out/'BEFORE.BIN').read_bytes(), (out/'AFTER.BIN').read_bytes()
    assert len(before) == 42 and before == after
    inputs = {n: sha(ROOT/n) for n in python_sources()}
    report = dict(passed=True, binary_sha256=manifest['binary_sha256'],
        golden_vectors=count, native_assertions=checks, invalid_extents_aliases=len(invalid),
        maximum_component_stack=model.maximum_stack, stack_budget=8192,
        hardware_restored=True, sources=manifest['sources'], test_sources=inputs,
        cases=[n for n, _ in cases], original_inputs=[],
        artifacts={p.name: sha(p) for p in out.iterdir() if p.is_file()},
        limitations=manifest['limitations'])
    (out/'result.json').write_text(json.dumps(report, indent=2)+'\n')
    print(f'DOS8086 PASS {count} vectors / {checks} assertions', flush=True)


if __name__ == '__main__':
    main()
