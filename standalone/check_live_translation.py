#!/usr/bin/env python3
"""Actual AltF10/namespace/loader/table/mask handoff with modeled DOS and UART."""
import hashlib
import json
from pathlib import Path
import struct
import re
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from check_live_setup_profile import Profile
from check_directory_live import word
from check_program_actions_live import ROOT, BINARY

IDENTITY = bytes(range(256))
CURRENT = b'D:\\WORK\\PCPLUS.XLT'


class Translation(Profile):
    def __init__(self):
        self.xlt_files = {}
        self.xlt_handles = {}
        self.xlt_positions = {}
        self.xlt_calls = []
        self.xlt_fault = None
        self.xlt_open_error = 0
        self.xlt_fragment = 256
        self.canonical_fault_paths = set()
        self.child_environment = None
        super().__init__()

    def interrupt(self, uc, number, data):
        ax = uc.reg_read(UC_X86_REG_AX);ah = ax >> 8;handle = uc.reg_read(UC_X86_REG_BX)
        if number == 0x21 and ax == 0x6000:
            source = self.string(uc.reg_read(UC_X86_REG_DS), uc.reg_read(UC_X86_REG_SI))
            if source in self.canonical_fault_paths:
                self.file_calls.append(('canonical-denied', source))
                uc.reg_write(UC_X86_REG_AX, 5);self.set_carry(True);return
        if number == 0x21 and (ax == 0x3d00 or ah in (0x3f, 0x3e) and handle in self.xlt_handles):
            error = answer = 0
            if ax == 0x3d00:
                path = self.string(uc.reg_read(UC_X86_REG_DS), uc.reg_read(UC_X86_REG_DX))
                if not path.endswith(b'.XLT'):
                    return super().interrupt(uc, number, data)
                error = self.xlt_open_error or (2 if path not in self.xlt_files else 0)
                if not error:
                    answer = next(h for h in range(12, 32) if h not in self.xlt_handles)
                    self.xlt_handles[answer] = path;self.xlt_positions[answer] = 0
            else:
                path = self.xlt_handles[handle]
                if ah == 0x3f:
                    at = self.xlt_positions[handle]
                    if self.xlt_fault == 'read' or self.xlt_fault == 'probe' and at == 256:
                        error = 5
                    else:
                        count = min(uc.reg_read(UC_X86_REG_CX), self.xlt_fragment)
                        blob = bytes(self.xlt_files[path][at:at+count]);answer = len(blob)
                        if blob:
                            uc.mem_write(uc.reg_read(UC_X86_REG_DS)*16+uc.reg_read(UC_X86_REG_DX), blob)
                        self.xlt_positions[handle] += answer
                else:
                    error = 6 if self.xlt_fault == 'close' else 0
                    if not error:
                        del self.xlt_handles[handle];del self.xlt_positions[handle]
            self.xlt_calls.append((ah, path, error, answer))
            uc.reg_write(UC_X86_REG_AX, error or answer);self.set_carry(bool(error));return
        answer = super().interrupt(uc, number, data)
        if number == 0x21 and ax == 0x4b00 and not self.exec_error and self.child_environment is not None:
            self.environment(self.child_environment)
        return answer

    def active(self, mode):
        self.put('terminal_translation_mode', mode)
        self.put('terminal_translation_enabled', int(mode == 1))
        self.put('uart_rx_mask', 127 if mode == 2 else 255)
        self.uc.mem_write(self.symbols['terminal_translation_table'], bytes(reversed(IDENTITY)))
        self.uc.mem_write(self.symbols['terminal_configuration_values']+40, struct.pack('<H', mode))
        self.raw = word(self.raw, 0x1e0, mode)
        return self

    def table(self):
        return bytes(self.uc.mem_read(self.symbols['terminal_translation_table'], 256))

    def outcome(self):
        return struct.unpack('<4H', self.uc.mem_read(self.symbols['terminal_setup_outcome'], 8))

    def assert_mode(self, expected):
        assert self.get('terminal_translation_mode') == expected
        assert self.get('terminal_translation_enabled') == int(expected == 1)
        assert self.get('uart_rx_mask') == (127 if expected == 2 else 255)
        assert bytes(self.uc.mem_read(self.symbols['terminal_configuration_values']+40, 2)) == struct.pack('<H', expected)


