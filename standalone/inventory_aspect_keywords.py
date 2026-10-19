#!/usr/bin/env python3
"""Optional read-only private ASPCOMP1.01 keyword-table inventory.

This is an analysis tool, never a source-only build input. Requires the exact
local original compiler; does not execute the compiler or any generated ASX.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
SHA = '5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a'
DATA_FILE_BASE = 0xc380
POINTER_TABLE = 0xff8a  # DS3C0A, loaded by original CS04F7
RECORD_SIZE = 20


def sha(data):
    return hashlib.sha256(data).hexdigest()


def inventory(binary):
    assert sha(binary) == SHA, 'Unsupported compiler identity'
    groups = []
    pointer = POINTER_TABLE
    starts = []
    while True:
        assert pointer+2 <= len(binary)
        offset = struct.unpack_from('<H', binary, pointer)[0]
        if offset == 0:
            break
        start = DATA_FILE_BASE+offset
        assert 0xcc5e <= start < POINTER_TABLE
        assert start not in starts
        starts.append(start)
        records = []
        position = start
        while binary[position] != 0:
            raw = binary[position:position+RECORD_SIZE]
            assert len(raw) == RECORD_SIZE and position+RECORD_SIZE <= POINTER_TABLE
            padded = raw[:11]
            assert 0 in padded
            name, padding = padded.split(b'\0', 1)
            assert name and not any(padding) and all(32 <= b <= 126 for b in name)
            assert raw[16:20] == b'\0'*4
            records.append(dict(name=name.decode('ascii'), file_offset=position,
                ds_offset=position-DATA_FILE_BASE, kind=raw[11], token_byte=raw[12],
                extra_byte=raw[13], value_or_callback_word=struct.unpack_from('<H', raw, 14)[0],
                trailing_words_initial=list(struct.unpack_from('<HH', raw, 16))))
            position += RECORD_SIZE
        assert binary[position:position+RECORD_SIZE] == b'\0'*RECORD_SIZE
        groups.append(dict(pointer_file_offset=pointer, start_file_offset=start,
            terminator_file_offset=position, count=len(records),
            kinds=dict(Counter(r['kind'] for r in records)),
            table_sha256=sha(binary[start:position+RECORD_SIZE]), records=records))
        pointer += 2
        assert len(groups) <= 32
    assert len(groups) == 18 and pointer == 0xffae
    physical = sorted(groups, key=lambda g: g['start_file_offset'])
    assert physical[0]['start_file_offset'] == 0xcc5e
    assert all(a['terminator_file_offset']+20 == b['start_file_offset'] for a, b in zip(physical, physical[1:]))
    assert physical[-1]['terminator_file_offset']+20 == POINTER_TABLE
    commands = groups[0]['records']
    assert len(commands) == 217 and all(r['kind'] == 1 for r in commands)
    by_name = {r['name']: r for r in commands}
    for name, expected in dict(TRANSMIT=0xbf, PAUSE=0x88, SET=0x9e,
                               EMULATE=0x2f, EXIT=0x33, HANGUP=0x55,
                               WAITFOR=0xd4, CLEAR=0x12, CALL=0xc7).items():
        assert by_name[name]['token_byte'] == expected
    aliases = defaultdict(list)
    for record in commands:
        aliases[record['token_byte']].append(record['name'])
    nonmarker = [r for r in commands if r['token_byte'] not in (0, 255)]
    assert all(r['token_byte'] <= 0xd6 for r in nonmarker)
    return dict(groups=groups, record_count=sum(g['count'] for g in groups),
        pointer_terminator_file_offset=pointer,
        command_summary=dict(records=len(commands), nonmarker_name_records=len(nonmarker),
            unique_nonmarker_tokens=len({r['token_byte'] for r in nonmarker}),
            compiler_token_zero=aliases[0], preprocessing_token_ff=aliases[255],
            shared_nonmarker_tokens={str(t): n for t, n in aliases.items() if t not in (0, 255) and len(n)>1},
            vm_slot_indices_without_nonmarker_command_name=[t for t in range(0xd7) if t not in {r['token_byte'] for r in nonmarker}]))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--compiler', type=Path, default=ROOT/'analysis/pcplus-install/ASPCOMP.EXE')
    p.add_argument('--evidence-bundle', type=Path, default=ROOT/'analysis/aspect-compiler/rea-compiler-complete.json')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    out = args.output.resolve()
    assert out.parent == ROOT/'analysis/aspect-vm-runtime' and out.name.startswith('keywords-')
    assert not args.compiler.name.lower().endswith('.analysis.exe')
    binary = args.compiler.read_bytes()
    result = inventory(binary)
    evidence = []
    if args.evidence_bundle.exists():
        bundle = json.loads(args.evidence_bundle.read_text())
        for record in bundle['records']:
            if record['parameters'].get('procedure') in ['FUN_1000_0547', 'FUN_1000_2267', 'FUN_1000_0f1b']:
                assert record['subject']['digest']['sha256'] == SHA
                evidence.append(dict(id=record['evidence_id'], operation=record['operation'], parameters=record['parameters']))
    result.update(compiler_sha256=SHA, harness_sha256=sha(Path(__file__).read_bytes()),
        data_file_base=DATA_FILE_BASE, pointer_table_file_offset=POINTER_TABLE,
        record_size=RECORD_SIZE,
        record_layout={'00..0A': '11-byte NUL-padded name', '0B': 'kind byte',
            '0C': 'token/type byte; context-dependent', '0D': 'extra byte; context-dependent',
            '0E..0F': 'near callback for command records; enum/value for other kinds',
            '10..13': 'two initially zero words; runtime metadata/link fields'},
        native_initializer=dict(cs_start=0x04f7, cs_end=0x0528,
            file_start=0x0af7, sha256=sha(binary[0x0af7:0x0b28]),
            observation='MOV DI,3C0A; reads near table base, tests first name byte for zero; adds14h record size; advances pointer word and tests zero terminator.'),
        retained_rea_evidence=evidence,
        retained_rea_bundle_sha256=sha(args.evidence_bundle.read_bytes()) if args.evidence_bundle.exists() else None,
        conclusions=['18 pointer-selected tables have explicit zero-name record terminators; original initialized records occupy contiguous fileCC5E..FF8A.',
            '217 command-kind records include compiler directives and aliases; token values do not form a complete application VM dispatch inventory.',
            'Kind01 command callback is read at+0E by retained original parser evidence; generic emitter reads token byte+0C.',
            'Kinds02,14h,19h,64h and others reuse the same record layout with context-dependent fields. No universal opcode interpretation is valid.'],
        limits=['Static exact-original table inventory only; no compiler or VM execution performed here.',
            'Field semantics beyond retained native evidence and independent compiler corpus remain unknown.',
            'Application opcode slots, operand tokens and command names require separate decoder/context evidence.',
            'Normal source-only build must not invoke this tool or read the original.'])
    out.mkdir(parents=True, exist_ok=False)
    (out/'inventory.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(passed=True, tables=len(result['groups']), records=result['record_count'],
        command_summary=result['command_summary'], output=str(out)), indent=2))


if __name__ == '__main__':
    main()
