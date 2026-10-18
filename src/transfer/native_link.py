"""Source-only native ordinary-receiver object preparation for TERMINAL.

Call build_native_receiver(ROOT, OUT); append result['objects'] to the link and
result['inputs'] to the source manifest. transfer_native_state.asm is compiled
by the existing src/terminal source glob, not by this helper. No diagnostic host,
fixture adapter, original artifact or native CRT FILE object is linked here.
"""
from pathlib import Path
import hashlib
import json
import subprocess

# Callback arguments follow the near return address; DS=SS throughout.
# Native callbacks may change AX/BX/CX/DX/ES/flags; preserve BP/SI/DI.
# Cdecl means caller removes the listed bytes. Pascal entries remove their own.
CALLBACK_ABI = {
    'terminal_transfer_timed_byte': 'timeout word; callee RET2; AX byte0..255 or ffff; must service local cancel/carrier/deadline while waiting',
    'terminal_transfer_header_byte': 'no args; RET; AX byte0..255 or ffff; bounded waiting; same cancel/carrier responsibilities',
    'terminal_transfer_flush_input': 'no args; RET; flush actual UART RX through real driver; never a duplicate queued-count word',
    'terminal_transfer_delay_ticks': 'BIOS tick-count word; callee RET2; native6b98 waits argument+1 tick changes; serviced cancellation/carrier',
    'terminal_transfer_delay_legacy': 'legacy calibrated unit word; callee RET2; native6b72 physical unit unknown, explicit maintained quiet-time policy required, never silently reinterpret as BIOS ticks/ms',
    'terminal_transfer_transmit_byte': 'byte word; callee RET2; bounded actual UART send, latch failures',
    'terminal_transfer_status': 'status word; cdecl caller2; latch/report native status without claiming success',
    'terminal_transfer_progress': 'no args; RET; report owned native counters',
    'terminal_transfer_file_open': 'path,mode; cdecl caller4; AX opaque nonzero token or0; maintained storage adapter only',
    'terminal_transfer_file_write': 'source,element size,element count,file token; cdecl caller8; AX complete elements; latch first storage error',
    'terminal_transfer_file_close': 'file token; cdecl caller2; AX0/ffff; seal only, owner installs after native+storage success',
    'terminal_transfer_setflow': 'gate word; cdecl caller2; real maintained flow ownership, preserve received data',
    'terminal_transfer_timestamp': 'path; cdecl caller2; explicit maintained timestamp policy/error latch',
    'terminal_transfer_local_cancel': 'no args; RET; AX nonzero cancels; consume local BIOS events under transfer ownership',
    'terminal_transfer_carrier_present': 'no args; RET; AX nonzero means carrier present',
    'terminal_transfer_clock': 'no args; RET; DX:AX clock units matching maintained transfer timeout adapter',
    'terminal_transfer_path_test': 'path; cdecl caller2; AX0 for already validated explicit stage path; no implicit prefix search',
    'terminal_transfer_display_path': 'path; cdecl caller2; AX bounded display-string pointer',
    'terminal_transfer_ui_print': 'text,attribute,position; callee RET6; actual transfer UI callback',
    'terminal_transfer_unsupported': 'varying native frame; MUST NOT RETURN; fail/cleanup explicitly; batch/window/protocol9/12/declared-size remainder are unsupported',
}

INTERNAL_ALIASES = {
    'receive_validated':'session_validated',
    'receive_buffer_full':'files_at_db2a',
    'receive_complete':'session_at_dc28',
    'receive_eot':'session_commit_enter',
    'receive_unsupported_control':'session_failure_return',
    'receive_disk_commit':'files_at_ddf6',
    'session_retry_limit':'receive_retry_limit',
    'session_accept_data':'receive_at_daea',
    'session_commit_buffer':'files_at_ddf6',
    'session_commit_partial':'files_at_de02',
    'session_commit_unknown_size':'files_at_de20',
    'session_header_checkpoint':'receive_at_dc6a',
    'receive_longjmp_boundary':'session_longjmp',
    'session_send_nak':'receive_nak',
    'session_control_status':'receive_control_status',
    'files_receive_resume':'receive_at_dc07',
    'files_receive_failure':'session_failure_return',
    'files_receive_stack_failure':'session_failure_cleanup_argument',
    'files_receive_success':'session_success_return',
}
CALLBACK_ALIASES = {
    'receive_timed_byte':'terminal_transfer_timed_byte',
    'session_timed_byte':'terminal_transfer_timed_byte',
    'receive_header_byte':'terminal_transfer_header_byte',
    'receive_flush_input':'terminal_transfer_flush_input',
    'receive_delay':'terminal_transfer_delay_legacy',
    'session_delay_ticks':'terminal_transfer_delay_ticks',
    'receive_transmit_byte':'terminal_transfer_transmit_byte',
    'session_transmit_byte':'terminal_transfer_transmit_byte',
    'receive_status':'terminal_transfer_status',
    'session_status':'terminal_transfer_status',
    'files_receive_status':'terminal_transfer_status',
    'receive_progress':'terminal_transfer_progress',
    'session_file_open':'terminal_transfer_file_open',
    'session_file_write':'terminal_transfer_file_write',
    'files_fwrite':'terminal_transfer_file_write',
    'session_file_close_boundary':'terminal_transfer_file_close',
    'files_fclose':'terminal_transfer_file_close',
    'files_receive_flow':'terminal_transfer_setflow',
    'session_serial_gate_set':'terminal_transfer_setflow',
    'files_receive_timestamp':'terminal_transfer_timestamp',
    'session_local_cancel':'terminal_transfer_local_cancel',
    'session_carrier_present':'terminal_transfer_carrier_present',
    'session_clock':'terminal_transfer_clock',
    'session_path_test':'terminal_transfer_path_test',
    'session_display_path':'terminal_transfer_display_path',
    'session_ui_print':'terminal_transfer_ui_print',
    'session_protocol9_boundary':'terminal_transfer_unsupported',
    'session_protocol12_boundary':'terminal_transfer_unsupported',
    'session_long_remainder':'terminal_transfer_unsupported',
    'session_batch_metadata_boundary':'terminal_transfer_unsupported',
}
QUEUE_ALIASES = {'session_queued_count':'uart_rx_count',
                 'receive_queued_count':'uart_rx_count'}


