#!/usr/bin/env python3
"""Actual source-built DOS/ASPECT to owned Synchronet through SIP/RTP/DSP."""
import argparse,datetime,json,os,re,shutil,signal,subprocess,sys,time
from pathlib import Path
from audio_bbs_relay import Relay
from audio_synchronet import ROOT,RUNTIME,PORT,snapshot,message_bodies,statistics,sha
from synthmodem_posttrain_validation import validate as validate_runtime
sys.path.insert(0,str(ROOT/'standalone'));sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source
from modem_fixtures import fixture
from directory_fixtures import directory
from directory_test_support import accounting_check
from test_terminal import SAMPLER
from modem import Telnet


def script(port):
 def mark(label):return f'fopen 0 "D:\\STAGES.LOG" "ab"\nfputs 0 "{label}|"\nfclose 0\n'
 def wait(token,label,timeout=180,quiet=True):return f'waitfor "{token}" {timeout}\nif waitfor == 0\n'+mark('FAIL-'+label)+'exit\nendif\n'+('waitquiet 2 120\n' if quiet else '')+mark(label)
 s='proc main\n'+wait('CONNECT> ','BRIDGE',45)+f'transmit "127.0.0.1:{port}^M"\n'
 for token,label,data in [('Login:','LOGIN','LABUSER^M'),('Password:','PASSWORD','LABPASS42^M'),('[Hit a key]','WELCOME',' '),('Enter number of bulletin or [','BULLETINS','Q'),('Search all groups for new messages?','SCAN','n^M'),('[Hit a key]','PAUSE',' '),('Read/Post Messages','MAIN','T'),('List Files in dir','FILES','J'),('Which, ','JOIN','11^M'),('PCPlus Lab:','AREA','U'),('Filename:','FILENAME','SXRCN003.BIN^M'),('to Main PCPlus Lab?','CONFIRM','y'),('Enter a description now.','DESCRIPTION','Synthetic PCPlus audio cancel^M'),('Protocol, ','PROTOCOL','1')]:s+=wait(token,label)+f'transmit "{data}"\n'
 s+=wait('Hang up after transfer?','HANGUP')+'transmit "n"\n'+'fopen 0 "D:\\SCRIPT.OK" "wb"\nfputs 0 "PASS"\nfclose 0\nendproc\n'
 return s


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--reference',type=Path,required=True);p.add_argument('--key-checks',type=Path,required=True);p.add_argument('--recipe-checks',type=Path,required=True);p.add_argument('--preflight',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 runtime=a.runtime.resolve();runtime_inputs=validate_runtime(runtime);server=snapshot();bodies=message_bodies();stats=statistics()
 reference=a.reference.resolve();keys=a.key_checks.resolve();assert reference.is_relative_to(ROOT/'build') and keys.is_relative_to(ROOT/'build')
 ref=json.loads(reference.read_text());kr=json.loads(keys.read_text());assert ref['passed'] and kr['passed'] and ref['server']==server
 assert all(sha(ROOT/n)==h for n,h in ref['reference_inputs'].items())
 assert {r['mode'] for r in kr['cases']}=={'phases_with_partial_markers','watchdog'}
 assert all(sha(ROOT/n)==h for n,h in kr['inputs'].items())
 recipe=a.recipe_checks.resolve();assert recipe.is_relative_to(ROOT/'build')
 rc=json.loads(recipe.read_text());assert rc['passed'] and all(c['raw_match_possible'] for c in rc['cases'])
 assert all(sha(ROOT/n)==h for n,h in rc['inputs'].items())
 names=['lab/bbs/synthmodem_synchronet_retry_startup_audio_dos.py','lab/bbs/audio_synchronet.py','lab/bbs/audio_synchronet_retry_startup.py','lab/bbs/audio_bbs_relay.py','lab/bbs/synchronet.py','lab/bbs/audio_synchronet_retry_startup_keys.asm','lab/bbs/check_audio_synchronet_retry_startup_keys.py','lab/bbs/audio_get_vector.asm',
  'lab/bbs/synthmodem_audio_serial.js','lab/bbs/serial_io_evidence.js','lab/bbs/internal_sip_capture.js','lab/bbs/synthmodem_posttrain_validation.py','docs/validation/synthmodem-posttrain-runtime.json',
  'standalone/modem_fixtures.py','standalone/directory_fixtures.py','standalone/directory_test_support.py','standalone/test_terminal.py','src/aspect/compiler.py',
  'lab/bbs/audit_synchronet_retry_startup_audio_dos.py','lab/bbs/audit_serial_io_evidence.py','lab/bbs/diagnose_audio_caller.js','lab/bbs/modem.py','lab/bbs/synthmodem_gateway.py',
  'nix/flake.nix','nix/flake.lock','tools/modem-dev','build/terminal/TERMINAL.EXE','build/terminal/terminal.map','build/aspect-runner/ASPECT.EXE',str(reference.relative_to(ROOT)),str(keys.relative_to(ROOT)),str(recipe.relative_to(ROOT)),'lab/bbs/check_synchronet_retry_startup_audio_recipe.py']
 preflight=a.preflight.resolve();assert preflight.is_relative_to(ROOT/'build')
 pf=json.loads(preflight.read_text());assert pf['passed'] and pf['server']==server and all(sha(ROOT/n)==h for n,h in pf['inputs'].items())
 assert all(sha(preflight.parent/n)==h for n,h in pf['captures_sha256'].items())
 from audio_synchronet_retry_startup import NAME,RETRY,AREA,payload,stored_files
 assert NAME not in stored_files() and RETRY not in stored_files() and stored_files()==pf['existing_files']
 names+=['lab/bbs/audit_indexed_controls.py','lab/bbs/observe_synchronet_retry_startup_partial.py','lab/bbs/audit_synchronet_retry_startup_metadata.py','lab/bbs/check_synchronet_retry_startup_controls.py','src/terminal/upload_actions.asm','src/terminal/transfer_actions.asm','standalone/check_terminal_upload_cancel_boundary.py','build/terminal/terminal-upload-cancel-boundary.json','build/terminal/terminal-upload-live-checks.json','build/terminal/terminal-transfer-live-checks.json']
 for n in names[-3:]:
  proof=json.loads((ROOT/n).read_text());assert proof['passed'] and proof['binary_sha256']==sha(ROOT/'build/terminal/TERMINAL.EXE')
 startup_proof=json.loads((ROOT/'build/terminal/terminal-upload-startup.json').read_text());assert startup_proof['passed'] and len(startup_proof['cases'])==43 and startup_proof['binary_sha256']==sha(ROOT/'build/terminal/TERMINAL.EXE')
 component=json.loads((ROOT/'docs/validation/terminal-upload-startup-fixed.json').read_text());assert component['passed'] and component['actual_DOS_startup_accepted'] and component['binary_sha256']==sha(ROOT/'build/terminal/TERMINAL.EXE')
 names+=['src/terminal/upload_startup.asm','src/terminal/upload_startup_bridge.asm','standalone/check_terminal_upload_startup.py','build/terminal/terminal-upload-startup.json']
 names+=['docs/validation/terminal-upload-startup-fixed.json','standalone/record_terminal_upload_startup.py']
 names+=[str(preflight.relative_to(ROOT)),'lab/bbs/prepare_synchronet_audio_retry_startup.py','lab/bbs/synchronet_transfer.py','lab/bbs/test_transfer_dos.py','lab/bbs/audit_audio_download.py','lab/bbs/enigma_transfer.py']
 frozen={n:sha(ROOT/n) for n in names};out.mkdir(parents=True)
 (out/'SEND').mkdir();upload_path=out/'SEND'/'RETRY.BIN';upload_path.write_bytes(payload(NAME))
 assert sha(upload_path)==pf['source_sha256']
 upload_stat=(upload_path.stat().st_ino,upload_path.stat().st_size,upload_path.stat().st_mtime_ns)
 (out/'server-inputs.json').write_text(json.dumps(server,indent=2)+'\n')
 stage=out/'program';stage.mkdir()
 for source,leaf in [('build/terminal/TERMINAL.EXE','TERMINAL.EXE'),('build/aspect-runner/ASPECT.EXE','ASPECT.EXE')]:shutil.copyfile(ROOT/source,stage/leaf)
 relay=Relay(PORT);relay.thread.start()
 source=script(relay.port);(stage/'AUDIO.ASP').write_text(source);(stage/'AUDIO.ASX').write_bytes(compile_source(source))
 profile=bytearray(fixture(timeout=60,autobaud=0));profile[0x79:0x79+25]=bytes(25);profile=bytes(profile);(out/'MODEM.PRM').write_bytes(profile)
 contact=bytearray(directory(entry=1,target=b'1',port=1,baud=6));contact[250+52:250+61]=b'AUDIO\0\0\0\0';contact=bytes(contact);(out/'CALL.DIR').write_bytes(contact)
 (out/'sampler.asm').write_text(SAMPLER)
 for src,leaf in [(out/'sampler.asm',out/'SNAP.COM'),(ROOT/'lab/bbs/audio_synchronet_retry_startup_keys.asm',stage/'EXITKEY.COM'),(ROOT/'lab/bbs/audio_get_vector.asm',stage/'KEYVEC.COM')]:subprocess.run(['nasm','-fbin',str(src),'-o',str(leaf)],check=True)
 generated={str(p.relative_to(out)):sha(p) for p in stage.iterdir()}
 date=datetime.datetime.strptime(stats['Global']['date'],'%b %d %Y');log=RUNTIME/'data/logs'/date.strftime('%m%d%y.log');boundary=(log.stat().st_ino,log.stat().st_size)
 tools={str(Path(shutil.which(n)).resolve()):sha(Path(shutil.which(n))) for n in ('dosbox-x','nasm')}
 anchors=[]
 def anchor(label):
  before=time.monotonic_ns();wall=time.time_ns();after=time.monotonic_ns();anchors.append(dict(label=label,monotonic_before_ns=str(before),wall_ns=str(wall),monotonic_after_ns=str(after)))
 node=dos=None;code=None
 with (out/'node.log').open('w') as nl,(out/'dosbox.log').open('w') as dl:
  try:
   node=subprocess.Popen(['node',str(ROOT/'lab/bbs/synthmodem_audio_serial.js'),str(runtime),str(out),'--carrier','--key-framing'],stdout=nl,stderr=nl,start_new_session=True)
   end=time.monotonic()+60
   while not (out/'serial-port.json').exists():assert node.poll() is None and time.monotonic()<end;time.sleep(.1)
   port=json.loads((out/'serial-port.json').read_text())['port']
   (out/'dosbox.conf').write_text(f'''[sdl]
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
''')
   anchor('before-DOS-launch');dos=subprocess.Popen(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],stdout=dl,stderr=dl,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),start_new_session=True)
   code=dos.wait(timeout=1250);anchor('after-DOS-exit');node.wait(timeout=60)
  finally:
   relay.stop.set();relay.thread.join(3)
   for process,seconds in ((dos,5),(node,8)):
    if process is not None and process.poll() is None:
     os.killpg(process.pid,signal.SIGTERM)
     try:process.wait(timeout=seconds)
     except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
 read=lambda n:(out/n).read_bytes() if (out/n).exists() else b''
 assert log.stat().st_ino==boundary[0]
 with log.open('rb') as stream:stream.seek(boundary[1]);server_log=stream.read()
 (out/'server-session.log').write_bytes(server_log)
 (out/'bbs-input.bin').write_bytes(relay.to_bbs);(out/'bbs-output.bin').write_bytes(relay.from_bbs)
 (out/'BBS-relay-events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in relay.trace));(out/'clock-anchors.json').write_text(json.dumps(anchors,indent=2)+'\n')
 n=json.loads((out/'node-result.json').read_text());sent,_=Telnet().feed(relay.to_bbs);display,_=Telnet().feed(relay.from_bbs)
 clean=Peer_clean(display);screen=read('SCREEN.BIN');text='\n'.join(screen[i*160:i*160+160:2].decode('cp437') for i in range(25)) if len(screen)==4000 else ''
 stages=read('STAGES.LOG').decode();wanted=['BRIDGE','LOGIN','PASSWORD','WELCOME','BULLETINS','SCAN','PAUSE','MAIN','FILES','JOIN','AREA','FILENAME','CONFIRM','DESCRIPTION','PROTOCOL','HANGUP']
 after=snapshot();after_stats=statistics()
 checks={'DOS_normal_exit':code==0 and bool(read('PASS.TXT')) and not read('FAIL.TXT'),'script_completed':read('SCRIPT.OK')==b'PASS','ordered_script_stages':stages=='|'.join(wanted)+'|',
  'UART_and_IRQ_PIC_restored':len(read('BEFORE.BIN'))==42 and read('BEFORE.BIN')==read('AFTER.BIN'),'keyboard_timer_restored':len(read('KEYOLD.BIN'))==4 and read('KEYOLD.BIN')==read('KEYNEW.BIN'),
  'numeric_AT_only':n['commands']==['ATZ','ATD1'],'real_DSP_CONNECT':n.get('callerInfo',{}).get('bps')==n.get('answerInfo',{}).get('bps')==1200,
  'actual_synthetic_login_in_server_log':len(re.findall(rb'LABUSER\s+Logon ',server_log))==1,
  'native_terminal_replies':b'\x1b[?1;2c' in sent and bool(re.search(rb'\x1b\[\d+;\d+R',sent)),
  'stock_upload_requested':'SXRCN003.BIN' in clean and 'Hang up after transfer?' in clean,
  'final_DOS_main_menu':'Read/Post Messages' in text and 'Main' in text,'no_unrecognized_command':'Unrecognized command' not in clean,
  'profile_unchanged':read('MODEM.PRM')==profile,'directory_accounting':accounting_check(contact,read('CALL.DIR'),1),
  'message_bodies_preserved':message_bodies()==bodies,'no_message_mail_or_download_writes':all(stats['Total'][k]==after_stats['Total'][k] for k in ('dnloads','dnloadb','posts','email','feedback')),
  'server_inputs_preserved':server==after,'inputs_unchanged':all(sha(ROOT/p)==h for p,h in frozen.items()) and all(sha(p)==h for p,h in runtime_inputs.items()) and all(sha(p)==h for p,h in tools.items()),
  'no_relay_errors':not relay.errors and not relay.thread.is_alive(),'no_gateway_errors':not n['errors'],'VM_exited':n['VM_exited'] and n['pool']=='stopped'}
 target=AREA/NAME;expected=payload(NAME);files=stored_files()
 partial=target.read_bytes() if target.is_file() else b''
 checks.update(no_complete_source_published=len(partial)<len(expected),retained_bytes_are_exact_source_prefix=expected.startswith(partial),
  only_expected_new_server_files=set(files)==set(pf['existing_files'])|{NAME,RETRY},
  exact_same_source_retry=(AREA/RETRY).is_file() and (AREA/RETRY).read_bytes()==expected+b'\x1a'*127,existing_server_files_preserved=all(files.get(n)==h for n,h in pf['existing_files'].items()),
  DOS_source_unchanged=upload_path.read_bytes()==expected and upload_stat==(upload_path.stat().st_ino,upload_path.stat().st_size,upload_path.stat().st_mtime_ns))
 result={'passed':all(checks.values()),'checks':{k:bool(v) for k,v in checks.items()},'peer':'synchronet','route':'xmodem-cancel-retry','server_partial_cleanup_accepted':not target.exists(),'posttrain_hold':True,'input_sequence_timeout_ms':250,
  'frozen_inputs':frozen,'runtime_inputs':runtime_inputs,'tool_inputs':tools,'generated_inputs':generated,'server':server,'message_bodies':bodies,'statistics_before':stats,'statistics_after':after_stats,
  'upload':{'name':NAME,'source_path':str(upload_path.relative_to(ROOT)),'source_sha256':sha(upload_path),'source_stat':upload_stat,'source_bytes':len(expected),'target_path':str(target.relative_to(ROOT)),'stored_sha256':sha(target) if target.is_file() else None,'stored_bytes':target.stat().st_size if target.is_file() else None,'existing_files_before':pf['existing_files']},
  'retry':{'name':RETRY,'target_path':str((AREA/RETRY).relative_to(ROOT)),'stored_sha256':sha(AREA/RETRY) if (AREA/RETRY).is_file() else None},
  'server_log_path':str(log),'script_stages':stages,'DOS_screen':text,'gateway':n,'clock_anchors':anchors,
  'captures_sha256':{p.name:sha(p) for p in out.iterdir() if p.suffix in ('.bin','.BIN','.log','.jsonl')},
  'scope':'Actual source-built DOS/ASPECT through synthetic local Hayes control and real SIP/RTP/DSP/Telnet to the pinned owned Synchronet board. Native Escape after visible ACKed progress; CAN cancellation and same-call full same-source retry under a fresh remote name, and actual post-retry Files/Main. Retained/indexed partial is a separate server cleanup gap; timer/key-framing runtime explicitly identified. No message/mail/download writes, physical modem/ATA/UART or full-application acceptance.'}
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'checks':result['checks']}));assert result['passed']


def Peer_clean(data):
 from synchronet import Peer
 return Peer.cleaned(data)

if __name__=='__main__':main()
