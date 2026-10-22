#!/usr/bin/env python3
"""Actual DOS Escape/Yes cancellation during PAUSE with the live confirmation owner."""
import json
import struct
import sys
from pathlib import Path
import test_aspect_renderer_dos as renderer
import test_aspect_abort_yes_dos as confirmed


def main():
    base = renderer.ROOT / 'build/aspect-pause-cancel-dos'
    confirmed.BASE = base
    original_definitions = confirmed.definitions
    def definitions():
        case = next(c for c in original_definitions() if c['name'] == 'abort-Yes-PAUSE')
        case['name'] = 'pause-Escape'
        return [case]
    confirmed.definitions = definitions
    assert confirmed.main() == 0
    folder = base / sys.argv[sys.argv.index('--label') + 1]
    report = json.loads((folder / 'confirmation-checks.json').read_text())
    case = folder / 'pause-Escape'
    exit_code = struct.unpack_from('<7H', (case / 'RENDER.BIN').read_bytes())[6]
    wire = (case / 'serial.bin').read_bytes()
    checks = dict(functional_cleanup_and_parent_keyboard=report['passed'],
                  explicit_child_cancelled_13=exit_code == 13,
                  subsequent_script_output_absent=b'UNREACHABLE' not in wire)
    result = dict(passed=all(checks.values()), checks=checks, child_exit=exit_code,
                  parent_sha256=report['parent_sha256'], runner_sha256=report['runner_sha256'],
                  checker_sha256=renderer.sha(Path(__file__)),
                  captures_sha256={str(p.relative_to(folder)): renderer.sha(p)
                                  for p in folder.rglob('*') if p.is_file()}, scope=__doc__)
    (folder / 'cancel-checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['checks']))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
