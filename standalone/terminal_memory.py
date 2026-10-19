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
 if 'terminal_snapshot_image' in symbols:
  frozen=address('terminal_snapshot_image');frozen_end=address('terminal_snapshot_image_end')
  frozen_seg,frozen_off=symbols['terminal_snapshot_image']
  assert frozen_end-frozen==2000 and frozen_off+2000<=65536
  assert frozen_end<=near_start or frozen>=near_start+near_size,'Frozen screen overlapsDGROUP'
  assert frozen_end<=shadow or frozen>=far_end,'Frozen screen overlaps shadow/history'
  assert word('terminal_snapshot_image_segment')==frozen_seg
  assert address('terminal_snapshot_image_segment') in relocations
  static_end=max(static_end,frozen_end)
  extra={'snapshot_relative_segment':frozen_seg,'snapshot_image_offset':frozen_off,'snapshot_bytes':2000,'snapshot_end_linear':frozen_end}
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
  assert config_bridges==79,'Incomplete configuration ABI validation'
  bridges+=config_bridges
  extra['configuration_bridge_pairs_verified']=config_bridges
 redisplay_bridges=0
 for name in ('terminal_redisplay_key','terminal_redisplay_before','terminal_redisplay_idle','terminal_redisplay_stop'):
  assert symbols[name][0]==near_code['relative_segment']
  assert symbols[name+'_far'][0]==symbols[name+'_impl'][0]==symbols['terminal_config_code_start'][0]
  far_call(name,name+'_far');near_call(name+'_far',name+'_impl')
  redisplay_bridges+=1
 bridges+=redisplay_bridges
 extra['redisplay_bridge_pairs_verified']=redisplay_bridges
 extra.update(resident_code_bytes=near_code['bytes'],resident_code_spare_bytes=65536-near_code['bytes'],code_segments=code_segments,far_code_bridge_pairs_verified=bridges)
 retained=(static_end+15)//16
 assert retained*16>=module_bytes,'PROGRAM retention would free serialized application data'
 allocated=((module_bytes+15)//16+header[5])*16
 assert allocated>=static_end,'MZ minimum allocation does not cover static storage'
 assert header[7]*16+header[8]==stack_end,'MZ SS:SP differs from linkedSTACK'
 assert retained+16<0xa000,'Static DOS parent cannot fit conventional memory'
 return {'near_bytes':near_size,'near_spare_bytes':65536-near_size,'near_relative_segment':ds,'far_relative_segment':far_seg,'shadow_offset':shadow_off,'history_offset':history_off,'far_bytes':71192,'history_relative_segment':history_seg,'history_bytes':63000,'far_end_linear':far_end,'stack_end_linear':stack_end,'loaded_module_bytes':module_bytes,'minimum_allocated_module_bytes':allocated,'retained_parent_paragraphs':retained+16,'far_pointer_relocations_verified':True,**extra}
