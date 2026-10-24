#!/usr/bin/env python3
"""Replay the optional child IRQ lease against actual linked 8086 code."""
import hashlib
import json
from pathlib import Path
import struct

import check_aspect_serial as base

ROOT = base.ROOT
OUT = ROOT / 'build/aspect-serial-custom-irq'
base.OUT = OUT
base.uart.BINARY = OUT / 'SERIAL.EXE'
base.uart.MAP = OUT / 'serial.map'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def machine(pic=255):
    m = base.Serial()
    m.registers[0x21] = pic
    m.vectors.update({13: (0x5555, 0xe000), 15: (0x7777, 0xd000)})
    m.initial = (dict(m.registers), list(m.divisor), dict(m.vectors))
    return m


def main():
    # Existing parser, ownership, ASIO, overflow, flow, BREAK and rollback cases
    # must also pass unchanged on this separately named executable.
    base.main()
    cases = []

    def done(name, count):
        cases.append(dict(case=name, inputs=count, passed=True))
        print(name, count, flush=True)

    count = 0
    for port in range(1, 5):
        for irq in (3, 4, 5, 7):
            for flow in ('N', 'S', 'H', 'B'):
                for pic in (0, 255, 0x55, 0xa5):
                    m = machine(pic)
                    before = dict(m.vectors)
                    assert m.open(f'/S{port}:0003:03:{flow}:I{irq}'.encode()) == 0
                    assert m.get('serial_vector') == irq + 8
                    assert m.registers[0x21] == pic & ~(1 << irq)
                    assert m.vectors[irq + 8] != before[irq + 8]
                    assert all(v == m.vectors[n] for n, v in before.items() if n != irq + 8)
                    m.call('_aspect_serial_poll')
                    m.tx.clear()
                    payload = b'\x00\x1a\x80\xff'
                    m.receive_irq(payload)
                    assert bytes(m.call('_aspect_serial_read') for _ in payload) == payload
                    assert m.call('_aspect_serial_try_write', [0x5a]) == 0 and m.tx == [0x5a]
                    assert m.registers[0x20] == 0x20
                    assert not any(p in (0xa0, 0xa1) for p, _ in m.physical_writes)
                    assert m.call('_aspect_serial_close') == 0
                    m.restored()
                    count += 1
    done('four-COMs-four-IRQs-four-flow-policies-four-PIC-baselines-real-ISR-and-restoration', count)
    count = 0
    for irq in (3, 4, 5, 7):
        for version in (1, 3):
            m = machine()
            suffix = m.descriptor() if version == 1 else m.descriptor3()
            assert m.open(b'/S2:0003:03:H' + suffix + f':i{irq}'.encode()) == 0
            m.receive_irq(b'RAW\x80\xff')
            assert m.call('_aspect_serial_close') == 0
            assert struct.unpack('<H', m.uc.mem_read(m.desc + 16, 2))[0] == 5
            assert struct.unpack('<H', m.uc.mem_read(m.desc + 22, 2))[0] == 1
            assert bytes(m.uc.mem_read(0x19000, 5)) == b'RAW\x80\xff'
            m.restored()
            count += 1
    done('ASIO-v1-v3-raw-handback-retains-ABI-with-explicit-IRQ-and-lowercase-suffix', count)
    bad = [b'', b':I', b':I0', b':I1', b':I2', b':I6', b':I8', b':I9', b':I15',
           b':I-1', b':I5x', b':i55', b':Q5', b'I5', b':I5:I7', b':I5:1800:0100']
    count = 0
    for descriptor in (False, True):
        for suffix in bad:
            if not suffix:
                continue
            m = machine()
            prefix = b'/S1:0003:03:N' + (m.descriptor() if descriptor else b'')
            assert m.open(prefix + suffix) == 1
            assert not m.physical_writes and not m.get('_aspect_serial_active')
            m.restored()
            count += 1
    for irq in (0, 1, 2, 6, 8, 15, 65535):
        m = machine()
        assert m.call('_aspect_serial_backend_open', [0, 3, 3, ord('N'), irq]) == 1
        assert not m.physical_writes and not m.get('_aspect_serial_active')
        m.restored()
        count += 1
    done('malformed-unsupported-and-direct-backend-IRQs-reject-before-hardware-write', count)
    m = machine()
    for flag, irq in [(b'/S1:0003:03:N:I5', 5), (b'/S1:0003:03:N:I7', 7),
                      (b'/S1:0003:03:N', 4), (b'/S2:0003:03:N', 3)]:
        assert m.open(flag) == 0 and m.get('serial_vector') == irq + 8
        for busy_flag in (b'/S1:0003:03:N:I5', b'/S2:0003:03:N:I7'):
            # The modeled physical base belongs to the already active owner;
            # a rejected candidate must not move the model to its target COM.
            m.uc.mem_write(m.data_base + m.argument, busy_flag + b'\0')
            assert m.call('_aspect_serial_open', [m.argument]) == 2
            assert m.get('serial_vector') == irq + 8
        assert m.call('_aspect_serial_close') == 0
        m.restored()
    done('reopen-busy-owner-and-legacy-defaults-do-not-inherit-a-previous-custom-IRQ', 4)
    count = 0
    for offset, flag, wanted in [(65519, b'/S1:0003:03:N:I5', 0),
                                 (65520, b'/S1:0003:03:N:I5', 1),
                                 (65522, b'/S1:0003:03:N', 0),
                                 (65523, b'/S1:0003:03:N', 1)]:
        m = machine()
        m.uc.mem_write(m.data_base + offset, flag + b'\0')
        assert m.call('_aspect_serial_open', [offset]) == wanted
        if not wanted:
            assert m.call('_aspect_serial_close') == 0
        else:
            assert not m.physical_writes
        m.restored()
        count += 1
    done('near-segment-final-NUL-boundary-and-overflow-refusal', count)
    manifest = json.loads((OUT / 'manifest.json').read_text())
    assert sha(OUT / 'SERIAL.EXE') == manifest['binary_sha256']
    sources = dict(manifest['sources'])
    for name in ('standalone/check_aspect_custom_irq.py', 'standalone/check_aspect_serial.py',
                 'standalone/check_uart.py'):
        sources[name] = sha(ROOT / name)
    for name, digest in sources.items():
        assert sha(ROOT / name) == digest
    result = dict(passed=True, cases=cases, inputs=sum(c['inputs'] for c in cases), sources=sources,
                  binary_sha256=sha(OUT / 'SERIAL.EXE'), original_inputs=[],
                  legacy_checks_sha256=sha(OUT / 'checks.json'),
                  scope=__doc__ + ' Modeled PIC/UART/DOS boundaries. No parent configuration or physical hardware claim.')
    (OUT / 'custom-irq-checks.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
