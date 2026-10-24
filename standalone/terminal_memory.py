"""Validate small-model near ABI and all retained static far extents from MZ/map."""
from pathlib import Path
import re,struct

def inspect_terminal_memory(binary,map_path):
 image=Path(binary).read_bytes();header=struct.unpack_from('<14H',image)
 assert image[:2]==b'MZ'
 size=(header[2]-1)*512+(header[1] or 512);start=header[4]*16
 assert start<=size<=len(image)
 module_bytes=size-start
 listing=Path(map_path).read_text()
 group=re.search(r'^DGROUP\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)',listing,re.M|re.I);assert group
 ds=int(group[1],16);near_start=ds*16+int(group[2],16);near_size=int(group[3],16)
 assert near_size<65536,'DS=SS near data/stack exceeds64KiB'
 symbols={name:(int(seg,16),int(off,16)) for seg,off,name in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
 def address(name):seg,off=symbols[name];return seg*16+off
 def word(name):
  at=start+address(name);assert at+2<=size,(name,'not in initialized image')
  return struct.unpack_from('<H',image,at)[0]
 shadow=address('erase_shadow_cells');history=address('terminal_history_buffer');far_end=address('terminal_far_storage_end');stack_end=address('terminal_stack_top')
 far_seg,shadow_off=symbols['erase_shadow_cells'];history_seg,history_off=symbols['terminal_history_buffer']
 assert history_seg==symbols['terminal_far_storage_end'][0] and far_seg!=history_seg
 assert far_end-history==63000 and history>=shadow+8192
 assert far_end<=near_start or shadow>=near_start+near_size,'Far storage overlaps DGROUP'
 assert shadow_off+8192<=65536 and history_off+63000<=65536,'Far storage wraps its segment'
 assert stack_end==near_start+near_size,'STACK end must cover all near data'
 assert word('erase_shadow_segment')==far_seg and word('erase_shadow_offset')==shadow_off
 assert word('terminal_history_start')==history_off and word('terminal_history_end')==history_off+63000
 assert word('terminal_history_pointer')==history_off
 assert struct.unpack_from('<H',image,start+address('terminal_history_pointer')+2)[0]==history_seg
 # Every serialized segment pointer must actually have an MZ relocation.
 relocations={seg*16+off for off,seg in (struct.unpack_from('<HH',image,header[12]+i*4) for i in range(header[3]))}
 assert address('erase_shadow_segment') in relocations
 assert address('terminal_history_pointer')+2 in relocations
 extra={};static_end=max(stack_end,far_end)
 if 'nreset_reset_data_image' in symbols:
  native_overlay=symbols['nreset_reset_data_image'][0]==0
  if native_overlay:
   workspace_seg,workspace_off=symbols['redisplay_snapshot'];assert workspace_off==0
   assert symbols['terminal_snapshot_image'][0]==workspace_seg,'Native workspace must share the checked far frame'
   native_start=address('redisplay_snapshot');workspace_end=address('terminal_snapshot_image_end')
   native_size=symbols['nreset_stack_top'][1];native_end=native_start+native_size
   native_image=native_start+symbols['nreset_reset_data_image'][1];native_top=native_end
   private_shadow=native_start+symbols['bank_shadow'][1];private_end=native_start+symbols['bank_shadow_end'][1]
   assert native_end==private_shadow and private_end<=workspace_end<=native_start+65536
   native_data_segment=0
  else:
   native_group=re.search(r'^RESET_GROUP\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)',listing,re.M|re.I);assert native_group
   native_start=int(native_group[1],16)*16+int(native_group[2],16)
   native_size=int(native_group[3],16);native_end=native_start+native_size
   native_image=address('nreset_reset_data_image');native_top=address('nreset_stack_top')
   private_shadow=address('bank_shadow');private_end=address('bank_shadow_end')
   native_data_segment=int(native_group[1],16)
  assert native_size<65536 and native_top-native_image==0xd600+4096 and native_top==native_end
  assert native_end<=near_start or native_start>=near_start+near_size,'Native reset bank overlaps root DGROUP'
  assert native_end<=shadow or native_start>=far_end,'Native reset bank overlaps root far buffers'
  native_shadow_bytes=6600 if 'terminal_native_width'in symbols else 6336
  assert private_end-private_shadow==native_shadow_bytes and symbols['bank_shadow'][1]+native_shadow_bytes<=65536
  assert private_end<=native_start or private_shadow>=native_end,'Native reset shadow overlaps private data'
  assert private_end<=near_start or private_shadow>=near_start+near_size,'Native reset shadow overlaps root DGROUP'
  assert private_end<=shadow or private_shadow>=far_end,'Native reset shadow aliases root far buffers'
  native_code=next(re.finditer(r'^RESET_CODE\s+FARCODE\s+\S+\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)',listing,re.M|re.I),None);assert native_code
  native_cs=int(native_code[1],16);assert int(native_code[3],16)<65536
  exported=[name for name in symbols if name.startswith('nreset_')]
  assert len(exported)>200 and all(symbols[name][0]in(native_cs,native_data_segment)for name in exported)
  assert symbols['screen_cursor_row'][0]==ds
  assert address('screen_cursor_row')!=address('nreset_screen_cursor_row')
  static_end=max(static_end,native_end,private_end)
  extra.update(native_reset_bank_bytes=native_size,native_reset_bank_start=native_start,
   native_reset_bank_end=native_end,native_reset_image_offset=native_image-native_start,
   native_reset_private_stack_bytes=4096,native_reset_shadow_bytes=native_shadow_bytes,native_reset_shadow_end=private_end,
   native_reset_namespace_symbols=len(exported),native_reset_code_segment=native_cs,
   native_reset_overlay=native_overlay,native_reset_additional_storage_bytes=0 if native_overlay else native_size+native_shadow_bytes)
  if native_overlay:extra.update(native_reset_workspace_end=workspace_end,native_reset_workspace_bytes=workspace_end-native_start)
 if 'terminal_snapshot_image' in symbols:
  frozen=address('terminal_snapshot_image');frozen_end=address('terminal_snapshot_image_end')
  frozen_seg,frozen_off=symbols['terminal_snapshot_image']
  assert frozen_end-frozen==2000 and frozen_off+2000<=65536
  assert frozen_end<=near_start or frozen>=near_start+near_size,'Frozen screen overlapsDGROUP'
  assert frozen_end<=shadow or frozen>=far_end,'Frozen screen overlaps shadow/history'
  assert word('terminal_snapshot_image_segment')==frozen_seg
  assert address('terminal_snapshot_image_segment') in relocations
  static_end=max(static_end,frozen_end)
  extra.update(snapshot_relative_segment=frozen_seg,snapshot_image_offset=frozen_off,snapshot_bytes=2000,snapshot_end_linear=frozen_end)
 # Independent full-screen owners must never alias across nested UI/EXEC.
 ui_buffers={}
 for name in ('browser_screen','ed_screen','program_screen','redisplay_live','redisplay_view'):
  if name not in symbols:continue
  lo=address(name);hi=address(name+'_end');seg,off=symbols[name]
  assert hi-lo==4000 and off+4000<=65536,(name,'invalid UI screen extent')
  assert hi<=near_start or lo>=near_start+near_size,(name,'UI screen overlapsDGROUP')
  assert hi<=shadow or lo>=far_end,(name,'UI screen overlaps native far storage')
  if 'terminal_snapshot_image' in symbols:assert hi<=frozen or lo>=frozen_end,(name,'UI screen overlaps frozen screen')
  for other in ui_buffers.values():assert hi<=other['start_linear'] or lo>=other['end_linear'],(name,'nested owners alias')
  assert lo>=module_bytes,(name,'UI buffer unexpectedly serialized in MZ')
  assert word(name+'_segment')==seg and address(name+'_segment') in relocations,(name,'invalid relocated segment pointer')
  ui_buffers[name]=dict(relative_segment=seg,offset=off,bytes=4000,start_linear=lo,end_linear=hi)
  static_end=max(static_end,hi)
 if ui_buffers:
  assert len(ui_buffers)==5,'Incomplete terminal UI screen ownership'
  assert len({b['relative_segment'] for b in ui_buffers.values()})==1
  extra.update(ui_screen_buffers=ui_buffers,far_ui_storage_bytes=20000)
 # Frozen redisplay bytes are independent of the live history writer.
 snap_lo=address('redisplay_snapshot');snap_hi=address('redisplay_snapshot_end')
 snap_seg,snap_off=symbols['redisplay_snapshot']
 assert snap_hi-snap_lo==63000 and snap_off+63000<=65536
 assert snap_lo>=module_bytes and (snap_hi<=near_start or snap_lo>=near_start+near_size)
 assert snap_hi<=shadow or snap_lo>=far_end
 if 'terminal_snapshot_image' in symbols:assert snap_hi<=frozen or snap_lo>=frozen_end,'Frozen redisplay overlaps screen snapshot'
 assert word('redisplay_snapshot_segment')==snap_seg and address('redisplay_snapshot_segment') in relocations
 for buf in ui_buffers.values():assert snap_hi<=buf['start_linear'] or snap_lo>=buf['end_linear']
 static_end=max(static_end,snap_hi)
 extra.update(redisplay_snapshot_bytes=63000,redisplay_snapshot_end_linear=snap_hi)
 # The far-aware viewer's row index shares the frozen-snapshot segment. It
 # must survive the parent's DOS memory shrink before a child EXEC as well.
 index_lo=address('_redisplay_row_index');index_hi=address('_redisplay_row_index_end')
 index_seg,index_off=symbols['_redisplay_row_index']
 assert index_seg==snap_seg and index_lo==snap_hi and index_hi-index_lo==494
 assert index_off+494<=65536 and index_lo>=module_bytes
 assert index_hi<=near_start or index_lo>=near_start+near_size
 assert index_hi<=shadow or index_lo>=far_end
 if 'terminal_snapshot_image' in symbols:assert index_hi<=frozen or index_lo>=frozen_end
 for buf in ui_buffers.values():assert index_hi<=buf['start_linear'] or index_lo>=buf['end_linear']
 static_end=max(static_end,index_hi)
 extra.update(redisplay_row_index_bytes=494,redisplay_row_index_relative_segment=index_seg,
              redisplay_row_index_offset=index_off,redisplay_row_index_end_linear=index_hi)
 # All executable segments must fit their real-mode segment and survive EXEC.
 code_segments=[]
 for name,kind,group,cseg,coff,csize in re.findall(r'^(\w+)\s+(CODE|FARCODE)\s+(\S+)\s+([0-9a-f]{4}):([0-9a-f]{4})\s+([0-9a-f]+)',listing,re.M|re.I):
  seg,off,length=int(cseg,16),int(coff,16),int(csize,16)
  lo=seg*16+off;hi=lo+length
  assert off+length<=65536,(name,'code segment exceeds64KiB')
  assert hi<=module_bytes,(name,'code absent from loaded image')
  assert hi<=near_start or lo>=near_start+near_size,(name,'code overlapsDGROUP')
  assert hi<=shadow or lo>=far_end,(name,'code overlaps shadow/history')
  for buf in ui_buffers.values():assert hi<=buf['start_linear'] or lo>=buf['end_linear'],(name,'code overlaps UI screen')
  assert hi<=static_end,(name,'PROGRAM would release executable code')
  for other in code_segments:
   other_lo=other['relative_segment']*16+other['offset']
   assert hi<=other_lo or lo>=other_lo+other['bytes'],(name,'code segments overlap')
  code_segments.append(dict(name=name,kind=kind,relative_segment=seg,offset=off,bytes=length))
 near_code=next(c for c in code_segments if c['name']=='_TEXT')
 if any(c['name']=='USAGE_CODE' for c in code_segments):
  usage=next(c for c in code_segments if c['name']=='USAGE_CODE')
  seg,off=symbols['terminal_usage'];end_seg,end_off=symbols['terminal_usage_end']
  assert seg==end_seg==usage['relative_segment'] and off==usage['offset']==0
  assert end_off==usage['bytes'] and seg!=ds,'Usage text must leave near data'
  # DOS09 needs the relocated far string's segment, with caller DS restored
  # before the shared shutdown/trap/exit path. Check the actual linked bytes.
  code=b'\x1e\xb8'+struct.pack('<H',seg)+b'\x8e\xd8\xba'+struct.pack('<H',off)+b'\xb4\x09\xcd\x21\x1f'
  module=image[start:start+module_bytes];at=module.find(code)
  assert at>=0 and module.find(code,at+1)<0 and at+2 in relocations,'Far usage DS/relocation boundary'
  assert near_code['relative_segment']*16<=at<near_code['relative_segment']*16+near_code['bytes']
  assert module[seg*16+end_off-1:seg*16+end_off]==b'$'
  extra.update(far_usage_bytes=usage['bytes'],far_usage_segment=seg,far_usage_DS_restore_verified=True)
 def raw(name,n):return image[start+address(name):start+address(name)+n]
 def far_call(source,target):
  assert raw(source,6)==b'\x9a'+struct.pack('<HH',symbols[target][1],symbols[target][0])+b'\xc3',(source,'far target/return')
  assert address(source)+3 in relocations,(source,'missing far-call relocation')
 def near_call(source,target,prefix=b'',suffix=b'\xcb'):
  code=raw(source,len(prefix)+3+len(suffix));assert code[:len(prefix)]==prefix
  at=len(prefix);assert code[at]==0xe8 and code[at+3:]==suffix,(source,'near call/return')
  displacement=struct.unpack_from('<h',code,at+1)[0]
  assert symbols[source][0]==symbols[target][0]
  assert (symbols[source][1]+at+3+displacement)&65535==symbols[target][1],(source,'wrong near target')
 bridges=0
 if 'terminal_process_code_start' in symbols:
  bank=next(c for c in code_segments if c['name']=='PROCESS_CODE')
  bank_seg=bank['relative_segment']
  assert bank_seg!=near_code['relative_segment'] and bank['offset']==0
  assert address('terminal_process_code_start')==bank_seg*16
  assert address('terminal_process_code_end')-address('terminal_process_code_start')==bank['bytes']
  assert symbols['process_run']==symbols['_process_run'] and symbols['process_run'][0]==near_code['relative_segment']
  for name in ['process_run_far','process_run_impl','process_string_length','process_result_disjoint','process_owned_disjoint',
               'process_saved_ds','process_saved_ss','process_saved_sp','process_exec_ax','process_exec_failed']:
   assert symbols[name][0]==bank_seg,name
  prefix=bytes.fromhex('55 89 e5 ff 76 08 ff 76 06 ff 76 04')
  suffix=bytes.fromhex('8d 66 00 5d c3')
  assert raw('process_run',22)==prefix+b'\x9a'+struct.pack('<HH',symbols['process_run_far'][1],bank_seg)+suffix
  assert address('process_run')+15 in relocations
  near_call('process_run_far','process_run_impl',prefix=bytes.fromhex('55 89 e5 ff 76 0a ff 76 08 ff 76 06'),suffix=bytes.fromhex('8d 66 00 5d cb'))
  extra.update(process_bank_bytes=bank['bytes'],process_bridge_pairs_verified=1,process_near_entry_bytes=22)
 if any(c['name']=='PRINT_CODE' for c in code_segments):
  far_code=next(c for c in code_segments if c['name']=='PRINT_CODE')
  controller_seg=far_code['relative_segment']
  assert controller_seg!=near_code['relative_segment'] and far_code['offset']==0,'Far code must have its own paragraph-aligned CS'
  assert address('terminal_controller_code_start')==controller_seg*16
  assert address('terminal_controller_code_end')-address('terminal_controller_code_start')==far_code['bytes']
  abi=Path(__file__).resolve().parents[1]/'src/terminal/controller_abi.inc'
  for kind,name in re.findall(r'^CONTROLLER_(ENTRY|SERVICE|STACK_SERVICE) (\w+)$',abi.read_text(),re.M):
   if kind=='ENTRY':
    assert symbols[name][0]==near_code['relative_segment']
    assert symbols[name+'_far'][0]==symbols[name+'_impl'][0]==controller_seg
    far_call(name,name+'_far');near_call(name+'_far',name+'_impl')
   else:
    assert symbols[name+'_service'][0]==controller_seg
    assert symbols[name+'_resident'][0]==symbols[name][0]==near_code['relative_segment']
    far_call(name+'_service',name+'_resident')
    near_call(name+'_resident',name,prefix=b'\x50' if kind=='STACK_SERVICE' else b'',suffix=b'\x58\xcb' if kind=='STACK_SERVICE' else b'\xcb')
   bridges+=1
  assert bridges==22,'Incomplete controller ABI validation'
  extra['controller_bridge_pairs_verified']=bridges
 if 'terminal_modem_code_start' in symbols:
  assert any(c['name']=='MODEM_CODE' for c in code_segments),'Modem segment missing from executable map'
 if any(c['name']=='MODEM_CODE' for c in code_segments):
  modem_code=next(c for c in code_segments if c['name']=='MODEM_CODE')
  modem_seg=modem_code['relative_segment']
  assert modem_seg!=near_code['relative_segment'] and modem_code['offset']==0,'Modem code needs a distinct paragraph-aligned CS'
  assert all(c['relative_segment']!=modem_seg for c in code_segments if c['name']!='MODEM_CODE'),'Modem CS aliases other code'
  assert address('terminal_modem_code_start')==modem_seg*16
  assert address('terminal_modem_code_end')-address('terminal_modem_code_start')==modem_code['bytes']
  abi=Path(__file__).resolve().parents[1]/'src/terminal/modem_abi.inc'
  modem_bridges=0
  for line in abi.read_text().splitlines():
   if not line or line.startswith(';'):continue
   fields=line.replace(',',' ').split();kind,name=fields[:2]
   if kind=='MODEM_ENTRY':
    assert len(fields)==2
    assert symbols[name][0]==near_code['relative_segment']
    assert symbols[name+'_far'][0]==symbols[name+'_impl'][0]==modem_seg
    far_call(name,name+'_far');near_call(name+'_far',name+'_impl')
   else:
    assert kind in ('MODEM_SERVICE','MODEM_CDECL_SERVICE')
    target=fields[2]
    assert symbols[name+'_service'][0]==modem_seg
    assert symbols[name+'_resident'][0]==symbols[target][0]==near_code['relative_segment']
    far_call(name+'_service',name+'_resident')
    prefix=b'';suffix=b'\xcb'
    if kind=='MODEM_CDECL_SERVICE':
     assert len(fields)==4
     count=int(fields[3]);assert 1<=count<=4
     prefix=b'\x55\x89\xe5'+b''.join(bytes([0xff,0x76,8+2*i]) for i in reversed(range(count)))
     suffix=b'\x8d\x66\x00\x5d\xcb'
    else:assert len(fields)==3
    near_call(name+'_resident',target,prefix=prefix,suffix=suffix)
   modem_bridges+=1
  assert modem_bridges==23,'Incomplete modem ABI validation'
  bridges+=modem_bridges
  extra['modem_bridge_pairs_verified']=modem_bridges
 if 'terminal_config_code_start' in symbols:
  assert any(c['name']=='CONFIG_CODE' for c in code_segments),'Configuration segment missing from executable map'
  config_code=next(c for c in code_segments if c['name']=='CONFIG_CODE')
  config_seg=config_code['relative_segment']
  assert config_code['kind']=='FARCODE' and config_code['offset']==0
  assert all(c['relative_segment']!=config_seg for c in code_segments if c['name']!='CONFIG_CODE'),'Configuration CS aliases other code'
  assert address('terminal_config_code_start')==config_seg*16
  assert address('terminal_config_code_end')-address('terminal_config_code_start')==config_code['bytes'],'Incomplete configuration extent'
  if 'terminal_record_receive_far' in symbols:
   lo=near_code['relative_segment']*16
   body=image[start+lo:start+lo+near_code['bytes']];sites=[]
   for name,count in (('terminal_record_receive_far',1),):
    assert symbols[name][0]==config_seg and symbols[name][1]<config_code['bytes'],(name,'RX recorder outside bank')
    pattern=b'\x9a'+struct.pack('<HH',symbols[name][1],config_seg)
    assert body.count(pattern)==count,(name,'RX binding count')
    offset=0
    for i in range(count):
     site=lo+body.index(pattern,offset);offset=site-lo+5
     assert site+3 in relocations,(name,'RX binding relocation')
     sites.append(site)
   # WAITFOR sees mapped normal leads. Parser continuations bypass it, so
   # recording before translation or inside the parser produces unmatchable
   # scripts even though every raw UART byte was faithfully captured.
   lead=address('terminal_receive_input');mapped=address('terminal_translate_input')
   assert image[start+lead:start+lead+3]==b'\xe8'+struct.pack('<H',(mapped-lead-3)&65535),'Record lead translation order'
   assert sites==[lead+3],'Recorder must follow translation at the sole normal lead boundary'
   extra['recording_matcher_lead_site']=lead
   auto_site=address('_terminal_auto_allowed')
   assert symbols['terminal_recording_owned_far'][0]==config_seg and symbols['terminal_recording_owned_far'][1]<config_code['bytes']
   assert image[start+auto_site:start+auto_site+5]==b'\x9a'+struct.pack('<HH',symbols['terminal_recording_owned_far'][1],config_seg)
   assert auto_site+3 in relocations
   sites.append(auto_site)
   code=image[start+config_seg*16:start+config_seg*16+config_code['bytes']]
   pattern=b'\x50\x9a'+struct.pack('<HH',symbols['_recording_terminal_receive'][1],config_seg)+b'\x83\xc4\x02'
   assert code.count(pattern)==1,'RX recorder callback arguments/cleanup/target'
   callback=config_seg*16+code.index(pattern)+1
   assert callback+3 in relocations,'RX callback relocation absent'
   extra.update(recording_rx_far_call_sites=sites,recording_rx_callback_site=callback)
   guards=[]
   for region_name,count in (('_TEXT',6),('MODEM_CODE',2),('PRINT_CODE',1)):
    region=next(c for c in code_segments if c['name']==region_name)
    lo=region['relative_segment']*16+region['offset'];code=image[start+lo:start+lo+region['bytes']]
    pattern=b'\x9a'+struct.pack('<HH',symbols['terminal_recording_owned_far'][1],config_seg)
    assert code.count(pattern)==count,(region_name,'recording actor guard count')
    offset=0
    for i in range(count):
     site=lo+code.index(pattern,offset);offset=site-lo+5
     assert site+3 in relocations,(region_name,'recording guard relocation')
     guards.append(site)
   code=image[start+config_seg*16:start+config_seg*16+config_code['bytes']]
   ui_sites=[];optimized=[]
   for name,count in (('_recording_ui_ready',2),('_terminal_autostart_busy',1)):
    assert symbols[name][0]==config_seg
    pattern=b'\x9a'+struct.pack('<HH',symbols[name][1],config_seg)
    far_count=code.count(pattern)
    local=[]
    if name=='_recording_ui_ready':
     # WLINK retains the far return frame when shortening same-CS C calls:
     # PUSH CS; CALL rel16; NOP, or PUSH CS; DS-prefix CALL rel16.
     for at in range(len(code)-5):
      if code[at:at+2]==b'\x0e\xe8' and code[at+4]==0x90:
       target=(at+4+struct.unpack_from('<h',code,at+2)[0])&65535
      elif code[at:at+3]==b'\x0e\x3e\xe8':
       target=(at+5+struct.unpack_from('<h',code,at+3)[0])&65535
      else:continue
      if target==symbols[name][1]:local.append(config_seg*16+at)
    assert far_count+len(local)==count,(name,'recorder UI boundary frames')
    ui_sites.extend(local);optimized.extend(local)
    offset=0
    for i in range(far_count):
     site=config_seg*16+code.index(pattern,offset);offset=site-config_seg*16+5
     assert site+3 in relocations,(name,'UI boundary relocation')
     ui_sites.append(site)
   extra.update(recording_actor_guard_sites=guards,recording_UI_boundary_sites=ui_sites,
                recording_UI_optimized_sites=optimized)
  if 'terminal_tx_origin_bits' in symbols:
   tag=address('terminal_tx_origin_bits');end=address('terminal_tx_origin_bits_end')
   assert symbols['terminal_tx_origin_bits'][0]==symbols['terminal_tx_origin_bits_end'][0]==config_seg
   assert end-tag==128 and end<=config_seg*16+config_code['bytes']
   assert image[start+tag:start+end]==bytes(128),'TX origins are not initialized in loaded storage'
   lo=near_code['relative_segment']*16
   near_body=image[start+lo:start+lo+near_code['bytes']]
   sites=[]
   for name,count in (('terminal_tx_origin_set_far',1),('terminal_tx_origin_delivered_far',2),('terminal_record_user_delivered_far',1)):
    assert symbols[name][0]==config_seg and symbols[name][1]<config_code['bytes'],(name,'TX provenance outside bank')
    pattern=b'\x9a'+struct.pack('<HH',symbols[name][1],config_seg)
    assert near_body.count(pattern)==count,(name,'missing/duplicated wire binding')
    offset=0
    for i in range(count):
     site=lo+near_body.index(pattern,offset);offset=site-lo+5
     assert site+3 in relocations,(name,'wire binding relocation')
     sites.append(site)
   code=image[start+config_seg*16:start+config_seg*16+config_code['bytes']]
   pattern=b'\x50\x9a'+struct.pack('<HH',symbols['_recording_terminal_transmit'][1],config_seg)+b'\x83\xc4\x02'
   assert code.count(pattern)==1,'Recorder wire callback argument/target/cleanup changed'
   callback=config_seg*16+code.index(pattern)+1
   assert callback+3 in relocations,'Recorder wire callback relocation absent'
   extra.update(recording_tx_origin_bytes=128,recording_tx_origin_start=tag,
    recording_tx_far_call_sites=sites,recording_tx_callback_site=callback)
  if '_recording_terminal_initialize' in symbols:
   for suffix in ('initialize','inspect','begin','transmit','receive','stop','cancel','cleanup','shutdown'):
    name='_recording_terminal_'+suffix
    assert symbols[name][0]==config_seg and symbols[name][1]<config_code['bytes'],(name,'foreground recorder outside bank')
   ranges=[]
   for name,length in (('_recording_terminal_owner',326),('_recording_terminal_path',64),('_recording_terminal_cookie',2)):
    lo=address(name);hi=lo+length
    assert symbols[name][0]==ds and near_start<=lo and hi<=near_start+near_size,(name,'foreground state outside DGROUP')
    assert all(hi<=other_lo or lo>=other_hi for other_lo,other_hi in ranges),(name,'foreground state alias')
    ranges.append((lo,hi))
   assert word('_recording_terminal_cookie')==0x5243,'Recorder initialization cookie absent or dirty'
   body=image[start+near_code['relative_segment']*16:start+near_code['relative_segment']*16+near_code['bytes']]
   sites=[]
   for name in ('_recording_terminal_initialize','_recording_terminal_shutdown'):
    pattern=b'\x9a'+struct.pack('<HH',symbols[name][1],symbols[name][0])
    assert body.count(pattern)==1,(name,'missing/duplicated foreground lifetime call')
    site=near_code['relative_segment']*16+body.index(pattern)
    assert site+3 in relocations,(name,'foreground lifetime relocation')
    sites.append(site)
   literals=(b'0123456789ABCDEF',b'transmitraw "',b'strcpy loc_prompt "',b'strpoke loc_prompt ',b' 34\r\n',
    b'waitfor loc_prompt ',b'if waitfor == 0\r\nexit\r\nendif\r\n',
    b'; LoC ASPECT recording - maintained runtime required\r\nstring loc_prompt\r\nproc main\r\n',b'endproc\r\n')
   code=image[start+config_seg*16:start+config_seg*16+config_code['bytes']]
   near=image[start+near_start:start+near_start+near_size]
   literal_sites=[]
   for i,literal in enumerate(literals):
    pattern=literal+b'\0'
    assert code.count(pattern)==1,('Recorder code template absent/duplicated',i)
    if i:assert pattern not in near,('Recorder template remains near',i)
    literal_sites.append(config_seg*16+code.index(pattern))
   extra.update(recording_terminal_state_bytes=392,recording_terminal_bank_functions_verified=9,
    recording_terminal_far_call_sites=sites,recorder_code_literal_bytes_verified=sum(len(x)+1 for x in literals),
    recorder_code_literal_sites=literal_sites)
  if '_recording_file_begin' in symbols:
   publisher_names=['_recording_file_'+n for n in ('begin','transmit','receive','flush','stop','cancel','cleanup','conflict')]
   core_names=['_aspect_recorder_'+n for n in ('start','transmit','receive','flush','stop','cancel')]
   for name in publisher_names+core_names:
    assert symbols[name][0]==config_seg,(name,'recording implementation outside CONFIG_CODE')
    assert symbols[name][1]<config_code['bytes'],(name,'recording function outside bank extent')
   table=address('_recording_dos_ops')
   assert near_start<=table and table+36<=near_start+near_size
   assert table+36<=module_bytes,'Recorder callback table relies on dirty BSS'
   callbacks=struct.unpack('<18H',raw('_recording_dos_ops',36))
   for i in range(9):
    off,seg=callbacks[2*i:2*i+2]
    assert seg==near_code['relative_segment'] and off<near_code['bytes'],('Recorder resident callback',i)
    assert table+4*i+2 in relocations,('Recorder callback relocation',i)
   # The DOS probe calls the far publisher; adapter reserve/release call their
   # far canonical owner APIs. Check actual compiled targets and relocations.
   body=image[start+near_code['relative_segment']*16:start+near_code['relative_segment']*16+near_code['bytes']]
   sites=[]
   for name in ('_recording_file_conflict','_capture_file_reserve','_capture_file_release'):
    pattern=b'\x9a'+struct.pack('<HH',symbols[name][1],symbols[name][0])
    assert body.count(pattern)==1,(name,'missing/duplicated recorder adapter call')
    site=near_code['relative_segment']*16+body.index(pattern)
    assert site+3 in relocations,(name,'recorder adapter relocation')
    sites.append(site)
   extra.update(recording_bank_functions_verified=14,recording_resident_callbacks_verified=9,
                recording_adapter_far_call_sites=sites)
  if '_capture_file_reserved' in symbols or '_capture_reservation' in symbols:
   for name in ('_capture_file_reserve','_capture_file_release','_capture_file_reserved'):
    assert symbols[name][0]==config_seg,(name,'reservation operation outside CONFIG_CODE')
   assert symbols['_capture_file_probe_owners'][0]==near_code['relative_segment'],'Reservation owner scan is not resident'
   descriptor=address('_capture_reservation')
   assert near_start<=descriptor and descriptor+8<=near_start+near_size,'Reservation guard outside near data'
   assert descriptor+8<=module_bytes,'Reservation guard relies on dirty BSS'
   assert image[start+descriptor:start+descriptor+8]==bytes(8),'Reservation guard not initialized idle'
   sites=[]
   for region,target in [(near_code,'_capture_file_reserved'),(config_code,'_capture_file_probe_owners')]:
    lo=region['relative_segment']*16+region['offset']
    body=image[start+lo:start+lo+region['bytes']]
    pattern=b'\x9a'+struct.pack('<HH',symbols[target][1],symbols[target][0])
    assert body.count(pattern)==1,(target,'missing/duplicated compiled far call')
    site=lo+body.index(pattern)
    assert site+3 in relocations,(target,'missing compiled far-call relocation')
    sites.append(site)
   extra['capture_reservation_far_bindings_verified']=2
   extra['capture_reservation_far_call_sites']=sites
   extra['capture_reservation_initialized_bytes']=8
  if '_command_menu_event' in symbols:
   assert symbols['_command_menu_event'][0]==config_seg,'Command menu is outside CONFIG_CODE'
   for name in ('_command_menu_active','_command_menu_action'):
    assert near_start<=address(name)<near_start+near_size-1,(name,'menu state outside DGROUP')
   extra['command_menu_far_code_verified']=True
  for name in ('_ymodem_run_impl','_batch_header_end_impl','_batch_header_encode_impl','_batch_header_decode_impl'):
   assert symbols[name][0]==config_seg,(name,'batch code outside CONFIG_CODE')
  assert near_start<=address('_ymodem_current') and address('_ymodem_current')+32<=near_start+near_size
  extra['ymodem_far_code_verified']=True
  if '_zm_run' in symbols:
   for name in ('_zm_run','_zw_headers','_zw_feed','_zw_header_encode','_zw_data_encode','_terminal_zmodem_store_impl'):
    assert symbols[name][0]==config_seg,(name,'ZMODEM outside CONFIG_CODE')
   table=address('_terminal_zmodem_ops')
   assert near_start<=table and table+40<=near_start+near_size,'ZMODEM callback table outside near data'
   callbacks=struct.unpack('<20H',raw('_terminal_zmodem_ops',40))
   names=('input','output','next','seek','read_file','close_source','open_received','write_received','commit','abort_received')
   for i,name in enumerate(names):
    off,seg=callbacks[2*i:2*i+2]
    assert (seg,off)==symbols['_terminal_zmodem_'+name],('ZMODEM callback identity',name)
    assert seg==config_seg and off<config_code['bytes'],('ZMODEM callback target',i)
    assert table+4*i+2 in relocations,('ZMODEM callback relocation',i)
   extra['zmodem_far_callbacks_verified']=10
  abi=Path(__file__).resolve().parents[1]/'src/terminal/config_abi.inc'
  config_bridges=0
  def cdecl_prefix(count,first):
   return b'\x55\x89\xe5'+b''.join(bytes([0xff,0x76,first+2*i]) for i in reversed(range(count)))
  for line in abi.read_text().splitlines():
   if not line or line.startswith(';'):continue
   fields=line.replace(',',' ').split();kind,name=fields[:2]
   if kind=='CONFIG_ENTRY':
    assert len(fields)==3
    count=int(fields[2]);assert 0<=count<=10
    assert symbols[name][0]==near_code['relative_segment']
    assert symbols[name+'_far'][0]==symbols[name+'_impl'][0]==config_seg
    prefix=cdecl_prefix(count,4);suffix=b'\x8d\x66\x00\x5d\xc3'
    code=raw(name,len(prefix)+5+len(suffix))
    assert code==prefix+b'\x9a'+struct.pack('<HH',symbols[name+'_far'][1],config_seg)+suffix,(name,'entry arguments/far target/return')
    assert address(name)+len(prefix)+3 in relocations,(name,'missing entry relocation')
    near_call(name+'_far',name+'_impl',prefix=cdecl_prefix(count,6),suffix=b'\x8d\x66\x00\x5d\xcb')
   else:
    assert kind in ('CONFIG_REGISTER','CONFIG_CDECL','CONFIG_ZERO')
    target=fields[2]
    service=name if kind=='CONFIG_REGISTER' else name+'_service'
    assert symbols[service][0]==config_seg
    assert symbols[name+'_resident'][0]==symbols[target][0]==near_code['relative_segment']
    far_call(service,name+'_resident')
    prefix=b'';suffix=b'\xcb'
    if kind=='CONFIG_CDECL':
     assert len(fields)==4
     count=int(fields[3]);assert 1<=count<=4
     prefix=cdecl_prefix(count,8);suffix=b'\x8d\x66\x00\x5d\xcb'
    else:assert len(fields)==3
    near_call(name+'_resident',target,prefix=prefix,suffix=suffix)
   config_bridges+=1
  assert config_bridges==94,'Incomplete configuration ABI validation'
  bridges+=config_bridges
  extra['configuration_bridge_pairs_verified']=config_bridges
 # Four unchanged resident no-argument APIs now enter the banked transfer UI.
 # Its BIOS keyboard/service callbacks must return to the bank with RETF.
 transfer_entries=('open','receiving','progress','restore')
 for suffix in transfer_entries:
  name='terminal_transfer_ui_'+suffix
  assert symbols[name][0]==near_code['relative_segment']
  assert symbols[name+'_impl'][0]==config_seg,(name,'UI outside CONFIG_CODE')
  far_call(name,name+'_impl')
 for suffix,target in (('service','terminal_transfer_service'),('keyboard','keyboard_poll'),('read','terminal_read_key')):
  name='terminal_transfer_ui_'+suffix+'_far'
  assert symbols[name][0]==symbols[target][0]==near_code['relative_segment']
  near_call(name,target)
 bridges+=7
 extra.update(transfer_ui_far_entries_verified=4,transfer_ui_resident_callbacks_verified=3)
 redisplay_bridges=0
 for name in ('terminal_redisplay_key','terminal_redisplay_before','terminal_redisplay_idle','terminal_redisplay_stop'):
  assert symbols[name][0]==near_code['relative_segment']
  assert symbols[name+'_far'][0]==symbols[name+'_impl'][0]==symbols['terminal_config_code_start'][0]
  far_call(name,name+'_far');near_call(name+'_far',name+'_impl')
  redisplay_bridges+=1
 bridges+=redisplay_bridges
 extra['redisplay_bridge_pairs_verified']=redisplay_bridges
 if any(c['name']=='ASPECT_CODE' for c in code_segments):
  aspect_code=next(c for c in code_segments if c['name']=='ASPECT_CODE')
  aspect_seg=aspect_code['relative_segment']
  if 'character_wide_edit_far'in symbols:
   assert symbols['character_wide_edit_far'][0]==symbols['character_wide_end'][0]==aspect_seg
   near_call('attribute_geometry_admit_far','attribute_geometry_admit')
   target=symbols['character_wide_edit_far'];call=b'\x9a'+struct.pack('<HH',target[1],target[0])
   resident=image[start+near_code['relative_segment']*16:start+near_code['relative_segment']*16+near_code['bytes']]
   assert resident.count(call)==2
   for at in (i for i in range(len(resident)-4)if resident[i:i+5]==call):assert near_code['relative_segment']*16+at+3 in relocations
   extra['wide_character_far_calls_verified']=2
  assert aspect_code['kind']=='FARCODE' and aspect_code['offset']==0
  assert all(c['relative_segment']!=aspect_seg for c in code_segments if c['name']!='ASPECT_CODE'),'ASPECT CS aliases other code'
  services=('terminal_render_prepare','terminal_render_revoke','terminal_render_validate',
            'terminal_render_failure_notice','terminal_render_unsupported',
            'terminal_render_typed_abort','terminal_render_read','terminal_render_read_now',
            'terminal_render_unread','terminal_render_send','terminal_render_string',
            'terminal_render_poll','terminal_render_cancel','terminal_render_control',
            'terminal_render_set_modes','terminal_render_reset_modes')
  for name in services+('resident_bridge_entry','resident_bridge_initialize',
                         'resident_bridge_disable','resident_bridge_callback',
                         'resident_bridge_abort','resident_bridge_caller_ds',
                         '_aspect_render_admit','_aspect_render_preflight_modes',
                         '_aspect_render_preflight_control','_aspect_render_client_admit'):
   assert symbols[name][0]==aspect_seg and symbols[name][1]<aspect_code['bytes'],(name,'ASPECT far code identity')
  for name in ('aspect_local_window','terminal_script_window','terminal_script_window_debug',
               'terminal_script_window_poll','local_window_key_poll','local_window_key_read'):
   assert symbols[name][0]==aspect_seg,(name,'script window escaped ASPECT code')
  for entry,target in [('terminal_script_window_keyboard_poll','keyboard_poll'),
                       ('terminal_script_window_keyboard_read','keyboard_read')]:
   assert symbols[entry][0]==near_code['relative_segment']
   near_call(entry,target)
  far_call('local_window_key_read','terminal_script_window_keyboard_read')
  extra['script_window_keyboard_far_adapters_verified']=True
  # Verify the actual resident adapters refer to relocated far service entries.
  # Symbol placement alone cannot prove the inter-segment calling convention.
  resident_lo=near_code['relative_segment']*16+near_code['offset']
  resident=image[start+resident_lo:start+resident_lo+near_code['bytes']]
  references=0
  controller_read_references=0
  for name in services:
   target=struct.pack('<HH',symbols[name][1],aspect_seg)
   if name=='terminal_render_read_now':
    owner_lo=address('line_controller_code_start');owner_hi=address('line_controller_code_end')
    owner=image[start+owner_lo:start+owner_hi]
    matches=[i for i in range(len(owner)-4) if owner[i]==0x9a and owner[i+1:i+5]==target
             and owner_lo+i+3 in relocations]
    assert len(matches)==1,(name,'missing relocated far-controller call')
    controller_read_references=len(matches)
    continue
   matches=[i for i in range(len(resident)-4)
            if resident[i] in (0x9a,0xea) and resident[i+1:i+5]==target
            and resident_lo+i+3 in relocations]
   assert matches,(name,'missing relocated resident far call/jump')
   references+=len(matches)
  assert symbols['terminal_aspect_emit_resident'][0]==symbols['terminal_receive_character'][0]==near_code['relative_segment']
  near_call('terminal_aspect_emit_resident','terminal_receive_character',prefix=b'\x50',suffix=b'\x83\xc4\x02\xcb')
  handoff=address('_script_handoff')
  assert near_start<=handoff and handoff+50<=near_start+near_size
  for offset,name in ((40,'_script_render_offset'),(42,'_script_render_segment'),
                      (44,'_script_render_token'),(46,'_script_render_version'),(48,'_script_flow_flags')):
   assert address(name)==handoff+offset,(name,'ASIOv5 flow capability layout')
  for name in ('terminal_aspect_active','terminal_aspect_adopt'):
   assert near_start<=address(name) and address(name)+2<=near_start+near_size
  assert address('terminal_aspect_adopt')==address('terminal_aspect_active')+2
  extra.update(aspect_far_services_verified=len(services),aspect_resident_far_references_verified=references,
               aspect_controller_read_references_verified=controller_read_references,
               aspect_emit_cdecl_bridge_verified=True,aspect_handoff_bytes=50,aspect_renderer_state_bytes=4)
  controller_start=address('line_controller_code_start');controller_end=address('line_controller_code_end')
  assert symbols['line_controller_code_start'][0]==symbols['line_controller_code_end'][0]==aspect_seg
  assert aspect_seg*16<=controller_start<controller_end<=aspect_seg*16+aspect_code['bytes']
  controller=image[start+controller_start:start+controller_end]
  controller_entries=(('csi_service_d668','line_insert_controller_far'),('csi_service_d73c','line_delete_controller_far'),
                      ('csi_service_daf2','line_alternate_controller_far'),('terminal_wait_control_n','line_wait_controller_far'))
  for entry,target in controller_entries:
   assert symbols[entry][0]==near_code['relative_segment'] and controller_start<=address(target)<controller_end
   far_call(entry,target)
  line_references=0
  def line_calls(source_bytes,source_start,target,wanted,opcode=0x9a):
   encoded=bytes([opcode])+struct.pack('<HH',symbols[target][1],symbols[target][0])
   matches=[i for i in range(len(source_bytes)-4) if source_bytes[i:i+5]==encoded and source_start+i+3 in relocations]
   assert len(matches)==wanted,(target,'line controller relocated far references')
  for name,wanted in (('terminal_line_insert_far',1),('terminal_line_delete_far',2)):
   assert symbols[name][0]==aspect_seg and symbols[name][1]<aspect_code['bytes'],(name,'line-plane far owner')
   line_calls(controller,controller_start,name,wanted);line_references+=wanted
  aspect_lo=aspect_seg*16
  aspect_bytes=image[start+aspect_lo:start+aspect_lo+aspect_code['bytes']]
  for bridge,target in (('line_native_insert_far','csi_insert_line'),('line_native_delete_far','csi_delete_line')):
   assert symbols[bridge][0]==symbols[target][0]==near_code['relative_segment']
   near_call(bridge,target,suffix=b'\xcb')
   line_calls(aspect_bytes,aspect_lo,bridge,2)
  for bridge,target,count in (('line_tick_far','terminal_tick_low',2),('line_poll_far','terminal_poll_io',1),('line_receive_far','uart_receive_byte',1)):
   assert symbols[bridge][0]==symbols[target][0]==near_code['relative_segment']
   near_call(bridge,target,suffix=b'\xcb');line_calls(controller,controller_start,bridge,count)
  assert symbols['attribute_screen_set_cursor_far'][0]==near_code['relative_segment']
  near_call('attribute_screen_set_cursor_far','screen_set_cursor',suffix=b'\xcb')
  line_calls(controller,controller_start,'attribute_screen_set_cursor_far',3)
  assert symbols['attribute_repair_admit_far'][0]==aspect_seg
  line_calls(controller,controller_start,'attribute_repair_admit_far',1)
  assert symbols['repair_abort_far'][0]==near_code['relative_segment']
  line_calls(controller,controller_start,'repair_abort_far',1,opcode=0xea)
  extra.update(line_attribute_far_entries_verified=2,line_attribute_controller_references_verified=line_references,
               line_attribute_video_callbacks_verified=2,line_controller_entry_pairs_verified=4,
               line_controller_register_callbacks_verified=3,line_controller_code_bytes=controller_end-controller_start)
 if 'terminal_status_live' in symbols:
  status_seg=next(c['relative_segment'] for c in code_segments if c['name']=='CONFIG_CODE')
  for name in ('terminal_status_live','status_renderer_refresh','terminal_reset_status_refresh',
               'terminal_reset_status_fill','status_ui_printf','status_character_fill',
               'status_message','status_sprintf','terminal_reset_sprintf','_status_format'):
   assert symbols[name][0]==status_seg,(name,'STATUS owner segment')
  for source,target,count in (('status_text_fill','text_fill_cells',3),
      ('status_text_packed','text_write_packed',2),('status_write_string','ui_write_string',3)):
   resident=source+'_resident'
   assert symbols[source][0]==status_seg and symbols[resident][0]==near_code['relative_segment']
   assert raw(source,8)==b'\x9a'+struct.pack('<HH',symbols[resident][1],symbols[resident][0])+b'\xc2'+struct.pack('<H',count*2)
   assert address(source)+3 in relocations
   prefix=b'\x55\x89\xe5'+b''.join(bytes([0xff,0x76,8+2*i]) for i in reversed(range(count)))
   near_call(resident,target,prefix=prefix,suffix=b'\x8d\x66\x00\x5d\xcb')
  far_call('status_strlen','status_strlen_resident')
  near_call('status_strlen_resident','program_strlen',prefix=b'\x55\x89\xe5\xff\x76\x08',suffix=b'\x8d\x66\x00\x5d\xcb')
  far_call('terminal_reset_uart_status','status_uart_resident')
  near_call('status_uart_resident','status_carrier_read')
  assert near_start<=address('terminal_reset_script_label') and address('terminal_reset_script_label')+15<=near_start+near_size
  extra.update(status_far_bridge_pairs_verified=5,status_script_label_bytes=15)
 if 'terminal_mouse_code_start' in symbols:
  mouse_code=next(c for c in code_segments if c['name']=='MOUSE_CODE')
  mouse_seg=mouse_code['relative_segment']
  assert mouse_code['offset']==0 and all(c['relative_segment']!=mouse_seg for c in code_segments if c['name']!='MOUSE_CODE')
  assert address('terminal_mouse_code_start')==mouse_seg*16
  assert address('terminal_mouse_code_end')-address('terminal_mouse_code_start')==mouse_code['bytes']
  for name,count,caller in [('_terminal_mouse_bootstrap',0,near_code['relative_segment']),
      ('_terminal_mouse_start',0,near_code['relative_segment']),
      ('_terminal_mouse_pause',0,near_code['relative_segment']),
      ('_terminal_mouse_resume',0,near_code['relative_segment']),
      ('_terminal_mouse_stage',2,config_seg),('_terminal_mouse_offer',2,config_seg),
      ('_terminal_mouse_commit',0,config_seg),('_terminal_mouse_discard',0,config_seg)]:
   assert symbols[name][0]==caller
   assert symbols[name+'_far'][0]==symbols[name+'_impl'][0]==mouse_seg
   prefix=cdecl_prefix(count,4);suffix=b'\x8d\x66\x00\x5d\xc3'
   assert raw(name,len(prefix)+5+len(suffix))==prefix+b'\x9a'+struct.pack('<HH',symbols[name+'_far'][1],mouse_seg)+suffix
   assert address(name)+len(prefix)+3 in relocations
   near_call(name+'_far',name+'_impl',prefix=cdecl_prefix(count,6),suffix=b'\x8d\x66\x00\x5d\xcb')
  for name in ('poll','read'):
   near_call('mouse_keyboard_'+name+'_resident','keyboard_'+name)
   assert symbols['_mouse_platform_'+name][0]==mouse_seg
  for name in ('mouse_callback','mouse_depth','_mouse_owner_bootstrap','_mouse_owner_open_impl',
      '_mouse_owner_suspend_impl','_mouse_owner_resume_impl','_mouse_owner_close_impl','terminal_mouse_exit'):
   assert symbols[name][0]==mouse_seg,name
  assert symbols['mouse_count']==symbols['keyboard_queue_count']
  assert symbols['mouse_code']==symbols['keyboard_queue_index']
  assert symbols['mouse_button_pending']==symbols['keyboard_queue_active']
  assert raw('mouse_enabled',6)==bytes([1]*6)
  assert raw('keyboard_queue_peek',12)==struct.pack('<6H',0x4800,0x4d00,0x5000,0x4b00,0x1c0d,0x011b)
  assert raw('keyboard_queue_values',12)==struct.pack('<6H',0x4800,0x4d00,0x5000,0x4b00,0x000d,0x001b)
  if 'terminal_trap_open' in symbols:
   code=raw('terminal_mouse_exit',96)
   assert b'\x9a'+struct.pack('<HH',*reversed(symbols['terminal_exit_guard_mouse_held'])) in code
  else:assert b'\xb8\x0e\x31\xcd\x21' in raw('terminal_mouse_exit',96),'Missing typed retained-memory fallback'
  extra.update(mouse_bridge_pairs_verified=10,mouse_code_bytes=mouse_code['bytes'],mouse_shared_native_state_bytes=28)
  bridges+=10
 bridges+=extra.get('process_bridge_pairs_verified',0)
 if 'native_reset_bank_bytes'in extra:
  code_end=max(item['relative_segment']*16+item['offset']+item['bytes']for item in code_segments)
  assert code_end<=native_start
  if not native_overlay:assert native_end<=near_start,'Static native bank must precede root data'
  owners=[(near_start,near_start+near_size),(shadow,far_end)]
  owners +=[(item['start_linear'],item['end_linear'])for item in ui_buffers.values()]
  if not native_overlay:
   owners.append((snap_lo,snap_hi))
   if 'terminal_snapshot_image'in symbols:owners.append((frozen,frozen_end))
   if '_redisplay_row_index'in symbols:
    owners.append((address('_redisplay_row_index'),address('_redisplay_row_index_end')))
  for lo,hi in owners:
   assert native_end<=lo or native_start>=hi,'Native data bank overlaps an existing live owner'
   assert private_end<=lo or private_shadow>=hi,'Native shadow overlaps an existing live owner'
  if 'terminal_native_width'in symbols:
   assert native_overlay
   entry=address('terminal_native_width');target_off=symbols['terminal_native_width_far'][1]
   assert symbols['terminal_native_width'][0]==near_code['relative_segment']
   assert image[start+entry:start+entry+6]==b'\x9a'+struct.pack('<HH',target_off,native_cs)+b'\xc3'
   assert entry+3 in relocations
   for name in ['terminal_native_width_far','reset_live_prepare','reset_live_finish','reset_live_validate',
                'reset_live_commit','reset_live_rollback','reset_live_active']:
    assert symbols[name][0]==native_cs,name
   # Inspect the compact projection against named root/native owners. A root
   # offset that grows past15 bits must never silently become a write flag.
   rows=[('csi_terminal_id',0),('attributes_normal_value',0),('attributes_current',1),('attributes_monochrome',0),
    ('screen_columns',0),('screen_video_row_bytes',0),('screen_attribute_row_bytes',1),('screen_last_column',1),
    ('csi_last_row',1),('screen_first_row',1),('screen_last_row',1),('screen_cursor_row',1),('screen_cursor_column',1),
    ('screen_visible_column',1),('screen_previous_row',1),('screen_previous_column',1),('screen_video_offset',1),
    ('screen_attribute_offset',1),('screen_viewport_enabled',1),('screen_viewport_active',1),('screen_viewport_offset',1),
    ('screen_viewport_left',1),('screen_viewport_right',0),('screen_use_bios_cursor',0),('screen_attribute_checks',0),('screen_cursor_wrap',0),
    ('screen_vertical_attribute_check',0),('screen_reverse_wrap_blocked',0),('erase_lineflags_enabled',0),('erase_protection_mode',0),
    ('erase_cell_count',1),('terminal_dec_keys',0),('terminal_tab_wrap',0),('csi_row_count',1)]
   assert address('reset_live_projection_end')-address('reset_live_projection')==len(rows)*4
   for i,(name,writable) in enumerate(rows):
    off=symbols[name][1];assert symbols[name][0]==ds and off<0x8000,name
    native='nreset_program_state_7a74'if name=='csi_row_count'else'nreset_'+name
    encoded=struct.unpack_from('<HH',image,start+address('reset_live_projection')+i*4)
    assert encoded==(off+writable*0x8000,symbols[native][1]),name
   extra['native_reset_projection_fields_verified']=len(rows)
   backup=ui_buffers['program_screen'];assert backup['bytes']==4000
   extra.update(native_reset_transaction=True,native_reset_backup_start=backup['start_linear'],
                native_reset_backup_bytes=4000,native_reset_transaction_bridge_verified=True)
 extra.update(resident_code_bytes=near_code['bytes'],resident_code_spare_bytes=65536-near_code['bytes'],code_segments=code_segments,far_code_bridge_pairs_verified=bridges)
 retained=(static_end+15)//16
 assert retained*16>=module_bytes,'PROGRAM retention would free serialized application data'
 allocated=((module_bytes+15)//16+header[5])*16
 assert allocated>=static_end,'MZ minimum allocation does not cover static storage'
 assert header[7]*16+header[8]==stack_end,'MZ SS:SP differs from linkedSTACK'
 assert retained+16<0xa000,'Static DOS parent cannot fit conventional memory'
 return {'near_bytes':near_size,'near_spare_bytes':65536-near_size,'near_relative_segment':ds,'far_relative_segment':far_seg,'shadow_offset':shadow_off,'history_offset':history_off,'far_bytes':71192,'history_relative_segment':history_seg,'history_bytes':63000,'far_end_linear':far_end,'stack_end_linear':stack_end,'loaded_module_bytes':module_bytes,'minimum_allocated_module_bytes':allocated,'retained_parent_paragraphs':retained+16,'far_pointer_relocations_verified':True,**extra}
