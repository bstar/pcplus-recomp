#!/usr/bin/env python3
"""Linked parent op29/bridge/auth replay with explicitly controlled admission."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

from unicorn import UC_HOOK_CODE, UC_HOOK_INTR, UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
from dos_image import DosImage

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ['screen_cursor_column', 'screen_cursor_row', 'screen_columns', 'ui_window_rows',
          'attributes_bold_value', 'attributes_preset_value', 'attributes_normal_value',
          'attributes_reverse_value', 'attributes_underline_value']
GETTERS = ['aspect_terminal_'+name for name in ('col', 'row', 'cols', 'rows',
           'bold', 'dim', 'norm', 'rev', 'uline')]
WORDS = (0, 1, 14, 15, 127, 128, 255, 256, 0x1234, 0x7fff, 0x8000, 0xff00, 0xffff)
CHILD_PSP, CHILD_DS, CLIENT, CHILD_STOP = 0x9000, 0x9200, 0x1000, 0xfd00


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Parent(DosImage):
    def __init__(self, product, capability=24):
        super().__init__(product/'TERMINAL.EXE', product/'terminal.map')
        self.phase = 'setup'
        self.current_psp = CHILD_PSP
        self.admit_result = 0
        self.events = []
        self.getters = []
        self.stopped = False
        self.completed = 0
        self.callback = [0x120, CHILD_PSP]
        self.parent_psp = 0x0ff0
        self.put('process_psp', self.parent_psp)
        self.put('terminal_program_active', 1)
        self.put('terminal_program_kind', 4)
        self.uc.mem_write((CHILD_PSP-1)*16, b'M'+struct.pack('<HH', CHILD_PSP, 0x1000)+b'\0'*11)
        self.uc.mem_write(0xb8000, bytes((i*37+11)&255 for i in range(8000)))
        self.allowed = [
            (self.symbols['terminal_render_prepare'], self.symbols['attribute_geometry_admit_far']),
            (self.symbols['resident_bridge_caller_ds'], self.symbols['resident_bridge_busy']),
            (self.symbols['_aspect_render_client_admit'], self.symbols['_aspect_render_admit']),
            (self.symbols['_compiler_overlay_loaned'], self.symbols['_compiler_overlay_loaned']+5),
            *[(self.symbols[name], self.symbols[name]+4) for name in GETTERS],
        ]
        banned = ['resident_bridge_callback', 'resident_bridge_abort',
            'terminal_render_failure_notice', 'terminal_script_window_poll',
            'terminal_render_unsupported', 'terminal_render_typed_abort',
            'terminal_render_read', 'terminal_render_read_now', 'terminal_render_unread',
            'terminal_render_send', 'terminal_render_poll', 'terminal_render_control',
            'terminal_render_command', 'terminal_render_set_modes',
            'terminal_render_reset_modes', 'terminal_render_string']
        self.forbidden = {self.symbols[name]: name for name in banned}
        self.uc.hook_add(UC_HOOK_CODE, self.code)
        self.uc.hook_add(UC_HOOK_INTR, self.interrupt)
        self.uc.hook_add(UC_HOOK_MEM_WRITE, self.write)
        assert self.far_prepare() == 0
        assert self.get('_script_render_version') == capability
        self.client_words = [0x5243, capability, self.get('_script_render_token'), *self.callback]
        self.publish_client()
        assert self.request(0, CLIENT) == 0
        self.phase = 'query'
        self.events.clear()

    def publish_client(self):
        self.uc.mem_write(CHILD_DS*16+CLIENT, struct.pack('<5H', *self.client_words))

    def ret(self, value, far=False):
        u = self.uc
        sp = u.reg_read(UC_X86_REG_SP)
        segment = u.reg_read(UC_X86_REG_SS)
        words = struct.unpack('<2H' if far else '<H', u.mem_read(segment*16+sp, 4 if far else 2))
        u.reg_write(UC_X86_REG_AX, value)
        if far:
            u.reg_write(UC_X86_REG_CS, words[1])
        u.reg_write(UC_X86_REG_IP, words[0])
        u.reg_write(UC_X86_REG_SP, sp+(4 if far else 2))

    def code(self, u, address, size, unused):
        if address == CHILD_PSP*16+CHILD_STOP:
            self.stopped = True
            u.emu_stop()
            return
        if address == self.code_base+self.return_offset:
            return  # DosImage's separate return sentinel hook stops prepare.
        assert address not in self.forbidden, ('unexpected callback/output/poll', self.forbidden.get(address))
        if address == self.symbols['_aspect_render_admit']:
            self.events.append(('pure-admission-model', u.reg_read(UC_X86_REG_BX)))
            # Watcom callers must not assume BX survives this C boundary.
            u.reg_write(UC_X86_REG_BX, 0xbad5)
            self.ret(self.admit_result)
            return
        if address == self.symbols['terminal_script_field']:
            assert self.phase == 'setup' and u.reg_read(UC_X86_REG_AX) == 5 and u.reg_read(UC_X86_REG_BX) == 1
            self.events.append(('setup-field-retirement-model', 0))
            self.ret(0, far=True)
            return
        assert any(begin <= address < end for begin, end in self.allowed), ('unexpected external instruction', hex(address))
        if address in [self.symbols[name] for name in GETTERS]:
            self.getters.append(GETTERS[[self.symbols[name] for name in GETTERS].index(address)])
        if address == self.symbols['_aspect_render_client_admit']:
            self.events.append(('actual-client-auth', 0))
        if self.phase == 'query' and u.reg_read(UC_X86_REG_EFLAGS)&0x200:
            assert u.reg_read(UC_X86_REG_DS) == u.reg_read(UC_X86_REG_SS), ('IF-visible DS/SS mismatch', hex(address))

    def interrupt(self, u, number, unused):
        assert number == 0x21 and u.reg_read(UC_X86_REG_AH) == 0x62, ('unexpected DOS/BIOS service', number)
        self.events.append(('DOS62-current-PSP-model', self.current_psp))
        u.reg_write(UC_X86_REG_BX, self.current_psp)

    def write(self, u, access, address, size, value, unused):
        if self.phase != 'query':
            return
        assert not (address < 0xb8000+8000 and address+size > 0xb8000), 'Query wrote video'
        for name in FIELDS:
            at = self.symbols[name]
            assert not (address < at+2 and address+size > at), ('Query mutated source WORD', name)

    def far_prepare(self):
        u = self.uc
        body_seg = self.aspect_segment
        sp = self.offset('terminal_stack_top')-64
        u.mem_write(self.data_base+sp, struct.pack('<HH', self.return_offset, self.code_segment))
        for reg, value in ((UC_X86_REG_CS, body_seg), (UC_X86_REG_DS, self.ds),
                (UC_X86_REG_SS, self.ds), (UC_X86_REG_SP, sp), (UC_X86_REG_EFLAGS, 0x202)):
            u.reg_write(reg, value)
        self.returned = False
        u.emu_start(self.symbols['terminal_render_prepare'], 0, count=100000)
        assert self.returned and u.reg_read(UC_X86_REG_SP) == sp+4
        return u.reg_read(UC_X86_REG_AX)

    @property
    def aspect_segment(self):
        # The actual relocated render descriptor is populated by prepare; the
        # map's symbol physical address alone admits many segment aliases.
        return self._aspect_segment

    def request(self, operation, payload, flags=0x643, ds=None, ss=None):
        u = self.uc
        ds = CHILD_DS if ds is None else ds
        ss = ds if ss is None else ss
        sp = 0x7000
        frame = struct.pack('<HH', CHILD_STOP, CHILD_PSP)
        u.mem_write(ss*16+sp, frame+b'RETURN-CANARY')
        registers = {UC_X86_REG_BX: payload, UC_X86_REG_CX: 0x1357,
            UC_X86_REG_DX: 0x2468, UC_X86_REG_SI: 0x369c, UC_X86_REG_DI: 0x47ad,
            UC_X86_REG_BP: 0x58be, UC_X86_REG_ES: 0x6789,
            UC_X86_REG_DS: ds, UC_X86_REG_SS: ss}
        for reg, value in registers.items():
            u.reg_write(reg, value)
        u.reg_write(UC_X86_REG_CS, self.aspect_segment)
        u.reg_write(UC_X86_REG_SP, sp)
        u.reg_write(UC_X86_REG_AX, operation)
        u.reg_write(UC_X86_REG_EFLAGS, flags)
        before_flags = u.reg_read(UC_X86_REG_EFLAGS)
        self.events.clear()
        self.getters.clear()
        self.stopped = False
        u.emu_start(self.symbols['resident_bridge_entry'], 0, count=100000)
        assert self.stopped, ('bridge did not return', operation, payload)
        assert u.reg_read(UC_X86_REG_SP) == sp+4
        assert u.reg_read(UC_X86_REG_EFLAGS) == before_flags
        for reg, value in registers.items():
            assert u.reg_read(reg) == value, ('bridge ABI', reg, value, u.reg_read(reg))
        assert bytes(u.mem_read(ss*16+sp, len(frame)+13)) == frame+b'RETURN-CANARY'
        self.completed += 1
        return u.reg_read(UC_X86_REG_AX)


def child_handshake(child, capability=24):
    """Actual linked descriptor/client validation ending at a controlled absent UART."""
    handshake = []
    import check_aspect_render_client as fixture
    child = child.resolve()
    child_manifest = json.loads((child/'manifest.json').read_text())
    assert sha(child/'ASPECT.EXE') == child_manifest['binary_sha256']
    assert child_manifest.get('experimental_terminal_builtins')
    fixture.q.BINARY, fixture.q.MAP = child/'ASPECT.EXE', child/'ASPECT.map'
    listing = fixture.q.MAP.read_text()
    stack = re.search(r'^STACK\s+STACK\s+DGROUP\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)', listing, re.M|re.I)
    code = re.search(r'^_TEXT\s+CODE\s+\S+\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)', listing, re.M|re.I)
    assert stack and code

    class Child(fixture.Client):
        def __init__(self):
            super().__init__()
            self.low = self.base+int(stack[1],16)*16+int(stack[2],16)-self.data_base
            self.top = self.low+int(stack[3],16)
            self.put('__STACKLOW', self.low);self.put('__STACKTOP', self.top)
            self.option = self.low+2304
            self.uc.mem_write(self.data_base+self.option, b'/S1:0003:03:N:6200:0100\0')

        def call(self, name, arguments=(), limit=250000, **unused):
            u = self.uc
            code_seg = self.base_segment+int(code[1],16)
            # Inherited stop hook is at load-base+F000, while this child's
            # actual near CODE can start at a nonzero relative paragraph.
            return_off = 0xf000-int(code[1],16)*16
            words = [return_off]+list(arguments)
            sp = self.top-64-2*len(words)
            u.mem_write(self.data_base+sp, struct.pack('<'+'H'*len(words), *words))
            for reg, value in ((UC_X86_REG_CS, code_seg), (UC_X86_REG_DS, self.ds),
                    (UC_X86_REG_SS, self.ds), (UC_X86_REG_SP, sp), (UC_X86_REG_EFLAGS, 0x202)):
                u.reg_write(reg, value)
            self.returned = False
            u.emu_start(self.symbols[name], 0, count=limit)
            assert self.returned and u.reg_read(UC_X86_REG_SP) == sp+2, name
            return u.reg_read(UC_X86_REG_AX)

        def open(self):
            return self.call('_aspect_serial_open', [self.option])

    for version in (0, 12, 20, 21, 22, 23, 24, 25, 255, 65535):
        client = Child()
        backend_calls = []

        def absent_backend(u, address, size, unused):
            if address != client.symbols['_aspect_serial_backend_open']:
                return
            backend_calls.append(True)
            assert u.reg_read(UC_X86_REG_DS) == u.reg_read(UC_X86_REG_SS) == client.ds
            sp = u.reg_read(UC_X86_REG_SP)
            ret = struct.unpack('<H', u.mem_read(client.data_base+sp, 2))[0]
            u.reg_write(UC_X86_REG_AX, 3)  # Explicit controlled ABSENT UART.
            u.reg_write(UC_X86_REG_IP, ret)
            u.reg_write(UC_X86_REG_SP, sp+2)

        client.uc.hook_add(UC_HOOK_CODE, absent_backend)
        client.words[22] = version;client.publish()
        result = client.open()
        assert result == (3 if version == capability else 1), (version, result)
        assert len(backend_calls) == (1 if version == capability else 0)
        assert not client.writes and not client.requests and not client.get('_aspect_serial_active')
        handshake.append(dict(version=version, result=result,
            reached_controlled_absent_backend=bool(backend_calls), passed=True))
    return handshake


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--product', type=Path, required=True)
    parser.add_argument('--child', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    product = args.product.resolve()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    out.mkdir(parents=True)
    manifest = json.loads((product/'manifest.json').read_text())
    assert sha(product/'TERMINAL.EXE') == manifest['binary_sha256']
    assert manifest.get('experimental_terminal_query')
    relevant = ['src/terminal/aspect_renderer.asm', 'src/aspect/terminal_builtins.asm',
        'src/aspect/resident_bridge.asm', 'src/aspect/renderer_client.c',
        'src/aspect/resident_render.h', 'src/process/compiler_overlay_front.asm']
    for name in relevant:
        assert sha(ROOT/name) == manifest['sources'][name], ('stale source', name)
    match = re.search(r'^([0-9a-f]{4}):[0-9a-f]{4}[*+ ]+\s+render_body\s*$',
                      (product/'terminal.map').read_text(), re.M|re.I)
    assert match
    Parent._aspect_segment = 0x1000+int(match[1], 16)
    cases = []
    m = Parent(product)
    for index, field in enumerate(FIELDS):
        for value in WORDS:
            for other, name in enumerate(FIELDS):
                m.put(name, (0x3179+other*0x1237)&65535)
            m.put(field, value)
            before = {name: m.get(name) for name in FIELDS}
            for high in (0, 1):
                result = m.request(29, index|(high<<8))
                assert result == 0xf000|((value>>(high*8))&255), (field, value, high, result)
                assert m.getters == [GETTERS[index]], m.getters
                assert sum(name == 'actual-client-auth' for name, _ in m.events) == 1
                assert ('pure-admission-model', index|(high<<8)) in m.events
                assert {name: m.get(name) for name in FIELDS} == before
            cases.append(dict(case='full-word-and-BX', index=index, value=value, passed=True))
    for payload in [*range(9, 256), *range(265, 512), 512, 0x8000, 0xffff]:
        assert m.request(29, payload) == 7, payload
        assert not m.getters
    cases.append(dict(case='invalid-wire-payload', inputs=497, passed=True))
    owners = ['render_program_owned', 'render_snapshot_owned', 'terminal_script_window_active',
              'terminal_script_confirm_active', 'terminal_script_field_active']
    for owner in owners:
        m = Parent(product)
        m.put(owner, 1)
        assert m.request(29, 0) == 10, owner
        assert not m.getters
        m.put(owner, 0)
        assert m.request(29, 0) == 0xf000|(m.get(FIELDS[0])&255)
        cases.append(dict(case='owner-reject-and-retry', owner=owner, passed=True))
    m = Parent(product)
    m.uc.mem_write(m.symbols['_script_handoff']+22, b'\1\0')
    assert m.request(29, 0) == 14 and not m.getters
    m.uc.mem_write(m.symbols['_script_handoff']+22, b'\0\0')
    assert m.request(29, 0) == 0xf000|(m.get(FIELDS[0])&255)
    cases.append(dict(case='returned-UART-reject-and-retry', passed=True))
    for status in (3, 7, 10, 14):
        m = Parent(product)
        m.admit_result = status
        assert m.request(29, 0x100) == status and not m.getters
        cases.append(dict(case='controlled-admission-refusal', result=status, passed=True))
    controls = ['inactive-program', 'wrong-kind', 'detached', 'wrong-PSP', 'wrong-DS',
        'DS-ne-SS', 'bad-magic', 'bad-token', 'changed-callback', 'bad-MCB-signature',
        'bad-MCB-owner', 'empty-MCB', 'callback-outside', 'descriptor-token',
        'descriptor-entry', 'descriptor-segment']
    controls += ['client-version-'+str(v) for v in (0, 12, 20, 21, 22, 23, 25, 255, 65535)]
    controls += ['descriptor-version-'+str(v) for v in (0, 12, 20, 21, 22, 23, 25, 255, 65535)]
    for control in controls:
        m = Parent(product)
        ds = ss = None
        if control == 'inactive-program':m.put('terminal_program_active', 0)
        elif control == 'wrong-kind':m.put('terminal_program_kind', 3)
        elif control == 'detached':m.put('render_attached', 0)
        elif control == 'wrong-PSP':m.current_psp = CHILD_PSP+1
        elif control == 'wrong-DS':ds = ss = CHILD_DS+1
        elif control == 'DS-ne-SS':ss = CHILD_DS+1
        elif control == 'bad-magic':m.client_words[0] ^= 1;m.publish_client()
        elif control == 'bad-token':m.client_words[2] ^= 1;m.publish_client()
        elif control == 'changed-callback':m.client_words[3] += 1;m.publish_client()
        elif control == 'bad-MCB-signature':m.uc.mem_write((CHILD_PSP-1)*16, b'Q')
        elif control == 'bad-MCB-owner':m.uc.mem_write((CHILD_PSP-1)*16+1, b'\x34\x12')
        elif control == 'empty-MCB':m.uc.mem_write((CHILD_PSP-1)*16+3, b'\0\0')
        elif control == 'callback-outside':m.client_words[3:]=[0, 0xa000];m.publish_client()
        elif control == 'descriptor-token':m.put('_script_render_token', m.get('_script_render_token')^1)
        elif control == 'descriptor-entry':m.put('_script_render_offset', m.get('_script_render_offset')^1)
        elif control == 'descriptor-segment':m.put('_script_render_segment', m.get('_script_render_segment')^1)
        elif control.startswith('client-version-'):m.client_words[1] = int(control.rsplit('-', 1)[1]);m.publish_client()
        elif control.startswith('descriptor-version-'):m.put('_script_render_version', int(control.rsplit('-', 1)[1]))
        expected = 0xfffc if control == 'DS-ne-SS' else 10
        # An invalid caller that enters with DS!=SS is an authored rejection
        # fixture, not an IF-visible transition created by the product bridge.
        flags = 0x443 if control == 'DS-ne-SS' else 0x643
        assert m.request(29, 0, ds=ds, ss=ss, flags=flags) == expected, control
        assert not m.getters, control
        cases.append(dict(case=control, result=expected, passed=True))
    # The first accepted half must not authorize the second after revocation.
    m = Parent(product)
    assert m.request(29, 0) & 0xff00 == 0xf000
    m.client_words[2] ^= 1;m.publish_client()
    assert m.request(29, 0x100) == 10 and not m.getters
    cases.append(dict(case='second-byte-reauthenticates', passed=True))
    handshake = child_handshake(args.child) if args.child else []
    report = dict(passed=True, cases=cases, tagged_word_cases=9*len(WORDS),
        tagged_byte_requests=9*len(WORDS)*2, invalid_payloads=497,
        handshake_cases=handshake, original_inputs=[],
        parent_sha256=sha(product/'TERMINAL.EXE'), parent_manifest_sha256=sha(product/'manifest.json'),
        child_sha256=sha(args.child/'ASPECT.EXE') if args.child else None,
        sources={name: sha(ROOT/name) for name in relevant+[
            'standalone/check_terminal_query_parent.py', 'standalone/dos_image.py',
            'standalone/check_aspect_render_client.py', 'standalone/check_uart.py']},
        scope=__doc__+' Actual linked prepare/BEGIN/bridge, per-byte parent descriptor/client/MCB/callback '
        'authentication, owner/returned-UART checks, selector routing, native WORD getters and tagged replies. '
        'Every request restores all caller non-result registers/FLAGS/DS=SS/SP and source WORDs; '
        'unexpected code/interrupt/callback/output paths reject. Pure renderer admission is explicitly '
        'modeled with BX clobber; setup-only field retirement and DOS62 PSP are controlled boundaries. '
        'Optional linked child handshake executes actual descriptor/client-stack validation with modeled DOS '
        'and an explicit ABSENT3 UART-open boundary: only capability24 reaches that boundary; '
        'mismatched capabilities return ARGUMENT1 before it. No UART or child far endpoint executes there. '
        'No CRT startup, real DOS EXEC, full geometry admission, physical/BBS or complete ASPECT claim.')
    (out/'result.json').write_text(json.dumps(report, indent=2)+'\n')
    print('PASS linked parent terminal query', len(cases), 'cases;', len(handshake), 'child handshake cases')


if __name__ == '__main__':
    main()
