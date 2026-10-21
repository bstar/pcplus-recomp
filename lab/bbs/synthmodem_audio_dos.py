#!/usr/bin/env python3
"""Actual DOS/ASPECT and owned ENiGMA through the trained audio gateway."""
import argparse,hashlib,json,os,re,shutil,signal,socket,struct,subprocess,sys,time
from pathlib import Path
import enigma
from synthmodem_bbs_dos import Relay
from synthmodem_vm_control import ROOT,sha
from synthmodem_sparse_runtime import validate as validate_runtime
from synthmodem_jitter_runtime import validate as validate_jitter_runtime
from synthmodem_lifecycle_runtime import validate as validate_lifecycle_runtime
from synthmodem_carrier_runtime import validate as validate_carrier_runtime
from synthmodem_carrier_trace_runtime import validate as validate_carrier_trace_runtime
from synthmodem_key_framing_runtime import validate as validate_key_framing_runtime
sys.path.insert(0,str(ROOT/'standalone'));sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source
from modem_fixtures import fixture
from directory_fixtures import directory
from directory_test_support import accounting_check
from test_terminal import SAMPLER

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--receive-trace',action='store_true');p.add_argument('--dmodem',choices=['baseline','candidate']);p.add_argument('--lifecycle',action='store_true');p.add_argument('--carrier',action='store_true');p.add_argument('--carrier-trace',action='store_true');p.add_argument('--key-framing',action='store_true');p.add_argument('--key-framing-trace',action='store_true');p.add_argument('--syscall-trace',action='store_true');p.add_argument('--route',choices=['menus','editor','download'],default='menus');a=p.parse_args()
 assert sum(bool(v) for v in (a.lifecycle,a.carrier,a.carrier_trace,a.key_framing,a.key_framing_trace,a.receive_trace,a.dmodem))<=1,'Choose one pinned runtime profile'
 a.key_framing=a.key_framing or a.key_framing_trace
 trace=a.receive_trace or a.carrier_trace or a.key_framing_trace
 runtime=a.runtime.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 ledger=ROOT/'docs/validation/synthmodem-gateway.json';prior=json.loads(ledger.read_text());assert prior['passed']
 if a.key_framing:runtime_inputs=validate_key_framing_runtime(runtime,trace=a.key_framing_trace)
 elif a.carrier_trace:runtime_inputs=validate_carrier_trace_runtime(runtime)
 elif a.carrier:runtime_inputs=validate_carrier_runtime(runtime)
 elif a.lifecycle:runtime_inputs=validate_lifecycle_runtime(runtime)
 elif a.receive_trace:
  trace_ledger=ROOT/'docs/validation/synthmodem-receive-trace.json';tr=json.loads(trace_ledger.read_text());assert tr['passed']
  reference=ROOT/'build/bbs-lab/synthmodem-receive-trace-01/runtime'
  runtime_inputs={str(runtime/Path(n).relative_to(reference)):h for n,h in tr['tested_inputs'].items()}
  assert {str(p) for p in runtime.rglob('*') if p.is_file()}==set(runtime_inputs)
  assert all(sha(Path(n))==h for n,h in runtime_inputs.items())
 elif a.dmodem:runtime_inputs=validate_jitter_runtime(runtime,a.dmodem)
 else:runtime_inputs=validate_runtime(runtime)
 pid=enigma.process_pid();assert pid and Path(f'/proc/{pid}/cwd').resolve()==enigma.SOURCE.resolve()
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=enigma.SOURCE,text=True).strip()==enigma.COMMIT
 assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=enigma.SOURCE,text=True).strip()
 server_names=['main.js','core/client.js','package-lock.json','config/config.hjson']+[str(p.relative_to(enigma.SOURCE)) for p in sorted((enigma.SOURCE/'config/menus').glob('*.hjson'))]
 server_inputs={n:sha(enigma.SOURCE/n) for n in server_names}
 names=['lab/bbs/synthmodem_audio_dos.py','lab/bbs/synthmodem_audio_serial.js','lab/bbs/serial_io_evidence.js','lab/bbs/check_serial_io_evidence.js','docs/validation/synthmodem-serial-io-evidence.json','lab/bbs/audio_exit_keys.asm','lab/bbs/audio_get_vector.asm',
  'lab/bbs/synthmodem_bbs_dos.py','lab/bbs/enigma.py','lab/bbs/synthmodem_sparse_runtime.py','lab/bbs/synthmodem_vm_control.py','docs/validation/synthmodem-sparse.json','standalone/modem_fixtures.py','standalone/directory_fixtures.py',
  'standalone/test_terminal.py','src/aspect/compiler.py','nix/flake.nix','nix/flake.lock','tools/modem-dev','build/terminal/TERMINAL.EXE','build/terminal/terminal.map','build/aspect-runner/ASPECT.EXE',str(ledger.relative_to(ROOT))]
 if a.receive_trace:names+=['docs/validation/synthmodem-receive-trace.json']
 if trace:names+=['lab/bbs/receive_trace_io.js','lab/bbs/qemu_trace_wrapper.py','lab/bbs/receive_trace_export.sh']
 names+=['lab/bbs/synthmodem_jitter_runtime.py','lab/bbs/synthmodem_lifecycle_runtime.py']
 if a.lifecycle or a.carrier or a.carrier_trace or a.key_framing:names+=['lab/bbs/internal_sip_capture.js','docs/validation/synthmodem-pool.json','docs/validation/synthmodem-registrar.json','docs/validation/synthmodem-jitter-policy.json']
 if a.carrier or a.carrier_trace or a.key_framing:names+=['lab/bbs/synthmodem_carrier_runtime.py','docs/validation/synthmodem-carrier-runtime.json']
 if a.carrier_trace:names+=['lab/bbs/synthmodem_carrier_trace_runtime.py','docs/validation/synthmodem-carrier-trace-runtime.json']
 if a.key_framing:names+=['lab/bbs/synthmodem_key_framing_runtime.py','docs/validation/synthmodem-key-framing-runtime.json','lab/bbs/patches/synthmodem-key-framing/InputSequenceFramer.js','lab/bbs/patches/synthmodem-key-framing/proxy.patch']
 if a.key_framing_trace:names+=['docs/validation/synthmodem-key-framing-trace-runtime.json','lab/bbs/synthmodem_carrier_trace_runtime.py','docs/validation/synthmodem-carrier-trace-runtime.json']
 if a.dmodem:names+=['docs/validation/synthmodem-jitter-policy.json','nix/dmodem.nix','tools/build-dmodem']
 download_path=download_before=None
 if a.route=='download':
  import audio_download
  download_path,download_before=audio_download.source()
  names+=['lab/bbs/audio_download.py','lab/bbs/audio_download_keys.asm','lab/bbs/check_audio_download_keys.py','docs/validation/audio-download-keys.json','lab/bbs/enigma_transfer.py',str(download_path.relative_to(ROOT)),str(audio_download.HELPER.relative_to(ROOT))]
 names+=['src/terminal/connection.asm','standalone/check_online_exit.py','docs/validation/online-exit.json']
 names+=['lab/bbs/check_audio_login_readiness.py','docs/validation/synthmodem-audio-login-readiness.json']
 if a.syscall_trace:names+=['lab/bbs/check_dosbox_socket_close.py','lab/bbs/dosbox_socket_close_probe.asm','docs/validation/dosbox-socket-close.json']
 if a.route=='editor':names+=['lab/bbs/audio_editor_keys.asm','lab/bbs/check_audio_editor_watchdog.py','docs/validation/synthmodem-audio-editor-watchdog.json']
 frozen={n:sha(ROOT/n) for n in names}
 stage=out/'program';stage.mkdir()
 for n,leaf in [('build/terminal/TERMINAL.EXE','TERMINAL.EXE'),('build/aspect-runner/ASPECT.EXE','ASPECT.EXE')]:shutil.copyfile(ROOT/n,stage/leaf)
 relay=Relay();relay.server.settimeout(90);relay.thread.start()
 def mark(label):return f'fopen 0 "D:\\STAGES.LOG" "ab"\nfputs 0 "{label}|"\nfclose 0\n'
 def wait(token,timeout,label):return f'waitfor "{token}" {timeout}\nif waitfor == 0\n'+mark('FAIL-'+label)+'exit\nendif\n'
 script='integer cancel_done,scan_done,main_seen\nproc main\ninteger attempts\ncancel_done=0\nscan_done=0\nmain_seen=0\n'
 script+=wait('CONNECT> ',45,'BRIDGE')+mark('BRIDGE')+f'transmit "127.0.0.1:{relay.port}^M"\n'
 script+=wait('lOGIN',150,'MATRIX')+'waitquiet 2 120\ntransmit "^M"\n'
 script+=wait('PASSW_',150,'FORM')+'waitquiet 2 120\n'+mark('FORM')+'transmit "loclab^M"\nwaitquiet 2 120\n'
 script+='when 0 "eyboard" call advance\nwhen 1 "nAH" call cancel\nwhen 2 "erform global newscan" call decline\ntransmit "LoC-Lab-2026!^M"\n'
 # WHEN CALL is deferred until WAITFOR returns. Short waits allow handlers
 # to acknowledge pause/newscan prompts instead of blocking for240 seconds.
 # A ready title consumed by a callback WAITQUIET must still latch. Reuse
 # retired cancel/newscan slots; native ASPECT has only three ordinary slots.
 script+='attempts=0\nwhile attempts < 240\nwaitfor "Main Menu" 1\nif waitfor\nmain_seen=1\nendif\nif main_seen\nexitwhile\nendif\nattempts += 1\nendwhile\nif attempts == 240\n'+mark('FAIL-MAIN')+'exit\nendif\n'
 script+='waitquiet 2 120\ncwhen 0\ncwhen 1\ncwhen 2\n'+mark('MAIN')
 if a.route=='download':script+=audio_download.navigation(wait,mark)
 else:
  script+='transmit "M^M"\n'+wait('MESSAGE AREA',150,'MESSAGES')+'waitquiet 2 120\n'+mark('MESSAGES')
  if a.route=='menus':
   script+='transmit "Q^M"\n'+wait('Main Menu',150,'RETURN')+'waitquiet 2 120\n'+mark('RETURN')+'transmit "F^M"\n'
   script+=wait('File Base',150,'FILES')+'waitquiet 2 120\n'+mark('FILES')
  else:
   script+='transmit "P^M"\n'+wait('INS',150,'HEADER')+'waitquiet 2 120\ntransmit "^M"\nwaitquiet 2 120\ntransmit "KEYTEST^M"\nwaitquiet 2 120\n'+mark('EDITOR')
 script+='fopen 0 "D:\\SCRIPT.OK" "wb"\nfputs 0 "PASS"\nfclose 0\nendproc\n'
 script+='proc advance\ncwhen 0\nwaitquiet 2 120\nwhen 0 "eyboard" call advance\ntransmit "^M"\nendproc\n'
 script+='proc cancel\nif cancel_done == 0\ncancel_done=1\ncwhen 1\nwhen 1 "Main Menu" call reached_main\nwaitquiet 2 120\ntransmit "^["\nendif\nendproc\n'
 script+='proc decline\nif scan_done == 0\nscan_done=1\ncwhen 2\nwhen 2 "Main Menu" call reached_main\nwaitquiet 2 120\ntransmit "N"\nendif\nendproc\n'
 script+='proc reached_main\nmain_seen=1\ncwhen 1\ncwhen 2\nendproc\n'
 (stage/'AUDIO.ASP').write_text(script);(stage/'AUDIO.ASX').write_bytes(compile_source(script))
 profile=bytearray(fixture(timeout=60,autobaud=0));profile[0x79:0x79+25]=bytes(25);profile=bytes(profile)
 if a.route=='download':profile=audio_download.configure_profile(profile,out)
 (out/'MODEM.PRM').write_bytes(profile)
 contact=bytearray(directory(entry=1,target=b'1',port=1,baud=6));contact[250+52:250+61]=b'AUDIO\0\0\0\0';contact=bytes(contact);(out/'CALL.DIR').write_bytes(contact)
 (out/'sampler.asm').write_text(SAMPLER);subprocess.run(['nasm','-fbin',str(out/'sampler.asm'),'-o',str(out/'SNAP.COM')],check=True)
 for name,leaf in [('audio_editor_keys.asm' if a.route=='editor' else 'audio_download_keys.asm' if a.route=='download' else 'audio_exit_keys.asm','EXITKEY.COM'),('audio_get_vector.asm','KEYVEC.COM')]:subprocess.run(['nasm','-fbin',str(ROOT/'lab/bbs'/name),'-o',str(stage/leaf)],check=True)
 generated={str(p.relative_to(out)):sha(p) for p in stage.iterdir()}
 log=enigma.SOURCE/'logs/enigma-bbs.log';boundary=(log.stat().st_ino,log.stat().st_size)
 tool_inputs={str(Path(shutil.which(n)).resolve()):sha(Path(shutil.which(n))) for n in (['dosbox-x','nasm','strace'] if a.syscall_trace else ['dosbox-x','nasm'])}
 clock_anchors=[]
 def clock_anchor(label):
  before=time.monotonic_ns();wall=time.time_ns();after=time.monotonic_ns()
  clock_anchors.append(dict(label=label,monotonic_before_ns=str(before),wall_ns=str(wall),monotonic_after_ns=str(after)))
 node=None;dos=None;doscode=None
 with (out/'node.log').open('w') as nl,(out/'dosbox.log').open('w') as dl:
  try:
   node=subprocess.Popen(['node',str(ROOT/'lab/bbs/synthmodem_audio_serial.js'),str(runtime),str(out)]+(['--receive-trace'] if trace else [])+(['--lifecycle'] if a.lifecycle else [])+(['--carrier'] if a.carrier or a.carrier_trace or a.key_framing else [])+(['--key-framing'] if a.key_framing else []),stdout=nl,stderr=nl,start_new_session=True)
   end=time.monotonic()+60
   while not (out/'serial-port.json').exists():
    assert node.poll() is None and time.monotonic()<end,'Audio gateway startup deadline';time.sleep(.1)
   port=json.loads((out/'serial-port.json').read_text())['port']
   cfg=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=386
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=nullmodem server:127.0.0.1 port:{port} transparent:1 rxdelay:200 txdelay:1
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{stage}"
mount d "{out}"
c:
D:\\SNAP B
EXITKEY
TERMINAL @D:\\MODEM.PRM /E:D:\\CALL.DIR /N:1
if errorlevel 1 goto fail
echo PASS>D:\\PASS.TXT
goto capture
:fail
echo FAIL>D:\\FAIL.TXT
:capture
KEYVEC
D:\\SNAP S
D:\\SNAP A
exit
'''
   (out/'dosbox.conf').write_text(cfg)
   command=['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')]
   if a.syscall_trace:command=['strace','--seccomp-bpf','-f','-ttt','-yy','-e','trace=network,close','-o',str(out/'DOS-syscalls.log')]+command
   clock_anchor('before-DOS-launch')
   dos=subprocess.Popen(command,stdout=dl,stderr=dl,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),start_new_session=True)
   doscode=dos.wait(timeout=1220 if a.route=='download' else 720 if a.route=='editor' else 600);clock_anchor('after-DOS-exit');node.wait(timeout=60)
  finally:
   relay.stop.set();relay.thread.join(3)
   if dos is not None and dos.poll() is None:
    # SIGTERM can open an emulator quit dialog. Kill the owned group if it
    # refuses to exit, including descendants retaining the serial socket.
    os.killpg(dos.pid,signal.SIGTERM)
    try:dos.wait(timeout=5)
    except subprocess.TimeoutExpired:os.killpg(dos.pid,signal.SIGKILL);dos.wait()
   if node is not None and node.poll() is None:
    os.killpg(node.pid,signal.SIGTERM)
    try:node.wait(timeout=8)
    except subprocess.TimeoutExpired:os.killpg(node.pid,signal.SIGKILL);node.wait()
 def read(n):return (out/n).read_bytes() if (out/n).exists() else b''
 assert log.stat().st_ino==boundary[0]
 with log.open('rb') as f:f.seek(boundary[1]);rows=[json.loads(b) for b in f if b.strip()]
 sessions={r.get('sessionId') for r in rows if r.get('menuName')=='telnetConnected'};assert len(sessions)==1,sessions
 rows=[r for r in rows if r.get('sessionId') in sessions];menus=[r['menuName'] for r in rows if r.get('menuName')]
 (out/'server-session.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
 (out/'bbs-input.bin').write_bytes(relay.to_bbs);(out/'bbs-output.bin').write_bytes(relay.from_bbs)
 (out/'BBS-relay-events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in relay.trace))
 (out/'clock-anchors.json').write_text(json.dumps(clock_anchors,indent=2)+'\n')
 n=json.loads((out/'node-result.json').read_text())
 from modem import Telnet
 sent,_=Telnet().feed(relay.to_bbs);display,_=Telnet().feed(relay.from_bbs)
 wanted=['mainMenu','fileBaseMainMenu','fileBaseSearch','fileBaseListEntries','fileBaseDownloadManager','fileTransferProtocolSelection','sendFilesToUser'] if a.route=='download' else ['mainMenu','messageBaseMainMenu','messageBaseNewPost'] if a.route=='editor' else ['mainMenu','messageBaseMainMenu','mainMenu','fileBaseMainMenu'];at=0
 for m in menus:
  if at<len(wanted) and m==wanted[at]:at+=1
 screen=read('SCREEN.BIN');text='\n'.join(screen[r*160:r*160+160:2].decode('cp437') for r in range(25)) if len(screen)==4000 else ''
 checks={'DOS_normal_exit':doscode==0 and read('PASS.TXT') and not read('FAIL.TXT'),'script_completed':read('SCRIPT.OK')==b'PASS',
  'UART_restored':len(read('BEFORE.BIN'))==42 and read('BEFORE.BIN')==read('AFTER.BIN'),
  'keyboard_helper_retired':len(read('KEYOLD.BIN'))==4 and read('KEYOLD.BIN')==read('KEYNEW.BIN'),
  'numeric_AT_only':n['commands']==['ATZ','ATD1'],'real_DSP_CONNECT':n.get('callerInfo',{}).get('bps')==1200 and n.get('answerInfo',{}).get('bps')==1200,
  'authenticated':any(r.get('msg')=='User "loclab" successfully logged in' for r in rows),
  'ordered_menus':at==len(wanted),'DOS_DA':b'\x1b[?1;2c' in sent,'DOS_CPR':bool(re.search(rb'\x1b\[\d+;\d+R',sent)),
  'final_file_menu':'file base' in text.lower(),'profile_unchanged':read('MODEM.PRM')==profile,
  'directory_accounting':accounting_check(contact,read('CALL.DIR'),1),'no_relay_errors':not relay.errors and not relay.thread.is_alive(),
  'no_gateway_errors':not n['errors'],'VM_exited':n['VM_exited'] and n['pool']=='stopped',
  'no_post_saved':not any('posted message to' in r.get('msg','') for r in rows),
  'inputs_unchanged':all(sha(ROOT/n)==h for n,h in frozen.items()) and all(sha(Path(n))==h for n,h in runtime_inputs.items()) and all(sha(Path(n))==h for n,h in tool_inputs.items()),
  'server_unchanged':all(sha(enigma.SOURCE/n)==h for n,h in server_inputs.items())}
 checks={k:bool(v) for k,v in checks.items()}
 editor=None
 if a.route=='editor':
  del checks['final_file_menu']
  clean=re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]',b'',display).decode('cp437')
  body=clean[clean.find('KEYTEST'):];positions=[(int(row),int(col)) for row,col in re.findall(r'(?:INS|OVR) (\d+),(\d+)',body)]
  expected_keys={'home':b'\x1b[H','end':b'\x1b[F','insert':b'\x1b[2~','delete':b'\x1b[3~','page_up':b'\x1b[5~','page_down':b'\x1b[6~','tab':b'\t','delete_line':b'\x19'}
  observed={key:value in sent for key,value in expected_keys.items()}
  editor={'positions':positions,'keys_emitted':observed,'scope':'Actual BIOS editor keys; one-line page keys test boundaries, no multiline scrolling. Connection closes with an unsaved draft; no Save command is sent.'}
  checks.update(editor_entered='messageBaseNewPost' in menus,typed_draft_sent=b'ABCDE' in sent,all_editor_keys_emitted=all(observed.values()),
   home_moves_before_marker=positions[:7]==[(1,2),(1,3),(1,4),(1,5),(1,6),(1,1),(1,2)],insert_toggles_overtype='OVR ' in body)
 download=None
 if a.route=='download':
  checks.pop('final_file_menu')
  extra,download=audio_download.check(out,rows,download_path,download_before);checks.update(extra)
  checks['posttransfer_filename_visible']='PCXTEST.BIN' in text
 result={'passed':all(checks.values()),'checks':checks,'frozen_inputs':frozen,'runtime_inputs':runtime_inputs,'server_inputs':server_inputs,
  'generated_inputs':generated,'tool_inputs':tool_inputs,'syscall_trace':a.syscall_trace,'clock_anchors':clock_anchors,'server_revision':enigma.COMMIT,'server_menus':menus,'script_stages':read('STAGES.LOG').decode('ascii'),'login_readiness':'WAITFOR plus reused one-shot WHEN latch','receive_trace':a.receive_trace,'dmodem_variant':a.dmodem,'lifecycle':a.lifecycle,'carrier':a.carrier,'carrier_trace':a.carrier_trace,'key_framing_trace':a.key_framing_trace,'input_sequence_timeout_ms':250 if a.key_framing else 0,
  'DOS_screen':text,'gateway':n,'route':a.route,'editor':editor,'download':download,'captures_sha256':{p.name:sha(p) for p in out.iterdir() if p.suffix in ('.bin','.BIN','.log','.jsonl')},
  'scope':'Actual source-built DOS terminal and ASPECT directory script through synthetic local Hayes control and real external/internal SIP, CallSession, pool, originating/guest DSP and Telnet to owned stock ENiGMA. No physical modem/ATA/UART acceptance.'}
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'checks':checks,'result':str(out/'result.json')},indent=2));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
