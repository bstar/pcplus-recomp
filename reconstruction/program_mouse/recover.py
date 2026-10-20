#!/usr/bin/env python3
"""Analyst-only regeneration; ordinary builds never read the original or REA."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SHA = '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
UNITS = [('probe', 0x76b4, 0x76e8), ('init', 0x76ea, 0x7722),
         ('bind', 0x7f92, 0x7fa0), ('callback', 0x8072, 0x8099),
         ('events', 0x809a, 0x815c), ('absolute', 0x9d66, 0x9d73)]
NAMES = {start: 'mouse_' + name for name, start, end in UNITS}
NAMES[0x8074] = 'mouse_callback'
STATE = {0x5dee: 'mouse_enabled', 0x7a50: 'mouse_scale_x',
         0x7a52: 'mouse_scale_y', 0x7a54: 'mouse_present',
         0x7a56: 'mouse_flags', 0x7a58: 'mouse_motion_x',
         0x7a5a: 'mouse_motion_y', 0x7a5c: 'mouse_base_x',
         0x7a5e: 'mouse_base_y', 0x7a60: 'mouse_button_pending',
         0x7a62: 'mouse_count', 0x7a64: 'mouse_code', 0x8072: 'mouse_depth'}


def evidence(path):
    data = json.loads(path.read_text())['structuredContent']
    assert data['subject']['digest']['sha256'] == SHA
    return data


def main():
    image = (ROOT / 'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes()
    assert hashlib.sha256(image).hexdigest() == SHA
    records = ROOT / 'analysis/program-mouse-01'
    callback = evidence(records / 'callback-bytes.json')
    loaded = bytes.fromhex(callback['normalized_result']['bytes_hex'])
    original = bytearray(image[0x9272:0x935c])
    # Original MZ relocates the callback's immediate DS segment by load1000h.
    original[13:15] = (int.from_bytes(original[13:15], 'little') + 0x1000).to_bytes(2, 'little')
    assert bytes(original) == loaded
    proof = dict(original_sha256=SHA, units=[], state={hex(k): v for k, v in STATE.items()},
                 callback_analysis='No Ghidra procedure at18074; callback/event boundaries reconstructed from registration, complete REA byte read and decoded far/near returns. No callback pseudocode claimed.')
    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)

        def assemble(text, at):
            (work / 'one.asm').write_text(f'BITS 16\nCPU 8086\nORG {at}\n%include "encodings.inc"\n' + text + '\n')
            result = subprocess.run(['nasm', '-fbin', '-I' + str(ROOT / 'reconstruction/uart') + '/',
                                     str(work / 'one.asm'), '-o', str(work / 'one.bin')], capture_output=True)
            return (work / 'one.bin').read_bytes() if result.returncode == 0 else None

        for name, start, end in UNITS:
            body = image[0x1200 + start:0x1200 + end]
            code_start = start + 2 if name == 'callback' else start
            (work / 'part').write_bytes(body[code_start - start:])
            rows = []
            for line in subprocess.check_output(['ndisasm', '-b16', '-o' + str(code_start), str(work / 'part')], text=True).splitlines():
                match = re.fullmatch(r'([0-9A-F]+)\s+([0-9A-F]+)\s+(.*)', line)
                assert match, line
                at, raw, text = int(match[1], 16), bytes.fromhex(match[2]), match[3]
                if raw[0] == 0xeb:
                    text = text.replace('jmp ', 'jmp short ', 1)
                elif raw[0] == 0xe9:
                    text = text.replace('jmp ', 'jmp near ', 1)
                elif 0x70 <= raw[0] <= 0x7f:
                    text = text.replace(' ', ' short ', 1)
                if assemble(text, at) != raw:
                    variants = []
                    if len(raw) == 2 and raw[1] >= 0xc0 and raw[0] in (2, 3, 10, 11, 18, 19, 26, 27, 34, 35, 42, 43, 50, 51, 58, 59, 138, 139):
                        op, operands = text.split(' ', 1)
                        variants.append(op + '_load ' + operands)
                    for width in ('word', 'byte'):
                        variants.append(re.sub(r',0x', ',strict ' + width + ' 0x', text))
                    text = next((v for v in variants if assemble(v, at) == raw), None)
                    assert text, (hex(at), line)
                rows.append((at, text))
            dependencies = {}
            states = {}
            for at, text in rows:
                call = re.fullmatch(r'(?:call|j\w+)\s+(?:(?:short|near)\s+)?(0x[0-9a-f]+)', text)
                if call and not start <= int(call[1], 16) < end:
                    target = int(call[1], 16)
                    dependencies[target] = NAMES[target]
                for token in re.findall(r'0x[0-9a-f]+', text):
                    if int(token, 16) in STATE:
                        states[int(token, 16)] = STATE[int(token, 16)]
            public = NAMES[code_start]
            header = ['; Exact native mouse instructions; see provenance.json.', 'BITS 16', 'CPU 8086', '%ifdef PROGRAM_MOUSE_OMF']
            if name == 'callback':
                header += ['SEGMENT _DATA public class=DATA use16', 'GROUP DGROUP _DATA']
            header += ['SEGMENT _TEXT public class=CODE use16', 'global ' + public]
            if name == 'callback':
                header += ['global mouse_depth', '%define mouse_group DGROUP']
                states.pop(0x8072)
            header += ['extern ' + n for n in [*dependencies.values(), *states.values()]]
            header += ['%define short', '%else', 'ORG ' + str(start)]
            header += [f'%define {n} {at}' for at, n in {**dependencies, **states}.items()]
            if name == 'callback':
                header += ['%define mouse_group 0xfb7']
            header += ['%endif', '%include "encodings.inc"']
            if name == 'callback':
                header += ['mouse_depth: dw 0xffff']
            header += [public + ':']
            for at, text in rows:
                branch = re.fullmatch(r'(j\w+|loop\w*|call)\s+(?:(short|near)\s+)?(0x[0-9a-f]+)', text)
                if branch:
                    target = int(branch[3], 16)
                    label = f'L_{target:04x}' if code_start <= target < end else NAMES[target]
                    text = branch[1] + ' ' + (branch[2] + ' ' if branch[2] else '') + label
                for address, symbol in states.items():
                    text = re.sub(r'(?<![\da-f])0x' + f'{address:x}' + r'(?![\da-f])', symbol, text)
                if name == 'callback':
                    text = text.replace('0x8072', 'mouse_depth').replace('0xfb7', 'mouse_group')
                if name == 'bind':
                    text = text.replace('0x8074', 'mouse_callback')
                header.append(f'L_{at:04x}: ' + text)
            if name == 'bind':
                header.insert(header.index('%define short'), 'extern mouse_callback')
                header.insert(header.index('%endif'), '%define mouse_callback 0x8074')
            path = HERE / (name + '.asm')
            path.write_text('\n'.join(header) + '\n')
            subprocess.run(['nasm', '-fbin', '-I' + str(ROOT / 'reconstruction/uart') + '/',
                            str(path), '-o', str(work / 'whole.bin')], check=True)
            assert (work / 'whole.bin').read_bytes() == body, name
            anchor = 0x8074 if name == 'callback' else start
            map_name = 'callback-map' if name == 'callback' else 'event-map' if name == 'events' else 'map-' + hex(0x10000 + anchor)
            mapping = evidence(records / (map_name + '.json'))
            assert mapping['normalized_result']['file_offset'] + start - anchor == 0x1200 + start
            record = (callback if name in ('callback', 'events') else evidence(records / 'absolute-bytes.json') if name == 'absolute'
                      else evidence(ROOT / 'analysis/pcplus-main/functions' / (hex(0x10000 + start) + '-asm.json')))
            proof['units'].append(dict(file=str(path.relative_to(ROOT)), start=start, end=end,
                file_offset=0x1200 + start, bytes=len(body), sha256=hashlib.sha256(body).hexdigest(),
                rea_evidence_id=record['evidence_id'], mapping_evidence_id=mapping['evidence_id']))
    proof['limitations'] = ['Module primitives only; no live terminal/PROGRAM publication.',
        'Native scale words are unchecked. Zero causes real divide fault; a maintained admission guard is required.',
        'Native callback installs its DS and supports a foreign SS through BP-based stack access. Later C/VM integrations retain their own ABI requirements.',
        'INT33 driver behavior and physical mouse input are separate from linked boundary replay.']
    (HERE / 'provenance.json').write_text(json.dumps(proof, indent=2) + '\n')
    print('Recovered', sum(u['bytes'] for u in proof['units']), 'native mouse bytes')


if __name__ == '__main__':
    main()