def main():
    groups = []
    def done(name, count):
        groups.append(dict(case=name, inputs=count, passed=True));print(name, count, flush=True)
    for active in (0, 1, 2):
        for desired in (0, 1, 2):
            m = Translation().active(active);m.xlt_files[CURRENT] = IDENTITY
            before = m.table();m.launch(word(m.raw, 0x1e0, desired))
            m.assert_mode(desired)
            assert m.outcome() == (0, 0, 2048 if desired != active else 0, 0)
            assert m.get('terminal_setup_translation_status') == int(desired != active)
            assert m.table() == (IDENTITY if desired == 1 and desired != active else before)
            assert bool(m.xlt_calls) == (desired == 1 and desired != active)
            m.intact()
    done('all-nine-mode-pairs-actual-foreground-confirmation-table-mask-and-config-commit', 9)

    for choice in (ord('N'), 27, 32, 13):
        for active, desired in ((0, 1), (1, 2), (2, 0)):
            m = Translation().active(active);m.xlt_files[CURRENT] = IDENTITY;before = m.table()
            m.launch(word(word(m.raw, 0x1e0, desired), 0x1ae, 30), choice)
            m.assert_mode(active);assert m.table() == before and m.get('attributes_normal_value') == 30
            assert m.outcome() == (0, 0, 32, 2048) and m.get('terminal_setup_translation_status') == 2
            m.intact()
    done('No-Escape-space-Enter-retain-mode-while-independent-display-edits-apply', 12)

    for fault in ('missing', 'empty', 'short', 'suffix', 'read', 'probe', 'close', 'access'):
        m = Translation().active(2);before = m.table()
        if fault != 'missing':
            m.xlt_files[CURRENT] = {'empty': b'', 'short': bytes(255), 'suffix': bytes(257)}.get(fault, IDENTITY)
        if fault in ('read', 'probe', 'close'):m.xlt_fault = fault
        if fault == 'access':m.xlt_open_error = 5
        m.launch(word(word(m.raw, 0x1e0, 1), 0x1ae, 30))
        m.assert_mode(2);assert m.table() == before and m.get('attributes_normal_value') == 30
        assert m.get('terminal_setup_translation_status') == 3 and m.outcome() == (0, 0, 32, 2048)
        assert b'Could not apply translation' in m.local_text
        m.intact()
    done('missing-size-read-probe-close-access-failures-retain-active-state-and-independent-edits', 8)

    for kind in ('current-cwd', 'fallback-cwd-environment', 'current-wins-bad-env', 'damaged-current-no-fallback'):
        m = Translation().active(0);m.child_cwd = b'D:\\OTHER'
        m.environment(b'PCPLUS=D:\\ENV\0\0')
        m.xlt_files[b'D:\\ENV\\PCPLUS.XLT'] = IDENTITY
        if kind in ('current-cwd', 'current-wins-bad-env'):m.xlt_files[CURRENT] = IDENTITY
        if kind == 'fallback-cwd-environment':m.child_environment = b'PCPLUS=D:\\WRONG\0\0'
        if kind == 'current-wins-bad-env':m.environment(b'PCPLUS='+b'A'*64+b'\0\0')
        if kind == 'damaged-current-no-fallback':m.xlt_files[CURRENT] = b''
        m.launch(word(m.raw, 0x1e0, 1))
        if kind == 'damaged-current-no-fallback':
            m.assert_mode(0);assert m.get('terminal_setup_translation_status') == 3
            assert [c[1] for c in m.xlt_calls if c[0] == 0x3d] == [CURRENT]
        else:
            m.assert_mode(1);assert m.table() == IDENTITY
            assert m.xlt_calls[-1][1] == (b'D:\\ENV\\PCPLUS.XLT' if kind == 'fallback-cwd-environment' else CURRENT)
        m.intact()
    done('pre-child-canonical-current-and-environment-snapshots-cannot-be-retargeted', 4)

    for kind in ('canonical-current', 'canonical-fallback', 'invalid-fallback'):
        m = Translation().active(2);m.environment(b'PCPLUS=D:\\ENV\0\0')
        m.xlt_files[b'D:\\ENV\\PCPLUS.XLT'] = IDENTITY
        if kind == 'canonical-current':m.canonical_fault_paths.add(b'PCPLUS.XLT')
        if kind == 'canonical-fallback':m.canonical_fault_paths.add(b'D:\\ENV\\PCPLUS.XLT')
        if kind == 'invalid-fallback':m.environment(b'PCPLUS='+b'A'*64+b'\0\0')
        before=m.table();m.launch(word(word(m.raw,0x1e0,1),0x1ae,30))
        m.assert_mode(2);assert m.table()==before and m.get('attributes_normal_value')==30
        assert m.get('terminal_setup_translation_io')==6
        assert [c[1] for c in m.xlt_calls if c[0]==0x3d] == ([] if kind=='canonical-current' else [CURRENT])
    done('unbound-current-or-fallback-namespaces-refuse-retargeting-and-keep-active-mode', 3)

    for marker in ('terminal_parser_active', 'terminal_transfer_active', 'terminal_transfer_pending',
                   'terminal_monitor_active', 'terminal_controller_active'):
        m = Translation().active(0);m.xlt_files[CURRENT] = IDENTITY
        # Inject an ownership change at actual child return; run every real
        # product owner normally. No function is bypassed or manually returned.
        fired = [False]
        def change(uc, address, size, data):
            if address == m.symbols['terminal_setup_complete'] and not fired[0]:
                m.put(marker, 1);fired[0] = True
        m.uc.hook_add(UC_HOOK_CODE, change)
        m.launch(word(word(m.raw, 0x1e0, 1), 0x1ae, 30))
        assert fired[0];m.assert_mode(0)
        assert not m.xlt_calls and m.get('terminal_setup_translation_status') == 3
        assert m.get('attributes_normal_value') == 30 and m.outcome() == (0, 0, 32, 2048)
    done('parser-transfer-monitor-controller-ownership-changes-refuse-mode-adoption-before-IO', 5)

    m = Translation().active(0);m.xlt_files[CURRENT] = IDENTITY;m.xlt_fragment = 13
    m.launch(word(m.raw, 0x1e0, 1));m.assert_mode(1);assert m.table() == IDENTITY
    assert sum(c[0] == 0x3f for c in m.xlt_calls) == 21
    m.xlt_files[CURRENT] = bytes(256)
    # Merely changing the file after staging/commit does not mutate the table.
    assert m.table() == IDENTITY
    m.launch(word(m.raw, 0x1e0, 2));m.assert_mode(2)
    m.launch(word(m.raw, 0x1e0, 1));m.assert_mode(1);assert m.table() == bytes(256)
    done('fragmented-read-EOF-and-repeated-mode-changes-use-fresh-stages', 3)

    mapping = bytes((i*73+19)&255 for i in range(256))
    m = Translation().active(0);m.xlt_files[CURRENT] = mapping
    m.launch(word(m.raw, 0x1e0, 1));m.assert_mode(1)
    for value in range(256):
        assert m.call('terminal_translate_input', ax=value) == mapping[value]
    done('all256-inputs-use-the-newly-committed-binary-table', 256)

    for active, desired in ((0, 2), (2, 0)):
        m = Translation().active(active);m.receive_irq(b'\xe9\xff')
        m.launch(word(m.raw, 0x1e0, desired));m.assert_mode(desired)
        assert m.get('uart_rx_count') == 2
        assert [m.call('uart_receive_byte') for _ in range(2)] == [v & (127 if desired == 2 else 255) for v in (233, 255)]
        assert bytes(m.rx) == b'R'  # Child's pending physical byte was not discarded.
        m.receive_irq(b'\x1bc')
        while m.get('uart_rx_count'):
            m.call('terminal_receive_input', ax=m.call('uart_receive_byte'), limit=1000000)
        m.assert_mode(desired)
    done('queued-raw-bytes-use-the-new-mask-and-native-RIS-retains-live-selection', 2)

    m = Translation().active(0);m.xlt_files[CURRENT] = IDENTITY
    fired = [False]
    def replace_file(uc, address, size, data):
        if address == m.symbols['_xlt_live_commit'] and not fired[0]:
            m.xlt_files[CURRENT] = bytes(256);fired[0] = True
    m.uc.hook_add(UC_HOOK_CODE, replace_file)
    m.launch(word(m.raw, 0x1e0, 1));m.assert_mode(1)
    assert fired[0] and m.table() == IDENTITY
    done('confirmation-commits-the-staged-snapshot-without-a-second-file-read', 1)

    m = Translation().active(0);m.xlt_files[CURRENT] = IDENTITY
    fired = [False]
    def change_late(uc, address, size, data):
        if address == m.symbols['terminal_setup_translation_commit'] and not fired[0]:
            m.put('terminal_parser_active', 1);fired[0] = True
    m.uc.hook_add(UC_HOOK_CODE, change_late)
    before = m.table();m.launch(word(word(m.raw, 0x1e0, 1), 0x1ae, 30), extra_ack=True)
    assert fired[0] and m.xlt_calls and m.table() == before
    m.assert_mode(0);assert m.outcome() == (0, 0, 32, 2048)
    done('ownership-is-rechecked-after-confirmation-before-copy-or-mask-mutation', 1)

    m = Translation().active(0);m.xlt_files[CURRENT] = IDENTITY
    fired = [False]
    def changed_proposal(uc, address, size, data):
        if address == m.symbols['terminal_setup_translation_commit'] and not fired[0]:
            uc.mem_write(m.symbols['terminal_setup_plan']+40, b'\x02\0');fired[0] = True
    m.uc.hook_add(UC_HOOK_CODE, changed_proposal)
    before = m.table();m.launch(word(word(m.raw, 0x1e0, 1), 0x1ae, 30), extra_ack=True)
    assert fired[0] and m.table() == before and m.get('terminal_setup_translation_io') == 7
    m.assert_mode(0);assert m.outcome() == (0, 0, 32, 2048)
    done('mismatched-staged-mode-refuses-copy-and-reports-commit-state-error', 1)

    m = Translation().active(0);m.xlt_files[CURRENT] = IDENTITY;before = m.table()
    fired = [False]
    def native_prepare_failure(uc, address, size, data):
        if address == m.symbols['terminal_connection_prepare'] and not fired[0] and m.get('terminal_setup_translation_status') == 1:
            uc.mem_write(m.symbols['terminal_modem_settings']+18, b'BAD^\0');fired[0] = True
    m.uc.hook_add(UC_HOOK_CODE, native_prepare_failure)
    raw=word(word(word(m.raw, 0x1e0, 1), 0x1ae, 30), 0xa, 46)
    m.launch(raw, extra_ack=True)
    assert fired[0] and m.get('terminal_setup_apply_status') == 6
    m.assert_mode(0);assert m.table() == before and m.get('attributes_normal_value') == 7
    assert m.outcome()[2] == 0 and m.get('terminal_setup_translation_status') == 0
    m.intact()
    done('native-modem-prepare-failure-never-installs-accepted-table-or-display-edits', 1)

    for profile_yes in (False,True):
        for mode_yes in (False,True):
            m=Translation().active(0);m.xlt_files[CURRENT]=IDENTITY
            m.after_raw=word(word(m.raw,0x194,6),0x1e0,1)
            m.keys.extend([0x7100,ord('Y' if profile_yes else 'N'),ord('Y' if mode_yes else 'N')])
            m.poll();m.safe();assert not m.keys and not m.get('terminal_program_active')
            m.assert_mode(int(mode_yes));assert m.get('csi_terminal_id')==(6 if profile_yes else 4)
            applied=(16 if profile_yes else 0)|(2048 if mode_yes else 0)
            deferred=(0 if profile_yes else 16)|(0 if mode_yes else 2048)
            assert m.outcome()==(0,0,applied,deferred)
            assert m.vector_value()==m.parent_vector and bytes(m.rx)==b'R'
    done('profile-and-translation-questions-consume-independent-answers-and-commit-independently', 4)

    m=Translation().active(0);m.child_busy=True
    m.after_raw=word(word(m.raw,0x1e0,2),2,8)
    m.keys.extend([0x7100,ord('Y'),ord('Y'),13]);m.poll();m.safe()
    m.assert_mode(2);assert not m.keys and m.outcome()==(0,0,2048,2)
    assert m.get('terminal_setup_link_status')==3 and (m.dll,m.dlm)==(3,0)
    assert b'Line busy; kept current serial settings' in m.local_text
    done('independent-mode-acceptance-does-not-hide-an-earlier-busy-link-notice', 1)

    m = Translation().active(0);m.xlt_files[CURRENT] = IDENTITY
    io = m.offset('terminal_setup_translation_io');table = m.offset('terminal_translation_table')
    assert m.call('_xlt_live_stage', [1, io]) == 7
    assert not m.call('_xlt_live_bind', [m.get('process_psp')])
    for mode, pointer in [(3, io), (65535, io), (1, 0), (1, 0xfffc)]:
        before_io = bytes(m.uc.mem_read(m.data_base+io, 8));calls = len(m.xlt_calls)
        assert m.call('_xlt_live_stage', [mode, pointer]) == 1
        assert bytes(m.uc.mem_read(m.data_base+io, 8)) == before_io and len(m.xlt_calls) == calls
    assert not m.call('_xlt_live_stage', [1, io]);before = m.table();calls = len(m.xlt_calls)
    assert m.table() == before and m.call('_xlt_live_commit', [2, table]) == 7
    assert m.call('_xlt_live_commit', [1, 0]) == 1
    assert m.call('_xlt_live_commit', [1, 0xff01]) == 1
    assert not m.call('_xlt_live_commit', [1, table]) and m.table() == IDENTITY
    assert m.call('_xlt_live_commit', [1, table]) == 7 and len(m.xlt_calls) == calls
    done('backend-unbound-argument-wrap-staging-and-single-consumption-commit-contract', 11)

    m = Translation();listing=(ROOT/'build/terminal/terminal.map').read_text()
    segment,offset,size=re.search(r'^_BSS\s+BSS\s+DGROUP\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)',listing,re.M|re.I).groups()
    m.uc.mem_write(m.base+int(segment,16)*16+int(offset,16), b'\xa5'*int(size,16))
    io=m.offset('terminal_setup_translation_io');table=m.offset('terminal_translation_table');before=m.table()
    assert m.call('_xlt_live_stage', [1,io])==7
    assert m.call('_xlt_live_commit', [1,table])==7 and m.table()==before and not m.xlt_calls
    done('serialized-unbound-guard-rejects-stage-and-commit-with-poisoned-DOS-BSS', 2)

    for active in (0, 1, 2):
        m = Translation().active(1);before = m.table()
        m.put('terminal_option_mask', m.get('terminal_option_mask') | 16384)
        m.launch(word(m.raw, 0x1e0, active));m.assert_mode(1)
        assert m.table() == before and not m.xlt_calls and m.outcome() == (0, 0, 0, 0)
        assert not any(c[0] == 'canonical' and c[1].endswith(b'.XLT') for c in m.file_calls)
    done('explicit-X-pins-active-table-and-suppresses-default-resource-binding', 3)

    for mode in (0, 1, 2):
        m = Translation().active(0);assert not m.call('terminal_setup_prepare')
        m.raw = word(m.raw, 0x1e0, mode)
        flag = 2048 if mode else 0
        assert not m.call('_live_setup_finish_policy', [m.offset('terminal_setup_plan'), m.offset('terminal_setup_outcome'), 2048])
        assert m.outcome() == (0, 0, flag, 0)
        assert bytes(m.uc.mem_read(m.symbols['terminal_setup_plan']+40, 2)) == struct.pack('<H', mode)
    m = Translation().active(0);assert not m.call('terminal_setup_prepare')
    m.raw = word(word(m.raw, 0, 1), 0x1e0, 2)
    assert not m.call('_live_setup_finish_policy', [m.offset('terminal_setup_plan'), m.offset('terminal_setup_outcome'), 2048])
    assert m.outcome() == (0, 0, 2048, 1)
    assert bytes(m.uc.mem_read(m.symbols['terminal_setup_plan'], 2)) == b'\x01\0'
    done('explicit-policy-permission-adopts-mode-independently-of-deferred-COM', 4)
    inputs = [Path(__file__).resolve(), ROOT/'src/translation/xlt_live.c', ROOT/'src/translation/xlt_live.h',
              ROOT/'src/terminal/setup_translation.asm', ROOT/'src/terminal/setup_live_apply.asm',
              ROOT/'src/config/live_setup_owner.c', ROOT/'src/config/live_setup_owner.h']
    inputs += [ROOT/'standalone'/name for name in ['live_setup_kernel.py','check_live_setup_profile.py',
              'check_live_setup_link.py','check_program_actions_live.py','check_meta_actions_live.py',
              'check_transport.py','dos_image.py','check_setup_model.py','terminal_config_fixtures.py']]
    result = dict(passed=True, binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
                  inputs=sum(g['inputs'] for g in groups), cases=groups,
                  sources={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
                  scope='Actual AltF10 scheduler, child handoff, canonical namespace binding, candidate owner, checked XLT reader and active mode/table/mask adoption. DOS/BIOS/UART boundaries modeled; ownership fault cases mutate state at child return without skipping any product function. No original/synthetic analysis executable, physical modem or same-mode table reload command claim.')
    (ROOT/'build/terminal/live-translation-checks.json').write_text(json.dumps(result, indent=2)+'\n')
    print('Live translation passed', result['inputs'])


if __name__ == '__main__':
    main()
