#!/usr/bin/env python3
"""Compose one native ordinary receiver owner; IO adapters remain replaceable."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--adapter',type=Path,default=ROOT/'standalone/transfer_session_composite_io.asm');p.add_argument('--output-dir',type=Path,default=ROOT/'build/transfer-session-composite');p.add_argument('--driver',type=Path);p.add_argument('--c-source',type=Path,action='append',default=[]);a=p.parse_args()
OUT=a.output_dir.resolve();OUT.mkdir(parents=True,exist_ok=True)
proofs={n:json.loads((ROOT/'reconstruction'/n/'provenance.json').read_text()) for n in ['transfer_session','transfer_receive','transfer_files']}
sources=[ROOT/'reconstruction/transfer_session'/u['source'] for u in proofs['transfer_session']['units']]+[ROOT/'reconstruction/transfer_receive'/u['source'] for u in proofs['transfer_receive']['units']]+[ROOT/'reconstruction/transfer_files'/n for n in ['periodic.asm','tail.asm']]+[ROOT/'reconstruction/transfer_blocks'/n for n in ['crc_update.asm','crc_finish.asm','crc_table.asm']]
for module,proof in proofs.items():
 for unit in proof['units']:
  source=ROOT/'reconstruction'/module/unit['source']
  if source not in sources:continue
  flat=OUT/(module+'_'+source.stem+'.bin');subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(flat)],check=True)
  assert len(flat.read_bytes())==unit['bytes'] and hashlib.sha256(flat.read_bytes()).hexdigest()==unit['sha256']
state={}
for module,proof in proofs.items():
 for address,name in proof['state'].items():
  if module=='transfer_files' and not name.startswith('files_receive_'):continue
  state.setdefault(int(address,16),set()).add(name)
lines=[]
for address,names in sorted(state.items()):
 for name in sorted(names):lines+=['global '+name,name+':']
 size={0x1ea0:80,0x9062:11264,0xcd94:10}.get(address)
 if size:lines+=[' times '+str(size)+' db 0']
 elif address==0x77f0:lines+=[" db 'wb',0"]
 else:lines+=[' dw '+('4' if address==0x3996 else '38400' if address==0x3270 else '0')]
(OUT/'composite_state.inc').write_text('\n'.join(lines)+'\n')
aliases={
 'receive_validated':'session_validated','receive_buffer_full':'files_at_db2a','receive_complete':'session_at_dc28','receive_eot':'session_commit_enter','receive_unsupported_control':'session_failure_return','receive_disk_commit':'files_at_ddf6','session_retry_limit':'receive_retry_limit','session_accept_data':'receive_at_daea','session_commit_buffer':'files_at_ddf6','session_commit_partial':'files_at_de02','session_commit_unknown_size':'files_at_de20','session_header_checkpoint':'receive_at_dc6a','receive_longjmp_boundary':'session_longjmp','session_send_nak':'receive_nak','session_control_status':'receive_control_status',
 'receive_timed_byte':'composite_timed_byte','session_timed_byte':'composite_timed_byte','receive_header_byte':'composite_header_byte','receive_flush_input':'composite_flush_input','receive_delay':'composite_delay_ticks','session_delay_ticks':'composite_delay_ticks','receive_transmit_byte':'composite_transmit_byte','session_transmit_byte':'composite_transmit_byte','receive_status':'composite_status','session_status':'composite_status','files_receive_status':'composite_status','receive_progress':'composite_progress','session_file_write':'composite_file_write','files_fwrite':'composite_file_write','session_file_close_boundary':'composite_file_close','files_fclose':'composite_file_close','files_receive_flow':'composite_setflow','session_serial_gate_set':'composite_setflow','files_receive_resume':'receive_at_dc07','files_receive_failure':'session_failure_return','files_receive_stack_failure':'session_failure_cleanup_argument','files_receive_success':'session_success_return','files_receive_timestamp':'composite_timestamp','session_local_cancel':'composite_local_cancel','session_carrier_present':'composite_carrier_present','session_clock':'composite_clock','session_path_test':'composite_path_test','session_display_path':'composite_display_path','session_file_open':'composite_file_open','session_ui_print':'composite_ui_print','session_protocol9_boundary':'composite_unsupported','session_protocol12_boundary':'composite_unsupported','session_long_remainder':'composite_unsupported','session_batch_metadata_boundary':'composite_unsupported'}
(OUT/'composite_aliases.asm').write_text('BITS 16\nCPU 8086\nSEGMENT _TEXT public class=CODE use16\n'+'\n'.join('global '+name+'\nextern '+target+'\n'+name+': jmp '+target for name,target in aliases.items())+'\n')
sources += [OUT/'composite_aliases.asm',ROOT/'standalone/transfer_session_composite_host.asm',a.adapter.resolve()]
objects=[]
for path in sources:
 obj=OUT/(path.parent.name+'_'+path.stem+'.obj');objects.append(str(obj));subprocess.run(['nasm','-fobj','-DTRANSFER_SESSION_OMF','-DTRANSFER_RECEIVE_OMF','-DTRANSFER_FILES_OMF','-DTRANSFER_BLOCKS_OMF','-I',str(ROOT/'reconstruction/uart')+'/', '-I',str(OUT)+'/', '-I',str(ROOT/'standalone')+'/',str(path),'-o',str(obj)],check=True)
(OUT/'main.c').write_text('unsigned __cdecl transfer_composite_dos_test(void);int main(void){return transfer_composite_dos_test();}\n')
c_sources=([a.driver.resolve()] if a.driver else [OUT/'main.c'])+[p.resolve() for p in a.c_source]
subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/transfer'),'-fm=composite.map','-fe=TRANSFER.EXE',*map(str,c_sources),*objects],cwd=OUT,check=True)
sources += c_sources
if a.c_source:sources += sorted((ROOT/'src/transfer').glob('*.h'))
manifest={'kind':'one-owner-native-ordinary-receiver-composition-replaceable-IO-adapter','binary_sha256':hashlib.sha256((OUT/'TRANSFER.EXE').read_bytes()).hexdigest(),'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources if p.is_relative_to(ROOT) and not p.is_relative_to(OUT)},'adapter':str(a.adapter),'custom_C_driver':str(a.driver) if a.driver else None,'limitations':['Actual one-session native state/context/handshake/block validation/file controller composition.','Default IO adapter is synthetic asynchronous-frame UART/time/UI and bounded memory-file sink, not live UART or DOS storage.','Native final write/close status is ignored; external maintained storage first-error/commit policy is mandatory.','Ordinary unknown-length XMODEM128/1024 CRC/checksum only; batch/streaming/window metadata and nonzero declared-size division are explicit traps.']}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Built one-owner TRANSFER.EXE',manifest['binary_sha256'])
