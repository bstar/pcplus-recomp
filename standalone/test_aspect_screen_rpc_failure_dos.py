#!/usr/bin/env python3
"""Active, bounded screen RPC refusal injection and same-parent overlay reuse.

An owned INT21 fixture identifies the real parent's AH62 PSP query for commit35
after twelve metadata requests, begin4 and two valid LOCATE arguments. It changes
one real policy WORD from0 to1. The authenticated parent returns unsupported3.
An owned INT1 trace restores that WORD at the real child RPC return and observes
the resident failure/abort/longjmp entries. No code or response is substituted.
The observer then launches GOOD.ASX through actual Alt-F5 in the same parent.
"""
import argparse
import hashlib
import inspect
import json
from pathlib import Path
import re
import struct
import sys

import test_aspect_get_vm_dos as base
import test_aspect_screen_dos as screen

ROOT = base.ROOT
FIELDS = ('injected restored saved_guard guard_after metadata begins arguments arg0 arg1 '
          'begin_kind rpc_return trace_stage traps gate_seen gate_error abort_seen longjmp_seen '
          'unsafe child_ds child_cs first_exit_cs first_error first_native first_opcode '
          'first_live first_file_live first_file_status reuse_stage prompt_seen first_jft_equal '
          'first_owners_equal first_history_equal parent_psp_first parent_ds_first second_seen second_ds '
          'first_phase first_count').split()
ORIGINAL_MAIN = inspect.getsource(base.main)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def symbols(path):
    return {n: (int(s, 16), int(o, 16)) for s, o, n in re.findall(
        r'^\s*([0-9a-f]+):([0-9a-f]+)[*+]?\s+(\w+)\s*$', Path(path).read_text(), re.M|re.I)}


def replace_once(source, old, new):
    assert source.count(old) == 1, old
    return source.replace(old, new)


def fixture():
    row = dict(screen.ORIGINAL_DEFINITIONS()[0])
    good = screen.inject(row['source'].replace('pause 0\n', 'get value 10\n'), held='GOOD.TXT')
    good = good.replace('proc main\n', 'proc main\ntransmit "SECONDREADY"\n', 1)
    bad = ('integer guard\nstring value\nproc main\nwaitfor "LOGIN:" 5\n'
           'guard=4321\nfopen 0 "FAILED.TXT" "w+b"\nfputs 0 "BEFORE|"\n'
           'transmit "RPCFAULTREADY"\nlocate 1 2\ntransmit "BADAFTERFAULT"\nendproc\n')
    row.update(name='screen-rpc-refusal-reuse', source=bad, direct_GET=True,
               scripts={'GOOD': good}, screen_rounds=1,
               peer_triggers=[('SECONDREADY', [(0.25, row['banner'].decode('ascii'))])])
    return row


