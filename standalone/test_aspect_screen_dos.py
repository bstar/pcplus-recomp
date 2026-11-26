#!/usr/bin/env python3
"""Full parent/child/DOS-compiler local screen family with unchanged GET checks.

The passive observer reads native BOX/SCROLL pixels during explicit script
milestones. It never draws, modifies product state or substitutes parser replies.
"""
import argparse
import hashlib
import inspect
import json
from pathlib import Path
import re
import struct
import subprocess
import sys

import test_aspect_get_vm_dos as base

ROOT = base.ROOT
ORIGINAL_DEFINITIONS = base.definitions
ORIGINAL_SOURCE_DEFINITIONS = base.source_memory_definitions
ORIGINAL_MAIN_SOURCE = inspect.getsource(base.main)
MAGIC = b'SCRN'
RECORD_BYTES = 118
RECORDS = 2
OBSERVER_BYTES = 8+RECORD_BYTES*RECORDS+24


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def guard(expression, label):
    return 'if '+expression+'\ntransmit "BAD'+label+'"\nendif\n'


def register_guard(label):
    return guard('n0!=n4 || n1!=46 || n2!=2222 || n3!=-3333 || n5!=5555 || '
                 'n6!=6666 || n7!=7777 || n8!=8008 || n9!=9009', label)


def family():
    seed = 'n0=4369\nn1=8738\nn2=2222\nn3=-3333\nn4=17476\nn5=5555\nn6=6666\nn7=7777\nn8=8008\nn9=9009\n'
    check = guard('n0!=4369 || n1!=8738 || n2!=2222 || n3!=-3333 || n4!=17476 || '
                  'n5!=5555 || n6!=6666 || n7!=7777 || n8!=8008 || n9!=9009', 'SELECTORREGISTERS')
    return (seed+'emulate ansi\n'+check+'emulate vt220\n'+check+
        'box 18 60 20 78 31\nn8=101\ntransmit "SCREENBOX^M"\npause 1\n'
        'scroll 0 18 60 20 78 7\nn8=102\ntransmit "SCREENSCROLL^M"\npause 1\n'
        'getvattr 24 79 n0\nn4=n0\nputvattr 24 79 46\ngetvattr 24 79 n1\n'
        +guard('n1!=46', 'ATTRIBUTEWRITE')+
        'putvattr 24 79 n0\ngetvattr 24 79 n1\n'+guard('n1!=n0', 'ATTRIBUTERESTORE')+
        'n1=46\nlocate 24 79\n'+guard('$row!=24 || $col!=79', 'PHYSICALCURSOR')+
        'home\n'+guard('$row!=0 || $col!=0', 'HOME')+
        'clear 31\ngetvattr 0 0 n6\n'+guard('$termnorm!=31 || n6!=31', 'CLEAROPTION')+
        'clear\ngetvattr 0 0 n6\n'+guard('$termnorm!=31 || n6!=31', 'CLEARDEFAULT')+
        'clear 7\nclear\ngetvattr 0 0 n6\n'+guard('$termnorm!=7 || n6!=7', 'CLEARNORMAL')+
        'n6=6666\nn8=8008\n'+register_guard('SCREENREGISTERS')+
        'set msg_crlf off\nmessage "FIRST BYTE SAFELOGIN:"\nset msg_crlf on\n'
        +guard('$row!=0 || $col!=21 || $scrncols!=80 || $scrnrows!=25 || $termnorm!=7', 'SCREENRESTORE')+
        'transmit "SCREENRESTORED"\n')


def inject(source, held=None, preserve=False):
    assert source.count('transmit "GETREADY"\n') == 1
    if preserve:
        source = source.replace('proc main\n', 'proc main\n'+register_guard('EXECUTEREGISTERS'), 1)
    prefix = ('fopen 0 "'+held+'" "w+b"\nfputs 0 "BEFORE|"\n') if held else ''
    source = source.replace('transmit "GETREADY"\n', prefix+family()+'transmit "GETREADY"\n', 1)
    if held:
        marker = 'get value 10\n'
        assert source.count(marker) == 1
        source = source.replace(marker, marker+register_guard('GETREGISTERS')+'fputs 0 value\nfclose 0\n', 1)
    return source


