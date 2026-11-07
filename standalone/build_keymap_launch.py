#!/usr/bin/env python3
"""Source-only rebuild of the original keymap helper caller and DOS ABI host."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    out.mkdir(parents=True)
    core = ROOT / 'reconstruction/keymap_launcher/launch.asm'
    proof_path = core.with_name('provenance.json')
    proof = json.loads(proof_path.read_text())
    include = str(ROOT / 'reconstruction/uart') + '/'
    subprocess.run(['nasm', '-fbin', '-I', include, str(core), '-o', str(out / 'launch.bin')], check=True)
    assert sha(out / 'launch.bin') == proof['sha256'] and (out / 'launch.bin').stat().st_size == proof['bytes']
    host = ROOT / 'standalone/keymap_launch_host.asm'
    objects = []
    for source in (host, core):
        obj = out / (source.stem + '.obj')
        subprocess.run(['nasm', '-fobj', '-DKEYMAP_LAUNCH_OMF', '-I', include, str(source), '-o', str(obj)], check=True)
        objects.append(str(obj))
    subprocess.run(['wlink', 'system', 'dos', 'option', 'quiet', 'option', 'map=' + str(out / 'keymap.map'),
                    'name', str(out / 'KMLAUNCH.EXE'), 'file', ','.join(objects)], check=True)
    symbols = {name: (int(segment, 16), int(offset, 16)) for segment, offset, name in
               re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})\s+(\w+)\s*$',
                          (out / 'keymap.map').read_text(), re.M | re.I)}
    image = (out / 'KMLAUNCH.EXE').read_bytes()
    header = struct.unpack_from('<14H', image)
    segment, entry = symbols['keymap_launch']
    start = header[4] * 16 + segment * 16 + entry
    body = bytearray(image[start:start + proof['bytes']])
    flat = (out / 'launch.bin').read_bytes()
    group, data_offset = symbols['keymap_profile']
    assert data_offset >= 128  # Host deliberately places PADSEG before _DATA.
    refs = ((8, 'keymap_filename'), (13, 'keymap_profile'), (16, 'keymap_format_text'),
            (20, 'keymap_tail'), (43, 'keymap_tail'), (47, 'keymap_program_name'))
    for at, name in refs:
        assert symbols[name][0] == group and struct.unpack_from('<H', body, at)[0] == symbols[name][1]
        body[at:at + 2] = flat[at:at + 2]
    calls = ((23, 'keymap_format'), (29, 'keymap_save_screen'), (50, 'keymap_locate'),
             (57, 'keymap_program'), (67, 'keymap_restore_screen'), (70, 'keymap_reload'))
    for at, name in calls:
        assert body[at] == 0xe8 and symbols[name][0] == segment
        assert (entry + at + 3 + struct.unpack_from('<h', body, at + 1)[0]) & 65535 == symbols[name][1]
        body[at + 1:at + 3] = flat[at + 1:at + 3]
    assert body == flat, 'Linked caller differs outside its declared data/call relocations'
    names = [core, proof_path, host, Path(__file__).resolve(), ROOT / 'reconstruction/uart/encodings.inc']
    result = dict(passed=True, original_inputs=[], flat_bytes=proof['bytes'], flat_sha256=sha(out / 'launch.bin'),
                  binary_sha256=sha(out / 'KMLAUNCH.EXE'), linked_data_references=6, linked_near_calls=6,
                  nonzero_DGROUP_data_offset=data_offset, linked_opcodes_verified=True,
                  sources={str(n.relative_to(ROOT)): sha(n) for n in names},
                  scope='Recovered78-byte caller plus authored six-service models; not PCKEYMAP editor or terminal integration.')
    (out / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Built78 exact keymap caller bytes and source-only DOS ABI diagnostic')


if __name__ == '__main__':
    main()
