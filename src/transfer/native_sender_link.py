"""Prepare live sender objects alongside native_link's receiver objects.

No diagnostic adapters, checkpoint duplicates, original artifacts or CRT FILE
objects. State source is compiled by the normal src/terminal glob. The root
upload owner supplies actual terminal_upload_* callbacks and exclusive ownership
of the receiver's11264-byte session_payload arena.
"""
from pathlib import Path
import hashlib,json,subprocess

CALLBACK_ABI={
 'terminal_upload_prepare_ui':'no args; RET; initialize real upload display/status; preserve BP/SI/DI',
 'terminal_upload_open_file':'path,mode; cdecl caller4; AX opaque nonzero token/0; maintained preflight stream adapter, r/rb reopen semantics',
 'terminal_upload_close_file':'file token; cdecl caller2; AX0/ffff; latch close errors independently of native return',
 'terminal_upload_read_file':'destination,element size,element count,file token; cdecl caller8; AX complete elements0..10240,ffff error; latch errors/short-read policy',
 'terminal_upload_status':'status word; cdecl caller2; actual owner status/error latch',
 'terminal_upload_filename_display':'path; cdecl caller2; AX bounded display-string pointer',
 'terminal_upload_display_text':'text,attribute,position; callee RET6; actual upload UI',
 'terminal_upload_display_start':'mode word; cdecl caller2; actual upload UI start',
 'terminal_upload_initialize_progress':'no args; RET; initialize maintained progress/time baseline',
 'terminal_upload_progress':'no args; RET; render native counters; NOT proof of ACK acceptance (native also counts15th failed attempt)',
 'terminal_upload_timed_byte':'timeout word; callee RET2; AX byte0..255/ffff; bounded serviced UART read, cancel/carrier/deadlines; distinguish block-ACK wait from handshake/EOT',
 'terminal_upload_header_byte':'no args; RET; bounded serviced UART header read, AX byte/ffff',
 'terminal_upload_receive_byte':'no args; RET; actual immediate UART byte/ffff; preserve ring ownership',
 'terminal_upload_transmit_byte':'byte word; callee RET2; bounded serviced actual UART send; latch failure',
 'terminal_upload_transmit_buffer':'length atBP+4,address atBP+6; callee RET4; bounded serviced physical UART send, not argument-order memcpy',
 'terminal_upload_local_cancel':'no args; RET; AX nonzero cancels; serviced local BIOS input under exclusive owner',
 'terminal_upload_carrier':'no args; RET; AX nonzero carrier present',
 'terminal_upload_flush_input':'no args; RET; bounded snapshot flush of actual UART ring, no duplicate count',
 'terminal_upload_unsupported':'varying native frame; MUST NOT RETURN; explicit owner failure/cleanup; protocol13,U,W,metadata3/5 unavailable',
}
ALIASES={
 'send_checkpoint':'session_setjmp','send_unwind':'session_longjmp',
 'send_prepare_ui':'terminal_upload_prepare_ui',
 'send_open_file':'terminal_upload_open_file','send_close_file':'terminal_upload_close_file',
 'send_read_file':'terminal_upload_read_file','send_status':'terminal_upload_status',
 'send_filename_display':'terminal_upload_filename_display','send_display_text':'terminal_upload_display_text',
 'send_display_start':'terminal_upload_display_start','send_initialize_progress':'terminal_upload_initialize_progress',
 'send_progress':'terminal_upload_progress','send_timed_byte':'terminal_upload_timed_byte',
 'send_header_byte':'terminal_upload_header_byte','send_receive_byte':'terminal_upload_receive_byte',
 'send_transmit_byte':'terminal_upload_transmit_byte','send_transmit_buffer':'terminal_upload_transmit_buffer',
 'send_local_cancel':'terminal_upload_local_cancel','send_carrier':'terminal_upload_carrier',
 'send_flush_input':'terminal_upload_flush_input',
 'send_delegate_protocol13':'terminal_upload_unsupported','send_delegate_U':'terminal_upload_unsupported',
 'send_delegate_W':'terminal_upload_unsupported','send_metadata3':'terminal_upload_unsupported',
 'send_metadata5':'terminal_upload_unsupported',
}