def build_native_receiver(root, output_dir):
    """Assemble actual receiver objects; return objects, manifest inputs and ABI.

    The caller supplies every terminal_transfer_* callback and owns storage,
    cancel/UI/flow policy. This helper deliberately emits no fallback callbacks.
    """
    root=Path(root).resolve(); output=Path(output_dir).resolve()/'native-receiver'
    output.mkdir(parents=True,exist_ok=True)
    modules=['transfer_session','transfer_receive','transfer_files','transfer_blocks']
    proofs={m:json.loads((root/'reconstruction'/m/'provenance.json').read_text()) for m in modules}
    sources=[root/'reconstruction'/m/u['source'] for m in modules[:2] for u in proofs[m]['units']]
    sources += [root/'reconstruction/transfer_files'/n for n in ['periodic.asm','tail.asm']]
    sources += [root/'reconstruction/transfer_blocks'/n for n in ['crc_update.asm','crc_finish.asm','crc_table.asm']]
    for module in modules:
        for unit in proofs[module]['units']:
            source=root/'reconstruction'/module/unit['source']
            if source not in sources: continue
            flat=output/(module+'_'+source.stem+'.bin')
            subprocess.run(['nasm','-fbin','-I',str(root/'reconstruction/uart')+'/',str(source),'-o',str(flat)],check=True)
            data=flat.read_bytes()
            assert len(data)==unit['bytes'] and hashlib.sha256(data).hexdigest()==unit['sha256'],source
    table=root/'reconstruction/transfer_blocks/crc_table.asm'
    flat=output/'crc_table.bin'
    subprocess.run(['nasm','-fbin',str(table),'-o',str(flat)],check=True)
    assert hashlib.sha256(flat.read_bytes()).hexdigest()==proofs['transfer_blocks']['crc_table']['sha256']
    aliases={**INTERNAL_ALIASES,**CALLBACK_ALIASES}
    alias_source=output/'native_aliases.asm'
    alias_source.write_text('BITS 16\nCPU 8086\nSEGMENT _TEXT public class=CODE use16\n'+
        '\n'.join('global '+name+'\nextern '+target+'\n'+name+': jmp '+target
                  for name,target in aliases.items())+'\n')
    objects=[]
    for source in sources+[alias_source]:
        obj=output/(source.parent.name+'_'+source.stem+'.obj');objects.append(obj)
        subprocess.run(['nasm','-fobj',*[f'-D{m.upper()}_OMF' for m in modules],
            *[f'-D{k}={v}' for k,v in QUEUE_ALIASES.items()],
            '-I',str(root/'reconstruction/uart')+'/',str(source),'-o',str(obj)],check=True)
    state_source=root/'src/terminal/transfer_native_state.asm'
    inputs=sources+[root/'reconstruction'/m/'provenance.json' for m in modules]+[
        Path(__file__).resolve(),state_source,root/'reconstruction/uart/encodings.inc']
    contract={'kind':'live-native-ordinary-receiver-link-preparation',
        'callbacks':CALLBACK_ABI,'queued_count_aliases':QUEUE_ALIASES,
        'objects':[str(p) for p in objects],
        'state_source':str(state_source),
        'entry':'_terminal_transfer_receive(filename), near cdecl caller2, preserves BP/BX/SI/DI/ES, DS=SS; AX native0/1, storage latch remains authoritative',
        'scope':'Protocol4 ordinary unknown-length receiver only. No fixture adapter, original artifact or CRT FILE implementation linked.'}
    (output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    return {'objects':objects,'inputs':inputs,'state_source':state_source,'contract':contract}
