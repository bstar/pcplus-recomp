#!/usr/bin/env python3
"""Compose logical width132 with real clipboard selection and strict X/YMODEM."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from product_inputs import ROOT, select_product
sys.path.insert(0, str(ROOT / 'standalone'))
import test_clipboard_transfer_dos as base


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class WideWire:
    def ready(self):
        super().ready()
        self.send(b'\x1b[?3h\x1b[2;121HBEFORE!\x1b[6n')
        self.expect(b'\x1b[2;128R')
        self.checks['actual_wide_before_selection'] = True
        self.log('wide-before-selection')


class WideResume:
    def resume(self):
        self.in_protocol = False
        self.send(b'\x1b[2;121HRESUMED\x1b[6n')
        self.expect(b'\x1b[2;128R')
        self.checks['actual_wide_after_protocol'] = True
        self.log('wide-after-protocol')
        super().resume()
        # Native width commits clear the screen. Repaint the remote menu after
        # narrowing so the existing final-video check has a valid expectation.
        self.send(b'\x1b[?3l\x1b[HAFTER TRANSFER\x1b[2;73HNARROW!\x1b[6n')
        self.expect(b'\x1b[2;80R')
        self.checks['actual_narrow_after_keyboard'] = True
        self.log('narrow-after-keyboard')


class Receive(WideResume, base.PromptMixin, WideWire, base.ReceivePeer):
    pass


class Upload(WideResume, base.PromptMixin, WideWire, base.UploadPeer):
    pass


class Batch(WideResume, base.PromptMixin, WideWire, base.BatchPeer):
    pass


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--terminal', type=Path, required=True)
    p.add_argument('--case', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    binary, inputs = select_product(a.terminal, 'TERMINAL.EXE')
    output = a.output.resolve()
    assert output.is_relative_to(ROOT / 'build') and not output.exists()
    output.mkdir(parents=True)
    source = Path(base.__file__).read_text()
    assert source.count('cputype=386') == 1
    scope = dict(base.__dict__)
    exec(compile(source.replace('cputype=386', 'cputype=8086'), base.__file__, 'exec'), scope)
    scope.update(BINARY=binary, OUT=output, PromptReceive=Receive, PromptUpload=Upload, PromptBatch=Batch)
    original_keys = scope['keys']
    scope['keys'] = lambda recipe: 'p900 enter ' + original_keys(recipe)
    inputs += [binary, Path(__file__), ROOT / 'lab/bbs/product_inputs.py']
    inputs += [ROOT / 'standalone' / name for name in [
        'test_clipboard_transfer_dos.py', 'clipboard_transfer_keys.asm', 'clipboard_watch.asm',
        'test_terminal_transfer_dos.py', 'test_terminal_upload_dos.py',
        'test_terminal_ymodem_dos.py', 'test_terminal.py']]
    frozen = {str(path.relative_to(ROOT)): sha(path) for path in inputs}
    selected = [r for r in base.recipes() if r['name'] == a.case]
    assert len(selected) == 1
    result = scope['run_case'](selected[0], 'wide', sha(binary))
    result['checks']['inputs_unchanged'] = frozen == {str(path.relative_to(ROOT)): sha(path) for path in inputs}
    result['passed'] = all(result['checks'].values())
    report = dict(passed=result['passed'], case=a.case, result=result, inputs=frozen,
                  binary_sha256=sha(binary),
                  artifacts={str(path.relative_to(ROOT)): sha(path) for path in output.rglob('*') if path.is_file()},
                  scope='Actual8086 DOS clipboard/UI/UART and independent strict X/YMODEM peers at logical132; real wide replies before selection and after protocol, then keyboard and narrow reply. No stock BBS/audio/physical acceptance.')
    (output / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=report['passed'], checks=result['checks']), indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
