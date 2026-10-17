#!/usr/bin/env python3
"""Build and test a precisely bounded compatibility patch on a preserved copy.

This is a patched original executable, not a full source rebuild of PCPlus.
"""
import hashlib
import json
from pathlib import Path
import subprocess

from check_ansi_freeze import check
from build_uart import build_units

ROOT = Path(__file__).resolve().parents[1]
original = (ROOT / "analysis/pcplus-originals/PCPLUS-main-2.01.EXE").read_bytes()
expected_sha = "6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904"
if hashlib.sha256(original).hexdigest() != expected_sha:
    raise SystemExit("Unrecognized original; refusing to patch")
at = 96067
if original[at:at + 2] != bytes.fromhex("7d03"):
    raise SystemExit("Original branch bytes do not match the analyzed baseline")
build = ROOT / "reconstruction/build"
build.mkdir(exist_ok=True)
replacement = build / "tech_net.bin"
subprocess.run(["nasm", "-f", "bin", "-o", str(replacement),
                str(ROOT / "reconstruction/patches/tech_net.asm")], check=True)
patch = replacement.read_bytes()
if patch != b"\x90\x90":
    raise SystemExit("Unexpected patch assembly")
source_units = build_units(original)
candidate_bytes = bytearray(original)
for unit in source_units:
    offset = unit["file_offset"]
    candidate_bytes[offset:offset + unit["bytes"]] = unit["blob"]
candidate_bytes[at:at + 2] = patch
candidate = bytes(candidate_bytes)
differences = [i for i, (a, b) in enumerate(zip(original, candidate)) if a != b]
if len(candidate) != len(original) or differences != [at, at + 1]:
    raise SystemExit("Candidate differs outside the intended two-byte patch")
results = check(original, candidate)
dist = ROOT / "reconstruction/dist/tech-net-candidate"
dist.mkdir(parents=True, exist_ok=True)
(dist / "PCPLUS.EXE").write_bytes(candidate)
(dist / "manifest.json").write_text(json.dumps({
    "kind": "partial-source-rebuild-with-compatibility-patch", "original_sha256": expected_sha,
    "candidate_sha256": hashlib.sha256(candidate).hexdigest(),
    "changed_file_offsets": differences,
    "historical_recipe": "analysis/archived-support/dp201/tech_net.dtp",
    "source_archive_url": "https://aspectscripting.com/support/pcplus2/dp201.exe",
    "rebuilt_source_units": [{k: v for k, v in unit.items() if k != "blob"} for unit in source_units],
    "original_bytes_rebuilt_from_source": sum(unit["bytes"] for unit in source_units),
    "handler_replay_tests": results,
    "limitations": ["This build embeds recovered source units in the original executable container; the complete source project is not recovered.",
                    "CPU replay supplies BIOS ticks. Full DOSBox integration results are separate in reconstruction/lab.",
                    "Not tested on a physical Wi-Fi modem or a public BBS.",
                    "The mounted card and its installed PCPlus are unchanged."],
}, indent=2) + "\n")
print("Candidate written to", dist)
