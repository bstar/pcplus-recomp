#!/usr/bin/env python3
"""DOS8086 ASPECT renderer lease with wide panes, fields and child-owned serial input."""
import argparse,hashlib,json,re,struct,subprocess
from pathlib import Path
import test_connection_dos as harness
from check_reset_live import fixture
from check_viewport_live import logical
from test_reset_live_dos import active_width_expected
from test_directory_key_bindings_dos import actions
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/aspect'))
from compiler import compile_source
import check_transport
ROOT=harness.ROOT
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--hidden-status',action='store_true');p.add_argument('--runner',type=Path,required=True);p.add_argument('--window',action='store_true');p.add_argument('--protected-erase',action='store_true');p.add_argument('--field-color',action='store_true');p.add_argument('--erase-case',choices=['all','K0','K2','J0','K1','J1','J2'],default='all');p.add_argument('--compiler',type=Path,help='Compile the source inside DOS with a compact passive observer');a=p.parse_args();binary=a.terminal.resolve();mft=json.loads((binary.parent/'manifest.json').read_text())
 assert mft['native_reset_transaction']and sha(binary)==mft['binary_sha256']
 assert mft['experimental_aspect_keys'], 'Wide ASPECT witness requires a parent built with --aspect-keys'
 for name,digest in mft['sources'].items():assert sha(ROOT/name)==digest,name
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build')and not out.exists();out.mkdir(parents=True)
 listing=(binary.parent/'terminal.map').read_text();symbols={n:(int(s,16),int(o,16))for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
 dg=int(re.search(r'^DGROUP\s+([0-9a-f]+):',listing,re.M|re.I)[1],16)
 names=['attributes_monochrome','screen_attribute_offset','screen_video_offset','screen_visible_column','screen_viewport_offset','screen_last_column','screen_attribute_row_bytes','csi_unimplemented_service','screen_columns','screen_attributes_base','screen_attribute_cells','erase_attribute_values_base','erase_attribute_values','screen_cursor_wrap','screen_attribute_checks','erase_protection_mode','attributes_preset_value','csi_erase_attribute','ui_flow_suppressed','erase_cell_count','screen_cursor_row','screen_cursor_column','screen_viewport_active','erase_shadow_offset','erase_shadow_segment','terminal_menu_pending','terminal_parser_active','terminal_deferred_count','_redisplay_active','_redisplay_live_ready']
 defines={n.upper().lstrip('_'):symbols[n][0]*16+symbols[n][1]-dg*16 for n in names}
 cs,off=symbols['terminal_native_width_far'];defines.update(DGROUP_REL=dg,LIVE_CODE_REL=cs,LIVE_OFF=off)
 lease_names=['render_attached','resident_bridge_busy','terminal_script_overlay_visible']
 assert len({symbols[n][0]for n in lease_names})==1
 defines.update(ASPECT_CODE_REL=symbols[lease_names[0]][0])
 defines.update({n.upper():symbols[n][1]for n in lease_names})
 (out/'wide_viewer_offsets.inc').write_text(''.join(f'%define {n} {v}\n'for n,v in defines.items()))
 watch=ROOT/'standalone/aspect_wide_watch.asm';observer=out/'VWATCH.COM'
 subprocess.run(['nasm','-fbin',*(['-DHIDDEN_STATUS']if a.hidden_status else[]),*(['-DCOMPACT_OBSERVER']if a.compiler else[]),*(['-DFIELD_COLOR']if a.field_color else[]),'-I'+str(out)+'/',str(watch),'-o',str(observer)],check=True);assert observer.stat().st_size<=0xff00
 # Bare explicit API fixture activates at the first cursor marker. All later
 # bytes, menus, deferred keys and replies execute through the product.
 banner=b'\x1b[6;18H\x1b[1;1HFIRST BYTE SAFE\x1b[6n\x1b[0c'
 rows=25 if a.hidden_status else 24
 packet=(b'3;121HREMOTE\x1b[6n\x1b[7;1H'+b'B'*132+b'\x1b[7;18H\x1b[3P\x1b[6n'+
  b'\x1b[2;4r\x1b[4;18H\x1bD\x1b[2;18H\x1bM\x1b[1;'+str(rows).encode()+b'r\x1b[4;132H!\x1b[6n\x1b[1;16HEND')
 if a.protected_erase:
  erase_commands={'K0':b'\x1b[3;121H\x1b[0K','K2':b'\x1b[7;18H\x1b[2K','J0':b'\x1b[2;60H\x1b[0J','K1':b'\x1b[5;80H\x1b[1K','J1':b'\x1b[6;79H\x1b[1J','J2':b'\x1b[4;52H\x1b[2J'}
  erase_packet=b''.join(erase_commands.values())if a.erase_case=='all'else erase_commands[a.erase_case]
  packet=packet[:-len(b'\x1b[1;16HEND')]+erase_packet+b'\x1b[1;16HEND'
 script='proc main\ntransmit "SCRIPTREADY^M"\nwaitfor "END" 10\nif waitfor\ntransmit "SCRIPTDONE^M"\nelse\ntransmit "SCRIPTFAIL^M"\nendif\nendproc\n'
 keys=('p900 enter 'if mft.get('special_edition')else'')+'p2300 a-1 '+('p600 a-z 'if a.window else'')+'p4500 r e a d y p500 a-x'
 source=Path(harness.__file__).read_text();needle="out=ROOT/'build/connection-dos'/name";assert source.count(needle)==1
 scope=dict(harness.__dict__);scope['LABEL_ROOT']=out;exec(compile(source.replace(needle,'out=LABEL_ROOT/name'),str(Path(harness.__file__)),'exec'),scope)
 short=out/'parent';short.mkdir();(short/'TERMINAL.EXE').write_bytes(binary.read_bytes());scope['BINARY']=short/'TERMINAL.EXE'
 runner=a.runner.resolve();rm=json.loads((runner.parent/'manifest.json').read_text());assert sha(runner)==rm['binary_sha256']
 for name,digest in rm['sources'].items():assert sha(ROOT/name)==digest,name
 (short/'ASPECT.EXE').write_bytes(runner.read_bytes())
 files={'VWATCH.COM':observer.read_bytes(),'ACTIONS.KEY':actions(b'D:\\WIDE.ASP'if a.compiler else b'D:\\WIDE.ASX',0)}
 if a.compiler:
  compiler=a.compiler.resolve();cm=json.loads((compiler.parent/'manifest.json').read_text());assert sha(compiler)==cm['binary_sha256']
  for name,digest in cm['sources'].items():assert sha(ROOT/name)==digest,name
  (short/'ASPCOMP.EXE').write_bytes(compiler.read_bytes());files['WIDE.ASP']=script.encode('cp437')
 else:files['WIDE.ASX']=compile_source(script)
 settings=bytearray(harness.fixture(timeout=5))
 if mft.get('experimental_custom_irq'):struct.pack_into('<HH',settings,0x184,4,3)
 if mft.get('experimental_mouse'):struct.pack_into('<HH',settings,0x4e4,8,4)
 result=scope['run']('product','success',keys,prm=bytes(settings),files=files,observer='VWATCH',cpu='8086',banner=banner,arguments='@D:\\TEST.PRM /D:CaseTest:23 /T:D:\\ACTIONS.KEY /A:NETWORK',online_triggers=[(b'SCRIPTREADY\r',[(.8,b'\x1b['),(1.4,packet)])])
 raw=(out/'product/WVIEW.BIN').read_bytes();assert len(raw)==(62 if a.compiler else 35810),len(raw)
 state=struct.unpack_from('<16H',raw);video=raw[32:4032];shadow=bytearray(raw[4032:12224]);flags=raw[12224:16320];values=raw[16320:20416]
 attached,bridge,overlay,service=struct.unpack_from('<4H',raw,32 if a.compiler else 35780)
 count,ticks=(0,0)if a.compiler else struct.unpack_from('<2H',raw,20416);assert count<=48
 frames=[raw[20420+i*320:20420+(i+1)*320]for i in range(count)]
 rows=25 if a.hidden_status else 24;size=rows*132
 # Independent field reshape oracle seeds a control terminal; it receives the
 # same complete wire payload without any local UI. It never supplies replies
 # or data to the DOS process under test.
 check_transport.BINARY=binary;check_transport.MAP=binary.parent/'terminal.map'
 m,address=fixture(rows=rows,hidden=int(a.hidden_status));assert m.call('terminal_native_width',ax=1,limit=3000000)==0
 f,v,words=active_width_expected(rows);m.uc.mem_write(address,struct.pack('<'+'H'*size,*words)+bytes(8192-size*2))
 for row in range(rows):m.uc.mem_write(0xb8000+row*160,struct.pack('<80H',*words[row*132:row*132+80]))
 m.uc.mem_write(m.symbols['screen_attribute_cells'],bytes(f)+bytes(4096-size));m.uc.mem_write(m.symbols['erase_attribute_values'],bytes(v)+bytes(4096-size));m.uc.mem_write(m.symbols['screen_line_flags'],bytes(128))
 for name,value in dict(screen_cursor_wrap=1,screen_attribute_checks=1,erase_protection_mode=1,attributes_preset_value=0x4e,attributes_monochrome=0 if a.field_color else 1).items():m.put(name,value)
 m.uc.mem_write(m.symbols['csi_erase_attribute'],b'\x07')
 m.feed(banner[len(b'\x1b[6;18H'):]+b'\x1b['+packet)
 if not a.compiler:
  for row in range(rows):shadow[row*264:row*264+160]=video[row*160:(row+1)*160]
 wire=(out/'product/serial.bin').read_bytes();checks=dict(result['checks'])
 if a.protected_erase:
  checks.pop('immediate_banner_not_dropped',None)
  checks['immediate_banner_parsed']=b'\x1b[1;16R'in wire and wire.index(b'\x1b[1;16R')<wire.index(b'SCRIPTREADY\r')
 checks.update(no_unimplemented_service=service==0,observer_header=state[0]==0x5756 and state[1:5]==(1,0,1,0),root_context_restored=state[5]==state[6]!=0,
  width_and_fields_retained=state[7]==size and state[10:14]==(1,1,1,1),final_cursor=state[8:10]==(0,18),
  actual_ASPECT_lease=attached>0,actual_script_window=(overlay>0 if a.window else overlay==0),
  actual_ASPECT_script=b'SCRIPTREADY\r'in wire and b'SCRIPTDONE\r'in wire and b'SCRIPTFAIL'not in wire,
  exact_logical_screen=bytes(shadow[:size*2])==logical(m,address,rows),
  exact_flags=flags==bytes(m.uc.mem_read(m.symbols['screen_attribute_cells'],4096)),exact_values=values==bytes(m.uc.mem_read(m.symbols['erase_attribute_values'],4096)),
  wide_CPR_during_child=b'\x1b[3;127R'in wire and b'\x1b[7;18R'in wire and b'\x1b[4;132R'in wire,
  post_child_keyboard=b'ready'in wire,unmodified_product=sha(short/'TERMINAL.EXE')==mft['binary_sha256'],unmodified_runner=sha(short/'ASPECT.EXE')==rm['binary_sha256'])
 if a.compiler:
  for name in ['exact_logical_screen','exact_flags','exact_values']:del checks[name]
  checks['exact_DOS_compiled_ASX']=(out/'product/WIDE.ASX').exists()and(out/'product/WIDE.ASX').read_bytes()==compile_source(script)
  checks['unmodified_compiler']=sha(short/'ASPCOMP.EXE')==cm['binary_sha256']
 report=dict(failure_geometry=list(struct.unpack_from('<11H',raw,40 if a.compiler else 35788)),unimplemented_service=service,passed=all(checks.values()),checks=checks,state=list(state),frame_count=count,viewer_ticks=ticks,attached_ticks=attached,bridge_ticks=bridge,overlay_ticks=overlay,binary_sha256=sha(binary),runner_sha256=sha(runner),field_color=a.field_color,protected_erase=a.protected_erase,erase_case=a.erase_case,source_compilation=bool(a.compiler),compiler_sha256=sha(compiler)if a.compiler else None,full_plane_snapshot=not bool(a.compiler),window=a.window,hidden_status=a.hidden_status,content_rows=rows,sources=mft['sources'],checker_sha256=sha(Path(__file__)),observer_sha256=sha(watch),original_inputs=[],artifacts={str(p.relative_to(ROOT)):sha(p)for p in out.rglob('*')if p.is_file()},scope=__doc__+(' Compact observer checks exact DOS source compilation and exit geometry, without full plane snapshots.'if a.compiler else' Full observer checks exact planes for a precompiled child.')+' Observer stages initial fields and explicit width once; actual ASX runs through parent/child RPC and UART. Passive exit planes compare against normal parser replay. No physical acceptance claimed.')
 (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print(('PASS'if report['passed']else'FAIL')+' DOS wide ASPECT '+json.dumps(checks));return 0 if report['passed']else 1
if __name__=='__main__':raise SystemExit(main())
