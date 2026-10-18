#!/usr/bin/env python3
"""Build recovered source units and validate their original layout and bytes."""
import hashlib
from pathlib import Path
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def build_units(original):
    directory = ROOT / "reconstruction/build"
    directory.mkdir(exist_ok=True)
    header_bytes = struct.unpack_from("<H", original, 8)[0] * 16
    reloc_count = struct.unpack_from("<H", original, 6)[0]
    reloc_table = struct.unpack_from("<H", original, 0x18)[0]
    relocations = [struct.unpack_from("<HH", original, reloc_table + n * 4)
                   for n in range(reloc_count)]
    units = []
    for source, lower, upper, file_offset, resident in [
        ("uart/core.asm", 0xaa5c, 0xaea7, header_bytes + 0xaa5c, True),
        ("uart/receive_timeout.asm", 0x5ca0, 0x5cce, header_bytes + 0x5ca0, True),
        # Overlay 12 has no relocations. Offset verified by its loader manifest.
        ("ansi/parameters.asm", 0xe3f2, 0xe4a1, 94370, False),
    ]:
        target = directory / (Path(source).stem + ".bin")
        subprocess.run(["nasm", "-f", "bin", "-I", str(ROOT / "reconstruction/uart") + "/",
                        "-o", str(target), str(ROOT / "reconstruction" / source)], check=True)
        rebuilt = target.read_bytes()
        expected = original[file_offset:file_offset + upper - lower]
        if rebuilt != expected:
            raise RuntimeError(f"Recovered source {source} no longer matches its baseline; review intentional changes separately")
        units.append({"source": f"reconstruction/{source}",
                      "file_offset": file_offset, "bytes": len(rebuilt),
                      "sha256": hashlib.sha256(rebuilt).hexdigest(),
                      "original_relocation_sites": [seg * 16 + off for off, seg in relocations
                                                     if resident and lower <= seg * 16 + off < upper],
                      "matched_original": True, "blob": rebuilt})
        print(source, len(rebuilt), "bytes; exact baseline match")
    return units
