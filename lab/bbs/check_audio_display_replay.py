#!/usr/bin/env python3
"""Replay a captured caller display through the actual linked receive engine."""
import argparse
import json
from pathlib import Path
import struct
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'standalone'))
from check_line_edit_live import Live, Abort
from synthmodem_vm_control import sha
from unicorn.x86_const import UC_X86_REG_AX, UC_X86_REG_CX


class DisplayReplay(Live):
    def __init__(self):
        self.cursor_shapes = []
        super().__init__()

    def interrupt(self, u, n, unused):
        if n == 0x10 and u.reg_read(UC_X86_REG_AX) >> 8 == 1:
            shape = u.reg_read(UC_X86_REG_CX)
            self.cursor_shapes.append(shape)
            u.mem_write(0x460, struct.pack('<H', shape)) # modeled BIOS cursor-shape BDA word
            return
        return super().interrupt(u, n, unused)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cohort', type=Path)
    out = parser.parse_args().cohort.resolve(); assert out.is_relative_to(ROOT/'build')
    capture = out/'caller-decoded.bin'; incoming = capture.read_bytes()
    producer = json.loads((out/'result.json').read_text())
    binary = ROOT/'build/terminal/TERMINAL.EXE'
    assert sha(binary) == producer['frozen_inputs']['build/terminal/TERMINAL.EXE']
    assert sha(capture) == producer['captures_sha256']['caller-decoded.bin']
    live = DisplayReplay(); error = None
    try: live.feed(incoming)
    except (Abort, AssertionError) as e: error = repr(e)
    result = {'passed': error is None, 'input_bytes': len(incoming), 'error': error,
              'unimplemented_service': live.get('csi_unimplemented_service'),
              'remaining_UART_bytes': live.get('uart_rx_count'),
              'cursor_shape_BIOS_calls': live.cursor_shapes,
              'retained_failed_attempts': [{'path':p.name,'sha256':sha(p)} for p in sorted(out.glob('display-replay-attempt-*'))],
              'binary_sha256': sha(binary), 'capture_sha256': sha(capture),
              'inputs': {str(n.relative_to(ROOT)): sha(n) for n in
                         [Path(__file__).resolve(), ROOT/'standalone/check_line_edit_live.py',
                          ROOT/'standalone/check_transport.py', ROOT/'standalone/check_scroll.py',
                          ROOT/'standalone/dos_image.py', ROOT/'build/terminal/terminal.map']},
              'scope': 'Actual linked UART/receive/CSI/video instructions over the complete recorded caller stream. Hardware-only modeled BIOS/video/clock; no DOS/ASPECT scheduler, live media or original-screen-state claim. A pass excludes an unsupported CSI stop in this explicit replay environment, not every reason for a failed live script.'}
    (out/'display-replay.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2)); assert result['passed']


if __name__ == '__main__': main()
