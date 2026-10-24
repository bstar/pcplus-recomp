#!/usr/bin/env python3
"""Linked optional editor/import and multi-UART IRQ ownership transactions."""
import json
from pathlib import Path
import struct
import subprocess

from build_guarded_helper import ROOT, LOOKUP
from package_special_edition import sha
import check_setup_model as setup
import check_transport as transport

TERMINAL = ROOT / 'build' / (LOOKUP + '-custom-irq') / 'TERMINAL.EXE'
transport.BINARY = TERMINAL
transport.MAP = TERMINAL.parent / 'terminal.map'
from check_port_handoff import Ports, BASES

OUT = ROOT / 'build/parent-custom-irq-linked'


class IRQPorts(Ports):
    def __init__(self):
        super().__init__()
        for vector, seed in [(13, (0x5555, 0x1357)), (15, (0x7777, 0x2468))]:
            self.vectors[vector] = seed
            self.uc.mem_write(vector * 4, struct.pack('<HH', *seed))

    def candidate_irq(self, port, irq):
        ptr = self.candidate(port)
        self.uc.mem_write(self.data_base + ptr + 34, struct.pack('<H', irq))
        return ptr

    def move(self, port, irq):
        return self.call('terminal_port_handoff', ax=self.candidate_irq(port, irq))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    setup.OUT = OUT / 'editor-model'
    setup.OUT.mkdir(exist_ok=True)
    setup.MOUSE = True
    subprocess.run(['wcl', '-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we', '-k8192',
                    '-dSETUP_MOUSE', '-dSETUP_SOUND', '-dTERMINAL_CUSTOM_IRQ',
                    '-i=' + str(ROOT / 'src/config'), '-fm=setup.map', '-fe=MODEL.EXE',
                    *[str(ROOT / p) for p in setup.SOURCES]], cwd=setup.OUT, check=True)
    cases = []

    def done(name, count):
        cases.append(dict(case=name, inputs=count, passed=True))
        print(name, count, flush=True)

    count = 0
    for port in range(1, 5):
        for irq in (3, 4, 5, 7):
            m = setup.Model()
            assert m.set(0, str(port).encode()) == 0
            before = bytearray(m.raw())
            assert m.set(8, str(irq).encode()) == 0
            struct.pack_into('<H', before, 0x184 + (port - 1) * 2, irq)
            assert m.raw() == before and m.get(8) == (0, str(irq).encode())
            assert m.validate() == (0, 65535)
            assert m.call('_terminal_import_decode', [m.b, m.t]) == 0
            plan = bytes(m.uc.mem_read(m.data_base + m.t, 44))
            assert struct.unpack_from('<H', plan)[0] == port
            assert struct.unpack_from('<HH', plan, 32) == (BASES[port - 1], irq)
            count += 1
    done('editor-selected-slot-only-roundtrip-and-real-import-all-COM-IRQ-pairs', count)
    count = 0
    for port in range(1, 5):
        for irq in (0, 1, 2, 6, 8, 15, 65535):
            m = setup.Model()
            assert m.set(0, str(port).encode()) == 0
            assert m.set(8, str(irq).encode()) == 2
            raw = bytearray(m.raw())
            struct.pack_into('<H', raw, 0x184 + (port - 1) * 2, irq)
            m.reset(raw)
            assert m.get(8)[0] == 3 and m.validate() == (3, 8)
            m.uc.mem_write(m.data_base + m.t, b'\xcc' * 44)
            assert m.call('_terminal_import_decode', [m.b, m.t]) == 2
            assert m.uc.mem_read(m.data_base + m.t, 44) == b'\xcc' * 44
            count += 1
    done('unsupported-saved-and-entered-IRQs-refuse-without-partial-import-or-edit', count)
    count = 0
    for port in range(1, 5):
        for irq in (3, 4, 5, 7, 0, 6, 65535):
            m = setup.Model()
            raw = bytearray(m.raw())
            struct.pack_into('<H', raw, 0x184 + (port - 1) * 2, irq)
            m.reset(raw)
            assert m.set(0, str(port).encode()) == 0
            wanted = irq if irq in (3, 4, 5, 7) else [4, 3, 4, 3][port - 1]
            assert m.get(8) == (0, str(wanted).encode())
            assert m.validate() == (0, 65535)
            count += 1
    done('selecting-COM-retains-valid-saved-custom-IRQ-and-repairs-invalid-default', count)
    count = 0
    states = [(port, irq) for port in range(1, 5) for irq in (3, 4, 5, 7)]
    for source in states:
        for target in states:
            if source == target:
                continue
            m = IRQPorts()
            if source != (1, 4):
                m.quiet()
                assert m.move(*source) == 0
                m.resume()
            m.quiet()
            saved = m.saved()
            before = len(m.writes)
            assert m.move(*target) == 0
            if source[0] == target[0]:
                # Only vector ownership changes. Original UART/PIC snapshot
                # remains exact, and a live asserted DTR never pulses low.
                for name in saved:
                    if name.startswith('uart_saved_'):
                        assert m.saved()[name] == saved[name], (source, target, name)
                mcr = BASES[target[0] - 1] + 4
                assert all(value & 1 for port, value in m.writes[before:] if port == mcr)
            else:
                assert m.hardware()[BASES[source[0] - 1]] == m.originals[BASES[source[0] - 1]]
            m.resume()
            m.rx.append(0xa5)
            m.call('uart_receive_interrupt', irq=True)
            assert m.call('uart_receive_byte') == 0xa5
            assert m.call('uart_try_write', ax=0x5a) == 0x5a
            m.shutdown()
            count += 1
    done('all-directed-COM-IRQ-pairs-actual-handoff-ISR-traffic-DTR-and-final-full-restoration', count)
    count = 0
    for name, value in [('connection_state', 6), ('terminal_parser_active', 1),
                        ('terminal_tx_count', 1), ('uart_rx_count', 1), ('uart_flow_pending', 17)]:
        m = IRQPorts()
        m.quiet()
        m.put(name, value, 1 if name == 'uart_flow_pending' else 2)
        before = (m.hardware(), m.saved(), m.pic, len(m.writes))
        assert m.move(1, 5) == 2
        assert (m.hardware(), m.saved(), m.pic, len(m.writes)) == before
        count += 1
    for irq in (0, 1, 2, 6, 8, 15, 65535):
        m = IRQPorts()
        m.quiet()
        before = (m.hardware(), m.saved(), m.pic, len(m.writes))
        assert m.move(1, irq) == 1
        assert (m.hardware(), m.saved(), m.pic, len(m.writes)) == before
        count += 1
    done('busy-or-invalid-same-UART-IRQ-moves-never-transfer-or-overwrite-baselines', count)
    manifest = json.loads((TERMINAL.parent / 'manifest.json').read_text())
    sources = dict(manifest['sources'])
    for name in ['standalone/check_parent_custom_irq.py', 'standalone/check_setup_model.py',
                 'standalone/setup_model_host.c', 'standalone/check_port_handoff.py',
                 'standalone/check_transport.py', 'standalone/check_meta_actions_live.py',
                 'standalone/check_program_actions_live.py', 'standalone/live_setup_kernel.py']:
        sources[name] = sha(ROOT / name)
    for name, digest in sources.items():
        assert sha(ROOT / name) == digest, name
    result = dict(passed=True, cases=cases, inputs=sum(c['inputs'] for c in cases), sources=sources,
                  terminal_sha256=sha(TERMINAL), model_sha256=sha(setup.OUT / 'MODEL.EXE'), original_inputs=[],
                  scope=__doc__ + ' Hardware/DOS boundaries modeled; full live settings invocation and actual DOS tests remain separate.')
    (OUT / 'result.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
