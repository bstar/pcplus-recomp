#!/usr/bin/env python3
"""Optional original getter replay with synthetic directory record bytes only.

This executes eight original overlay16 getter bodies, not the full application
or its overlay loader. No private directory/configuration files are opened.
"""
import argparse
import hashlib
import json
from pathlib import Path
from check_directory_dial_original import Original, DATA, EXPECTED
from unicorn.x86_const import UC_X86_REG_AX, UC_X86_REG_SP

ROOT = Path(__file__).resolve().parents[1]
FIELDS = [('$D_LDATE', 61, 8), ('$D_KBDFILE', 95, 8), ('$D_METAKEY', 86, 8),
          ('$D_NAME', 0, 24), ('$D_NOTE', 105, 8), ('$D_PHONE', 25, 20),
          ('$D_PWORD', 75, 10), ('$D_SCRIPT', 52, 8)]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    args = parser.parse_args()
    image = args.original.read_bytes()
    assert sha(image) == EXPECTED
    manifest_path = ROOT / 'analysis/pcplus-overlays/manifest.json'
    overlays = [o for o in json.loads(manifest_path.read_text())['overlays'] if o['id'] == 16]
    assert len(overlays) == 1
    overlay = overlays[0]
    cases = []
    for variant in ('empty', 'maximum', 'highbyte'):
        record = bytearray(114)
        expected = []
        for slot, (name, offset, maximum) in enumerate(FIELDS):
            value = (b'' if variant == 'empty' else bytes([65 + slot]) * maximum
                     if variant == 'maximum' else bytes([128 + slot, 255, 94, 126]))
            record[offset:offset + len(value) + 1] = value + b'\0'
            expected.append(value)
        for slot, (name, offset, maximum) in enumerate(FIELDS):
            instance = Original(image, overlays)
            instance.uc.mem_write(DATA + 0xe650, bytes(record))
            instance.call(0xdaa2 + 4 * slot)
            pointer = instance.uc.reg_read(UC_X86_REG_AX)
            assert pointer == 0xe650 + offset
            assert instance.string(pointer, maximum + 1) == expected[slot]
            assert bytes(instance.uc.mem_read(DATA + 0xe650, 114)) == bytes(record)
            assert instance.uc.reg_read(UC_X86_REG_SP) == 0xd002
            entry = 0xdaa2 + 4 * slot
            file_offset = overlay['source_file_offset'] + entry - overlay['relative_load_segment'] * 16
            cases.append(dict(name=name, slot=slot, variant=variant, entry=entry,
                              file_offset=file_offset, code_sha256=sha(image[file_offset:file_offset + 4]),
                              returned_record_offset=offset, expected_hex=expected[slot].hex(), passed=True))
    report = dict(passed=True, checker_sha256=sha(Path(__file__).read_bytes()),
                  original_inputs=[str(args.original)], original_sha256=EXPECTED,
                  overlay_manifest_sha256=sha(manifest_path.read_bytes()), cases=cases,
                  scope='24 original overlay16 MOV AX,record-pointer/RET executions with owned empty, '
                  'maximum-length and CP437 synthetic fields. Original getter instructions execute; '
                  'CS/DS/SS, selected record and near return stack supplied by Unicorn. No original '
                  'application loader/selector dispatcher/UI, private files, serial IO or transmission observed.')
    output = ROOT / 'analysis/aspect-directory/original-getters-01.json'
    assert not output.exists(), 'Preserve prior native evidence; choose a fresh output name before rerun'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print('24 actual original directory getter cases passed')


if __name__ == '__main__':
    main()
