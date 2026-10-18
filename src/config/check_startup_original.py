#!/usr/bin/env python3
"""Optional original startup-state slice replay; verified EXE, synthetic settings.

Does not execute the original UI/filesystem or claim a whole-application startup.
Never reads a PRM, directory or installed configuration.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE
from unicorn.x86_const import (UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_SS,
                              UC_X86_REG_ES, UC_X86_REG_SP, UC_X86_REG_IP)

SHA = '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
PROFILE_FLAGS = {0xd122: 1, 0x8fe8: 1, 0x8ff6: 0, 0x8ff8: 0,
                 0x9004: 0, 0xcd36: 0, 0x9038: 0, 0x900c: 0,
                 0x9018: 0, 0x9020: 0, 0x9026: 0, 0x9032: 0,
                 0x903e: 0, 0x9048: 0, 0x904c: 0, 0x9056: 0, 0x9058: 1}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('--output', type=Path, default=Path('build/config-analysis/startup-replay.json'))
    args = parser.parse_args()
    image = args.original.read_bytes()
    if hashlib.sha256(image).hexdigest() != SHA:
        raise ValueError('Original EXE does not match the proved revision')
    uc = Uc(UC_ARCH_X86, UC_MODE_16)
    uc.mem_map(0, 0x100000)
    uc.mem_write(0x10000, image[0x1200:0x1200 + 53456])
    uc.mem_write(0x30000, image[153936:153936 + 60080])
    for reg, value in ((UC_X86_REG_CS, 0x1000), (UC_X86_REG_DS, 0x3000),
                       (UC_X86_REG_SS, 0x3000), (UC_X86_REG_ES, 0x3000)):
        uc.reg_write(reg, value)
    def put(address, value):
        uc.mem_write(0x30000 + address, struct.pack('<H', value))
    def get(address):
        return struct.unpack('<H', uc.mem_read(0x30000 + address, 2))[0]
    def run(start, end):
        uc.emu_start(0x10000 + start, 0x10000 + end, count=10000)
        assert uc.reg_read(UC_X86_REG_IP) == end
    reports = []
    for profile in (4, 6):
        for address in PROFILE_FLAGS:
            put(address, 0xa5a5)
        put(0x1d18, profile)
        run(0x20c0, 0x2284)  # Stop before keymap loader0cd2: no IO boundary is skipped.
        want = dict(PROFILE_FLAGS)
        want[0x8ff6] = int(profile == 6)
        actual = {address: get(address) for address in want}
        assert actual == want, (profile, actual, want)
        reports.append({'terminal_id': profile, 'derived_flags': {f'{a:04x}': v for a, v in actual.items()}})
    combinations = 0
    for soft in (0, 1):
        for hard in (0, 1):
            for scroll in (0, 1):
                put(0x1d1c, soft)
                put(0x1d1e, hard)
                put(0x1d22, scroll)
                run(0x4102, 0x4114)
                assert (get(0x3354), get(0x3356), get(0x9016)) == (soft, hard, scroll)
                combinations += 1
    # Actual reset tail makes current normal and restores saved scroll, but does
    # not clear397c (bold). Fresh-process clean state must not be inferred from it.
    for scroll in (0, 1):
        put(0x9016, scroll)
        put(0x1d20, scroll)  # Exercise both0/1; saved-wrap CD24 is separate.
        put(0x1d22, 1 - scroll)
        put(0x1d32, 0x1e)
        put(0x1f70, 0xff)
        put(0x397c, 0x1234)
        put(0x397e, 0x1234)
        uc.mem_write(0x3321c, b'\x01')
        run(0x2287, 0x2305)
        assert (get(0x1d22), get(0xd004), get(0x1f70), get(0xcdd4)) == (scroll, scroll, 0x1e, 0x1e)
        assert get(0x1d20) == scroll and get(0xcd24) == 1
        assert get(0x397e) == 0 and get(0x397c) == 0x1234
        assert bytes(uc.mem_read(0x3321c, 1)) == b'\0'
    stop = 0x1c000
    def halt(uc, address, size, unused):
        if address == stop:
            uc.emu_stop()
    uc.hook_add(UC_HOOK_CODE, halt)
    for profile, want in ((4, 0x1e), (6, 7)):
        put(0x8ff6, int(profile == 6))
        put(0x1d32, 0x1e)
        put(0x1f70, 0x80)
        uc.reg_write(UC_X86_REG_SP, 0xf000)
        uc.mem_write(0x3f000, struct.pack('<H', 0xc000))
        uc.emu_start(0x11c8c, 0x20000, count=1000)
        assert uc.reg_read(UC_X86_REG_IP) == 0xc000
        assert get(0x1f70) == want and get(0x397c) == 0 and get(0x397e) == 0
    result = {'passed': True, 'source_sha256': SHA, 'profiles': reports,
              'flow_scroll_copy_combinations': combinations,
              'reset_scroll_attribute_cases': 2, 'sgr_normal_profile_cases': 2,
              'scope': 'Actual original20c0..2283 profile derivation,4102..4113 flow/scroll copy,2287..2304 reset tail and1c8c SGR normal with synthetic state. No original UI/filesystem/startup execution.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
