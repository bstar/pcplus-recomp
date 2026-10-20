#!/usr/bin/env python3
"""Analyst-only proof: independent MZ bytes plus retained REA reads/mappings."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]


def main():
    source = ROOT / 'analysis/pcplus-originals/PCPLUS-main-2.01.EXE'
    original = source.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    assert digest == '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
    bundle = json.loads((ROOT / 'analysis/program-break-01.rea.json').read_text())
    rows = bundle['records']
    units = []
    for name, start, size in [('install', 0x7508, 80), ('restore', 0x758a, 36), ('ignore', 0x7f90, 1)]:
        address = hex(0x10000 + start)
        read = next(r for r in rows if r['operation'] == 'read_bytes' and r['normalized_result']['address'] == address)
        mapping = next(r for r in rows if r['operation'] == 'address_to_file_offset' and r['normalized_result']['address'] == address)
        offset = mapping['normalized_result']['file_offset']
        # Independent DOS header paragraph size and resident CS load mapping.
        assert offset == int.from_bytes(original[8:10], 'little') * 16 + start
        data = original[offset:offset+size]
        assert read['normalized_result']['complete'] and bytes.fromhex(read['normalized_result']['bytes_hex']) == data
        units.append(dict(file='reconstruction/program_break/' + name + '.asm', start=start,
            bytes=size, file_offset=offset, sha256=hashlib.sha256(data).hexdigest(),
            read_evidence=read['evidence_id'], mapping_evidence=mapping['evidence_id']))
    proof = dict(source_sha256=digest, units=units,
        functions=[dict(evidence_id=r['evidence_id'], address=r['normalized_result']['procedure']['address'])
            for r in rows if r['operation'] == 'analyze_function'],
        state={'0x7ab6':'program_break_original_1b','0x7aba':'program_break_original_23','0x7abe':'program_break_original_flag'},
        limitations=['Native component only; no production controller binding or nested ownership policy.',
            '7f90 is a source-mapped CF byte referenced by7508; Ghidra has no function at that entry.',
            'Decompiler guessed phantom parameters for758a; decoded RET and assembly define the recovered ABI.'])
    (ROOT / 'reconstruction/program_break/provenance.json').write_text(json.dumps(proof, indent=2)+'\n')


if __name__ == '__main__':
    main()