def fixtures():
    template = dict(ORIGINAL_DEFINITIONS()[0])
    template.update(source=template['source'].replace('pause 0\n', 'get value 10\n'), direct_GET=True)
    normal = dict(template, source=inject(template['source'], held='OWNED.TXT'), screen_rounds=1,
                  owned_outputs={'OWNED.TXT': b'BEFORE|LoC42'.hex()})
    source_rows = ORIGINAL_SOURCE_DEFINITIONS()
    for row in source_rows:
        if row['source_memory'] == 'start':
            row['source'] = inject(row['source'], held='OWNED.TXT')
            row.update(screen_rounds=1, owned_outputs={'OWNED.TXT': b'BEFORE|LoC42'.hex()})
        else:
            row['source'] = inject(row['source'])
            row['scripts']['NEXT'] = inject(row['scripts']['NEXT'], held='TARGET.TXT', preserve=True)
            row.update(screen_rounds=2, owned_outputs={'OWNED.TXT': b'BEFORE|'.hex(), 'TARGET.TXT': b'BEFORE|LoC42'.hex()})
    errors = []
    for label, before, fault in (
        ('row', 'n0=4369\n', 'getvattr 25 0 n0\n'),
        ('attribute', 'getvattr 24 79 n0\n', 'putvattr 24 79 256\n')):
        source = ('string value\nproc main\nwaitfor "LOGIN:" 5\n'
            'fopen 0 "OWNED.TXT" "w+b"\nfputs 0 "BEFORE|"\n'+before+
            'transmit "SCREENERRORREADY"\n'+fault+'transmit "BADAFTERSCREENERROR"\nendproc\n')
        errors.append(dict(template, name='screen-error-'+label, source=source, success=False,
            expected_exit=7, field_BIOS_words=[], expect_GET_boundary=False, screen_rounds=0,
            screen_error=label, owned_outputs={'OWNED.TXT': b'BEFORE|'.hex()}))
    return [normal], source_rows, errors


