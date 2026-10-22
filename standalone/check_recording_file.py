#!/usr/bin/env python3
"""Host C recorder publication with explicit filesystem/ownership fault models.

No actual DOS filesystem, terminal UI, kernel or modem acceptance is granted.
"""
import argparse
import ctypes as C
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from check_aspect_recorder import Session as Core

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src/aspect'))
from compiler import compile_source
U, P, I = C.c_uint, C.c_void_p, C.c_int
F3 = C.CFUNCTYPE(U, P, P, P)
FW = C.CFUNCTYPE(U, P, I, P, U, P)
FC = C.CFUNCTYPE(U, P, I)
F2 = C.CFUNCTYPE(U, P, P)


class Ops(C.Structure):
    _fields_ = [(name, kind) for name, kind in [('canonical', F3), ('attributes', F3),
        ('create', F3), ('write', FW), ('close', FC), ('rename', F3),
        ('remove', F2), ('reserve', F2), ('release', F2)]]


class Owner(C.Structure):
    _fields_ = [('ops', Ops), ('context', P), ('recorder', Core)] + [(name, U) for name in
        ('state', 'status', 'dos_error', 'close_error', 'cleanup_error', 'publish_error', 'restore_error', 'reservation_error',
         'mode', 'busy', 'claimed', 'stage_owned', 'backup_owned', 'published', 'handle_state', 'sequence', 'directory_length')] + [
        ('handle', I), ('target', C.c_char * 128), ('stage', C.c_char * 13), ('backup', C.c_char * 13)]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    out.mkdir(parents=True)
    inputs = [Path(__file__).resolve(), ROOT / 'standalone/check_aspect_recorder.py',
              ROOT / 'src/recording/file.c', ROOT / 'src/recording/file.h', ROOT / 'src/aspect/recorder.c',
              ROOT / 'src/aspect/recorder.h', ROOT / 'src/aspect/compiler.py']
    frozen = {str(path.relative_to(ROOT)): sha(path) for path in inputs}
    for path in inputs:
        copy = out / 'frozen-source' / path.relative_to(ROOT)
        copy.parent.mkdir(parents=True, exist_ok=True)
        copy.write_bytes(path.read_bytes())
    (out / 'abi.c').write_text('#include "file.h"\nunsigned recording_owner_size(void){return sizeof(recording_file);}\n')
    subprocess.run(['gcc', '-std=c89', '-Wall', '-Wextra', '-Werror', '-Wno-misleading-indentation',
                    '-shared', '-fPIC', '-I' + str(ROOT / 'src/recording'), str(out / 'abi.c'),
                    str(inputs[2]), str(inputs[4]), '-o', str(out / 'file.so')], check=True)
    lib = C.CDLL(str(out / 'file.so'))
    assert lib.recording_owner_size() == C.sizeof(Owner)
    lib.recording_file_begin.argtypes = [P, P, P, P, U, U]
    for name in ('transmit', 'receive'):
        getattr(lib, 'recording_file_' + name).argtypes = [P, P, U]
    for name in ('flush', 'stop', 'cancel', 'cleanup'):
        getattr(lib, 'recording_file_' + name).argtypes = [P]
    lib.recording_file_conflict.argtypes = [P, P]
    cases = []

    class FS:
        def __init__(self):
            self.owner = Owner()
            self.files = {}
            self.handles = {}
            self.foreign = set()
            self.calls = []
            self.errors = []
            self.claim = None
            self.cwd = 'C:\\'
            self.short = 65535
            self.write_error = self.close_error = self.create_error = self.release_error = 0
            self.zero_write = self.over_write = False
            self.rename_errors = {}
            self.remove_error = 0
            self.rename_count = 0
            self.close_releases = False
            self.reenter = False
            self.reentry_results = []
            self.attrs = {}
            self.attr_errors = {}
            self.canonical_error = 0
            self.canonical_override = None
            self.callbacks = []
            for name, kind in Ops._fields_:
                method = getattr(self, name)
                def invoke(*args, method=method):
                    try:
                        return method(*args)
                    except BaseException as exc:
                        self.errors.append(repr(exc))
                        return 5
                self.callbacks.append(kind(invoke))
            self.ops = Ops(*self.callbacks)

        def string(self, p):
            return C.string_at(p).decode('ascii')

        def canonical(self, ctx, name, destination):
            name = self.string(name)
            self.calls.append(('canonical', name))
            if self.canonical_error:
                return self.canonical_error
            name = self.canonical_override or (name if ':\\' in name else self.cwd + name.removeprefix('C:').lstrip('\\'))
            C.memmove(destination, name.encode() + b'\0', len(name) + 1)
            return 0

        def attributes(self, ctx, name, result):
            name = self.string(name)
            self.calls.append(('attributes', name))
            C.cast(result, C.POINTER(U))[0] = self.attrs.get(name, 0)
            return self.attr_errors.get(name, 0 if name in self.files else 2)

        def create(self, ctx, name, result):
            name = self.string(name)
            self.calls.append(('create', name))
            if self.create_error:
                return self.create_error
            if name in self.files:
                return 80
            handle = 5
            while handle in self.handles:
                handle += 1
            self.files[name] = bytearray()
            self.handles[handle] = name
            C.cast(result, C.POINTER(I))[0] = handle
            return 0

        def write(self, ctx, handle, data, count, result):
            self.calls.append(('write', handle, count))
            if self.reenter:
                self.reentry_results.append(lib.recording_file_cancel(C.byref(self.owner)))
            if handle not in self.handles:
                return 6
            actual = 0 if self.zero_write else min(count, self.short)
            if self.write_error:
                actual = min(actual, 3)
            C.cast(result, C.POINTER(U))[0] = count + 1 if self.over_write else actual
            self.files[self.handles[handle]].extend(C.string_at(data, actual))
            return self.write_error

        def close(self, ctx, handle):
            self.calls.append(('close', handle))
            if handle not in self.handles:
                return 6
            if not self.close_error or self.close_releases:
                del self.handles[handle]
            return self.close_error

        def rename(self, ctx, source, destination):
            source, destination = self.string(source), self.string(destination)
            self.calls.append(('rename', source, destination))
            self.rename_count += 1
            if self.rename_count in self.rename_errors:
                return self.rename_errors[self.rename_count]
            if destination in self.files:
                return 80
            if source not in self.files:
                return 2
            self.files[destination] = self.files.pop(source)
            return 0

        def remove(self, ctx, name):
            name = self.string(name)
            self.calls.append(('remove', name))
            if self.remove_error:
                return self.remove_error
            if name in self.handles.values():
                return 5
            if name not in self.files:
                return 2
            del self.files[name]
            return 0

        def reserve(self, ctx, owner):
            self.calls.append(('reserve',))
            if self.claim is not None and self.claim != owner:
                return 2
            if any(lib.recording_file_conflict(owner, C.create_string_buffer(name.encode())) for name in self.foreign):
                return 2
            self.claim = owner
            return 0

        def release(self, ctx, owner):
            self.calls.append(('release',))
            if self.release_error:
                return self.release_error
            if self.claim != owner:
                return 3
            self.claim = None
            return 0

        def begin(self, mode=1, name=b'REC.ASP', timeout=30):
            return lib.recording_file_begin(C.byref(self.owner), C.byref(self.ops), None, C.create_string_buffer(name), mode, timeout)

        def call(self, name, data=None):
            fn = getattr(lib, 'recording_file_' + name)
            if name in ('transmit', 'receive'):
                return fn(C.byref(self.owner), C.create_string_buffer(data), len(data))
            return fn(C.byref(self.owner))

        def sibling(self, name):
            target = bytes(self.owner.target).decode()
            return target[:self.owner.directory_length] + bytes(getattr(self.owner, name)).decode()

        def payload(self, data):
            for at in range(0, len(data), 40):
                assert self.call('transmit', data[at:at+40]) == 0

        def count(self, operation):
            return sum(call[0] == operation for call in self.calls)

    def record(name, fs, expected=None):
        assert not fs.errors, (name, fs.errors)
        if expected is not None:
            assert fs.owner.published and bytes(fs.files['C:\\REC.ASP']).endswith(b'endproc\r\n')
            source = bytes(fs.files['C:\\REC.ASP'])
            compile_source(source.decode('cp437'))
            encoded = re.findall(rb'transmitraw "([A-F0-9]*)"\r\n', source)
            assert bytes.fromhex(b''.join(encoded).decode()) == expected
        item = dict(case=name, passed=True, state=fs.owner.state, status=fs.owner.status,
                    dos_error=fs.owner.dos_error, close_error=fs.owner.close_error,
                    cleanup_error=fs.owner.cleanup_error, publish_error=fs.owner.publish_error,
                    restore_error=fs.owner.restore_error, published=fs.owner.published,
                    reservation_error=fs.owner.reservation_error,
                    handle_state=fs.owner.handle_state, claimed=fs.owner.claimed,
                    stage_owned=fs.owner.stage_owned, backup_owned=fs.owner.backup_owned,
                    files={path: bytes(data).hex() for path, data in fs.files.items()}, calls=fs.calls)
        cases.append(item)

    for label, short in [('new-all-octets', 65535), ('positive-short-writes', 1)]:
        fs = FS();fs.short = short
        assert fs.begin() == 0
        fs.payload(bytes(range(256)))
        assert fs.call('stop') == fs.call('stop') == 0
        assert fs.owner.state == 2 and not fs.claim and fs.count('close') == 1
        assert set(fs.files) == {'C:\\REC.ASP'}
        record(label, fs, bytes(range(256)))
    fs = FS();fs.files['C:\\REC.ASP'] = bytearray(b'ORIGINAL')
    assert fs.begin() == 6 and fs.count('create') == fs.count('close') == 0 and not fs.claim
    assert fs.files['C:\\REC.ASP'] == b'ORIGINAL';record('new-existing-target', fs)
    fs = FS();fs.files['C:\\LPR00001.TMP'] = bytearray(b'KEEP')
    assert fs.begin() == 0 and fs.sibling('stage') == 'C:\\LPR00002.TMP'
    assert fs.call('stop') == 0 and fs.files['C:\\LPR00001.TMP'] == b'KEEP';record('scratch-collision', fs, b'')
    fs = FS();fs.foreign.add('C:\\REC.ASP')
    assert fs.begin() == 2 and fs.count('create') == 0 and fs.count('attributes') == 0;record('open-target-owner', fs)
    fs = FS();fs.foreign.add('C:\\LPR00001.TMP')
    assert fs.begin() == 0 and fs.sibling('stage') == 'C:\\LPR00002.TMP'
    assert fs.call('cancel') == 14 and not fs.files and not fs.claim;record('open-scratch-owner', fs)
    fs = FS();assert fs.begin() == 0;fs.cwd = 'C:\\OTHER\\'
    fs.payload(b'FIXED');assert fs.call('stop') == 0;record('fixed-canonical-directory', fs, b'FIXED')
    fs = FS();fs.reenter = True
    assert fs.begin() == 0;fs.payload(b'REENTRY');assert fs.call('stop') == 0
    assert fs.reentry_results and set(fs.reentry_results) == {2};record('reentrant-cancel-blocked', fs, b'REENTRY')
    for label, field, value in [('partial-write-error', 'write_error', 112),
                                ('zero-progress', 'zero_write', True), ('overreported-write', 'over_write', True)]:
        fs = FS();setattr(fs, field, value)
        assert fs.begin() == 8 and fs.count('close') == 1 and not fs.files and not fs.claim
        count = len(fs.calls);assert fs.call('stop') == 8 and len(fs.calls) == count;record(label, fs)
    for label, released in [('uncertain-close-retains-handle', False), ('uncertain-close-kernel-released', True)]:
        fs = FS();fs.close_error = 6;fs.close_releases = released
        assert fs.begin() == 0 and fs.call('stop') == 9
        assert fs.owner.handle_state == 2 and fs.owner.claimed and fs.owner.stage_owned
        assert fs.begin() == 13
        assert fs.call('cleanup') == 9 and fs.count('close') == 1 and fs.count('remove') == 0
        record(label, fs)
    fs = FS();fs.write_error = 112;fs.close_error = 6
    assert fs.begin() == 8 and fs.owner.dos_error == 112 and fs.owner.close_error == 6
    assert fs.call('cancel') == 8 and fs.count('close') == 1 and fs.owner.stage_owned;record('write-primary-close-secondary', fs)
    fs = FS();fs.create_error = 5
    assert fs.begin() == 7 and not fs.claim and fs.count('close') == 0 and not fs.files;record('create-error', fs)
    fs = FS();fs.files['C:\\REC.ASP'] = bytearray(b'ORIGINAL');fs.write_error = 112
    assert fs.begin(mode=2) == 8 and fs.files == {'C:\\REC.ASP': bytearray(b'ORIGINAL')} and not fs.claim
    record('replace-write-error-preserves-original', fs)
    fs = FS();fs.files['C:\\REC.ASP'] = bytearray(b'ORIGINAL');fs.attrs['C:\\REC.ASP'] = 1
    assert fs.begin(mode=2) == 1 and fs.count('create') == 0 and not fs.claim
    assert fs.files['C:\\REC.ASP'] == b'ORIGINAL';record('readonly-replacement-rejected', fs)
    fs = FS();fs.canonical_error = 15
    assert fs.begin() == 4 and fs.count('reserve') == fs.count('create') == 0;record('canonical-error', fs)
    fs = FS();fs.attr_errors['C:\\REC.ASP'] = 5
    assert fs.begin() == 5 and not fs.claim and not fs.files;record('attribute-error', fs)
    fs = FS();assert fs.begin() == 0;fs.payload(b'pending')
    assert fs.call('cancel') == 14 and fs.count('close') == 1 and not fs.files and not fs.claim;record('cancel-unpublished', fs)
    fs = FS();assert fs.begin() == 0;fs.files['C:\\REC.ASP'] = bytearray(b'RACED IN')
    assert fs.call('stop') == 6 and fs.owner.stage_owned and fs.files['C:\\REC.ASP'] == b'RACED IN'
    assert fs.call('cleanup') == 6 and set(fs.files) == {'C:\\REC.ASP'} and not fs.claim;record('new-target-race', fs)
    fs = FS();assert fs.begin() == 0;fs.rename_errors = {1: 5}
    assert fs.call('stop') == 10 and fs.owner.stage_owned and fs.owner.claimed and not fs.owner.published
    assert fs.call('cleanup') == 10 and not fs.files and not fs.claim;record('new-publish-error-explicit-cleanup', fs)
    for label, errors, expected_restore in [('replace-success', {}, 0), ('replace-backup-rename-error', {1: 5}, 0),
                                           ('replace-publish-error-restored', {2: 5}, 0), ('replace-restore-error', {2: 5, 3: 6}, 6)]:
        fs = FS();fs.files['C:\\REC.ASP'] = bytearray(b'ORIGINAL')
        assert fs.begin(mode=2) == 0 and fs.files['C:\\REC.ASP'] == b'ORIGINAL'
        fs.payload(b'NEW');fs.rename_errors = errors
        status = fs.call('stop')
        assert status == (10 if errors else 0) and fs.owner.restore_error == expected_restore
        assert fs.count('close') == 1
        if not errors:
            assert set(fs.files) == {'C:\\REC.ASP'} and not fs.claim;record(label, fs, b'NEW')
        elif expected_restore:
            assert fs.owner.backup_owned and fs.owner.stage_owned and fs.claim and 'C:\\REC.ASP' not in fs.files
            assert fs.files[fs.sibling('backup')] == b'ORIGINAL'
            count = len(fs.calls);assert fs.call('cleanup') == 10 and len(fs.calls) == count;record(label, fs)
        else:
            assert fs.files['C:\\REC.ASP'] == b'ORIGINAL' and fs.owner.stage_owned and fs.claim
            assert fs.call('cleanup') == 10 and set(fs.files) == {'C:\\REC.ASP'} and not fs.claim;record(label, fs)
    fs = FS();fs.files['C:\\REC.ASP'] = bytearray(b'ORIGINAL');assert fs.begin(mode=2) == 0
    fs.payload(b'NEW');fs.remove_error = 5
    assert fs.call('stop') == 11 and fs.owner.published and fs.owner.backup_owned and fs.claim
    fs.remove_error = 0;assert fs.call('cleanup') == 11 and fs.owner.published and not fs.claim
    assert set(fs.files) == {'C:\\REC.ASP'};record('published-backup-cleanup-error', fs, b'NEW')
    fs = FS();assert fs.begin() == 0;fs.release_error = 5
    assert fs.call('stop') == 12 and fs.owner.published and fs.owner.claimed
    fs.release_error = 0;assert fs.call('cleanup') == 12 and not fs.claim;record('release-error-after-publication', fs, b'')
    fs = FS();assert fs.begin() == 0;fs.remove_error = 5
    assert fs.call('cancel') == 14 and fs.owner.stage_owned and fs.owner.cleanup_error == 5
    fs.remove_error = 0;assert fs.call('cleanup') == 14 and not fs.claim and not fs.files;record('cancel-cleanup-error', fs)
    fs = FS();assert fs.begin() == 0
    # Declared counter-boundary fixture; no claim of an actual4GiB stream.
    fs.owner.recorder.received_bytes = 0xffffffff
    assert fs.call('receive', b'A') == 15 and fs.owner.dos_error == 0
    assert not fs.claim and not fs.files and fs.count('close') == 1
    record('counter-limit-has-no-fabricated-DOS-error', fs)
    fs = FS()
    for name in (b'', b'CON.ASP', b'CLOCK$.ASP', b'COM1.ASP', b'..\\REC.ASP', b'ABCDEFGHI.ASP', b'REC.ASXX', b'A*B.ASP'):
        old = bytes(fs.owner);assert fs.begin(name=name) == 1 and bytes(fs.owner) == old and not fs.calls
    for mode, timeout in [(0, 30), (3, 30), (1, 0), (1, 32768)]:
        old = bytes(fs.owner);assert fs.begin(mode=mode, timeout=timeout) == 1 and bytes(fs.owner) == old and not fs.calls
    assert fs.call('cleanup') == 0 and fs.owner.state == 0
    assert fs.begin() == 0;old = bytes(fs.owner);count = len(fs.calls)
    assert fs.call('transmit', b'X' * 41) == 1 and fs.call('receive', b'X' * 17) == 1
    assert fs.begin() == 2 and bytes(fs.owner) == old and len(fs.calls) == count
    assert fs.call('cancel') == 14;record('argument-and-active-state-guards', fs)
    for name, digest in frozen.items():
        assert sha(ROOT / name) == sha(out / 'frozen-source' / name) == digest, name
    result = dict(passed=True, host_model_only=True, case_count=len(cases), cases=cases, inputs=frozen,
                  library_sha256=sha(out / 'file.so'), scope=__doc__)
    with (out / 'result.json').open('x') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=True, host_model_only=True, case_count=len(cases))))


if __name__ == '__main__':
    main()
