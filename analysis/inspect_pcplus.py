#!/usr/bin/env python3
"""Inventory this exact PCPlus image using its REA-analyzed PLINK86 loader.

This is a target-specific parser, not a general PLINK86 format implementation.
Table interpretation: REA functions at 0x1b081, 0x1afba and 0x1b106.
"""
import hashlib
import json
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "pcplus-originals/PCPLUS-main-2.01.EXE"
EXPECTED = "6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904"


def main():
    data = SOURCE.read_bytes()
    assert hashlib.sha256(data).hexdigest() == EXPECTED, "Unrecognized input"
    header = struct.unpack_from("<14H", data)
    module_end = (header[2] - 1) * 512 + (header[1] or 512)
    table = 0xc930
    output = ROOT / "pcplus-overlays"
    output.mkdir(exist_ok=True)
    entries = [struct.unpack_from("<8H", data, table + index * 16)
               for index in range(33)]
    assert entries[-1][3] == 0xffff
    trampolines = []
    for match in re.finditer(b"\x9a\xec\x02\xec\x0a(..)\xea(....)", data[:module_end], re.S):
        overlay = struct.unpack("<H", match[1])[0]
        offset, segment = struct.unpack("<HH", match[2])
        assert 1 <= overlay <= 32
        trampolines.append({"file_offset": match.start(), "overlay": overlay,
                            "target_relative_address": segment * 16 + offset})
    overlays = []
    for index, (current, following) in enumerate(zip(entries, entries[1:]), 1):
        file_offset = (following[0] + (following[1] << 16)) * 16
        relocation_count = current[4]
        relocation_bytes = ((relocation_count + 3) // 4) * 16
        initialized_bytes = min(following[2], current[6] - current[5]) * 16
        code_offset = file_offset + relocation_bytes
        end = code_offset + initialized_bytes
        expected_end = ((entries[index + 1][0] + (entries[index + 1][1] << 16)) * 16
                        if index < 32 else len(data))
        assert end == expected_end, (index, end, expected_end)
        blob = data[code_offset:end]
        assert len(blob) == initialized_bytes
        relocations = [struct.unpack_from("<HH", data, file_offset + number * 4)
                       for number in range(relocation_count)]
        entrypoints = sorted({item["target_relative_address"] for item in trampolines
                              if item["overlay"] == index})
        assert all(current[5] * 16 <= address < current[5] * 16 + len(blob)
                   for address in entrypoints), (index, entrypoints)
        filename = f"overlay-{index:02d}.bin"
        (output / filename).write_bytes(blob)
        overlays.append({
            "id": index, "file": filename, "source_file_offset": code_offset,
            "initialized_bytes": initialized_bytes,
            "relative_load_segment": current[5], "relative_end_segment": current[6],
            "parent_id": current[3] & 0x1fff, "flags": current[3] & 0xe000,
            "relocation_records": relocations, "entrypoints": entrypoints,
            "sha256": hashlib.sha256(blob).hexdigest(),
        })
    other = (ROOT / "pcplus-originals/PCPLUS-utils-2.01.EXE").read_bytes()
    differences = [i for i, (a, b) in enumerate(zip(data, other)) if a != b]
    assert len(other) == len(data)
    manifest = {
        "source_sha256": EXPECTED, "source_file": str(SOURCE.relative_to(ROOT)),
        "resident_header_bytes": header[4] * 16,
        "resident_initialized_bytes": module_end - header[4] * 16,
        "appended_bytes": len(data) - module_end,
        "loader_evidence_files": ["pcplus-main/functions/0x1b081-asm.json",
                                  "pcplus-main/functions/0x1afba-asm.json",
                                  "pcplus-main/functions/0x1b106-asm.json"],
        "comparison": {"other": "PCPLUS-utils-2.01.EXE", "differing_offsets": differences,
                       "different_file_lengths": len(data) != len(other)},
        "trampolines": trampolines, "overlays": overlays,
        "limitations": [
            "Overlay role names and source module names have not been recovered.",
            "Extracted bytes are original on-disk bytes; DOS segment relocations have not been applied.",
            "Overlay routines have not yet been decompiled in their runtime parent/data context.",
            "The original source, object files, compiler identity and linker build script remain unknown.",
        ],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Extracted {len(overlays)} overlays; validated all file boundaries and "
          f"{len(trampolines)} entry trampolines. {len(differences)} differing bytes in second copy.")


if __name__ == "__main__":
    main()
