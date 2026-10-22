#!/usr/bin/env python3
"""Reject damaged configuration call frames, relocations and segment extents."""
import hashlib,json,re,struct,tempfile
from pathlib import Path
from terminal_memory import inspect_terminal_memory
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/terminal'
def main():
 binary=OUT/'TERMINAL.EXE';mp=OUT/'terminal.map';raw=binary.read_bytes();listing=mp.read_text()
 memory=inspect_terminal_memory(binary,mp)
 # The aggregate includes four transfer-UI entries and three callbacks in
 # addition to the80 configuration/23 modem/22 controller/four redisplay pairs.
 assert memory['configuration_bridge_pairs_verified']==80 and memory['far_code_bridge_pairs_verified']==136
 assert memory['capture_reservation_far_bindings_verified']==2
 assert memory['capture_reservation_initialized_bytes']==8
 header=struct.unpack_from('<14H',raw);start=header[4]*16
 symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
 def at(name):s,o=symbols[name];return start+s*16+o
 mutations=[]
 for field in (0,2,4,6):
  bad=bytearray(raw);bad[at('_capture_reservation')+field]^=1
  mutations.append((f'reservation-initial-state-field-{field}',bad,listing))
 for i,site in enumerate(memory['capture_reservation_far_call_sites']):
  for field in (1,3):
   bad=bytearray(raw);bad[start+site+field]^=1
   mutations.append((f'reservation-call-{i}-target-field-{field}',bad,listing))
  bad=bytearray(raw);wanted=site+3
  for j in range(header[3]):
   off,seg=struct.unpack_from('<HH',bad,header[12]+4*j)
   if seg*16+off==wanted:struct.pack_into('<HH',bad,header[12]+4*j,0,0);break
  else:raise AssertionError(('Missing reservation relocation',i))
  mutations.append((f'reservation-call-{i}-missing-relocation',bad,listing))
 for name in ('_capture_file_reserve','_capture_file_release','_capture_file_reserved','_capture_file_probe_owners','_capture_reservation'):
  segment=0 if name!='_capture_file_probe_owners' else symbols['_capture_file_reserve'][0]
  bad_listing=re.sub(r'(?m)^[0-9a-f]{4}:([0-9a-f]{4})([*+ ]+\s+'+name+r'\s*)$',lambda m:f'{segment:04x}:'+m[1]+m[2],listing)
  assert bad_listing!=listing
  mutations.append((name+':wrong-segment',raw,bad_listing))
 entries=[(name,int(n)) for name,n in re.findall(r'^CONFIG_ENTRY (\w+),(\d+)$',(ROOT/'src/terminal/config_abi.inc').read_text(),re.M)]
 assert len(entries)==34 and {n for _,n in entries}=={0,1,2,3,5,6,7,8,9,10}
 for name,count in entries:
  for suffix,delta,kind in [('',5,'near-argument-offset'),('',3+count*3+1,'far-target'),('',3+count*3+5+4,'near-return'),('_far',5,'far-argument-offset'),('_far',3+count*3+1,'implementation-target'),('_far',3+count*3+3+4,'far-return')]:
   bad=bytearray(raw);bad[at(name+suffix)+delta]^=1;mutations.append((name+':'+kind,bad,listing))
 for name in ['_config_terminal_auto_deliver','_config_terminal_auto_allowed','_config_terminal_auto_start','_config_terminal_auto_ticks','config_memmove_service_','_config_clipboard_transport','config_strcmp_service_','_config_history_file','_config_process_run','_config_xlt_open','_config_xlt_read','_config_xlt_close','config_memcpy_service_','config_memset_service_','config_memcmp_service_','config_strchr_service_','config_canonical_service_','_config_terminal_decode','_config_modem_decode','_config_prm_read','_config_directory_read','_config_number_expand','_config_live_expand','config_u4div_service_','config_u4mul_service_','_config_ym_crc','_config_ym_read','_config_ym_put','_config_ym_unread','_config_ym_poll','_config_ym_progress','_config_ym_modem','_config_bd_begin','_config_bd_open','_config_bd_append','_config_bd_finish','_config_bd_cleanup','_config_bu_begin','_config_bu_read','_config_bu_next','_config_bu_close','_config_bu_abort','config_strcpy_service_','_config_bu_seek','_config_bu_skip','_config_bd_exact']:
  service=name if name.endswith('_') else name+'_service'
  for label,location in [('service-far-target',at(service)+1),('resident-call-frame',at(name+'_resident')+1)]:
   bad=bytearray(raw);bad[location]^=1;mutations.append((name+':'+label,bad,listing))
 # Remove one required segment relocation from every public entry and callback.
 for name,segment_offset in [('_terminal_script_prepare',15),('_config_clipboard_transport_service',3),('config_strcmp_service_',3),('_config_history_file_service',3),('_program_execute',12),('_config_process_run_service',3),('_redisplay_event',15),('_xlt_live_bind',9),('_xlt_live_stage',12),('_xlt_live_commit',12),('_xlt_live_initialize',21),('_xlt_live_reload',15),('_xlt_live_editor',15),('_xlt_dos_read_default',15),('_xlt_dos_read',15),('_config_xlt_open_service',3),('_config_xlt_read_service',3),('_config_xlt_close_service',3),('_directory_live_read_context',33),('_live_configuration_decode',27),('config_memcpy_service_',3),('_config_number_expand_service',3),('_live_setup_bind',15),('_live_setup_begin',21),('_live_setup_finish',12),('_live_setup_abort',9),('_live_setup_finish_policy',15),('_live_setup_acknowledge',9),('config_canonical_service_',3),('_config_live_expand_service',3),('_ymodem_run', 12),('_batch_header_end', 12),('_batch_header_encode', 24),('_batch_header_decode', 15),('config_u4div_service_', 3),('config_u4mul_service_', 3),('_config_ym_crc_service', 3),('_config_ym_read_service', 3),('_config_ym_put_service', 3),('_config_ym_unread_service', 3),('_config_ym_poll_service', 3),('_config_ym_progress_service', 3),('_config_ym_modem_service',3),('_config_bd_begin_service', 3),('_config_bd_open_service', 3),('_config_bd_append_service', 3),('_config_bd_finish_service', 3),('_config_bd_cleanup_service', 3),('_config_bu_begin_service', 3),('_config_bu_read_service', 3),('_config_bu_next_service', 3),('_config_bu_close_service', 3),('_config_bu_abort_service', 3),('_terminal_zmodem_store',9),('config_strcpy_service_',3),('_config_bu_seek_service',3),('_config_bu_skip_service',3),('_config_bd_exact_service',3)]:
  bad=bytearray(raw);wanted=at(name)-start+segment_offset
  for i in range(header[3]):
   off,seg=struct.unpack_from('<HH',bad,header[12]+4*i)
   if seg*16+off==wanted:struct.pack_into('<HH',bad,header[12]+4*i,0,0);break
  else:raise AssertionError(('No relocation for',name))
  mutations.append((name+':missing-MZ-relocation',bad,listing))
 for name,count in entries:
  if name not in ('_terminal_preferences_read','_terminal_directory_preferences_read','_terminal_autostart_initialize','_terminal_autostart_flush','_terminal_autostart_poll','_terminal_autostart_input','_live_setup_transfer_settings'):continue
  bad=bytearray(raw);wanted=at(name)-start+6+count*3
  for j in range(header[3]):
   off,seg=struct.unpack_from('<HH',bad,header[12]+4*j)
   if seg*16+off==wanted:struct.pack_into('<HH',bad,header[12]+4*j,0,0);break
  else:raise AssertionError(('No new entry relocation',name))
  mutations.append((name+':missing-new-entry-relocation',bad,listing))
 for i in range(10):
  for field in (0,2):
   bad=bytearray(raw);bad[at('_terminal_zmodem_ops')+4*i+field]^=1
   mutations.append((f'zmodem-callback-{i}-field-{field}',bad,listing))
  bad=bytearray(raw);wanted=at('_terminal_zmodem_ops')-start+4*i+2
  for j in range(header[3]):
   off,seg=struct.unpack_from('<HH',bad,header[12]+4*j)
   if seg*16+off==wanted:struct.pack_into('<HH',bad,header[12]+4*j,0,0);break
  else:raise AssertionError(('No callback relocation',i))
  mutations.append((f'zmodem-callback-{i}-missing-relocation',bad,listing))
 missing=listing.replace('CONFIG_CODE','UNRECOGNIZED_CONFIG_CODE')
 oversized=re.sub(r'(?m)^(CONFIG_CODE\s+FARCODE\s+\S+\s+\S+\s+)\w+',r'\g<1>00010001',listing)
 wrong_end=re.sub(r'(?m)^([0-9a-f]{4}):[0-9a-f]{4}([*+ ]+\s+terminal_config_code_end\s*)$',r'\g<1>:0001\g<2>',listing)
 for label,text in [('missing-class',missing),('oversized-code',oversized),('incomplete-C-extent',wrong_end)]:
  assert text!=listing;mutations.append((label,raw,text))
 with tempfile.TemporaryDirectory() as directory:
  exe=Path(directory)/'BAD.EXE';mapfile=Path(directory)/'bad.map'
  for label,data,text in mutations:
   exe.write_bytes(data);mapfile.write_text(text)
   try:inspect_terminal_memory(exe,mapfile)
   except AssertionError:pass
   else:raise AssertionError(('Damaged configuration ABI accepted',label))
 result=dict(passed=True,binary_sha256=hashlib.sha256(raw).hexdigest(),configuration_bridge_pairs_verified=80,entry_argument_counts=[0,1,2,3,5,6,7,8,9,10],rejected_mutations=[m[0] for m in mutations],memory=memory,scope='Serialized DOS MZ and linker-map validation of 34 explicit near-cdecl entries including zero and ten arguments, ten compiler register callbacks, 24 resident word-cdecl callbacks and twelve explicit zero-argument callbacks and ten typed far ZMODEM callback pointers; exact argument-copy frames, target calls/returns, relocations and full configuration C extent. Independent CPU candidate/directory/owner suites and actual DOS child allocation exercise behavior.')
 (OUT/'config-far-checks.json').write_text(json.dumps(result,indent=2)+'\n');print('Configuration ABI:',len(mutations),'damaged frames/layouts rejected')
if __name__=='__main__':main()