def priority_proof(folder):
    """Run generated x86 failure capture, then all resident scratch-call gates."""
    source = inspect.getsource(screen.observer_priority)
    source = replace_once(source, 'def observer_priority(folder, parent, child):',
                          'def rpc_priority(folder, parent, child):')
    source = replace_once(source, '    def code(machine,address,size,user):\n',
        '    def code(machine,address,size,user):\n'
        "        if state.get('forbid_scratch'):assert not at+OBSERVER_BYTES<=address<at+len(expected_snapshots), 'Overwritten RPC bytes executed'\n")
    source = replace_once(source, '    protected = bytes(uc.mem_read(at,size+256))\n',
        "    protected = bytes(uc.mem_read(at,size+256))\n    state['forbid_scratch']=True\n")
    marker = '    result = dict(passed=True,cases=3,checks=7,observer_sha256=sha(binary),'
    extra = '''    old_vector=bytes(uc.mem_read(observer*16+label('rpc_old1'),4))
    for gate in ('rpc_dos','rpc_reuse'):
        run(label(gate),0xff00)
        assert bytes(uc.mem_read(at,size+256))==protected
    word(data*16+offsets['screen_vertical_attribute_check'],1)
    word(data*16+0xf002,observer)
    word(data*16+0xf004,0x302)
    run(label('rpc_trap'),0xff00)
    assert bytes(uc.mem_read(at,size+256))==protected
    assert bytes(uc.mem_read(observer*16+label('rpc_old1'),4))==old_vector
    assert int.from_bytes(uc.mem_read(data*16+offsets['screen_vertical_attribute_check'],2),'little')==0
    assert not uc.reg_read(UC_X86_REG_EFLAGS)&0x100
    assert int.from_bytes(uc.mem_read(observer*16+label('rpc_storage_lost'),2),'little')==1
'''
    source = replace_once(source, marker, extra+marker.replace('cases=3,checks=7','cases=6,checks=14'))
    namespace = dict(screen.__dict__)
    exec(compile(source, screen.__file__, 'exec'), namespace)
    result = namespace['rpc_priority'](folder, PARENT, CHILD)
    result.update(adapted_priority_source_sha256=hashlib.sha256(source.encode()).hexdigest(),
        scope='Actual generated observer x86: unchanged complete3538-byte failure snapshot and256-byte BDA replace scratch code/data; pixel/exit writers and all three resident RPC call gates then refuse overwritten bytes. INT1 safe gate clears fixture TF/restores sole policy WORD without executing scratch, retains old vector and leaves diagnostic snapshot bytes unchanged. Synthetic CPU fixture, separate from actual DOS application behavior.')
    (folder/'rpc-priority.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def attach(source, offsets, child_symbols, parent_map, child_group, case):
    source = screen.screen_observer(source, offsets, child_symbols, parent_map, child_group, case)
    ps = symbols(parent_map)
    cs = symbols(CHILD/'ASPECT.map')
    parent_cs, body = ps['render_body']
    binary = (PARENT/'TERMINAL.EXE').read_bytes()
    h = struct.unpack_from('<14H', binary)
    code = binary[h[4]*16:]
    # This exact source-owned helper establishes the interrupted CS:IP anchor.
    assert code[parent_cs*16+body-9:parent_cs*16+body] == bytes.fromhex('53b462cd2189d85bc3')
    transaction_cs, retire = ps['terminal_screen_retire']
    retire_bytes = code[transaction_cs*16+retire:transaction_cs*16+retire+15]
    assert retire_bytes[:3] == retire_bytes[7:10] == bytes.fromhex('2ec706')
    assert retire_bytes[5:7] == retire_bytes[12:14] == b'\0\0' and retire_bytes[14] == 0xc3
    phase, count = struct.unpack_from('<H',retire_bytes,3)[0],struct.unpack_from('<H',retire_bytes,10)[0]
    assert phase == retire+15 and count == phase+4
    # The real child request returns from its parent FAR call at offset17.
    raw = (CHILD/'ASPECT.EXE').read_bytes()
    ch = struct.unpack_from('<14H', raw)
    child_code = raw[ch[4]*16:]
    req_cs, req_ip = cs['_aspect_render_request']
    prefix = child_code[req_cs*16+req_ip:req_cs*16+req_ip+17]
    assert prefix[:13] == bytes.fromhex('5589e5535657068b46048b5e06') and prefix[13:15] == b'\xff\x1e'
    constants = dict(PARENT_CS=parent_cs, PSP_RETURN=body-4,
        GUARD=offsets['screen_vertical_attribute_check'], PENDING=offsets['terminal_program_pending'],
        ATTACHED=ps['render_attached'][1], CHILD_DS=ps['render_child_ds'][1],
        CHILD_GROUP=child_group, CHILD_TEXT=req_cs, REQUEST_RETURN=req_ip+17,
        FAILURE=cs['_screen_runtime_failure'][1], ABORT=cs['aspect_abort'][1],
        LONGJMP=cs['session_longjmp'][1], ERROR=child_symbols['_runtime_error'],
        NATIVE=child_symbols['_runtime_native_error_code'], OPCODE=child_symbols['_runtime_last_opcode'],
        LIVE=child_symbols['_runtime_live'], FILE_LIVE=child_symbols['_runtime_script_file_live'],
        FILE_STATUS=child_symbols['_runtime_file']+14)
    constants.update(TRANSACTION_CS=transaction_cs, TRANSACTION_PHASE=phase, TRANSACTION_COUNT=count)
    assert ps['render_attached'][0] == ps['render_child_ds'][0] == parent_cs
    storage = ("rpc_sample: db 'SRPC'\ndw 1\n"+
        ''.join('rpc_'+n+': dw 0\n' for n in FIELDS)+
        'rpc_first_header: times 7 dw 0\nrpc_first_probe: times 6 dw 0\n'
        'rpc_first_allocations: times 14 dw 0\n')
    source = replace_once(source, 'get_input_injected: dw 0',
        'rpc_old1: dw 0,0\nrpc_storage_lost: dw 0\nget_input_injected: dw 0')
    source = replace_once(source, ' mov bp,sp\n cmp byte [ss:bp+17],0x4b',
                          ' mov bp,sp\n call rpc_dos\n cmp byte [ss:bp+17],0x4b')
    source = replace_once(source, 'get_finish_tick:\n', 'get_finish_tick:\n call rpc_reuse\n jc .done\n')
    source = replace_once(source, ' mov [old21+2],es\n', ''' mov [old21+2],es
 mov ax,0x3501
 int 0x21
 mov [rpc_old1],bx
 mov [rpc_old1+2],es
 mov dx,rpc_trap
 mov ax,0x2501
 int 0x21
''')
    source = replace_once(source, ' mov ax,[es:old1c]\n', ''' mov ax,[es:rpc_old1]
 mov [rpc_saved1],ax
 mov ax,[es:rpc_old1+2]
 mov [rpc_saved1+2],ax
 mov ax,[es:old1c]
''')
    source = replace_once(source, ' mov dx,filename\n', ''' push ds
 mov dx,[rpc_saved1]
 mov ds,[rpc_saved1+2]
 mov ax,0x2501
 int 0x21
 pop ds
 mov dx,filename
''')
    source = replace_once(source, 'saved1c: dw 0,0', 'rpc_saved1: dw 0,0\nsaved1c: dw 0,0')
    # These bytes precede the base observer's later macro definitions.
    macros = ''
    for name in ('save','restore'):
        definition = re.search(r'%macro '+name+r' 0\n.*?%endmacro', source, re.S)[0]
        macros += definition.replace('%macro '+name+' ', '%macro rpc_'+name+' ')+'\n'
    body = re.sub(r'^ (save|restore)$', lambda m: ' rpc_'+m[1], ASM, flags=re.M)
    body_source = '\n'.join('%define RPC_'+k+' '+str(v) for k, v in constants.items())+'\n'+macros+body
    # The complete existing snapshot extent remains available to its original
    # failure writer. Only otherwise idle bytes after the268-byte screen sample
    # hold this fixture's code/data. Small always-resident gates refuse them as
    # soon as the original writer publishes admit_seen, before overwriting.
    source = replace_once(source, 'admit_snapshots: times SNAPSHOT_SIZE db 0',
        'admit_snapshots:\n times '+str(screen.OBSERVER_BYTES)+' db 0\n'+storage+body_source+
        '\n%if ($-admit_snapshots)>SNAPSHOT_SIZE\n%error RPC scratch extent\n%endif\n'
        ' times SNAPSHOT_SIZE-($-admit_snapshots) db 0')
    gates = '''
rpc_dos:
 cmp word [cs:admit_seen],0
 jne .return
 jmp rpc_dos_impl
.return: ret
rpc_reuse:
 cmp word [cs:admit_seen],0
 jne .return
 jmp rpc_reuse_impl
.return: clc
 ret
rpc_trap:
 cmp word [cs:admit_seen],0
 jne .lost
 jmp rpc_trap_impl
.lost:
 push bp
 mov bp,sp
 push ax
 push es
 mov word [cs:rpc_storage_lost],1
 mov ax,[cs:parent_ds]
 mov es,ax
 mov word [es:RPC_GUARD],0
 and word [ss:bp+6],0xfeff
 pop es
 pop ax
 pop bp
 iret
'''
    return replace_once(source, 'resident_end:\nstart:', gates+'\nresident_end:\nstart:')


ASM = r'''
; BP points at the existing observer's untouched saved INT21 frame.
rpc_dos_impl:
 save
 cmp word [cs:exec_seen],1
 jne .done
 cmp word [cs:exec_done],0
 jne .done
 cmp word [cs:rpc_reuse_stage],0
 jne .second
 cmp byte [ss:bp+17],0x4c
 je .exit
 cmp word [cs:rpc_injected],0
 jne .done
 cmp byte [ss:bp+17],0x62
 jne .done
 mov ax,[cs:parent_psp]
 add ax,16+RPC_PARENT_CS
 cmp [ss:bp+22],ax
 jne .done
 cmp word [ss:bp+20],RPC_PSP_RETURN
 jne .done
 mov es,ax
 cmp word [es:RPC_ATTACHED],1
 jne .done
 mov ax,[es:RPC_CHILD_DS]
 mov [cs:rpc_child_ds],ax
 sub ax,RPC_CHILD_GROUP
 add ax,RPC_CHILD_TEXT
 mov [cs:rpc_child_cs],ax
 mov ax,[cs:parent_ds]
 cmp [ss:bp+2],ax
 jne .unsafe
 mov es,ax
 cmp word [ss:bp+6],32
 jne .begin
 inc word [cs:rpc_metadata]
 jmp .done
.begin:
 cmp word [ss:bp+6],33
 jne .argument
 inc word [cs:rpc_begins]
 mov ax,[ss:bp+14]
 mov [cs:rpc_begin_kind],ax
 jmp .done
.argument:
 cmp word [ss:bp+6],34
 jne .commit
 mov bx,[cs:rpc_arguments]
 cmp bx,2
 jae .unsafe
 shl bx,1
 mov ax,[ss:bp+14]
 mov [cs:rpc_arg0+bx],ax
 inc word [cs:rpc_arguments]
 jmp .done
.commit:
 cmp word [ss:bp+6],35
 jne .done
 cmp word [cs:rpc_metadata],12
 jne .unsafe
 cmp word [cs:rpc_begins],1
 jne .unsafe
 cmp word [cs:rpc_begin_kind],4
 jne .unsafe
 cmp word [cs:rpc_arguments],2
 jne .unsafe
 cmp word [cs:rpc_arg0],1
 jne .unsafe
 cmp word [cs:rpc_arg1],2
 jne .unsafe
 cmp word [es:RPC_GUARD],0
 jne .unsafe
 test word [ss:bp+24],0x100
 jnz .unsafe
 mov ax,[es:RPC_GUARD]
 mov [cs:rpc_saved_guard],ax
 mov word [es:RPC_GUARD],1
 mov word [cs:rpc_injected],1
 mov word [cs:rpc_trace_stage],1
 or word [ss:bp+24],0x100
 jmp .done
.exit:
 mov ax,[ss:bp+22]
 mov [cs:rpc_first_exit_cs],ax
 mov ax,[cs:rpc_child_ds]
 mov es,ax
%macro RPC_SAMPLE 2
 mov ax,[es:RPC_%2]
 mov [cs:rpc_first_%1],ax
%endmacro
 RPC_SAMPLE error,ERROR
 RPC_SAMPLE native,NATIVE
 RPC_SAMPLE opcode,OPCODE
 RPC_SAMPLE live,LIVE
 RPC_SAMPLE file_live,FILE_LIVE
 RPC_SAMPLE file_status,FILE_STATUS
%unmacro RPC_SAMPLE 2
 mov ax,[cs:parent_psp]
 add ax,16+RPC_TRANSACTION_CS
 mov es,ax
 mov ax,[es:RPC_TRANSACTION_PHASE]
 mov [cs:rpc_first_phase],ax
 mov ax,[es:RPC_TRANSACTION_COUNT]
 mov [cs:rpc_first_count],ax
 jmp .done
.second:
 cmp byte [ss:bp+17],0x4c
 jne .done
 inc word [cs:rpc_second_seen]
 mov ax,[ss:bp+2]
 mov [cs:rpc_second_ds],ax
 jmp .done
.unsafe:
 mov word [cs:rpc_unsafe],1
.done:
 restore
 ret

; Explicit debugger fixture: trace only this one refusal until resident
; session_longjmp. It never changes AX/results, IP, SP or application code.
rpc_trap_impl:
 save
 mov bp,sp
 cld
 cmp word [cs:rpc_trace_stage],1
 jb .chain
 cmp word [cs:rpc_trace_stage],6
 jae .chain
 inc word [cs:rpc_traps]
 cmp word [cs:rpc_traps],60000
 jae .unsafe
 ; Broker/checkpoint POPF restores a previously saved application FLAGS WORD.
 ; Carry only this fixture's TF through that real restore; all other bits stay.
 mov ax,[ss:bp+22]
 mov es,ax
 mov si,[ss:bp+20]
 cmp byte [es:si],0x9d
 jne .not_popf
 or word [ss:bp+26],0x100
.not_popf:
 mov ax,[cs:rpc_child_cs]
 cmp [ss:bp+22],ax
 jne .return
 mov ax,[ss:bp+20]
 cmp word [cs:rpc_trace_stage],1
 jne .failure
 cmp ax,RPC_REQUEST_RETURN
 jne .return
 mov ax,[ss:bp+16]
 mov [cs:rpc_rpc_return],ax
 mov ax,[cs:parent_ds]
 mov es,ax
 mov ax,[cs:rpc_saved_guard]
 mov [es:RPC_GUARD],ax
 mov [cs:rpc_guard_after],ax
 inc word [cs:rpc_restored]
 mov word [cs:rpc_trace_stage],2
 jmp .return
.failure:
 cmp ax,RPC_FAILURE
 jne .abort
 inc word [cs:rpc_gate_seen]
 mov ax,[ss:bp+30]
 mov [cs:rpc_gate_error],ax
 mov word [cs:rpc_trace_stage],3
 jmp .return
.abort:
 cmp ax,RPC_ABORT
 jne .longjmp
 inc word [cs:rpc_abort_seen]
 mov word [cs:rpc_trace_stage],4
 jmp .return
.longjmp:
 cmp ax,RPC_LONGJMP
 jne .return
 inc word [cs:rpc_longjmp_seen]
 mov word [cs:rpc_trace_stage],6
 and word [ss:bp+24],0xfeff
 jmp .return
.unsafe:
 mov word [cs:rpc_unsafe],1
 and word [ss:bp+24],0xfeff
 ; Restore the sole injected state even if the bounded trace fails.
 mov ax,[cs:parent_ds]
 mov es,ax
 mov ax,[cs:rpc_saved_guard]
 mov [es:RPC_GUARD],ax
.return:
 restore
 iret
.chain:
 restore
 jmp far [cs:rpc_old1]

rpc_reuse_impl:
 cmp word [cs:rpc_reuse_stage],0
 jne .menu
 cmp word [cs:exec_done],1
 jne .allow
 cmp word [cs:rpc_injected],1
 jne .allow
 cmp word [cs:rpc_restored],1
 jne .allow
 cmp word [cs:rpc_rpc_return],3
 jne .allow
 cmp word [cs:rpc_trace_stage],6
 jne .allow
 mov ax,[cs:parent_ds]
 or ax,ax
 jz .allow
 mov es,ax
 cmp word [es:PROGRAM_ACTIVE],0
 jne .allow ; Let the unchanged finish helper acknowledge the real error.
 cmp word [es:RPC_PENDING],0
 jne .allow
 push cs
 pop ds
 push cs
 pop es
 mov si,sample
 mov di,rpc_first_header
 mov cx,7
 rep movsw
 mov si,get_child_ds
 mov di,rpc_first_probe
 mov cx,6
 rep movsw
 mov si,get_allocation_probe
 mov di,rpc_first_allocations
 mov cx,14
 rep movsw
 mov ax,[parent_psp]
 mov [rpc_parent_psp_first],ax
 mov ax,[parent_ds]
 mov [rpc_parent_ds_first],ax
 mov si,before_jft
 mov di,after_jft
 mov cx,20
 call rpc_equal
 mov [rpc_first_jft_equal],ax
 mov si,before_owners
 mov di,after_owners
 mov cx,416
 call rpc_equal
 mov [rpc_first_owners_equal],ax
 mov si,exit_history
 mov di,after_history
 mov cx,72
 call rpc_equal
 mov [rpc_first_history_equal],ax
 ; Rearm only fixture-owned per-interpreter counters, retaining first proof.
 mov word [exec_seen],0
 mov word [exec_done],0
 mov word [child_exits],0
 mov word [exit_code],0xffff
 mov word [get_input_injected],0
 mov word [get_finish_phase],0
 mov word [get_finish_ticks],0
 mov word [rpc_reuse_stage],1
 mov dx,0x6c00
 call get_finish_key
 jc .unsafe
 stc
 ret
.menu:
 cmp word [cs:rpc_reuse_stage],2
 jae .allow
 mov ax,0xb800
 mov es,ax
 mov di,1762*2
 mov si,rpc_prompt
 mov cx,20
.prompt:
 mov al,[es:di]
 cmp al,[cs:si]
 jne .hold
 inc si
 add di,2
 loop .prompt
 mov word [cs:rpc_prompt_seen],1
 push cs
 pop ds
 mov si,rpc_filename
 mov cx,9
.key:
 lodsw
 mov dx,ax
 call get_finish_key
 jc .unsafe
 loop .key
 mov word [cs:rpc_reuse_stage],2
.hold:
 stc
 ret
.unsafe:
 mov word [cs:rpc_unsafe],1
 stc
 ret
.allow:
 clc
 ret
rpc_equal:
 repe cmpsb
 mov ax,0
 jne .return
 inc ax
.return:
 ret
rpc_prompt: db 'Script DOS 8.3 path: '
rpc_filename: dw 0x2247,0x184f,0x184f,0x2044,0x342e,0x1e41,0x1f53,0x2d58,0x1c0d
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('parent-dir', 'child-dir', 'compiler-dir', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--cpu', choices=('8086', '386'), default='8086')
    args = parser.parse_args()
    # Retain the same owned MCB/PSP/code verification for a pre-EXEC timeout,
    # where the base diagnostic intentionally accepts only exec_seen==1.
    import dosbox_timeout_snapshot as diagnostic
    diagnostic_source = replace_once(inspect.getsource(diagnostic.snapshot),
        'sample[0:2]==(0x524e,1)', 'sample[0]==0x524e and sample[1] in (0,1)')
    diagnostic_scope = dict(diagnostic.__dict__)
    exec(compile(diagnostic_source, diagnostic.__file__, 'exec'), diagnostic_scope)
    diagnostic.snapshot = diagnostic_scope['snapshot']
    global PARENT, CHILD
    PARENT, CHILD, compiler, out = (getattr(args, name.replace('-', '_')).resolve()
        for name in ('parent-dir', 'child-dir', 'compiler-dir', 'output'))
    assert all(p.is_relative_to(ROOT/'build') for p in (PARENT, CHILD, compiler, out)) and not out.exists()
    row = fixture()
    base.definitions = lambda: [row]
    source = ORIGINAL_MAIN
    marker = "   temporary=dict(renderer.__dict__);exec(compile(observer_source,__file__,'exec'),temporary)"
    source = replace_once(source, marker,
        "   observer_source=rpc_attach(observer_source,offsets,child_symbols,parent/'terminal.map',int(group[1],16),active_case[0])\n"+marker)
    marker = "   case=next(r for r in rows if r['name']==args[0])\n"
    source = replace_once(source, marker, marker+
        "   for leaf in ('PCMETA.OVL','PCLINE.OVL'):kwargs['files'][leaf]=(parent/leaf).read_bytes()\n")
    marker = "  module=types.ModuleType('get_vm_modem_peer');module.__file__=str(path)"
    source = replace_once(source, marker,
        "  peer=peer.replace(\"result=subprocess.run(['dosbox-x'\",\"result=__import__('dosbox_timeout_snapshot').run(['dosbox-x'\")\n"+marker)
    base.rpc_attach = attach
    exec(compile(source, base.__file__, 'exec'), base.__dict__)
    sys.argv = [sys.argv[0], '--parent-dir', str(PARENT), '--child-dir', str(CHILD),
                '--get-compiler-dir', str(compiler), '--output', str(out), '--cpu', args.cpu, '--allocation-probe']
    status = base.main()
    report = json.loads((out/'checks.json').read_text())
    case = report['cases'][0]
    folder = out/row['name']
    priority = priority_proof(folder)
    raw = (folder/'RENDER.BIN').read_bytes()
    wire = (folder/'serial.bin').read_bytes()
    at = raw.find(b'SRPC')
    assert at >= 0 and raw.count(b'SRPC') == 1
    assert struct.unpack_from('<H', raw, at+4)[0] == 1
    values = struct.unpack_from('<'+str(len(FIELDS))+'H', raw, at+6)
    observed = dict(zip(FIELDS, values))
    pos = at+6+2*len(FIELDS)
    first_header = list(struct.unpack_from('<7H', raw, pos));pos += 14
    first_probe = list(struct.unpack_from('<6H', raw, pos));pos += 12
    first_allocations = list(struct.unpack_from('<14H', raw, pos))
    checks = case['checks']
    checks.update(
        injected_once_and_restored_once=observed['injected'] == observed['restored'] == 1,
        original_guard_zero_restored=observed['saved_guard'] == observed['guard_after'] == 0,
        metadata_and_valid_LOCATE_arguments_before_fault=(observed['metadata'], observed['begins'],
            observed['begin_kind'], observed['arguments'], observed['arg0'], observed['arg1']) == (12,1,4,2,1,2),
        actual_parent_RPC_unsupported3=observed['rpc_return'] == 3,
        actual_resident_failure_gate=observed['gate_seen'] == 1 and observed['gate_error'] == 3,
        actual_resident_abort_and_longjmp=observed['abort_seen'] == observed['longjmp_seen'] == 1 and observed['trace_stage'] == 6,
        bounded_trace_no_unsafe=0 < observed['traps'] < 60000 and observed['unsafe'] == 0,
        first_real_child_typed_exit3=first_header[:4] == [0x524e,1,1,1] and first_header[6] == observed['first_error'] == 3,
        first_exit_resident_CS=observed['first_exit_cs'] == observed['child_cs'],
        first_RPC_failure_is_not_native_operand_error=observed['first_native'] == 0 and observed['first_opcode'] == 0x6a,
        first_file_and_globals_closed=observed['first_file_status'] == observed['first_live'] == observed['first_file_live'] == 0,
        first_allocation_probe_closed=first_allocations[1] == first_allocations[5] == first_allocations[3] == 0,
        first_parent_owners_retired=observed['first_jft_equal'] == observed['first_owners_equal'] == observed['first_history_equal'] == 1,
        first_parent_screen_transaction_retired=observed['first_phase'] == observed['first_count'] == 0,
        same_parent_after_real_Alt_F5=(observed['reuse_stage'],observed['prompt_seen'],observed['second_seen']) == (2,1,1)
            and observed['parent_psp_first'] == case['passive_observer_header'][5]
            and observed['parent_ds_first'] == case['passive_observer_header'][4],
        no_trailing_failed_script=wire.count(b'RPCFAULTREADY') == wire.count(b'SECONDREADY') == 1 and b'BAD' not in wire,
        failed_stream_flushed=(folder/'FAILED.TXT').read_bytes() == b'BEFORE|',
        second_screen_and_GET_stream=(folder/'GOOD.TXT').read_bytes() == b'BEFORE|LoC42',
        successful_screen_overlay_reused=all(wire.count(marker)==1 for marker in (b'SCREENBOX\r',b'SCREENSCROLL\r',b'SCREENRESTORED')),
        frozen_products_unmodified=sha(folder/'TERMINAL.EXE') == sha(PARENT/'TERMINAL.EXE')
            and sha(folder/'ASPECT.EXE') == sha(CHILD/'ASPECT.EXE'),
        original_failure_capture_and_RPC_gates_priority=priority['passed'])
    # Reuse the existing passive native pixel schema after the second script.
    pixel_at = raw.find(screen.MAGIC)
    assert pixel_at >= 0 and raw.count(screen.MAGIC) == 1
    sample = raw[pixel_at:pixel_at+screen.OBSERVER_BYTES]
    version, count = struct.unpack_from('<2H', sample, 4)
    checks['second_native_pixel_samples'] = version == 1 and count == 2
    glyphs = bytes.fromhex('c9cdbbbabccdc8ba')
    for index in range(count):
        record = sample[8+index*screen.RECORD_BYTES:8+(index+1)*screen.RECORD_BYTES]
        stage, ds = struct.unpack_from('<2H', record)
        expected = bytearray(b' \x07'*57)
        if index == 0:
            expected = bytearray(b' \x1f'*57)
            for col in range(1,18):
                expected[col*2] = glyphs[1];expected[(38+col)*2] = glyphs[5]
            for cell,glyph in ((0,glyphs[0]),(18,glyphs[2]),(56,glyphs[4]),(38,glyphs[6]),(19,glyphs[7]),(37,glyphs[3])):
                expected[cell*2] = glyph
        checks['second_native_pixels_'+str(index)] = record[4:] == bytes(expected) and stage == 101+index and ds == case['child_exit_probe']['DS']
    case.update(rpc_injection=observed,observer_priority=priority,first_header=first_header,first_probe=first_probe,
                first_allocations=first_allocations,passed=status == 0 and all(checks.values()))
    (folder/'result.json').write_text(json.dumps(case,indent=2)+'\n')
    dependencies = [Path(__file__).resolve(), Path(base.__file__), Path(screen.__file__),
        ROOT/'standalone/test_aspect_renderer_dos.py', ROOT/'standalone/test_connection_dos.py',
        ROOT/'standalone/directory_fixtures.py', ROOT/'standalone/modem_fixtures.py',
        ROOT/'standalone/terminal_config_fixtures.py', ROOT/'standalone/dosbox_timeout_snapshot.py']
    result = dict(passed=case['passed'],cases=[case],parent_sha256=sha(PARENT/'TERMINAL.EXE'),
        child_sha256=sha(CHILD/'ASPECT.EXE'),compiler_sha256=sha(compiler/'ASPCOMP.EXE'),cpu=args.cpu,
        sources={str(p.relative_to(ROOT)):sha(p) for p in dependencies},original_inputs=[],
        adapted_harness_source_sha256=hashlib.sha256(source.encode()).hexdigest(),
        adapted_timeout_snapshot_sha256=hashlib.sha256(diagnostic_source.encode()).hexdigest(),
        active_fault_injection=True,original_checks_preserved=True,scope=__doc__+
        ' Real authenticated policy rejection, unchanged binaries/results, held FILE/global cleanup, retired parent screen phase/count from exact native retirement operands, resident error3/LOCATE opcode6A/native0, same-parent real filename prompt and second ASPECT, native BOX/SCROLL pixels and GET, with inherited UART/parser/JFT/history/owner/heap/return checks. Screen transaction retirement is distinct from the outer PROGRAM/attachment lifetime, which follows ordinary script cleanup. Trace changes only its own TF (including saved POPF words) and one temporary parent policy WORD. Emulated DOS/BIOS/UART and owned peer; not passive, physical hardware or full application qualification.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('SCREEN_RPC_FAILURE',len(checks),'checks',result['passed'])
    assert result['passed'],[n for n,v in checks.items() if not v]


if __name__ == '__main__':
    main()