def screen_observer(source, offsets, child_symbols, parent_map, child_group, case):
    """Reuse idle observer snapshot bytes; admission failure retains priority.

    The base observer reads admit_snapshots only when admit_seen is nonzero.
    Its original timer sets that flag and replaces the complete snapshot in
    one IF=0 interval. Both added writers refuse the flagged state, so their
    temporary records cannot overwrite actual failure evidence. All original
    sample offsets, allocation sizes and failure capture instructions remain.
    """
    symbols = {name: (int(seg, 16), int(off, 16)) for seg, off, name in re.findall(
        r'^\s*([0-9a-f]+):([0-9a-f]+)[*+ ]+\s+(\w+)\s*$', parent_map.read_text(), re.M|re.I)}
    segment, child_ds = symbols['render_child_ds']
    assert symbols['render_attached'][0] == segment
    fields = ('screen_sample equ admit_snapshots\nscreen_count equ screen_sample+6\n'
        'screen_records equ screen_sample+8\nscreen_exit_registers equ screen_records+'+str(RECORDS*RECORD_BYTES)+'\n'
        'screen_exit_cs equ screen_exit_registers+20\nscreen_exit_cell equ screen_exit_registers+22\n'
        '%if SNAPSHOT_SIZE < '+str(OBSERVER_BYTES)+'\n%error Insufficient observer snapshot storage\n%endif\n')
    choices = [source.index(marker) for marker in ('get_compiler_largest: dw 0', 'get_allocation_probe: times ', 'get_input_injected: dw 0') if marker in source]
    at = min(choices)
    source = source[:at]+fields+source[at:]
    marker = " cmp byte [0x82],'T'\n jne collect\n"
    assert source.count(marker) == 1
    # Installation code lies after resident_end and adds no retained bytes.
    source = source.replace(marker, marker+' mov word [screen_sample],0x4353\n mov word [screen_sample+2],0x4e52\n mov word [screen_sample+4],1\n')
    marker = 'timer:\n save\n cld'
    assert source.count(marker) == 1
    source = source.replace(marker, marker+'\n call screen_tick')
    marker = ' mov [cs:get_child_ds],ax\n'
    assert source.count(marker) == 1
    source = source.replace(marker, marker+'''
.screen_exit_capture:
 cmp word [cs:admit_seen],0
 jne .screen_exit_done
 mov ax,[ss:bp+22]
 mov [cs:screen_exit_cs],ax
 mov si,SCREEN_REGISTERS
 mov di,screen_exit_registers
 mov cx,10
.screen_registers:
 mov ax,[es:si]
 mov [cs:di],ax
 add si,2
 add di,2
 loop .screen_registers
 push es
 mov ax,0xb800
 mov es,ax
 mov ax,[es:3998]
 mov [cs:screen_exit_cell],ax
 pop es
.screen_exit_done:
'''.replace('SCREEN_REGISTERS', str(child_symbols['_runtime_integer_a'])))
    body = '''
screen_tick:
 cmp word [cs:admit_seen],0
 jne .done
 cmp word [cs:exec_seen],1
 jne .done
 cmp word [cs:exec_done],0
 jne .done
 cmp word [cs:screen_count],2
 jae .done
 mov ax,[cs:parent_psp]
 add ax,16+SCREEN_SEGMENT
 mov es,ax
 cmp word [es:SCREEN_ATTACHED],1
 jne .done
 mov ax,[es:SCREEN_CHILD_DS]
 or ax,ax
 jz .done
 mov es,ax
 cmp word [es:SCREEN_COMPILER_PAUSE],0
 jne .done
 cmp word [es:SCREEN_COMPILER_SCOPE],0
 jne .done
 mov bx,[es:SCREEN_REGISTERS+16]
 mov ax,[cs:screen_count]
 and ax,1
 add ax,101
 cmp ax,bx
 jne .done
 mov ax,[cs:screen_count]
 mov dx,118
 mul dx
 mov di,screen_records
 add di,ax
 mov [cs:di],bx
 mov [cs:di+2],es
 mov ax,0xb800
 mov es,ax
 add di,4
 mov si,3000
 mov dx,3
.row:
 mov cx,19
.cell:
 mov ax,[es:si]
 mov [cs:di],ax
 add si,2
 add di,2
 loop .cell
 add si,122
 dec dx
 jnz .row
 inc word [cs:screen_count]
.done:
 ret
'''
    values = dict(SCREEN_SEGMENT=segment, SCREEN_ATTACHED=symbols['render_attached'][1], SCREEN_CHILD_DS=child_ds,
        SCREEN_COMPILER_PAUSE=child_symbols['_aspect_serial_compile_pause_owned'], SCREEN_COMPILER_SCOPE=child_symbols['_runtime_compiler_scope_state'],
        SCREEN_REGISTERS=child_symbols['_runtime_integer_a'], SCREEN_ROW=offsets['screen_cursor_row'],
        SCREEN_COLUMN=offsets['screen_cursor_column'], SCREEN_NORMAL=offsets['attributes_normal_value'], SCREEN_CURRENT=offsets['attributes_current'])
    for name, value in values.items():
        body = body.replace(name, str(value))
    marker = 'resident_end:\nstart:'
    assert source.count(marker) == 1
    source = source.replace(marker, body+'\n'+marker)
    # Keep the original failure path byte-for-byte at the source level. This
    # comparison includes flag publication and every owner/BDA snapshot copy.
    original = inspect.getsource(base.renderer.observer)
    begin = ' cmp word [cs:admit_seen],0\n jne .done\n push cs'
    end = '.done:\n restore\n jmp far [cs:old1c]'
    expected = original[original.index(begin):original.index(end)+len(end)]
    assert source.count(expected) == 1
    return source


