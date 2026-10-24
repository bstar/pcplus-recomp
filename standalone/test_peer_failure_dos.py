#!/usr/bin/env python3
"""Real DOS peer-width refusal, nonlocal ASPECT unwind and interrupted CSI.

The product binaries are unchanged. A declared startup setting selects the
native-refusal fixture; all later observer work is passive. No return value,
wire reply or runtime product instruction is patched.
"""
import argparse,hashlib,json,re,struct,subprocess,sys
from pathlib import Path
import test_connection_dos as harness
from test_directory_key_bindings_dos import actions
ROOT=harness.ROOT
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def product(path):
 path=path.resolve();m=json.loads((path.parent/'manifest.json').read_text())
 assert path.is_relative_to(ROOT/'build')and sha(path)==m['binary_sha256']and not m.get('original_inputs')
 for name,digest in m['sources'].items():assert sha(ROOT/name)==digest,name
 return path,m
def symbols(path):return {n:(int(s,16),int(o,16))for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',path.read_text(),re.M|re.I)}
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--terminal',type=Path,required=True);p.add_argument('--runner',type=Path,required=True);p.add_argument('--compiler',type=Path)
 p.add_argument('--output',type=Path,required=True);p.add_argument('--case',choices=['native','preflight','can','sub'],required=True)
 p.add_argument('--ordinary',action='store_true');p.add_argument('--window',action='store_true');p.add_argument('--hidden-status',action='store_true')
 p.add_argument('--profile',type=int,choices=[4,6],default=6);a=p.parse_args()
 assert not a.ordinary or(not a.compiler and not a.window and a.case!='preflight')
 binary,mft=product(a.terminal);runner,rm=product(a.runner)
 assert mft['native_reset_transaction']and mft['experimental_aspect_keys']
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build')and not out.exists();out.mkdir(parents=True)
 sy=symbols(binary.parent/'terminal.map');dg=int(re.search(r'^DGROUP\s+([0-9a-f]+):',(binary.parent/'terminal.map').read_text(),re.M|re.I)[1],16)
 names='attributes_color_mode render_translation_enabled render_translation_table render_translation_mask render_direct_output attributes_monochrome screen_attribute_offset screen_video_offset screen_visible_column screen_viewport_offset screen_last_column screen_attribute_row_bytes csi_unimplemented_service screen_columns screen_attributes_base screen_attribute_cells erase_attribute_values_base erase_attribute_values screen_cursor_wrap screen_attribute_checks erase_protection_mode attributes_preset_value csi_erase_attribute ui_flow_suppressed erase_cell_count screen_cursor_row screen_cursor_column screen_viewport_active erase_shadow_offset erase_shadow_segment terminal_menu_pending terminal_parser_active terminal_deferred_count _redisplay_active _redisplay_live_ready terminal_aspect_active terminal_ansi_wait_active screen_use_bios_cursor csi_row_count'.split()
 defs={n.upper().lstrip('_'):sy[n][0]*16+sy[n][1]-dg*16 for n in names}
 cs,off=sy['terminal_native_width_far'];defs.update(DGROUP_REL=dg,LIVE_CODE_REL=cs,LIVE_OFF=off)
 for n in('reset_live_active','reset_bank_busy'):assert sy[n][0]==cs;defs[n.upper()]=sy[n][1]
 lease=['render_attached','resident_bridge_busy','terminal_script_overlay_visible'];assert len({sy[n][0]for n in lease})==1
 defs['ASPECT_CODE_REL']=sy[lease[0]][0];defs.update({n.upper():sy[n][1]for n in lease})
 child=symbols(runner.parent/'ASPECT.map')
 defs.update({key:child[name][1]for key,name in [('COMPILER_CALLS','_runtime_compiler_calls'),('COMPILER_EXIT','_runtime_compiler_exit'),('COMPILER_ERROR','_runtime_compiler_dos_error')]})
 (out/'wide_viewer_offsets.inc').write_text(''.join(f'%define {n} {v}\n'for n,v in defs.items()))
 observer=out/'VWATCH.COM';watch=ROOT/'standalone/peer_failure_watch.asm'
 subprocess.run(['nasm','-fbin',*(['-DNATIVE_REFUSE']if a.case=='native'else[]),*(['-DHIDDEN_STATUS']if a.hidden_status else[]),'-I'+str(out)+'/','-I'+str(ROOT/'standalone')+'/',str(watch),'-o',str(observer)],check=True)
 script='proc main\ntransmit "SCRIPTREADY^M"\nwaitfor "END" 10\nif waitfor\ntransmit "SCRIPTDONE^M"\nelse\ntransmit "SCRIPTFAIL^M"\nendif\nendproc\n'
 short=out/'parent';short.mkdir();(short/'TERMINAL.EXE').write_bytes(binary.read_bytes());(short/'ASPECT.EXE').write_bytes(runner.read_bytes())
 files={'VWATCH.COM':observer.read_bytes(),'ACTIONS.KEY':actions(b'D:\\WIDE.ASP'if a.compiler else b'D:\\WIDE.ASX',0)}
 if a.compiler:
  compiler,cm=product(a.compiler);(short/'ASPCOMP.EXE').write_bytes(compiler.read_bytes());files['WIDE.ASP']=script.encode('ascii')
 else:files['WIDE.ASX']=compile_source(script)
 refused=a.case in('native','preflight');fatal=a.ordinary and refused
 ready=b'go'if a.ordinary else b'SCRIPTREADY\r'
 recover=b'\x1bc\x1b[?3h\x1b[2;121HRECOVER\x1b[6n'
 if a.case=='native':chunks=[(.8,b'\x1b[?3'),(1.4,b'h')]
 elif a.case=='preflight':chunks=[(.8,b'\x1b[?3;12'),(1.4,b'h')]
 else:chunks=[(.8,b'\x1b[?3'),(1.4,bytes([24 if a.case=='can'else 26])+b'\x1b[6n'+recover[2:]+b'END')]
 triggers=[(ready,chunks)]
 if not fatal:triggers.append((b'ready',recover if refused else b'\x1b[6n'))
 keys=('p900 enter 'if mft.get('special_edition')else'')+('p2300 g o 'if a.ordinary else'p2300 a-1 ')
 keys+=('p600 a-z 'if a.window else'')+'p5000 r e a d y p1300 a-x'
 text=Path(harness.__file__).read_text();needle="out=ROOT/'build/connection-dos'/name";assert text.count(needle)==1
 scope=dict(harness.__dict__);scope['LABEL_ROOT']=out;exec(compile(text.replace(needle,'out=LABEL_ROOT/name'),str(Path(harness.__file__)),'exec'),scope);scope['BINARY']=short/'TERMINAL.EXE'
 prm=bytearray(harness.fixture(timeout=5));struct.pack_into('<H',prm,0x194,a.profile)
 if mft.get('experimental_custom_irq'):struct.pack_into('<HH',prm,0x184,4,3)
 if mft.get('experimental_mouse'):struct.pack_into('<HH',prm,0x4e4,8,4)
 result=scope['run']('product','success',keys,prm=bytes(prm),files=files,observer='VWATCH',cpu='8086',profile=a.profile,
  expected=2 if fatal else 0,banner=b'\x1b[6;18H\x1b[1;1HFIRST BYTE SAFE\x1b[6n\x1b[0c',arguments='@D:\\TEST.PRM /D:CaseTest:23 /T:D:\\ACTIONS.KEY /A:NETWORK',online_triggers=triggers)
 raw=(out/'product/WVIEW.BIN').read_bytes();assert len(raw)==108,len(raw)
 state=struct.unpack_from('<16H',raw);attached,bridge,overlay,unused=struct.unpack_from('<4H',raw,32)
 compilation=struct.unpack_from('<6H',raw,62);child_state=struct.unpack_from('<10H',raw,74);final=struct.unpack_from('<7H',raw,94)
 wire=(out/'product/serial.bin').read_bytes();checks=dict(result['checks']);checks.pop('immediate_banner_not_dropped',None)
 checks.update(observer_header=state[:5]==(0x5756,1,0,1,2 if fatal else 0),root_DS_SS=state[5]==state[6]!=0,
  initial_banner_parsed=b'\x1b[1;16R'in wire,correct_final_marker=final[0]==(0x2a6e if fatal else 0),
  final_native_idle=final[5:]==(0,0),final_scope_idle=final[3]==0,unmodified_runner=sha(short/'ASPECT.EXE')==rm['binary_sha256'])
 if a.ordinary:checks['no_child']=compilation==(0,0,0,0,0,0)and child_state==(65535,)*10 and attached==bridge==overlay==0
 else:
  checks.update(actual_ASPECT_lease=attached>0,actual_window=(overlay>0)==a.window,child_exit=child_state[0]==(3 if refused else 0),
   child_scopes_idle=child_state[4:9]==(0,0,0,0,0),child_failure_marker=child_state[9]==(0x2a6e if a.case=='native'else 0),compiler_observed=compilation[0]==(2 if a.compiler else 1)and compilation[1]==compilation[2]!=0 and compilation[3:]==((1,0,0)if a.compiler else(0,0,0)))
  if refused:checks['no_width_commit_on_rejection']=child_state[1:4]==(80,25,2000)and b'SCRIPTDONE'not in wire and b'SCRIPTFAIL'not in wire
  else:checks['script_resumed']=b'SCRIPTDONE\r'in wire and b'SCRIPTFAIL'not in wire
 if fatal:checks['fatal_width_unchanged']=final[1]==80 and state[7]==2000
 else:
  checks.update(recovered_width=final[1]==132 and state[7]==(25 if a.hidden_status else 24)*132,
   actual_post_recovery_CPR=b'\x1b[2;128R'in wire,keyboard_resumed=b'ready'in wire,final_parser_idle=final[2:5]==(0,0,0))
  if not refused:
   # Profile6's default control-glyph setting renders SUB as CP4371A;
   # profile4 dispatches its native no-op provider. The following ESC
   # resynchronizes the interrupted CSI; CAN/SUB alone are not claimed to
   # abandon the historical parameter reader.
   expected_interrupted=b'\x1b[1;17R'if a.case=='sub'and a.profile==6 else b'\x1b[1;16R'
   checks['interrupted_CSI_resynchronized']=(wire.count(expected_interrupted)>=(1 if a.case=='sub'and a.profile==6 else 2)and b'\x1b[2;131R'in wire)
 if a.compiler:
  checks['exact_DOS_ASX']=(out/'product/WIDE.ASX').read_bytes()==compile_source(script);checks['unmodified_compiler']=sha(short/'ASPCOMP.EXE')==cm['binary_sha256']
 inputs={str(p.relative_to(ROOT)):sha(p)for p in [Path(__file__),watch,ROOT/'standalone/aspect_wide_watch.asm',Path(harness.__file__),ROOT/'standalone/test_terminal.py',ROOT/'standalone/modem_fixtures.py',ROOT/'standalone/terminal_config_fixtures.py',ROOT/'standalone/test_directory_key_bindings_dos.py',ROOT/'src/aspect/compiler.py']}
 report=dict(passed=all(checks.values()),checks=checks,case=a.case,ordinary=a.ordinary,window=a.window,hidden_status=a.hidden_status,profile=a.profile,source_compilation=bool(a.compiler),state=list(state),child_state=list(child_state),final_state=list(final),compiler_observation=list(compilation),attached_ticks=attached,bridge_ticks=bridge,overlay_ticks=overlay,binary_sha256=sha(binary),runner_sha256=sha(runner),compiler_sha256=sha(compiler)if a.compiler else None,sources=mft['sources'],test_sources=inputs,original_inputs=[],artifacts={str(p.relative_to(ROOT)):sha(p)for p in out.rglob('*')if p.is_file()},scope=__doc__+' Synthetic modem and declared startup fixture; real DOS parser/ASPECT/RIS recovery. No full-plane snapshot, carrier/audio/physical or arbitrary OS interruption claim.')
 (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS'if report['passed']else'FAIL','peer failure',a.case,json.dumps(checks));print('Child/final states:',child_state,final)
 return 0 if report['passed']else 1
if __name__=='__main__':raise SystemExit(main())
