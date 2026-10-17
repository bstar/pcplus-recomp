#!/usr/bin/env python3
"""Build synthetic, non-runnable analysis images for each PLINK86 overlay.

Original resident code, active overlay/parent code, and the startup data overlay
are placed at their loader-derived relative addresses. Trampolines are replaced
with direct jumps for the active parent chain and RET for inactive overlays.
This lets Ghidra follow the active code without mistaking overlapping overlays
for a single simultaneously resident program. These are NOT deployable builds.
"""
import hashlib
import argparse
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--entry-anchors", action="store_true")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "pcplus-overlays/manifest.json").read_text())
    original = (ROOT / manifest["source_file"]).read_bytes()
    assert hashlib.sha256(original).hexdigest() == manifest["source_sha256"]
    overlays = {item["id"]: item for item in manifest["overlays"]}
    header_bytes = manifest["resident_header_bytes"]
    resident_bytes = manifest["resident_initialized_bytes"]
    original_header = list(struct.unpack_from("<14H", original))
    root_relocs = [struct.unpack_from("<HH", original, original_header[12] + i * 4)
                   for i in range(original_header[3])]
    trampoline_ranges = [(t["file_offset"] - header_bytes,
                          t["file_offset"] - header_bytes + 12)
                         for t in manifest["trampolines"]]
    # Old relocations inside replaced instructions must not modify the adapter.
    retained_relocs = [(off, seg) for off, seg in root_relocs
                       if not any(a <= seg * 16 + off < b for a, b in trampoline_ranges)]
    output = ROOT / ("pcplus-overlay-entry-images" if args.entry_anchors else "pcplus-overlay-images")
    output.mkdir(exist_ok=True)
    images = []
    for number in range(1, 32):
        active = []
        index = number
        while index:
            assert index not in active, "Cyclic parent chain"
            active.append(index)
            index = overlays[index]["parent_id"]
        active.reverse()
        data = overlays[32]
        initialized_end = data["relative_load_segment"] * 16 + data["initialized_bytes"]
        module = bytearray(initialized_end)
        module[:resident_bytes] = original[header_bytes:header_bytes + resident_bytes]
        ranges = [{"role": "resident", "relative_address": 0,
                   "source_file_offset": header_bytes, "bytes": resident_bytes}]
        relocations = list(retained_relocs)
        for layer in active + [32]:
            item = overlays[layer]
            start = item["relative_load_segment"] * 16
            blob = (ROOT / "pcplus-overlays" / item["file"]).read_bytes()
            assert hashlib.sha256(blob).hexdigest() == item["sha256"]
            module[start:start + len(blob)] = blob
            relocations.extend(item["relocation_records"])
            ranges.append({"role": f"overlay-{layer}", "relative_address": start,
                           "source_file_offset": item["source_file_offset"], "bytes": len(blob)})
        for t in manifest["trampolines"]:
            at = t["file_offset"] - header_bytes
            if t["overlay"] in active:
                target = t["target_relative_address"]
                assert 0 <= target < 0x10000 and 0 <= at < 0x10000
                patch = b"\xe9" + struct.pack("<H", (target - at - 3) & 0xffff) + b"\x90" * 9
            else:
                patch = b"\xc3" + b"\x90" * 11
            module[at:at + 12] = patch
        anchor_start = None
        anchor_entries = []
        if args.entry_anchors:
            anchor_start = len(module)
            assert anchor_start % 16 == 0
            anchor_entries = sorted({entry for layer in active for entry in overlays[layer]["entrypoints"]})
            # The parent shared block may have no exported entrypoint itself.
            anchor_entries.extend(overlays[layer]["relative_load_segment"] * 16
                                  for layer in active if not overlays[layer]["entrypoints"])
            for entry in sorted(set(anchor_entries)):
                at = len(module)
                module.extend(b"\x9a" + struct.pack("<HH", entry, 0))
                relocations.append(((at + 3) % 16, (at + 3) // 16))
            at = len(module)
            module.extend(b"\xea" + struct.pack("<HH", original_header[10], original_header[11]))
            relocations.append(((at + 3) % 16, (at + 3) // 16))
            module.extend(b"\x90" * (-len(module) % 16))
        header = bytearray(original[:header_bytes])
        words = list(original_header)
        total = len(header) + len(module)
        words[1] = total % 512
        words[2] = (total + 511) // 512
        words[3] = len(relocations)
        original_memory_paragraphs = (resident_bytes + 15) // 16 + original_header[5]
        words[5] = max(0, original_memory_paragraphs - (len(module) + 15) // 16)
        words[9] = 0
        if anchor_start is not None:
            words[10] = 0
            words[11] = anchor_start // 16
        struct.pack_into("<14H", header, 0, *words)
        assert words[12] + len(relocations) * 4 <= header_bytes
        for i, (off, seg) in enumerate(relocations):
            assert seg * 16 + off + 2 <= len(module)
            struct.pack_into("<HH", header, words[12] + i * 4, off, seg)
        image = bytes(header) + module
        name = f"overlay-{number:02d}.analysis.exe"
        (output / name).write_bytes(image)
        item = overlays[number]
        images.append({"overlay": number, "file": name, "active_parent_chain": active,
                       "sha256": hashlib.sha256(image).hexdigest(), "source_ranges": ranges,
                       "region_start": 0x10000 + item["relative_load_segment"] * 16,
                       "region_end": 0x10000 + item["relative_load_segment"] * 16 + item["initialized_bytes"],
                       "synthetic_entry_anchor_relative_address": anchor_start,
                       "entry_anchors": sorted(set(anchor_entries))})
    (output / "manifest.json").write_text(json.dumps({
        "original_sha256": manifest["source_sha256"], "images": images,
        "limitations": [
            "Synthetic analysis inputs only; never run or deploy these images.",
            "Trampoline substitutions deliberately omit overlay loading and inactive calls.",
            "Source ranges describe copied layers before trampoline/header substitutions.",
            "Static analysis cannot prove that all overlay functions or data types were discovered.",
            "Optional synthetic far-call entry anchors drive function discovery; their call semantics are not runtime evidence.",
        ],
    }, indent=2) + "\n")
    print(f"Created {len(images)} synthetic overlay analysis images; originals untouched.")


if __name__ == "__main__":
    main()