def observer_priority(folder, parent, child):
    """Replay actual observer bytes: original failure capture beats both writers."""
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE
    from unicorn.x86_const import (UC_X86_REG_AX, UC_X86_REG_BP, UC_X86_REG_CS,
        UC_X86_REG_DS, UC_X86_REG_ES, UC_X86_REG_SS, UC_X86_REG_SP, UC_X86_REG_EFLAGS)
    listing = folder/'observer-priority.lst'
    binary = folder/'observer-priority.com'
    subprocess.run(['nasm','-fbin','-l',str(listing),str(folder/'observer.asm'),'-o',str(binary)], check=True)
    assert binary.read_bytes() == (folder/'RENDER.COM').read_bytes()
    lines = listing.read_text().splitlines()

    def label(name):
        indexes = [i for i,line in enumerate(lines) if re.search(r'(?<!\w)'+re.escape(name)+r':',line)]
        assert len(indexes) == 1, name
        for line in lines[indexes[0]:]:
            match = re.match(r'^\s*\d+\s+([0-9a-fA-F]{8})\s',line)
            if match:
                return int(match[1],16)+0x100
        raise AssertionError(name)

    def table(name):
        asm = (folder/'observer.asm').read_text()
        match = re.search(r'^'+name+r': dw ([0-9,]+)$',asm,re.M)
        assert match, name
        return [int(value) for value in match[1].split(',')]

    offsets = base.renderer.map_offsets(parent/'terminal.map')
    group = base.renderer.GROUP_REL
    psp, data, observer = 0x1000, 0x1010+group, 0x8000
    uc = Uc(UC_ARCH_X86,UC_MODE_16)
    uc.mem_map(0,0x100000)
    uc.mem_write(observer*16+0x100,binary.read_bytes())
    uc.mem_write(data*16,bytes((i*29+7)&255 for i in range(65536)))
    uc.mem_write(0x400,bytes((i*11+3)&255 for i in range(256)))
    uc.mem_write(psp*16,b'\xcd\x20')

    def word(at,value):
        uc.mem_write(at,struct.pack('<H',value))

    for name,value in (('process_psp',psp),('terminal_program_active',1),('terminal_program_kind',4),('terminal_program_status',5)):
        word(data*16+offsets[name],value)
    for name,value in (('parent_psp',psp),('parent_ds',data),('exec_seen',0),('exec_done',0),('admit_seen',0)):
        word(observer*16+label(name),value)
    at = observer*16+label('admit_snapshots')
    size = label('admit_bda')-label('admit_snapshots')
    assert size >= OBSERVER_BYTES
    # Simulate a prior complete screen record without replacing executable code.
    uc.mem_write(at,MAGIC+struct.pack('<HH',1,2)+bytes([0xa5])*(OBSERVER_BYTES-8))
    word(observer*16+label('old1c'),0xff00)
    word(observer*16+label('old1c')+2,observer)
    state = dict(stop=None,stopped=False)

    def code(machine,address,size,user):
        if address == state['stop']:
            state['stopped'] = True
            machine.emu_stop()
    uc.hook_add(UC_HOOK_CODE,code)

    def run(start,stop):
        state.update(stop=observer*16+stop,stopped=False)
        word(data*16+0xf000,0xff00)
        for register,value in ((UC_X86_REG_CS,observer),(UC_X86_REG_DS,data),(UC_X86_REG_SS,data),
                (UC_X86_REG_ES,0),(UC_X86_REG_SP,0xf000),(UC_X86_REG_BP,0x7000),(UC_X86_REG_AX,0),
                (UC_X86_REG_EFLAGS,2)):
            uc.reg_write(register,value)
        uc.emu_start(observer*16+start,0,count=100000)
        assert state['stopped'], 'Observer priority replay did not stop'

    # Execute the unchanged original timer admission-failure path. It must
    # overwrite the scratch record with every actual source byte and BDA byte.
    expected_words = b''.join(struct.pack('<H',int.from_bytes(uc.mem_read(data*16+off,2),'little')) for off in table('policy_table'))
    chunks = table('snapshot_table')
    expected_snapshots = b''.join(bytes(uc.mem_read(data*16+off,count)) for off,count in zip(chunks[::2],chunks[1::2]))
    expected_bda = bytes(uc.mem_read(0x400,256))
    run(label('timer'),0xff00)
    assert int.from_bytes(uc.mem_read(observer*16+label('admit_seen'),2),'little') == 1
    assert bytes(uc.mem_read(observer*16+label('admit_words'),len(expected_words))) == expected_words
    assert bytes(uc.mem_read(at,size)) == expected_snapshots
    assert bytes(uc.mem_read(observer*16+label('admit_bda'),256)) == expected_bda
    protected = bytes(uc.mem_read(at,size+256))
    run(label('screen_tick'),0xff00)
    assert bytes(uc.mem_read(at,size+256)) == protected
    run(label('.screen_exit_capture'),label('.screen_exit_done'))
    assert bytes(uc.mem_read(at,size+256)) == protected
    result = dict(passed=True,cases=3,checks=7,observer_sha256=sha(binary),
        snapshots_preserved_bytes=size,bda_preserved_bytes=256,new_snapshot_storage_bytes=0,
        scope='Actual source-owned observer x86 bytes: complete original admission failure capture replaces prior scratch, then timer and exit writers preserve all failure snapshot/BDA bytes. Synthetic parent data and interrupt-chain endpoint; no application admission model substituted into DOS execution.')
    (folder/'observer-priority.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def run_suite(label, rows, *, parent, child, compiler, out, cpu):
    base.definitions = (lambda: ORIGINAL_DEFINITIONS()) if label == 'source' else (lambda: rows)
    base.source_memory_definitions = lambda: rows
    marker = "   temporary=dict(renderer.__dict__);exec(compile(observer_source,__file__,'exec'),temporary)"
    assert ORIGINAL_MAIN_SOURCE.count(marker) == 1
    source = ORIGINAL_MAIN_SOURCE.replace(marker,
        "   observer_source=screen_observer(observer_source,offsets,child_symbols,parent/'terminal.map',int(group[1],16),active_case[0])\n"+marker)
    base.screen_observer = screen_observer
    exec(compile(source, base.__file__, 'exec'), base.__dict__)
    sys.argv = [sys.argv[0], '--parent-dir', str(parent), '--child-dir', str(child), '--get-compiler-dir', str(compiler),
                '--output', str(out), '--cpu', cpu, '--allocation-probe']
    if label == 'source':
        sys.argv.append('--source-lease-cases')
    elif label == 'get':
        sys.argv.append('--stream-probe')
    status = base.main()
    report = json.loads((out/'checks.json').read_text())
    child_listing = (child/'ASPECT.map').read_text()
    child_text = int(re.search(r'^_TEXT\s+CODE\s+\S+\s+([0-9a-f]+):', child_listing, re.M|re.I)[1], 16)
    for result in report['cases']:
        row = next(row for row in rows if row['name'] == result['case'])
        folder = out/result['case']
        raw = (folder/'RENDER.BIN').read_bytes()
        wire = (folder/'serial.bin').read_bytes()
        priority = observer_priority(folder,parent,child)
        at = raw.find(MAGIC)
        usable = not result['admission_failure_observed'] and at >= 0 and raw.count(MAGIC) == 1
        sample = raw[at:at+OBSERVER_BYTES] if usable else bytes(OBSERVER_BYTES)
        version, count = struct.unpack_from('<2H', sample, 4)
        checks = result['checks']
        checks['screen_observer_schema'] = usable and version == 1 and len(sample) == OBSERVER_BYTES
        checks['screen_original_failure_diagnostics_take_priority'] = priority['passed']
        checks['screen_no_guard_or_post_error_output'] = b'BAD' not in wire
        checks['screen_file_and_global_owners_retired'] = result['allocation_probe']['_runtime_script_file_live'] == result['allocation_probe']['_runtime_live'] == result['child_exit_probe']['file_status'] == 0
        checks['screen_expected_snapshot_count'] = count == min(row['screen_rounds'],1)*2
        assert count <= RECORDS, 'Observer record extent'
        checks['screen_distinct_wire_milestones'] = all(wire.count(marker) == row['screen_rounds'] for marker in (b'SCREENBOX\r', b'SCREENSCROLL\r', b'SCREENRESTORED'))
        samples = []
        glyphs = bytes.fromhex('c9cdbbbabccdc8ba')
        for index in range(count):
            record = sample[8+index*RECORD_BYTES:8+(index+1)*RECORD_BYTES]
            stage, ds = struct.unpack_from('<2H', record)
            phase = index%2
            expected = bytearray(b' \x07'*57)
            if not phase:
                expected = bytearray(b' \x1f'*57)
                for col in range(1,18):
                    expected[col*2] = glyphs[1]
                    expected[(38+col)*2] = glyphs[5]
                for cell, glyph in ((0, glyphs[0]), (18, glyphs[2]), (56, glyphs[4]), (38, glyphs[6]), (19, glyphs[7]), (37, glyphs[3])):
                    expected[cell*2] = glyph
            checks['screen_native_pixels_'+str(index)] = record[4:] == bytes(expected)
            checks['screen_stage_identity_'+str(index)] = stage == 101+phase and ds == result['child_exit_probe']['DS']
            samples.append(dict(stage=stage, child_ds=ds, rectangle_hex=record[4:].hex()))
        end = 8+RECORDS*RECORD_BYTES
        registers = list(struct.unpack_from('<10H', sample, end))
        exit_cs, exit_cell = struct.unpack_from('<2H', sample, end+20)
        expected_cs = result['child_exit_probe']['DS']-int(re.search(r'DGROUP\s+([0-9a-f]+):', child_listing, re.I)[1],16)+child_text
        checks['screen_exit_in_resident_TEXT'] = exit_cs == expected_cs
        if row.get('screen_error') == 'row':
            checks['screen_bad_row_preserves_integer_destination'] = registers[0] == 4369
        if row.get('screen_error') == 'attribute':
            checks['screen_bad_attribute_preserves_video_byte'] = registers[0] == exit_cell>>8
        if row.get('screen_error'):
            checks['screen_error_site_reached_once'] = wire.count(b'SCREENERRORREADY') == 1
            checks['screen_error_native_operand_status'] = result['child_exit_probe']['error'] == 7 and result['allocation_probe']['_runtime_native_error_code'] == 1
        for leaf, expected in row['owned_outputs'].items():
            checks['screen_owned_stream_'+leaf] = (folder/leaf).is_file() and (folder/leaf).read_bytes() == bytes.fromhex(expected)
        if row['success']:
            checks['screen_attribute_write_changes_original'] = registers[0] != 46
            checks['screen_get_registers_persist'] = registers[1:4] == [46,2222,(-3333)&65535] and registers[4] == registers[0] and registers[5:] == [5555,6666,7777,8008,9009]
        result.update(screen_samples=samples, screen_exit_registers=registers, screen_exit_cs=exit_cs,observer_priority=priority,
            screen_exit_status_cell=exit_cell, passed=all(checks.values()))
        (folder/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    report.update(passed=status == 0 and all(case['passed'] for case in report['cases']),
        adapted_harness_source_sha256=hashlib.sha256(source.encode()).hexdigest())
    (out/'result.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('parent-dir', 'child-dir', 'compiler-dir', 'output'):
        parser.add_argument('--'+name, required=True, type=Path)
    parser.add_argument('--suite', choices=('all','get','source','errors'), default='all')
    parser.add_argument('--cpu', choices=('8086','386'), default='8086')
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    parent, child, compiler = (getattr(args, name+'_dir').resolve() for name in ('parent','child','compiler'))
    out.mkdir(parents=True)
    normal, sources, errors = fixtures()
    suites = []
    for label, rows in (('get',normal), ('source',sources), ('errors',errors)):
        if args.suite != 'all' and args.suite != label:
            continue
        report = run_suite(label, rows, parent=parent, child=child, compiler=compiler, out=out/label, cpu=args.cpu)
        suites.append(dict(suite=label, passed=report['passed'], cases=report['cases'], report=str(out/label/'result.json')))
        if not report['passed']:
            break
    dependencies = [Path(__file__).resolve(), Path(base.__file__), ROOT/'standalone/test_aspect_renderer_dos.py',
        ROOT/'standalone/test_connection_dos.py', ROOT/'standalone/directory_fixtures.py']
    result = dict(passed=all(suite['passed'] for suite in suites), suites=suites,
        cases=sum(len(suite['cases']) for suite in suites), sources={str(path.relative_to(ROOT)):sha(path) for path in dependencies},
        parent_sha256=sha(parent/'TERMINAL.EXE'), child_sha256=sha(child/'ASPECT.EXE'), compiler_sha256=sha(compiler/'ASPCOMP.EXE'), cpu=args.cpu,
        original_inputs=[], scope=__doc__+' Actual source-only full products, real DOS/Python compiler byte agreement and DOS'+args.cpu+' execution. All underlying GET, return, UART/parser, stream, file/heap and source-lease assertions remain active. BOX/SCROLL114-byte pixel samples cover the first command pass in each case, using passive reads at script phase and wire milestones; seven local native commands, physical status-row attributes/cursor, normal/current attribute effects, N0..9 and EMULATE selector separation, source EXECUTE and typed-abort cleanup are checked. Synthetic DOS/BIOS/UART and owned loopback peer; no physical hardware, live BBS or whole-ASPECT qualification.')
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print('SCREEN_FULL_DOS',result['cases'],'cases',result['passed'])
    assert result['passed']


if __name__ == '__main__':
    main()
