#!/usr/bin/env python3
"""DOS8086 wide UI with passive timer frames, real split-parser input and exit planes."""
import argparse,hashlib,json,re,struct,subprocess
from pathlib import Path
import test_connection_dos as harness
from check_reset_live import fixture
from check_viewport_live import logical
from test_reset_live_dos import active_width_expected
import check_transport
ROOT=harness.ROOT
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--hidden-status',action='store_true');a=p.parse_args();binary=a.terminal.resolve();mft=json.loads((binary.parent/'manifest.json').read_text())
 assert mft['native_reset_transaction']and sha(binary)==mft['binary_sha256']
 for name,digest in mft['sources'].items():assert sha(ROOT/name)==digest,name
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build')and not out.exists();out.mkdir(parents=True)
 listing=(binary.parent/'terminal.map').read_text();symbols={n:(int(s,16),int(o,16))for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
 dg=int(re.search(r'^DGROUP\s+([0-9a-f]+):',listing,re.M|re.I)[1],16)
 names=['screen_columns','screen_attributes_base','screen_attribute_cells','erase_attribute_values_base','erase_attribute_values','screen_cursor_wrap','screen_attribute_checks','erase_protection_mode','attributes_preset_value','csi_erase_attribute','ui_flow_suppressed','erase_cell_count','screen_cursor_row','screen_cursor_column','screen_viewport_active','erase_shadow_offset','erase_shadow_segment','terminal_menu_pending','terminal_parser_active','terminal_deferred_count','_redisplay_active','_redisplay_live_ready']
 defines={n.upper().lstrip('_'):symbols[n][0]*16+symbols[n][1]-dg*16 for n in names}
 cs,off=symbols['terminal_native_width_far'];defines.update(DGROUP_REL=dg,LIVE_CODE_REL=cs,LIVE_OFF=off)
 (out/'wide_viewer_offsets.inc').write_text(''.join(f'%define {n} {v}\n'for n,v in defines.items()))
 watch=ROOT/'standalone/wide_viewer_watch.asm';observer=out/'VWATCH.COM'
 subprocess.run(['nasm','-fbin',*(['-DHIDDEN_STATUS']if a.hidden_status else[]),'-I'+str(out)+'/',str(watch),'-o',str(observer)],check=True);assert observer.stat().st_size<=0xff00
 # Bare explicit API fixture activates at the first cursor marker. All later
 # bytes, menus, deferred keys and replies execute through the product.
 banner=b'\x1b[6;18H\x1b[1;1HFIRST BYTE SAFE\x1b[6n\x1b[0c'
 background=b'\x1b[3;121HREMOTE\x1b[6n\x1b[2;1HLIVE'
 field=b'\x1b[7;1H'+b'B'*132+b'\x1b[7;18H\x1b[3P\x1b[6n'
 completion=b'4;132H!\x1b[6n'+background+field+b'\x1b[1;16H'
 keys=('p900 enter 'if mft.get('special_edition')else'')+'p1600 a-z p500 right p400 right p400 enter p400 escape p a u s e enter p400 a-z p300 right p300 right p1800 escape p400 a-= p600 escape p400 r e a d y p400 a-x'
 source=Path(harness.__file__).read_text();needle="out=ROOT/'build/connection-dos'/name";assert source.count(needle)==1
 scope=dict(harness.__dict__);scope['LABEL_ROOT']=out;exec(compile(source.replace(needle,'out=LABEL_ROOT/name'),str(Path(harness.__file__)),'exec'),scope)
 short=out/'parent';short.mkdir();(short/'TERMINAL.EXE').write_bytes(binary.read_bytes());scope['BINARY']=short/'TERMINAL.EXE'
 settings=bytearray(harness.fixture(timeout=5))
 if mft.get('experimental_custom_irq'):struct.pack_into('<HH',settings,0x184,4,3)
 if mft.get('experimental_mouse'):struct.pack_into('<HH',settings,0x4e4,8,4)
 result=scope['run']('product','success',keys,prm=bytes(settings),files={'VWATCH.COM':observer.read_bytes()},observer='VWATCH',cpu='8086',banner=banner,online_triggers=[(b'pause\r',[(0,b'\x1b['),(1.4,completion)])])
 raw=(out/'product/WVIEW.BIN').read_bytes();assert len(raw)==35780,len(raw)
 state=struct.unpack_from('<16H',raw);video=raw[32:4032];shadow=bytearray(raw[4032:12224]);flags=raw[12224:16320];values=raw[16320:20416]
 count,ticks=struct.unpack_from('<2H',raw,20416);assert count<=48
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
 for name,value in dict(screen_cursor_wrap=1,screen_attribute_checks=1,erase_protection_mode=1,attributes_preset_value=0x4e).items():m.put(name,value)
 m.uc.mem_write(m.symbols['csi_erase_attribute'],b'\x07')
 m.feed(banner[len(b'\x1b[6;18H'):]+b'\x1b['+completion)
 for row in range(rows):shadow[row*264:row*264+160]=video[row*160:(row+1)*160]
 wire=(out/'product/serial.bin').read_bytes();checks=dict(result['checks'])
 checks.update(observer_header=state[0]==0x5756 and state[1:5]==(1,0,1,0),root_context_restored=state[5]==state[6]!=0,
  width_and_fields_retained=state[7]==size and state[10:14]==(1,1,1,1),final_cursor=state[8:10]==(0,15),
  actual_menu=any(b'Command Menu'in f[:80]for f in frames),actual_history=any(b'Redisplay'in f[:80]for f in frames),actual_clipboard=any(b'Filename Clipboard'in f[80:160]for f in frames),
  deferred_menu_during_real_parser=state[14]>0,queued_arrows_during_real_parser=state[15]>0,
  passive_timer_frames=ticks>10 and count>5,exact_logical_screen=bytes(shadow[:size*2])==logical(m,address,rows),
  exact_flags=flags==bytes(m.uc.mem_read(m.symbols['screen_attribute_cells'],4096)),exact_values=values==bytes(m.uc.mem_read(m.symbols['erase_attribute_values'],4096)),
  wide_CPR_during_UI=b'\x1b[3;127R'in wire and b'\x1b[7;18R'in wire and b'\x1b[4;132R'in wire,
  post_UI_keyboard=b'ready'in wire,local_UI_keys_not_on_wire=b'\x1b[C'not in wire,
  unmodified_product=sha(short/'TERMINAL.EXE')==mft['binary_sha256'])
 report=dict(passed=all(checks.values()),checks=checks,state=list(state),frame_count=count,viewer_ticks=ticks,binary_sha256=sha(binary),hidden_status=a.hidden_status,content_rows=rows,sources=mft['sources'],checker_sha256=sha(Path(__file__)),observer_sha256=sha(watch),original_inputs=[],artifacts={str(p.relative_to(ROOT)):sha(p)for p in out.rglob('*')if p.is_file()},scope=__doc__+' Observer stages initial fields and invokes explicit width once, then passively samples video/lifecycle and exit state. Model replay supplies only expected output. No product patch, peer width negotiation, external BBS or physical acceptance.')
 (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print(('PASS'if report['passed']else'FAIL')+' DOS wide viewers '+json.dumps(checks));return 0 if report['passed']else 1
if __name__=='__main__':raise SystemExit(main())
