#!/usr/bin/env python3
"""Read Datastorm DTP patch recipes and compare bytes; never apply patches."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
original = (ROOT / "pcplus-originals/PCPLUS-main-2.01.EXE").read_bytes()
results = []
for source in sorted((ROOT / "archived-support").rglob("*.dtp")):
    target, size, offset, values, chunks, unknown = None, None, None, [], [], []

    def flush():
        if offset is not None and values:
            chunks.append({"file_offset": offset, "replacement_hex": bytes(values).hex()})

    for raw in source.read_text(encoding="cp437").replace("\x1a", "").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("@"):
            target = line[1:]
        elif line.startswith("="):
            size = int(line[1:])
        elif line.startswith("O"):
            flush()
            offset, values = int(line[1:]), []
        elif line[:1].lower() == "x":
            values.append(int(line[1:], 16))
        elif line.isdecimal():
            values.append(int(line))
        else:
            unknown.append(line)
    flush()
    if target and target.upper() == "PCPLUS.EXE":
        for chunk in chunks:
            at = chunk["file_offset"]
            replacement = bytes.fromhex(chunk["replacement_hex"])
            current = original[at:at + len(replacement)]
            chunk["current_hex"] = current.hex()
            chunk["replacement_already_present"] = current == replacement
    results.append({"recipe": str(source.relative_to(ROOT)), "target": target,
                    "expected_size": size, "matches_main_size": size == len(original),
                    "chunks": chunks, "unsupported_lines": unknown,
                    "fully_interpreted": bool(chunks) and not unknown, "applied": False})
(ROOT / "archived-support/patch-audit.json").write_text(json.dumps(results, indent=2) + "\n")
for item in results:
    if item["target"] and item["target"].upper() == "PCPLUS.EXE":
        print(Path(item["recipe"]).name, "replacement present:",
              (all(c.get("replacement_already_present") for c in item["chunks"])
               if item["fully_interpreted"] else "unknown"),
              "unsupported commands:", len(item["unsupported_lines"]))