def build_native_sender(root,output_dir):
 """Append returned objects/inputs to a receiver-enabled terminal build.

 Native checkpoint.asm is intentionally omitted. CRCbuffer alone is added;
 update/finish/table and session setjmp/longjmp come from native_link.py.
 """
 root=Path(root).resolve();output=Path(output_dir).resolve()/'native-sender';output.mkdir(parents=True,exist_ok=True)
 proof=json.loads((root/'reconstruction/transfer_send/provenance.json').read_text())
 crc=json.loads((root/'reconstruction/transfer_blocks/provenance.json').read_text())
 sources=[root/'reconstruction/transfer_send'/name for name in ['session.asm','cancel.asm']]
 sources += [root/'reconstruction/transfer_blocks/crc_buffer.asm']
 for module,p in [('transfer_send',proof),('transfer_blocks',crc)]:
  for unit in p['units']:
   source=root/'reconstruction'/module/unit['source']
   if source not in sources:continue
   flat=output/(module+'_'+source.stem+'.bin')
   subprocess.run(['nasm','-fbin','-I',str(root/'reconstruction/uart')+'/',str(source),'-o',str(flat)],check=True)
   raw=flat.read_bytes();assert len(raw)==unit['bytes'] and hashlib.sha256(raw).hexdigest()==unit['sha256'],source
 alias_source=output/'sender_aliases.asm'
 alias_source.write_text('BITS 16\nCPU 8086\nSEGMENT _TEXT public class=CODE use16\n'+'\n'.join(
  'global '+name+'\nextern '+target+'\n'+name+': jmp '+target for name,target in ALIASES.items())+'\n')
 objects=[]
 for source in sources+[alias_source]:
  obj=output/(source.parent.name+'_'+source.stem+'.obj');objects.append(obj)
  subprocess.run(['nasm','-fobj','-DTRANSFER_SEND_OMF','-DTRANSFER_BLOCKS_OMF','-Dsend_queued_count=uart_rx_count',
   '-I',str(root/'reconstruction/uart')+'/',str(source),'-o',str(obj)],check=True)
 state=root/'src/terminal/transfer_sender_state.asm'
 inputs=sources+[root/'reconstruction/transfer_send/provenance.json',root/'reconstruction/transfer_blocks/provenance.json',Path(__file__).resolve(),state,root/'reconstruction/uart/encodings.inc']
 contract={'kind':'live-native-ordinary-sender-link-preparation','callbacks':CALLBACK_ABI,
  'objects':[str(p) for p in objects],'state_source':str(state),
  'entry':'_terminal_transfer_send(filename),near cdecl caller2,DS=SS,preservesBP/BX/SI/DI/ES; AXnative0/1, independent storage/close/ACK oracle required',
  'callback_registers':'DS=SS, DFclear; preserveBP/SI/DI, other working registers/ES/flags volatile unless callback explicitly documents more',
  'owner_context':'Root outer nonlocal context must be live before invoking wrapper; native own checkpoint occurs after open/UI/setup',
  'native_progress_warning':'blocks_counted/padded totals/progress also advance on15thfailed block attempt; independent ACK oracle required',
  'preflight_size':'Root sets terminal_upload_file_size_low/high (also underscoreC aliases) before call; outside reset-clear region',
  'shared_code':['session_setjmp','session_longjmp','transfer_crc_update_original','transfer_crc_finish_original','transfer_crc_table'],
  'shared_storage':['uart_rx_count','session_payload11264 (exclusive owner only)'],
  'policy':'Maintained native reset sets protocol2,ordinary/nonstreaming,preflightDWORDsize,sharedarena; sender counters/context separate from receiver.'}
 (output/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
 return {'objects':objects,'inputs':inputs,'state_source':state,'contract':contract}
