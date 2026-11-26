#!/usr/bin/env python3
"""Source-only CPU checks for the native protocol getter; optional original checks."""
import argparse, hashlib, json, random, struct, subprocess
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_MEM_READ
from unicorn.x86_const import (UC_X86_REG_AX, UC_X86_REG_BX, UC_X86_REG_CX,
    UC_X86_REG_DX, UC_X86_REG_BP, UC_X86_REG_SI, UC_X86_REG_DI,
    UC_X86_REG_SP, UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_ES,
    UC_X86_REG_SS, UC_X86_REG_EFLAGS)

ROOT = Path(__file__).resolve().parents[1]
CODES = [5,11,7,17,8,4,13,3,16,12,9,14,6,0,1,2,10,15]
ORIGINAL = '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--original', type=Path)
    a = p.parse_args(); out = a.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    out.mkdir(parents=True)
    binary = out/'proto.bin'
    source = ROOT/'src/aspect/directory_proto.asm'
    subprocess.run(['nasm','-fbin','-I'+str(ROOT/'reconstruction/uart')+'/',
        '-DASPECT_DIRECTORY_PROTO_FLAT',str(source),'-o',str(binary)],check=True)
    code = binary.read_bytes()
    assert code == bytes.fromhex('b006f62e98e68bd88b87d84dc3')
    original = None
    if a.original:
        assert sha(a.original) == ORIGINAL
        image = a.original.read_bytes()
        manifest = json.loads((ROOT/'analysis/pcplus-overlays/manifest.json').read_text())
        overlay = next(o for o in manifest['overlays'] if o['id'] == 16)
        at = overlay['source_file_offset']-overlay['relative_load_segment']*16+0xd9c8
        assert image[at:at+13] == code
        thunk = struct.unpack_from('<H',image,0x25950+0x4cb6+14)[0]
        assert image[0x1200+thunk:0x1200+thunk+12] == bytes.fromhex('9aec02ec0a1000eac8d90000')
        assert [struct.unpack_from('<H',image,0x25950+0x4dd8+6*i)[0] for i in range(1,19)] == CODES
        original = dict(sha256=ORIGINAL,code_file_offset=at,resident_thunk=hex(thunk),
                        table_DS='0x4dd8',consumed_table_words=18,
                        reserved_index0_word=struct.unpack_from('<H',image,0x25950+0x4dd8)[0])
    rng = random.Random(0xd9c8); count = 0
    u = Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000)
    u.mem_write(0x1d9c8,code); reads = []
    u.hook_add(UC_HOOK_MEM_READ,lambda uc,access,address,size,value,user: reads.append((address,size)))
    for codes in [CODES]+[[rng.randrange(65536) for _ in CODES] for _ in range(32)]:
        data = bytearray(rng.randbytes(65536))
        for i,value in enumerate(codes,1):struct.pack_into('<H',data,0x4dd8+6*i,value)
        for index in range(256):
            data[0xe698] = index
            struct.pack_into('<H',data,0x8000,0x100)
            u.mem_write(0x40000,bytes(data))
            preserved = {r:rng.randrange(65536) for r in (UC_X86_REG_CX,UC_X86_REG_DX,
                         UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_ES)}
            preserved.update({UC_X86_REG_CS:0x1000,UC_X86_REG_DS:0x4000,UC_X86_REG_SS:0x4000})
            for reg,value in preserved.items():u.reg_write(reg,value)
            u.reg_write(UC_X86_REG_SP,0x8000);u.reg_write(UC_X86_REG_AX,rng.randrange(65536))
            u.reg_write(UC_X86_REG_EFLAGS,0x602);reads.clear()
            u.emu_start(0x1d9c8,0x10100,count=8)
            signed = index if index < 128 else index-256; product = signed*6
            offset = (0x4dd8+product)&65535
            assert u.reg_read(UC_X86_REG_AX) == struct.unpack_from('<H',data,offset)[0]
            assert u.reg_read(UC_X86_REG_BX) == product&65535
            assert reads == [(0x4e698,1),(0x40000+offset,2),(0x48000,2)],reads
            assert all(u.reg_read(reg)==value for reg,value in preserved.items())
            assert u.reg_read(UC_X86_REG_SP)==0x8002
            flags = u.reg_read(UC_X86_REG_EFLAGS)
            assert flags&0x600==0x600 and bool(flags&1)==bool(flags&0x800)==(not -128<=product<=127)
            assert bytes(u.mem_read(0x40000,65536)) == data
            count += 1
    result = dict(passed=True,cpu_cases=count,valid_index_cases=18*33,raw_indices=256,
        original_comparison=original,original_inputs=[str(a.original)] if a.original else [],
        source_sha256=sha(source),checker_sha256=sha(Path(__file__)),binary_sha256=sha(binary),
        encodings_sha256=sha(ROOT/'reconstruction/uart/encodings.inc'),
        codes=CODES,scope='Exact13-byte native routine, all256 raw signed indices over33 independent DS tables, exact read addresses/stride and registers/stack/CF/OF/IF/DF. Native indexing unchecked; runtime bounds are separate.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS',count,'native protocol getter CPU cases')


if __name__ == '__main__':main()
