#!/usr/bin/env python3
"""Read-only stock BBS navigation after the actual script-time Alt-Z window."""
import argparse,asyncio,contextlib,hashlib,json,re,shutil,struct,subprocess,sys,types
from pathlib import Path
import test_dos
from modem import Telnet
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'standalone'));sys.path.insert(0,str(ROOT/'src/aspect'))
import test_aspect_script_window_dos as window
from compiler import compile_source
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())

def source(name):
 navigation,back,prompt,main=(('T','Q','List Files in dir','Read/Post Messages') if name=='synchronet'
  else ('M^M','Q^M','Message Menu','Main Menu'))
 return ('proc main\nmessage "WINDOW READY"\npause 15\ntransmit "'+navigation+'"\n'
  'waitfor "'+prompt+'" 30\nif waitfor\nwaitquiet 1 10\ntransmit "'+back+'"\n'
  'waitfor "'+main+'" 30\nif waitfor\nwaitquiet 1 10\nfopen 5 "WIN.OK" "wb"\n'
  'fputs 5 "OK"\nfclose 5\nmessage "WINDOW DONE"\nendif\nendif\nendproc\n')

async def main(a):
 assert re.fullmatch(r'[A-Za-z0-9_-]+',a.label) and re.fullmatch(r'[A-Za-z0-9_-]+',a.baseline_label)
 stage=ROOT/'build/bbs-lab/script-window'/a.name/a.label
 out=ROOT/'build/bbs-lab/results'/a.name/a.label
 assert not stage.exists() and not out.exists();stage.mkdir(parents=True);out.mkdir(parents=True)
 inputs={};selected=[]
 for directory,binary in [('terminal','TERMINAL.EXE'),('aspect-runner','ASPECT.EXE')]:
  base=ROOT/'build'/directory;m=read(base/'manifest.json');assert m['binary_sha256']==sha(base/binary)
  assert not m.get('diagnostic_build',False)
  for name,digest in m['sources'].items():assert sha(ROOT/name)==digest;inputs[name]=digest
  for p in [base/binary,base/'manifest.json',*base.glob('*.map')]:inputs[str(p.relative_to(ROOT))]=sha(p)
  shutil.copy2(base/binary,stage/binary)
 # Freeze the independently accepted login prefix; require every subsequent
 # byte, including window dismissals and modeled hangup, rather than stripping
 # arbitrary controls to make the navigation tail match.
 baseline=ROOT/'build/bbs-lab/recording'/a.name/a.baseline_label/'result.json'
 prior=read(baseline);assert prior['passed'] and prior['binary_sha256']==sha(stage/'TERMINAL.EXE')
 assert prior['runner_sha256']==sha(stage/'ASPECT.EXE')
 payload=b'TQ' if a.name=='synchronet' else b'M\rQ\r';hangup=b'+++ATH\r'
 previous=bytes.fromhex(prior['sessions']['record']['user_hex'])
 assert previous.endswith(payload+hangup);login_prefix=previous[:-len(payload+hangup)]
 # Use the existing audio lab's blank hangup fixture: this Hayes/Telnet model
 # cannot turn online+++ATH into a local modem command. Preserve every byte
 # of the selected profile instead of forwarding synthetic shutdown input.
 expected=login_prefix+payload
 support=['lab/bbs/script_window_dos.py','lab/bbs/test_dos.py','lab/bbs/modem.py','lab/bbs/editor-recipes.json',
  'standalone/test_aspect_script_window_dos.py','standalone/test_aspect_keys_dos.py','standalone/test_aspect_renderer_dos.py',
  'standalone/test_connection_dos.py','standalone/test_terminal.py','standalone/terminal_config_fixtures.py',
  'standalone/modem_fixtures.py','standalone/directory_fixtures.py','standalone/directory_test_support.py','src/aspect/compiler.py',
  'lab/bbs/audio_recording_keys.asm','lab/bbs/audio_get_vector.asm']
 for name in support:inputs[name]=sha(ROOT/name)
 provenance='build/bbs-lab/'+('synchronet/provenance.json' if a.name=='synchronet' else 'enigma/metadata.json')
 assert sha(ROOT/provenance)==prior['inputs'][provenance]
 inputs[provenance]=sha(ROOT/provenance)
 inputs[str(baseline.relative_to(ROOT))]=sha(baseline)
 text=source(a.name);(stage/'WIN.ASP').write_text(text);(stage/'WIN.ASX').write_bytes(compile_source(text))
 renderer=window.keys.renderer;previous_out=renderer.OUT;renderer.OUT=stage
 try:
  builder=window.make_observer(renderer.observer,window.symbols(ROOT/'build/terminal/terminal.map'),window.symbols(ROOT/'build/aspect-runner/ASPECT.map'))
  builder(renderer.map_offsets(ROOT/'build/terminal/terminal.map'))
 finally:renderer.OUT=previous_out
 # Reuse the established private BIOS driver, with an explicit three-stage
 # recipe. It waits for the script's own completed-body marker before opening
 # the regular menu. It never writes product, serial or success-file state.
 driver=(ROOT/'lab/bbs/audio_recording_keys.asm').read_text()
 ready="ready_marker: db 'RECORDER READY',0";assert driver.count(ready)==1
 driver=driver.replace(ready,"ready_marker: db 'WINDOW DONE',0")
 begin=driver.index('stages:\n');end=driver.index('STAGE_COUNT equ',begin)
 driver=driver[:begin]+('stages:\n dw ready_marker,open_menu,90\n'
  ' dw menu_marker,escape_key,18\n dw ready_marker,exit_keys,180\n')+driver[end:]
 (stage/'POSTKEY.ASM').write_text(driver)
 subprocess.run(['nasm','-fbin','-DRECORD_WATCHDOG_TICKS=2700',str(stage/'POSTKEY.ASM'),'-o',str(stage/'POSTKEY.COM')],check=True)
 subprocess.run(['nasm','-fbin',str(ROOT/'lab/bbs/audio_get_vector.asm'),'-o',str(stage/'KEYVEC.COM')],check=True)
 if a.name=='synchronet':
  port=23231;login='p13000 L A B U S E R enter p2000 L A B P A S S 4 2 enter p8000 space p3000 Q enter p5000 space p4000 '
 else:
  port=23233;canonical=read(ROOT/'lab/bbs/editor-recipes.json')['enigma_unsaved']['keyboard_input']
  login=canonical[:canonical.index('M enter')]
 keys=login+'a-z p300 a p300 w i n . a s x enter p1500 a-z p5500 a-z p2000 escape'
 assert len('ADDKEY p1000 '+keys)<500
 for name,digest in inputs.items():
  p=stage/'frozen-source'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,p);assert sha(p)==digest
 generated={p.name:sha(p) for p in stage.iterdir() if p.is_file()}
 (stage/'start.json').write_text(json.dumps(dict(inputs=inputs,generated=generated,keys=keys,
  expected_user_hex=expected.hex(),payload_hex=payload.hex(),scope=__doc__),indent=2)+'\n')
 # Install/collect the existing passive observer. It reads product/video state;
 # ADDKEY remains the sole key driver, and only the actual ASPECT script writes
 # WIN.OK after both board prompts have matched.
 path=ROOT/'lab/bbs/test_dos.py';harness=path.read_text()
 before='D:'+chr(92)*2+'SNAP B';after='D:'+chr(92)*2+'SNAP S'
 assert harness.count(before)==harness.count(after)==1
 harness=harness.replace(before,before+'\nRENDER T\nPOSTKEY').replace(after,'POSTKEY R\nKEYVEC\nRENDER\n'+after)
 automatic_exit="keys=prefix+args.keys+f' p{args.wait*1000} a-x'"
 assert harness.count(automatic_exit)==1
 harness=harness.replace(automatic_exit,'keys=prefix+args.keys')
 module=types.ModuleType('stock_window_peer');module.__file__=str(path)
 exec(compile(harness,str(path),'exec'),module.__dict__)
 fixture=module.modem_fixture
 def profile(**options):
  data=bytearray(fixture(**options));data[0x79:0x79+25]=bytes(25);return bytes(data)
 module.modem_fixture=profile
 options=argparse.Namespace(name=a.name,label=a.label,port=port,com=2,baud=19200,flow='HARD',packet_delay_ms=0,
  dial_fixture=True,directory_fixture=False,directory_browser=False,entry=3,binary=stage/'TERMINAL.EXE',
  config_fixture=False,keymap_fixture=None,server_log=None,keys=keys,wait=2,timeout=170)
 with (out/'harness.log').open('w') as capture,contextlib.redirect_stdout(capture):code=await module.run(options)
 r=read(out/'result.json');report=(out/'RENDER.BIN').read_bytes() if (out/'RENDER.BIN').exists() else b''
 header=struct.unpack_from('<7H',report) if len(report)>=14 else ()
 observed=struct.unpack('<5H',report[-10:]) if len(report)>=10 else ()
 actor=(out/'RECKEY.BIN').read_bytes() if (out/'RECKEY.BIN').exists() else b''
 actor=struct.unpack('<8H',actor) if len(actor)==16 else ()
 sent,_=Telnet().feed((out/'bbs-sent.bin').read_bytes())
 user=re.sub(rb'\x1b\[(?:\?[0-9;]*c|[0-9]+;[0-9]+R)',b'',sent)
 clean=re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]',b'',(out/'display.bin').read_bytes()).decode('cp437')
 (out/'display-clean.txt').write_text(clean)
 checks=dict(DOS_hardware_configuration=code==0 and r['passed'] and all(r['checks'].values()),
  actual_child_normal_exit=bool(header) and header[:4]==(0x524e,1,1,1) and header[6]==0,
  reference_and_help_observed=bool(observed) and observed[0:2]==(1,1),
  window_wait_exceeds_parser_budget=bool(observed) and observed[2]>72,
  regular_parent_menu_after_child_exit=bool(observed) and observed[4]==1,
  completion_gated_BIOS_recipe=bool(actor) and actor[:4]==(0x524b,3,3,1),
  key_timer_restored=(out/'KEYOLD.BIN').is_file() and (out/'KEYNEW.BIN').is_file() and
   (out/'KEYOLD.BIN').read_bytes()==(out/'KEYNEW.BIN').read_bytes() and (out/'KEYOLD.BIN').stat().st_size==4,
  script_completed=(stage/'WIN.OK').is_file() and (stage/'WIN.OK').read_bytes()==b'OK',
  exact_whole_user_stream=user==expected,script_source_unchanged=(stage/'WIN.ASP').read_text()==text,
  script_bytecode_unchanged=(stage/'WIN.ASX').read_bytes()==compile_source(text),
  inputs_unchanged=all(sha(ROOT/name)==digest for name,digest in inputs.items()),
  no_relay_errors=not [event for event in read(out/'modem.json')['events'] if event['kind']=='error'])
 if a.name=='synchronet':
  checks.update(authenticated='Logging on to LoC Protocol Lab as LABUSER' in clean,
   actual_file_roundtrip=clean.count('■ File ■')==1 and '■ Main ■' in clean[clean.rfind('■ File ■'):],
   no_unknown_command='Unrecognized command' not in clean)
 else:
  boundary=read(out/'server-log-start.json');path=Path(boundary['path']);assert path.stat().st_ino==boundary['inode']
  with path.open('rb') as f:f.seek(boundary['byte_offset']);rows=[json.loads(line) for line in f if line.strip()]
  ids={row['sessionId'] for row in rows if row.get('msg')=='User "loclab" successfully logged in'}
  own=[row for row in rows if row.get('sessionId') in ids];menus=[row['menuName'] for row in own if row.get('menuName')]
  (out/'server-session.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in own))
  checks.update(unique_authenticated_session=len(ids)==1,
   actual_message_roundtrip='mainMenu' in menus and menus[menus.index('mainMenu'):]==['mainMenu','messageBaseMainMenu','mainMenu'])
 result=dict(passed=all(checks.values()),checks=checks,inputs=inputs,binary_sha256=sha(stage/'TERMINAL.EXE'),
  runner_sha256=sha(stage/'ASPECT.EXE'),observer_sha256=sha(stage/'RENDER.COM'),helper_header=header,
  window_observation=observed,actor_report=actor,actual_user_hex=user.hex(),expected_user_hex=expected.hex(),
  captures_sha256={str(p.relative_to(ROOT)):sha(p) for base in (stage,out) for p in base.rglob('*') if p.is_file() and not p.is_relative_to(stage/'frozen-source')},
  scope=__doc__+' Actual DOS and owned stock loopback BBS. Passive window/help/parent-menu observations and full typed-stream identity; no screen, serial or product-state injection. The script pauses while the window owns keys, then navigates normally. This does not test sustained BBS output during the window, SIP/audio or physical modem behavior.')
 (stage/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(passed=result['passed'],checks=checks,window_observation=observed)),flush=True)
 assert result['passed'],'Preserve the failed BBS window attempt and inspect its artifacts'

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('name',choices=('enigma','synchronet'));p.add_argument('--label',required=True);p.add_argument('--baseline-label',default='script-window-compat-02')
 asyncio.run(main(p.parse_args()))
