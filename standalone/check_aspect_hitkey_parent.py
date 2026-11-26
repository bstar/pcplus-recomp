#!/usr/bin/env python3
"""Linked HITKEY parent latch/auth/native peek replay with explicit BIOS/admission models."""
import argparse
import json
from pathlib import Path
import re
import struct

from unicorn import UC_HOOK_MEM_READ
from unicorn.x86_const import *
from check_aspect_keyboard import expected
from check_aspect_hitkey_native import PEEK, READ
from check_terminal_query_parent import (Parent, ROOT, CHILD_DS, CHILD_PSP,
    CLIENT, sha, child_handshake)

RAW = (0, 1, 14, 15, 127, 128, 255, 256, 0x011b, 0x0e08, 0x0e7f,
       0x1c0d, 0x1c0a, 0x3729, 0x372a, 0x3920, 0x4800, 0x4be0,
       0xe061, 0xe000, 0xff00, 0xffff, 0x8001)


class HitkeyParent(Parent):
    def __init__(self, product):
        self.native = {}
        self.entries = []
        self.mode, self.raw, self.available = 0, 0, False
        self.bios_calls = 0
        self.cleanup_model = False
        super().__init__(product, capability=25)
        lengths = {'aspect_hitkey_native': 8, 'terminal_hitkey_sample': 4,
                   'keyboard_peek': 22, 'keyboard_normalize_bios': 43,
                   'keyboard_bios_peek': 21}
        self.native = {self.symbols[n]: n for n in lengths}
        self.allowed += [(self.symbols[n], self.symbols[n]+length)
                         for n, length in lengths.items()]
        for n in ('keyboard_read', 'keyboard_poll', 'keyboard_bios_read',
                  'keyboard_queue_read', 'keyboard_read_extended'):
            self.forbidden[self.symbols[n]] = n
        self.protected = [(self.symbols[n], size, n) for n, size in (
            ('keyboard_queue_peek', 12), ('keyboard_queue_values', 12),
            ('keyboard_queue_count', 2), ('keyboard_queue_index', 2),
            ('keyboard_queue_active', 2), ('keyboard_bios_mode', 1))]
        self.protected.append((0x400, 256, 'BIOS-data-area'))
        self.uc.mem_write(0x400, bytes((i*43+19)&255 for i in range(256)))
        self.uc.mem_write(self.symbols['keyboard_queue_peek'], struct.pack('<6H', *PEEK))
        self.uc.mem_write(self.symbols['keyboard_queue_values'], struct.pack('<6H', *READ))
        self.table_reads = []
        at = self.symbols['keyboard_queue_peek']
        self.uc.hook_add(UC_HOOK_MEM_READ, self.table_read, None, at, at+11)
        self.stage()

    def code(self, u, address, size, unused):
        if self.cleanup_model:
            cleanup = {'terminal_script_field': True, 'terminal_script_window_close': False,
                       'terminal_break_ui': True, '_compiler_overlay_retire': True}
            for name, far in cleanup.items():
                if address == self.symbols[name]:
                    self.events.append(('cleanup-only-model', name))
                    self.ret(0, far=far)
                    return
        if address in self.native:
            self.entries.append(self.native[address])
        super().code(u, address, size, unused)

    def interrupt(self, u, number, unused):
        if number != 0x16:
            return super().interrupt(u, number, unused)
        function = u.reg_read(UC_X86_REG_AH)
        assert self.mode in (0, 16) and function == self.mode+1, (
            'consuming or unexpected BIOS keyboard operation', function)
        self.bios_calls += 1
        flags = u.reg_read(UC_X86_REG_EFLAGS)
        u.reg_write(UC_X86_REG_EFLAGS, flags & ~0x40 if self.available else flags | 0x40)
        u.reg_write(UC_X86_REG_AX, self.raw if self.available else 0x6b31)
        self.events.append(('non-consuming-BIOS16-model', function))

    def write(self, u, access, address, size, value, unused):
        super().write(u, access, address, size, value, unused)
        if self.phase != 'query':
            return
        for at, length, name in getattr(self, 'protected', ()):
            assert not (address < at+length and address+size > at), ('peek mutated input', name)

    def table_read(self, u, access, address, size, value, unused):
        self.table_reads.append((address-self.symbols['keyboard_queue_peek'], size))

    def stage(self, raw=0, available=True, mode=0, count=0, index=0):
        self.raw, self.available, self.mode = raw, available, mode
        self.put('keyboard_bios_mode', mode, 1)
        self.put('keyboard_queue_count', count)
        self.put('keyboard_queue_index', index)
        self.put('keyboard_queue_active', 0x1234)

    def request(self, *args, **kwargs):
        self.entries, self.table_reads = [], []
        self.bios_calls = 0
        before = [(at, bytes(self.uc.mem_read(at, size)))
                  for at, size, _ in getattr(self, 'protected', ())]
        available = self.available
        result = super().request(*args, **kwargs)
        assert self.available == available, 'BIOS model key was consumed'
        assert all(bytes(self.uc.mem_read(at, len(data))) == data for at, data in before)
        return result

    def sample(self, want, queued=False, index=0):
        assert self.request(30, 0) == 0xf000 | (want & 255)
        assert self.get('render_hitkey_pending') == 1
        assert self.get('render_hitkey_word') == want
        assert self.entries == ['terminal_hitkey_sample', 'aspect_hitkey_native', 'keyboard_peek'] + (
            [] if queued else ['keyboard_bios_peek']) + ['keyboard_normalize_bios'], self.entries
        assert self.bios_calls == (0 if queued else 1)
        assert self.table_reads == ([(2*index, 2)] if queued else [])
        assert sum(n == 'actual-client-auth' for n, _ in self.events) == 1
        assert sum(n == 'pure-admission-model' for n, _ in self.events) == 1

    def high(self, want):
        assert self.request(31, 0) == 0xf000 | (want >> 8)
        assert self.get('render_hitkey_pending') == 0
        assert not self.entries and not self.table_reads and self.bios_calls == 0
        assert sum(n == 'actual-client-auth' for n, _ in self.events) == 1
        assert sum(n == 'pure-admission-model' for n, _ in self.events) == 1

    def far_lifecycle(self, name):
        self.cleanup_model = True
        u = self.uc
        sp = self.offset('terminal_stack_top')-64
        u.mem_write(self.data_base+sp, struct.pack('<HH', self.return_offset, self.code_segment))
        for reg, value in ((UC_X86_REG_CS, self.aspect_segment), (UC_X86_REG_DS, self.ds),
                          (UC_X86_REG_SS, self.ds), (UC_X86_REG_SP, sp), (UC_X86_REG_EFLAGS, 0x202)):
            u.reg_write(reg, value)
        self.returned = False
        u.emu_start(self.symbols[name], 0, count=100000)
        assert self.returned and u.reg_read(UC_X86_REG_SP) == sp+4
        self.cleanup_model = False
        return u.reg_read(UC_X86_REG_AX)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--product', type=Path, required=True)
    p.add_argument('--child', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    product, child, out = a.product.resolve(), a.child.resolve(), a.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    manifest = json.loads((product/'manifest.json').read_text())
    assert manifest['experimental_hitkey_parent'] and sha(product/'TERMINAL.EXE') == manifest['binary_sha256']
    relevant = ['src/terminal/aspect_renderer.asm', 'src/aspect/hitkey.asm',
        'reconstruction/keyboard/core.asm', 'src/aspect/resident_bridge.asm',
        'src/aspect/renderer_client.c', 'src/aspect/resident_render.h']
    for name in relevant:
        assert manifest['sources'][name] == sha(ROOT/name), ('stale parent source', name)
    cm = json.loads((child/'manifest.json').read_text())
    assert cm['experimental_hitkey'] and sha(child/'ASPECT.EXE') == cm['binary_sha256']
    match = re.search(r'^([0-9a-f]{4}):[0-9a-f]{4}[*+ ]+\s+render_body\s*$',
                      (product/'terminal.map').read_text(), re.M | re.I)
    assert match
    Parent._aspect_segment = 0x1000+int(match[1], 16)
    cases = []
    m = HitkeyParent(product)
    for mode in (0, 16):
        for raw in RAW:
            m.stage(raw=raw, mode=mode)
            want = expected(raw or 0x100)
            m.sample(want)
            m.high(want)
            cases.append(dict(case='BIOS-full-word', mode=mode, raw=raw, value=want, passed=True))
        m.stage(raw=0x4800, mode=mode, available=False)
        m.sample(0)
        m.high(0)
        cases.append(dict(case='BIOS-empty-ZF', mode=mode, passed=True))
    for mode in sorted(set(range(256))-{0, 16}):
        m.stage(raw=0x4800, mode=mode)
        m.put('render_hitkey_word', 0xbeef)
        assert m.request(30, 0) == 7
        assert not m.entries and not m.table_reads and not m.bios_calls
        assert not m.get('render_hitkey_pending') and m.get('render_hitkey_word') == 0xbeef
        cases.append(dict(case='invalid-BIOS-mode-refuses-before-peek', mode=mode, result=7, passed=True))
    for index, raw in enumerate(PEEK):
        m.stage(mode=255, count=1, index=index)
        m.sample(expected(raw), queued=True, index=index)
        m.high(expected(raw))
        cases.append(dict(case='mouse-priority-ignores-invalid-BIOS-mode', mode=255, index=index, passed=True))
    for queued in (False, True):
        m.stage(raw=0xe061, count=int(queued))
        want = expected(PEEK[0]) if queued else 0xe061
        m.sample(want, queued=queued)
        m.stage(raw=0xff00, mode=255, count=0, index=65535)
        m.high(want)
        assert m.request(30, 0) == 7 and not m.entries and not m.bios_calls
        assert not m.get('render_hitkey_pending')
        cases.append(dict(case='cached-high-ignores-later-invalid-BIOS-mode', queued=queued, mode=255, passed=True))
    for count in (1, 6, 65535):
        for index, raw in enumerate(PEEK):
            m.stage(raw=0xe061, count=count, index=index)
            m.sample(expected(raw), queued=True, index=index)
            m.high(expected(raw))
            cases.append(dict(case='mouse-priority-no-consume', count=count, index=index, passed=True))
    for raw in RAW:
        m.uc.mem_write(m.symbols['keyboard_queue_peek']+10, struct.pack('<H', raw))
        m.stage(count=1, index=5)
        m.sample(expected(raw), queued=True, index=5)
        m.high(expected(raw))
        cases.append(dict(case='mouse-full-word', raw=raw, value=expected(raw), passed=True))
    for index in (6, 7, 255, 256, 65535):
        m.stage(count=1, index=index)
        assert m.request(30, 0) == 7 and not m.entries and not m.table_reads
        assert not m.get('render_hitkey_pending')
        cases.append(dict(case='corrupt-mouse-index', index=index, passed=True))
    for index in (6, 65535):
        m.stage(raw=0x4800, count=0, index=index)
        m.sample(0x4800)
        m.high(0x4800)
        cases.append(dict(case='empty-mouse-ignores-index', index=index, passed=True))
    for source in ('BIOS-key-change', 'BIOS-empty-key-arrival', 'mouse-change', 'mouse-arrival'):
        m = HitkeyParent(product)
        empty = source == 'BIOS-empty-key-arrival'
        m.stage(raw=0x4be0, available=not empty, count=1 if source == 'mouse-change' else 0)
        old = expected(PEEK[0]) if source == 'mouse-change' else (0 if empty else 0x4be0)
        m.sample(old, queued=source == 'mouse-change')
        m.uc.mem_write(m.symbols['keyboard_queue_peek']+2, struct.pack('<H', 0xe061))
        m.stage(raw=0xff00, count=1 if source.startswith('mouse-') else 0, index=1)
        m.high(old)
        new = 0xe061 if source.startswith('mouse-') else 0xff00
        m.sample(new, queued=source.startswith('mouse-'), index=1)
        m.high(new)
        cases.append(dict(case='one-observation-pair', arrival=source, first=old, next=new, passed=True))
    m = HitkeyParent(product)
    m.stage(raw=0x4800)
    assert m.request(31, 0) == 10 and not m.entries
    m.sample(0x4800)
    assert m.request(30, 0) == 10 and not m.get('render_hitkey_pending') and not m.entries
    m.sample(0x4800)
    m.high(0x4800)
    cases.append(dict(case='high-needs-pending-and-overlap-retires', passed=True))
    for operation in (30, 31):
        for payload in (1, 255, 256, 0xffff):
            m = HitkeyParent(product)
            m.stage(raw=0x4800)
            m.sample(0x4800)
            assert m.request(operation, payload) == 7
            assert not m.get('render_hitkey_pending') and not m.entries
            cases.append(dict(case='payload-reject-retires', operation=operation, payload=payload, passed=True))
    for owner in ('terminal_script_field_active', 'terminal_script_window_active', 'terminal_script_confirm_active'):
        m = HitkeyParent(product)
        m.stage(raw=0xe061)
        m.put(owner, 1)
        m.sample(0xe061)
        m.high(0xe061)
        assert m.get(owner) == 1
        cases.append(dict(case='read-only-owner-compatible', owner=owner, passed=True))
    controls = ['inactive-program', 'wrong-kind', 'detached', 'wrong-PSP', 'wrong-DS',
        'bad-magic', 'bad-token', 'changed-callback', 'bad-MCB-signature', 'bad-MCB-owner',
        'empty-MCB', 'callback-outside', 'descriptor-token', 'descriptor-entry', 'descriptor-segment',
        'client-version24', 'descriptor-version24', 'returned-UART', 'program-owned', 'admission-refusal']
    for control in controls:
        m = HitkeyParent(product)
        m.stage(raw=0x4800)
        m.sample(0x4800)
        kwargs = {}
        if control == 'inactive-program':m.put('terminal_program_active', 0)
        elif control == 'wrong-kind':m.put('terminal_program_kind', 3)
        elif control == 'detached':m.put('render_attached', 0)
        elif control == 'wrong-PSP':m.current_psp = CHILD_PSP+1
        elif control == 'wrong-DS':kwargs.update(ds=CHILD_DS+1, ss=CHILD_DS+1)
        elif control == 'bad-magic':m.client_words[0] ^= 1;m.publish_client()
        elif control == 'bad-token':m.client_words[2] ^= 1;m.publish_client()
        elif control == 'changed-callback':m.client_words[3] += 1;m.publish_client()
        elif control == 'bad-MCB-signature':m.uc.mem_write((CHILD_PSP-1)*16, b'Q')
        elif control == 'bad-MCB-owner':m.uc.mem_write((CHILD_PSP-1)*16+1, b'\x34\x12')
        elif control == 'empty-MCB':m.uc.mem_write((CHILD_PSP-1)*16+3, b'\0\0')
        elif control == 'callback-outside':m.client_words[3:] = [0, 0xa000];m.publish_client()
        elif control == 'descriptor-token':m.put('_script_render_token', m.get('_script_render_token')^1)
        elif control == 'descriptor-entry':m.put('_script_render_offset', m.get('_script_render_offset')^1)
        elif control == 'descriptor-segment':m.put('_script_render_segment', m.get('_script_render_segment')^1)
        elif control == 'client-version24':m.client_words[1] = 24;m.publish_client()
        elif control == 'descriptor-version24':m.put('_script_render_version', 24)
        elif control == 'returned-UART':m.uc.mem_write(m.symbols['_script_handoff']+22, b'\1\0')
        elif control == 'program-owned':m.put('render_program_owned', 1)
        elif control == 'admission-refusal':m.admit_result = 3
        result = 14 if control == 'returned-UART' else 3 if control == 'admission-refusal' else 10
        assert m.request(31, 0, **kwargs) == result, control
        assert not m.get('render_hitkey_pending') and not m.entries and not m.bios_calls, control
        cases.append(dict(case='high-reauthenticates-and-retires', control=control, result=result, passed=True))
    m = HitkeyParent(product)
    m.stage(raw=0x4800)
    m.sample(0x4800)
    assert m.request(31, 0, ss=CHILD_DS+1, flags=0x443) == 0xfffc
    assert m.get('render_hitkey_pending') == 1 and not m.entries
    m.high(0x4800)
    cases.append(dict(case='broker-DS-ne-SS-refusal-does-not-enter-body-or-retire-owner', passed=True))
    for operation, payload in ((29, 0), (0, CLIENT), (32, 0)):
        m = HitkeyParent(product)
        m.stage(raw=0x4800)
        m.sample(0x4800)
        m.request(operation, payload)
        assert not m.get('render_hitkey_pending')
        assert m.request(31, 0) == 10
        cases.append(dict(case='other-body-operation-disarms', operation=operation, passed=True))
    for lifecycle in ('END-BEGIN', 'prepare', 'revoke'):
        m = HitkeyParent(product)
        m.stage(raw=0x4800)
        m.sample(0x4800)
        if lifecycle == 'END-BEGIN':
            m.cleanup_model = True
            assert m.request(2, 0) == 0xe000
            m.cleanup_model = False
            assert not m.get('render_attached') and not m.get('render_hitkey_pending')
            m.put('render_hitkey_pending', 1)
            assert m.request(0, CLIENT) == 0
            assert not m.get('render_hitkey_pending')
        else:
            name = 'terminal_render_prepare' if lifecycle == 'prepare' else 'terminal_render_revoke'
            assert m.far_lifecycle(name) == 0
            assert not m.get('render_attached') and not m.get('render_hitkey_pending')
        cases.append(dict(case='lifecycle-disarms', operation=lifecycle, passed=True))
    handshake = child_handshake(child, capability=25)
    out.mkdir(parents=True)
    sources = {n: sha(ROOT/n) for n in relevant+['standalone/check_aspect_hitkey_parent.py',
        'standalone/check_terminal_query_parent.py', 'standalone/check_aspect_keyboard.py',
        'standalone/check_aspect_hitkey_native.py', 'standalone/dos_image.py',
        'standalone/check_aspect_render_client.py', 'standalone/check_uart.py']}
    report = dict(passed=True, cases=cases, handshake_cases=handshake,
        parent_sha256=sha(product/'TERMINAL.EXE'), parent_manifest_sha256=sha(product/'manifest.json'),
        child_sha256=sha(child/'ASPECT.EXE'), child_manifest_sha256=sha(child/'manifest.json'),
        sources=sources, original_inputs=[],
        scope=__doc__+' Actual prepare/BEGIN/bridge/per-request authentication, native getter8bytes, '
        'far adapter4bytes, native queue peek22bytes, normalizer43bytes and BIOS peek21bytes execute. '
        'Low30 samples once, high31 returns and retires the cached high byte; key/mouse arrival '
        'between halves cannot tear the observation. BIOS INT16 is explicitly non-consuming AH1/11 '
        'with controlled ZF/raw word; pure admission, setup/cleanup UI retirement and DOS62 PSP are '
        'modeled. All254 invalid BIOS-mode bytes refuse before INT16 when no mouse word is '
        'queued; a valid queued word and an already-latched high half bypass that mode safely. '
        'This maintained admission leaves the recovered native flat getter unchanged. '
        'Input queue/BDA/video/source WORDs and all bridge caller registers/FLAGS/SP are '
        'checked. Unexpected output/parser/transport/callback or consuming keyboard paths reject. '
        'Body errors retire the latch; a broker DS!=SS refusal occurs before the application body '
        'and intentionally leaves owner state for a subsequent fully authenticated request. '
        'Only capability25 reaches the child handshake controlled ABSENT UART boundary;24 rejects. '
        'No real IRQ, DOS EXEC, actual BIOS implementation, UART, hardware/BBS or full ASPECT claim.')
    (out/'result.json').write_text(json.dumps(report, indent=2)+'\n')
    print('PASS linked HITKEY parent', len(cases), 'cases;', len(handshake), 'child handshake cases')


if __name__ == '__main__':
    main()
