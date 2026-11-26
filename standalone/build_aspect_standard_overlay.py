#!/usr/bin/env python3
"""Experimental GET/Help and optional screen overlays; no package/physical promotion."""
import argparse,json,re,shutil,struct,subprocess
from pathlib import Path
from build_path_session import ROOT,sha


def mz_overlay(data):
 assert len(data)>=32
 h=struct.unpack_from('<14H',data);assert h[0]==0x5a4d and h[13]==0 and h[2] and h[1]<512
 declared=h[2]*512-(512-h[1] if h[1] else 0);header=h[4]*16
 assert 32<=header<declared<len(data) and h[12]>=28 and h[12]+h[3]*4<=header
 import hashlib
 digest=lambda b:hashlib.sha256(b).hexdigest()
 return dict(header_bytes=header,root_declared_bytes=declared,root_image_bytes=declared-header,
  root_image_sha256=digest(data[header:declared]),overlay_trailer_bytes=len(data)-declared,
  overlay_trailer_sha256=digest(data[declared:]),
  exact_minimum_including_PSP=((declared-header+15)//16+h[5]+16)*16,
  page_minimum_including_PSP=(h[2]*32-h[4]+h[5]+16)*16,
  limitation='Root MZ bounds and separate complete trailer identity, not a general parser of arbitrary overlay records. No header padding inserted.')


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--notice',action='store_true',help='Also share notice code; requires resident notice checkpoint preparation')
 p.add_argument('--program',action='store_true',help='Also share the synchronous PROGRAM controller; keep its platform/IRQ adapters resident')
 p.add_argument('--screen',action='store_true',help='Also share native local-screen handlers; keep client gates/state resident')
 p.add_argument('--serial',action='store_true',help='Also share cold ASIO code; requires resident hot readers and split serial gates')
 p.add_argument('--checked-io',action='store_true',help='Reject short overlay code/relocation reads through a source-owned DOS I/O adapter')
 a=p.parse_args()
 assert not a.program or a.notice
 base=a.base.resolve();out=a.output.resolve()
 assert base.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
 m=json.loads((base/'manifest.json').read_text());assert m['experimental_overlay_layout_ready']
 if a.screen:assert m['experimental_screen_commands']
 if a.serial:assert m.get('experimental_serial_overlay_ready') and m['experimental_serial_bank'] and m['experimental_register_handoff']
 assert sha(base/'ASPECT.EXE')==m['binary_sha256'] and m['original_inputs']==[]
 for name,h in m['sources'].items():assert sha(ROOT/name)==h,name
 out.mkdir();groups=[[],[],[],[],[],[],[]];objects={}
 help_names={'input-view.obj','input-notice_content.obj','input-format.obj','input-document.obj','input-resource.obj',
             'help-cursor.obj','help-resource-io.obj','help_overlay_bridge_overlay.obj'}
 get_names={'get_runtime-c-bank.obj','get_context-c-bank.obj','get_command-c-bank.obj','get_native_field-c-bank.obj',
  'get_vm_bindings-c-bank.obj','get-field-bank.obj','get_native-bank.obj','get_checkpoint-bank.obj','get_command-bank.obj',
  'get_native_field-bank.obj','get_vm_bindings-bank.obj','get_bank_overlay-bank.obj'}
 notice_names={'notice-shared-owner-normal.obj','notice-shared-runtime.obj','notice-resident-checkpoint.obj','program_notice.obj'}
 screen_names={'screen_commands.obj','screen-runtime.obj','screen-client.obj','screen-bank-overlay.obj'}
 serial_names={'serial.o','serial-bank-overlay.obj','register_handoff.o'}
 seen=set()
 for line in (base/'GETVM.lnk').read_text().splitlines():
  if not line.startswith('file '):continue
  original=Path(line[5:])
  if not original.is_absolute():
   original=base/original
   if not original.exists():original=original.with_suffix('.o')
  assert original.is_file(),original
  name='obj'+str(len(objects)).zfill(4)+'.obj';shutil.copyfile(original,out/name)
  objects[name]=dict(original=str(original.relative_to(ROOT)),sha256=sha(out/name))
  group=1 if original.name in get_names else 2 if original.name in help_names else 0
  if a.notice and (original.parent==ROOT/'build/notice-bank' or original.name in notice_names):group=3
  if a.program and original.name=='native_program_far.obj':group=4
  if a.screen and original.name in screen_names:group=5
  if a.serial and original.name in serial_names:group=6
  seen.add(original.name);groups[group].append('file '+name)
 assert get_names<=seen and help_names<=seen
 if a.notice:assert notice_names<=seen
 if a.program:assert 'native_program_far.obj' in seen
 if a.screen:assert screen_names<=seen and 'screen-bank-root.obj' in seen
 if a.serial:assert serial_names<=seen and 'serial-bank-root.obj' in seen and 'serial_bank.obj' not in seen
 if a.checked_io:
  path=ROOT/'src/aspect/overlay_io.asm';obj=out/'checked-io.obj'
  subprocess.run(['nasm','-fobj',str(path),'-o',str(obj)],check=True)
  groups[0].append('file checked-io.obj')
  objects['checked-io.obj']=dict(original='src/aspect/overlay_io.asm',sha256=sha(obj))
  m['sources']['src/aspect/overlay_io.asm']=sha(path)
 link=['system dos','option quiet','option stack=8192','option standard','option packcode=0',
       # Use DOSSEG rather than a manual ORDER. Its overlay-aware ordering
       # keeps manager tables in its CS and sorts the preloaded data section
       # too: far state before DGROUP, _NULL first, BSS then stack last.
       'name ASPECT.EXE','option map=ASPECT.map',*groups[0],'begin','section',*groups[1],'section',*groups[2],
       *(['section',*groups[3]] if a.notice else []),*(['section',*groups[4]] if a.program else []),
       *(['section',*groups[5]] if a.screen else []),*(['section',*groups[6]] if a.serial else []),'end']
 (out/'OVERLAY.lnk').write_text('\n'.join(link)+'\n')
 subprocess.run(['wlink','@OVERLAY.lnk'],cwd=out,check=True)
 layout=mz_overlay((out/'ASPECT.EXE').read_bytes());text=(out/'ASPECT.map').read_text()
 symbols={n:(int(s,16)*16+int(o,16)) for s,o,n in re.findall(r'^\s*([0-9a-f]{4}):([0-9a-f]{4,8})[*+]?\s+(\w+)\s*$',text,re.M|re.I)}
 segments={n:dict(segment=int(s,16),offset=int(o,16),size=int(z,16)) for n,cls,s,o,z in re.findall(
  r'^(\w+)\s+(\w+)\s+\w+\s+([0-9a-f]{4}):([0-9a-f]{4,8})\s+([0-9a-f]{8})\s*$',text,re.M|re.I) if cls!='_OVLCODE'}
 group=re.search(r'DGROUP\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)',text,re.I)
 ds=int(group[1],16)*16+int(group[2],16);size=int(group[3],16)
 assert size<=65536 and ds<=symbols['get_resident_checkpoint_state']<ds+size
 if a.notice:assert ds<=symbols['notice_resident_checkpoint_state']<ds+size
 assert segments['STACK']['size']==8192 and segments['_TEXT']['size']<=65536
 assert all(symbols[n]<layout['root_image_bytes'] for n in ('__OVLTAB__','__OVLSTARTVEC__','__LOVLLDR__'))
 assert symbols['__OVLENDVEC__']<=layout['root_image_bytes']
 addresses={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^\s*([0-9a-f]{4}):([0-9a-f]{4,8})[*+]?\s+(\w+)\s*$',text,re.M|re.I)}
 assert all(addresses[n][0]==addresses['__LOVLLDR__'][0] for n in ('__OVLTAB__','__OVLSTARTVEC__','__OVLENDVEC__'))
 assert segments['GET_RUNTIME_STORAGE']['size']==206
 linear=lambda name:segments[name]['segment']*16+segments[name]['offset']
 assert linear('GET_RUNTIME_STORAGE')+206<=linear('_NULL')==ds
 assert linear('_NULL')<linear('CONST')<linear('_BSS')<linear('STACK')
 assert linear('STACK')+8192==ds+size
 serial_layout=None
 screen_layout=None
 if a.screen:
  bank=segments['SCRIPT_SCREEN_CODE'];near=segments['_TEXT']
  in_segment=lambda name,segment:addresses[name][0]==segment['segment'] and segment['offset']<=addresses[name][1]<segment['offset']+segment['size']
  entries=['aspect_screen_'+name+'_entry' for name in ('box','clear','locate','scroll','getvattr','putvattr','home')]
  readers=['screen_'+name+'_resident' for name in ('bounded','store','byte','option')]
  resident=entries+readers+['_screen_runtime_failure','_screen_wire_request','_screen_client_check','_aspect_render_screen_ready']
  assert all(in_segment(name,near) and symbols[name]<layout['root_image_bytes'] for name in resident)
  assert all(in_segment('screen_'+name+'_far',bank) for name in ('box','clear','locate','scroll','getvattr','putvattr','home'))
  assert all(in_segment(name,bank) for name in ('aspect_screen_box','aspect_screen_scroll','aspect_screen_getvattr','_runtime_screen_enter','_runtime_screen_scroll','_runtime_screen_read'))
  assert ds<=symbols['_runtime_screen_values'] and symbols['_runtime_screen_values']+12<=ds+size
  assert symbols['aspect_screen_physical_stride']==symbols['_runtime_screen_values']+10
  # The scalar client shares its callers' overlay; private owner admission and
  # near client validation remain resident behind a declared FAR entry.
  assert 'SCREEN_CLIENT_CODE' not in segments
  assert in_segment('_aspect_render_screen_scalar',bank)
  section=3+int(a.notice)+int(a.program)
  assert re.search(r'Overlay section '+str(section)+r' address [^\n]+\n=+.*?\nSCRIPT_SCREEN_CODE\s',text,re.S)
  screen_layout=dict(passed=True,screen_bank_bytes=bank['size'],resident_ready_in_near_code=True,
   resident_data_bytes=12,resident_entry_count=len(entries),resident_reader_count=len(readers),
   overlay_section=section,overlay_objects=sorted(screen_names),
   scope='Trusted-linker placement: seven resident entry gates, four resident operand readers, resident abort/wire/client/owner-admission gates and12-byte data; native handlers, scalar client, C runtime and bank-local wrappers overlay. Execution/unwind and DOS memory acceptance require separate tests.')
 if a.serial:
  bank=segments['ASIO_CODE'];near=segments['_TEXT']
  in_segment=lambda name,segment:addresses[name][0]==segment['segment'] and segment['offset']<=addresses[name][1]<segment['offset']+segment['size']
  hot=['_aspect_serial_'+n for n in ('directory_entry','directory_record','translate','translation_policy')]
  cold=['_aspect_serial_'+n for n in ('preload','open','close','compile_pause','compile_resume')]
  callbacks=['_serial_bank_'+n+'_resident' for n in ('psp','render_active','render_prepare','accounting','backend_open','render_attach','break_release','flow_alive','ticks','poll','tx_empty','backend_close','compile_hold','compile_release')]
  resident=hot+cold+callbacks+['uart_receive_interrupt','_aspect_serial_backend_open','_aspect_serial_backend_close','_aspect_serial_poll','_aspect_render_client_check','_aspect_render_request','_aspect_render_callback_dispatch','_aspect_render_callback_offset']
  assert all(in_segment(name,near) and symbols[name]<layout['root_image_bytes'] for name in resident)
  assert all(in_segment(name+'_far',bank) for name in cold)
  assert all(in_segment('_aspect_register_'+name,bank) for name in ('validate','attach','start','publish'))
  assert all(in_segment(name+'_impl',bank) for name in hot+cold)
  fields={'_aspect_serial_input_translation':256,'_aspect_serial_input_translation_mode':2,'_aspect_serial_directory_record_data':114,'_aspect_serial_directory_entry_data':2}
  assert all(ds<=symbols[name] and symbols[name]+count<=ds+size for name,count in fields.items())
  section=3+int(a.notice)+int(a.program)+int(a.screen)
  assert re.search(r'Overlay section '+str(section)+r' address [^\n]+\n=+.*?\nASIO_CODE\s',text,re.S)
  vectors=text.split('|   Overlay Vectors   |',1)[1].split('Overlay section ',1)[0]
  for name in cold+['_aspect_register_start']:
   assert re.search(r'section '+str(section)+r' : '+re.escape(name+'_far' if name in cold else name)+r'\s*$',vectors,re.M)
  assert not any(re.search(r' : '+re.escape(name)+r'\s*$',vectors,re.M) for name in hot)
  serial_layout=dict(passed=True,serial_bank_bytes=bank['size'],resident_entry_count=9,resident_hot_reader_count=4,
   resident_callback_count=len(callbacks),existing_hot_data_bytes=sum(fields.values()),overlay_section=section,
   overlay_objects=sorted(serial_names),scope='Trusted-linker placement only: resident hot readers, public/callback gates, UART/backend and renderer private admission; cold serial and all register APIs share ASIO_CODE. No new DATA or reduced buffers/stacks; actual hot equivalence, loader and lifecycle proof required.')
 if a.checked_io:
  # The only non-exact read allowed by the adapter is the linker's initial
  # far-data/DGROUP preload ending in BSS/stack. Bind that identity to this
  # trusted layout; replaceable code and relocation scratch cannot alias it.
  assert symbols['_runtime_get_field_storage']==linear('GET_RUNTIME_STORAGE')
  assert symbols['_runtime_file']==linear('_BSS')==symbols['__End_YI']
  assert linear('_BSS')>linear('GET_RUNTIME_STORAGE')
 for name in ('LOCHELP.HLP','help-resource.json'):
  if (base/name).exists():shutil.copyfile(base/name,out/name)
 m.pop('MZ_header_layout',None)
 m.update(binary_sha256=sha(out/'ASPECT.EXE'),experimental_standard_overlays=True,experimental_notice_overlay=a.notice,experimental_program_overlay=a.program,experimental_screen_overlay=a.screen,experimental_serial_overlay=a.serial,package_eligible=False,
  base_manifest_sha256=sha(base/'manifest.json'),base_binary_sha256=sha(base/'ASPECT.EXE'),overlay_objects=objects,
  MZ_overlay_layout=layout,
  GET_bank_layout=dict(passed=True,near_code_bytes=segments['_TEXT']['size'],near_code_spare=65536-segments['_TEXT']['size'],
   GET_code_bytes=segments['GET_VM_CODE']['size'],editor_code_bytes=segments['GET_FIELD_CODE']['size'],
   Help_code_bytes=segments['HELP_OVL_CODE']['size'],field_state_bytes=206,DGROUP_bytes=size,stack_bytes=8192,
   notice_code_bytes=segments['NOTICECODE']['size'],notice_overlay=a.notice,
   program_code_bytes=segments['PROGRAMCODE']['size'],program_overlay=a.program,
   screen_overlay=a.screen,screen_code_bytes=segments['SCRIPT_SCREEN_CODE']['size'] if 'SCRIPT_SCREEN_CODE' in segments else 0,
   minimum_DOS_bytes_including_PSP=layout['exact_minimum_including_PSP'],
   page_rounded_minimum_including_PSP=layout['page_minimum_including_PSP'],
   scope='Preliminary trusted-linker map/MZ bounds only; full callback, checkpoint, recovery and allocation acceptance requires DOS execution.'),
  scope='Experimental standard overlays for GET and Help, with resident ISR/mouse code and SS-relative GET checkpoint state. Not packaged or physically verified.')
 m['sources']['standalone/build_aspect_standard_overlay.py']=sha(Path(__file__))
 if screen_layout:m['screen_bank_layout']=screen_layout
 if serial_layout:m['serial_bank_layout']=serial_layout
 if a.checked_io:
  m['experimental_checked_overlay_io']=True
  m['checked_overlay_io_preload']=dict(segment=addresses['_runtime_get_field_storage'][0],offset=0,
   initialized_prefix_bytes=linear('_BSS')-linear('GET_RUNTIME_STORAGE'),
   scope='Only the exact initial far-data preload may end after the complete initialized prefix; code/relocation short reads fail.')
 (out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps(dict(binary=m['binary_sha256'],layout=m['GET_bank_layout']),indent=2))


if __name__=='__main__':main()
