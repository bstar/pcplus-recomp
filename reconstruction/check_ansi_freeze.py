#!/usr/bin/env python3
"""Replay the original CSI-q handler in a 16-bit CPU with controlled BIOS ticks.

This tests a handler state, not full terminal parsing, DOS, UART hardware, a
Wi-Fi modem, or a live BBS. No original or candidate DOS executable is launched.
"""
import json
from pathlib import Path
import struct

from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE, UC_HOOK_INSN
from unicorn.x86_const import (UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_SS,
                              UC_X86_REG_SP, UC_X86_INS_IN, UC_X86_INS_OUT)

ROOT = Path(__file__).resolve().parents[1]


def load_image(image):
    manifest = json.loads((ROOT / "analysis/pcplus-overlays/manifest.json").read_text())
    uc = Uc(UC_ARCH_X86, UC_MODE_16)
    uc.mem_map(0, 0x100000)
    header = struct.unpack_from("<14H", image)
    header_bytes = header[4] * 16
    resident_end = (header[2] - 1) * 512 + (header[1] or 512)
    uc.mem_write(0x10000, image[header_bytes:resident_end])
    relocations = [struct.unpack_from("<HH", image, header[12] + i * 4)
                   for i in range(header[3])]
    for number in (12, 32):
        overlay = manifest["overlays"][number - 1]
        source = overlay["source_file_offset"]
        uc.mem_write(0x10000 + overlay["relative_load_segment"] * 16,
                     image[source:source + overlay["initialized_bytes"]])
        relocations.extend(overlay["relocation_records"])
    for offset, segment in relocations:
        at = 0x10000 + segment * 16 + offset
        value = struct.unpack("<H", uc.mem_read(at, 2))[0]
        uc.mem_write(at, struct.pack("<H", (value + 0x1000) & 0xffff))
    uc.reg_write(UC_X86_REG_CS, 0x1000)
    uc.reg_write(UC_X86_REG_DS, 0x1fb7)
    # Startup 0x1815c establishes the small-model DS == SS invariant.
    uc.reg_write(UC_X86_REG_SS, 0x1fb7)
    uc.reg_write(UC_X86_REG_SP, 0xf2a0)
    return uc


def replay(image, parameter_count, second_parameter):
    uc = load_image(image)
    for offset, value in [(0xcb5c, parameter_count), (0xcb3e, second_parameter),
                          (0xcb3c, 0), (0xcd38, ord("q")), (0x8e20, 0)]:
        uc.mem_write(0x1fb70 + offset, struct.pack("<H", value))
    state = {"instructions": 0, "receive_calls": 0, "simulated_bios_ticks": 0,
             "reached_handler_epilogue": False}

    def hook(machine, address, size, user_data):
        state["instructions"] += 1
        if address == 0x1e9ce:
            state["reached_handler_epilogue"] = True
            machine.emu_stop()
            return
        if address == 0x15ca0:
            state["receive_calls"] += 1
        if state["instructions"] % 16 == 0:
            state["simulated_bios_ticks"] += 1
            machine.mem_write(0x46c, struct.pack("<H", state["simulated_bios_ticks"] & 0xffff))

    uc.hook_add(UC_HOOK_CODE, hook)
    uc.emu_start(0x1e4b2, 0, count=200000)
    if not state["reached_handler_epilogue"]:
        raise RuntimeError(f"CSI-q handler failed to return: {state}")
    return state


def query_reply(image, parameter):
    uc = load_image(image)
    for offset, value in [(0xcb3c, parameter), (0x900a, 0x3fd), (0x9012, 0x3f8),
                          (0x8ffe, 0x3fe), (0x3356, 0), (0x39a6, 0),
                          (0xceb0, 0), (0x399c, 9), (0x399e, 19),
                          (0x904c, 0), (0xceac, 0)]:
        uc.mem_write(0x1fb70 + offset, struct.pack("<H", value))
    uc.mem_write(0x1fb70 + 0xf2a0, struct.pack("<H", 0xfff0))
    reply = bytearray()
    state = {"returned": False}

    def input_port(machine, port, size, user_data):
        return {0x3fd: 0x60, 0x3fe: 0xb0}.get(port, 0)

    def output_port(machine, port, size, value, user_data):
        if port == 0x3f8:
            reply.append(value & 0xff)

    def stop(machine, address, size, user_data):
        if address == 0x1fff0:
            state["returned"] = True
            machine.emu_stop()

    uc.hook_add(UC_HOOK_INSN, input_port, None, 1, 0, UC_X86_INS_IN)
    uc.hook_add(UC_HOOK_INSN, output_port, None, 1, 0, UC_X86_INS_OUT)
    uc.hook_add(UC_HOOK_CODE, stop)
    uc.emu_start(0x1de04, 0, count=100000)
    if not state["returned"]:
        raise RuntimeError("Query handler did not return")
    return bytes(reply)


def check(original, candidate):
    results = []
    for name, image, count, value, expected_reads in [
        ("baseline-q-one-parameter", original, 1, 4, 0),
        ("baseline-q-two-parameters", original, 2, 4, 20),
        ("candidate-q-one-parameter", candidate, 1, 4, 0),
        ("candidate-q-two-parameters", candidate, 2, 4, 0),
    ]:
        result = replay(image, count, value)
        if result["receive_calls"] != expected_reads:
            raise RuntimeError(f"{name}: expected {expected_reads} reads; got {result}")
        if expected_reads and result["simulated_bios_ticks"] < expected_reads * 36:
            raise RuntimeError(f"{name}: timeout behavior was not reproduced: {result}")
        results.append({"case": name, **result})
        print(name, result)
    for label, image in [("baseline", original), ("candidate", candidate)]:
        for parameter, expected in [(5, b"\x1b[0n"), (6, b"\x1b[10;20R")]:
            reply = query_reply(image, parameter)
            if reply != expected:
                raise RuntimeError(f"{label} CSI {parameter}n: {reply!r} != {expected!r}")
            results.append({"case": f"{label}-CSI-{parameter}n",
                            "serial_reply_hex": reply.hex(), "matched_expected": True})
            print(label, f"CSI {parameter}n reply", repr(reply))
    return results
