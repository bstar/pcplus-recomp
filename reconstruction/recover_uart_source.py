#!/usr/bin/env python3
"""Recover editable NASM for the original resident UART block.

Generation is an explicit analysis step, not part of normal builds. Output goes
to build/recovered-uart; maintained source is never overwritten. All
instructions must assemble exactly; no opaque fallback to original bytes is
permitted. Small scratch-data regions are declared separately from code.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reconstruction/uart"
OUTPUT = ROOT / "build/recovered-uart"
OUTPUT.mkdir(parents=True, exist_ok=True)
START, END = 0xaa5c, 0xaea7
image = (ROOT / "analysis/pcplus-originals/PCPLUS-main-2.01.EXE").read_bytes()
EXPECTED = "6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904"
if hashlib.sha256(image).hexdigest() != EXPECTED:
    raise SystemExit("Wrong input image")

names = {
    0xaa5c: "uart_carrier_detect", 0xaa65: "uart_receive_byte",
    0xaad9: "uart_available", 0xab0b: "uart_transmit_byte",
    0xab92: "uart_transmit_buffer", 0xabac: "uart_transmit_string",
    0xabc1: "uart_clear_to_send", 0xabca: "uart_clear_receive_buffer",
    0xabde: "uart_unreceive_byte", 0xabfa: "uart_set_rts",
    0xac27: "uart_set_baud_divisor", 0xac5d: "uart_set_line_control",
    0xacb8: "uart_receive_interrupt", 0xad65: "uart_install_interrupt",
    0xad93: "uart_transmit_cl", 0xada4: "uart_restore_interrupt",
    0xadba: "uart_disable", 0xadd6: "uart_mask_irq",
    0xadeb: "uart_enable", 0xae25: "uart_wait_transmitter_empty",
    0xae32: "uart_save_hardware_state", 0xae69: "uart_restore_hardware_state",
}
rows = []
with tempfile.TemporaryDirectory(prefix="pcplus-uart-source-") as directory:
    work = Path(directory)
    for lower, upper in [(START, 0xacb2), (0xacb8, 0xae31), (0xae32, END)]:
        part = work / "part.bin"
        part.write_bytes(image[0x1200 + lower:0x1200 + upper])
        decoded = subprocess.check_output(["ndisasm", "-b16", f"-o{lower}", str(part)], text=True)
        for line in decoded.splitlines():
            match = re.fullmatch(r"([0-9A-F]+)\s+([0-9A-F]+)\s+(.*)", line)
            if not match:
                raise RuntimeError(line)
            at, encoded, instruction = int(match[1], 16), bytes.fromhex(match[2]), match[3]
            if instruction.startswith("db "):
                raise RuntimeError(f"Undecoded code at {at:x}")
            rows.append((at, encoded, instruction))

    def assemble(instruction, address):
        (work / "one.asm").write_text(
            f'BITS 16\nCPU 8086\nORG {address}\n%include "encodings.inc"\n{instruction}\n')
        result = subprocess.run(["nasm", "-f", "bin", "-I", str(SOURCE) + "/",
                                 "-o", str(work / "one.bin"), str(work / "one.asm")],
                                capture_output=True, text=True)
        return (work / "one.bin").read_bytes() if result.returncode == 0 else None

    resolved = []
    for at, encoded, text in rows:
        instruction = text
        if encoded[0] == 0xeb:
            instruction = instruction.replace("jmp ", "jmp short ", 1)
        elif encoded[0] == 0xe9:
            instruction = instruction.replace("jmp ", "jmp near ", 1)
        elif 0x70 <= encoded[0] <= 0x7f:
            instruction = instruction.replace(" ", " short ", 1)
        if assemble(instruction, at) != encoded:
            candidates = []
            if len(encoded) == 2 and encoded[1] >= 0xc0 and encoded[0] in (
                0x02, 0x03, 0x0a, 0x0b, 0x12, 0x13, 0x1a, 0x1b,
                0x22, 0x23, 0x2a, 0x2b, 0x32, 0x33, 0x3a, 0x3b, 0x8a, 0x8b,
            ):
                operation, operands = text.split(" ", 1)
                candidates.append(operation + "_load " + operands)
            if re.search(r",(?:-?0x[0-9a-f]+)$", instruction):
                for width in ("word", "byte"):
                    candidates.append(re.sub(r",(-?0x[0-9a-f]+)$", rf",strict {width} \1", instruction))
            instruction = next((c for c in candidates if assemble(c, at) == encoded), None)
            if instruction is None:
                raise RuntimeError(f"No exact instruction encoding at {at:x}: {text} {encoded.hex()}")
        resolved.append((at, encoded, text, instruction))

    addresses = {row[0] for row in rows}
    lines = [
        "; Recovered assembly, not original source. Source image SHA-256: " + EXPECTED,
        "; Resident UART block [0xaa5c, 0xaea7); original relocation sites retained.",
        "; Names are analyst annotations; DS offsets and external calls retain original addresses.",
        "; Code corroboration: analysis/pcplus-main/functions and pcplus-uart-entry/evidence.",
        "BITS 16", "CPU 8086", f"ORG 0x{START:x}", '%include "encodings.inc"', "",
    ]
    for at, encoded, decoded, instruction in resolved:
        if at == 0xacb8:
            lines.extend(["uart_saved_ds: dw 0", "uart_previous_irq_offset: dw 0",
                          "uart_previous_irq_segment: dw 0", ""])
        if at == 0xae32:
            lines.append("db 0 ; original alignment byte at 0xae31")
        if at in names:
            lines.extend(["", names[at] + ":"])
        branch = re.fullmatch(r"(j\w+|call)\s+(?:(short|near)\s+)?(0x[0-9a-f]+)", instruction)
        if branch and int(branch[3], 16) in addresses:
            target = int(branch[3], 16)
            instruction = branch[1] + " " + ((branch[2] + " ") if branch[2] else "") + f"L_{target:04x}"
        lines.append(f"L_{at:04x}: {instruction:45s} ; original {at:04x}: {decoded}")
    path = OUTPUT / "core.asm"
    path.write_text("\n".join(lines) + "\n")
    output = OUTPUT / "uart-core.bin"
    subprocess.run(["nasm", "-f", "bin", "-I", str(SOURCE) + "/", "-o", str(output), str(path)], check=True)
    expected = image[0x1200 + START:0x1200 + END]
    if output.read_bytes() != expected:
        raise RuntimeError("Combined UART assembly does not match the original")
    manifest = {"source_sha256": EXPECTED, "start": START, "end": END,
                "bytes": len(expected), "decoded_instructions": len(resolved),
                "scratch_data_bytes": 6, "alignment_bytes": 1,
                "exact_encoding_macros": sum("_load " in r[3] for r in resolved),
                "block_sha256": hashlib.sha256(expected).hexdigest(),
                "matched_original": True,
                "limitations": ["Generated assembly with analyst-selected code/data boundaries and names.",
                                "This is one resident module, not the full PCPlus source project."]}
    (OUTPUT / "core-provenance.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))
