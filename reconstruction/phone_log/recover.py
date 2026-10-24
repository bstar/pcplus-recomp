#!/usr/bin/env python3
"""Explicit analyst-only recovery; ordinary builds never read these inputs."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
START, END = 0xe2a9, 0xe3ab
STATE = {0x1d6a: 'phone_log_enabled', 0x333a: 'phone_log_pending',
         0x3320: 'phone_log_filename', 0x7094: 'phone_log_append_mode',
         0x4a08: 'phone_log_error_format', 0x4a1a: 'phone_log_heading_name',
         0x4a20: 'phone_log_heading_format', 0xe650: 'phone_log_name',
         0xe669: 'phone_log_number', 0x7097: 'phone_log_connect_format',
         0x2c7c: 'phone_log_elapsed', 0x70ad: 'phone_log_disconnect_format'}
SERVICES = {0x37a5: 'phone_log_stop_clock', 0x3f61: 'phone_log_start_clock',
            0x353d: 'phone_log_resolve', 0x3673: 'phone_log_exists',
            0x48a1: 'phone_log_prepare', 0x841a: 'phone_log_open',
            0x82b6: 'phone_log_sprintf', 0x427f: 'phone_log_notice',
            0x9786: 'phone_log_fprintf', 0x498b: 'phone_log_time',
            0x36d4: 'phone_log_date', 0x8318: 'phone_log_close'}


def main():
    image = (ROOT / 'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes()
    assert hashlib.sha256(image).hexdigest() == EXPECTED
    layout = json.loads((ROOT / 'analysis/pcplus-overlays/manifest.json').read_text())
    overlay = next(row for row in layout['overlays'] if row['id'] == 4)
    offset = overlay['source_file_offset'] + START - overlay['relative_load_segment'] * 16
    blob = image[offset:offset + END - START]
    with tempfile.TemporaryDirectory() as temporary:
        work = Path(temporary)
        def assemble(text, origin):
            (work / 'one.asm').write_text(f'bits 16\ncpu 8086\norg {origin}\n%include "encodings.inc"\n' + text + '\n')
            result = subprocess.run(['nasm', '-fbin', '-I' + str(ROOT / 'reconstruction/uart') + '/',
                                     str(work / 'one.asm'), '-o', str(work / 'one.bin')], capture_output=True)
            return (work / 'one.bin').read_bytes() if result.returncode == 0 else None
        (work / 'raw').write_bytes(blob)
        listing = subprocess.check_output(['ndisasm', '-b16', '-o' + str(START), str(work / 'raw')], text=True)
        rows = []
        for line in listing.splitlines():
            match = re.fullmatch(r'([0-9A-F]+)\s+([0-9A-F]+)\s+(.*)', line)
            assert match, line
            address, raw, text = int(match[1], 16), bytes.fromhex(match[2]), match[3]
            assert not text.startswith('db ')
            instruction = text
            if raw[0] == 0xeb:
                instruction = text.replace('jmp ', 'jmp short ', 1)
            elif raw[0] == 0xe9:
                instruction = text.replace('jmp ', 'jmp near ', 1)
            elif 0x70 <= raw[0] <= 0x7f:
                instruction = text.replace(' ', ' short ', 1)
            if assemble(instruction, address) != raw:
                candidates = []
                if len(raw) == 2 and raw[1] >= 0xc0 and raw[0] in (2, 3, 10, 11, 18, 19, 26, 27, 34, 35, 42, 43, 50, 51, 58, 59, 138, 139):
                    op, operands = text.split(' ', 1)
                    candidates.append(op + '_load ' + operands)
                candidates += [re.sub(r',(-?0x[0-9a-f]+)$', rf',strict {width} \1', instruction) for width in ('word', 'byte')]
                instruction = next((candidate for candidate in candidates if assemble(candidate, address) == raw), None)
                assert instruction is not None, (hex(address), text, raw.hex())
            rows.append((address, instruction))
        source = ['; Recovered PCPlus2.01 telephone-call log controller, overlay4:E2A9..E3AA.',
                  '; REA ev_8fbdeb2c8c59e1604bf53207279cda86462bc7e81ef53e858cf6bb35fb013b96.',
                  '; Near callee-cleaned stop argument (RET2); DS=SS; BP/DI preserved.',
                  'BITS 16', 'CPU 8086', '%include "encodings.inc"', '%ifdef PHONE_LOG_OMF',
                  'SEGMENT _TEXT public class=CODE use16', 'global phone_log_native']
        source += ['extern ' + name for name in [*STATE.values(), *SERVICES.values()]]
        source += ['%define short', '%else', f'ORG 0x{START:x}']
        source += [f'%define {name} 0x{address:x}' for address, name in (STATE | SERVICES).items()]
        source += ['%endif', 'phone_log_native:']
        for address, text in rows:
            branch = re.fullmatch(r'(j\w+|call)\s+(?:(short|near)\s+)?(0x[0-9a-f]+)', text)
            if branch:
                target = int(branch[3], 16)
                name = f'L_{target:04x}' if START <= target < END else SERVICES[target]
                text = branch[1] + ' ' + (branch[2] + ' ' if branch[2] else '') + name
            else:
                for state, name in STATE.items():
                    text = re.sub(r'(?<![\da-f])0x' + f'{state:x}' + r'(?![\da-f])', name, text)
            source.append(f'L_{address:04x}: {text}')
        destination = ROOT / 'reconstruction/phone_log/controller.asm'
        destination.write_text('\n'.join(source) + '\n')
        subprocess.run(['nasm', '-fbin', '-I' + str(ROOT / 'reconstruction/uart') + '/', str(destination), '-o', str(work / 'whole.bin')], check=True)
        assert (work / 'whole.bin').read_bytes() == blob
    proof = dict(source_sha256=EXPECTED, source_file_offset=offset, start=START, end=END,
                 bytes=len(blob), instructions=len(rows), sha256=hashlib.sha256(blob).hexdigest(),
                 rea_evidence='ev_8fbdeb2c8c59e1604bf53207279cda86462bc7e81ef53e858cf6bb35fb013b96',
                 analysis_artifact_sha256='d9b4c834ff96f6d4971976ad3f6a4471365ce6ef6460c73ba9b2ee8e304b7648',
                 state={f'{address:04x}': name for address, name in STATE.items()},
                 services={f'{address:04x}': name for address, name in SERVICES.items()},
                 limitations=['Static-only overlay image is never executed.',
                              'Exact controller only; clock, path, FILE/format and notice providers remain separate dependencies.',
                              'Original ignores formatted-write/close errors and updates pending before close; production persistence needs explicit failure handling.'])
    (ROOT / 'reconstruction/phone_log/provenance.json').write_text(json.dumps(proof, indent=2) + '\n')
    print('Recovered', len(blob), 'exact telephone-log controller bytes')


if __name__ == '__main__':
    main()
