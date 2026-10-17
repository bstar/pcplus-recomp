#!/usr/bin/env python3
"""Reassemble four original routines and require byte-for-byte equality."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
original = (ROOT / "analysis/pcplus-originals/PCPLUS-main-2.01.EXE").read_bytes()
assert hashlib.sha256(original).hexdigest() == "6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904"
output = ROOT / "reconstruction/build"
output.mkdir(exist_ok=True)
results = []
for name, source, start, end in [
    ("carrier_detect", "status.asm", 0xaa5c, 0xaa65),
    ("clear_to_send", "status.asm", 0xabc1, 0xabca),
    ("transmit", "transmit.asm", 0xad93, 0xada4),
    ("receive_timeout", "receive_timeout.asm", 0x5ca0, 0x5cce),
]:
    target = output / (name + ".bin")
    subprocess.run(["nasm", "-f", "bin", f"-DROUTINE={name}",
                    "-o", str(target), str(ROOT / "reconstruction/uart" / source)], check=True)
    blob = target.read_bytes()
    expected = original[0x1200 + start:0x1200 + end]
    assert blob == expected, (name, blob.hex(), expected.hex())
    results.append({"routine": name, "bytes": len(blob), "matched_original": True,
                    "source_file_offset": 0x1200 + start,
                    "sha256": hashlib.sha256(blob).hexdigest()})
    print(f"{name}: {len(blob)} bytes, identical to original")
(output / "verification.json").write_text(json.dumps(results, indent=2) + "\n")
