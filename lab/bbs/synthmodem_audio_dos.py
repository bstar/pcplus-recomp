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
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--receive-trace',action='store_true');p.add_argument('--dmodem',choices=['baseline','candidate']);p.add_argument('--lifecycle',action='store_true');p.add_argument('--carrier',action='store_true');p.add_argument('--carrier-trace',action='store_true');p.add_argument('--key-framing',action='store_true');p.add_argument('--key-framing-trace',action='store_true');p.add_argument('--syscall-trace',action='store_true');p.add_argument('--route',choices=['menus','editor','download','upload','recording'],default='menus');p.add_argument('--fixture-lab',type=Path);p.add_argument('--upload-cancel',action='store_true');p.add_argument('--upload-cancel-retry',action='store_true');p.add_argument('--upload-key-checks',type=Path);p.add_argument('--posttrain-hold',action='store_true')
 p.add_argument('--recording-key-checks',type=Path,help='Validated BIOS Record/compile/replay helper proof')
 p.add_argument('--recording-tcp-checks',type=Path,help='Actual DOS/BBS control with the unchanged recording helper')
 p.add_argument('--recording-marker-trace',type=Path,help='Diagnostic visibility probe proof; this run cannot establish production audio acceptance')
 p.add_argument('--buffered-runtime-proof',type=Path,help='Validated normal200ms d-modem runtime receipt')
 p.add_argument('--editor-burst-checks',type=Path,help='Enable one-tick editor BIOS keys using a passing guarded-helper probe')
 p.add_argument('--editor-multiline-checks',type=Path,help='Enable30-line BIOS draft and page movement with a passing helper/TCP proof')
 p.add_argument('--download-pressure-preparation',type=Path,help='Explicit >64KiB fixture/reference/BIOS preparation proof')
 p.add_argument('--zmodem-receive-credit',type=int,help='Explicit DOS /Z:1..8192 receive policy; default unchanged')
 a=p.parse_args()
 if a.recording_marker_trace:assert a.route=='recording'
 if a.route=='recording':assert a.recording_key_checks and a.recording_tcp_checks and not a.fixture_lab
 elif a.recording_key_checks or a.recording_tcp_checks:raise AssertionError('Recording helper proof requires recording route')
 capture_proof=ROOT/'docs/validation/capture-durability.json';capture=json.loads(capture_proof.read_text())
 assert capture['passed'] and all(row['passed'] for row in capture['cases'])
 assert all(sha(ROOT/n)==h for n,h in capture['inputs'].items())
 if a.zmodem_receive_credit is not None:
  assert a.route=='download' and 1<=a.zmodem_receive_credit<=8192
 server_fixture=None
 if a.fixture_lab:
  from enigma_fixture import bind
  server_fixture=bind(a.fixture_lab,a.route)
 pressure_download=None
 if a.download_pressure_preparation:
  assert a.route=='download','Pressure preparation requires the download route'
  from audio_pressure_download import PressureDownload,OUTER_TIMEOUT
  pressure_download=PressureDownload(a.download_pressure_preparation)
 if a.editor_multiline_checks:
  assert a.route=='editor' and not a.editor_burst_checks,'Choose one editor sequence'
  from editor_multiline_evidence import load as load_multiline,message_count
  multiline_proof=a.editor_multiline_checks.resolve();multiline,_,_,_=load_multiline(multiline_proof)
  multiline_messages_before=message_count()
 if a.editor_burst_checks:
  assert a.route=='editor','Burst editor keys require the editor route'
  burst_proof=a.editor_burst_checks.resolve();assert burst_proof.is_relative_to(ROOT/'build')
  burst=json.loads(burst_proof.read_text());assert burst['passed'] and burst['default_helper_binary_exact']
  assert {c['mode'] for c in burst['cases']}=={'complete-final-screen','text-only-blocks-exit','cursor-only-blocks-exit','prerequisite-watchdog','final-screen-watchdog'}
  assert all(v for c in burst['cases'] for v in c['checks'].values())
  assert all(sha(ROOT/n)==h for n,h in burst['inputs'].items())
 # The buffered image has the same normal post-training/key-framing sources;
 # its explicit receipt selects only the different d-modem binary.
 if a.buffered_runtime_proof:
  assert not any((a.lifecycle,a.carrier,a.carrier_trace,a.key_framing,a.key_framing_trace,a.receive_trace,a.dmodem)),'Choose one pinned runtime profile'
  a.posttrain_hold=True
 if a.posttrain_hold:a.key_framing=True
 a.upload_cancel=a.upload_cancel or a.upload_cancel_retry
 if a.upload_cancel:assert a.route=='upload' and a.fixture_lab and a.upload_key_checks,'Cancellation requires an explicit isolated upload fixture'
 assert sum(bool(v) for v in (a.lifecycle,a.carrier,a.carrier_trace,a.key_framing,a.key_framing_trace,a.receive_trace,a.dmodem))<=1,'Choose one pinned runtime profile'
 a.key_framing=a.key_framing or a.key_framing_trace
 trace=a.receive_trace or a.carrier_trace or a.key_framing_trace
 runtime=a.runtime.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 ledger=ROOT/'docs/validation/synthmodem-gateway.json';prior=json.loads(ledger.read_text());assert prior['passed']
 if a.buffered_runtime_proof:
  from synthmodem_buffered_runtime import validate as validate_buffered
  runtime_inputs=validate_buffered(runtime,a.buffered_runtime_proof)
 elif a.posttrain_hold:
  from synthmodem_posttrain_validation import validate as validate_posttrain
  runtime_inputs=validate_posttrain(runtime)
 elif a.key_framing:runtime_inputs=validate_key_framing_runtime(runtime,trace=a.key_framing_trace)
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
 if a.route=='upload':server_names+=['core/upload.js','core/file_transfer.js','core/file_entry.js','core/view_controller.js','core/toggle_menu_view.js']+['art/themes/luciano_blocktronics/'+n+'.ANS' for n in ['ULOPTS','ULDETAIL','ULCHECK','ULDUPES']]
 server_inputs={n:sha(enigma.SOURCE/n) for n in server_names}
 names=['lab/bbs/synthmodem_audio_dos.py','lab/bbs/bbs_log_capture.py','lab/bbs/check_capture_durability.py','docs/validation/capture-durability.json','lab/bbs/synthmodem_audio_serial.js','lab/bbs/serial_io_evidence.js','lab/bbs/check_serial_io_evidence.js','docs/validation/synthmodem-serial-io-evidence.json','lab/bbs/audio_exit_keys.asm','lab/bbs/audio_get_vector.asm',
  'lab/bbs/synthmodem_bbs_dos.py','lab/bbs/enigma.py','lab/bbs/synthmodem_sparse_runtime.py','lab/bbs/synthmodem_vm_control.py','docs/validation/synthmodem-sparse.json','standalone/modem_fixtures.py','standalone/directory_fixtures.py',
  'standalone/test_terminal.py','src/aspect/compiler.py','nix/flake.nix','nix/flake.lock','tools/modem-dev','build/terminal/TERMINAL.EXE','build/terminal/terminal.map','build/aspect-runner/ASPECT.EXE',str(ledger.relative_to(ROOT))]
 if a.receive_trace:names+=['docs/validation/synthmodem-receive-trace.json']
 if trace:names+=['lab/bbs/receive_trace_io.js','lab/bbs/qemu_trace_wrapper.py','lab/bbs/receive_trace_export.sh']
 names+=['lab/bbs/synthmodem_jitter_runtime.py','lab/bbs/synthmodem_lifecycle_runtime.py']
 if a.lifecycle or a.carrier or a.carrier_trace or a.key_framing:names+=['lab/bbs/internal_sip_capture.js','docs/validation/synthmodem-pool.json','docs/validation/synthmodem-registrar.json','docs/validation/synthmodem-jitter-policy.json']
 if a.carrier or a.carrier_trace or a.key_framing:names+=['lab/bbs/synthmodem_carrier_runtime.py','docs/validation/synthmodem-carrier-runtime.json']
 if a.carrier_trace:names+=['lab/bbs/synthmodem_carrier_trace_runtime.py','docs/validation/synthmodem-carrier-trace-runtime.json']
 if a.key_framing:names+=['lab/bbs/synthmodem_key_framing_runtime.py','docs/validation/synthmodem-key-framing-runtime.json','lab/bbs/patches/synthmodem-key-framing/InputSequenceFramer.js','lab/bbs/patches/synthmodem-key-framing/proxy.patch']
 if a.posttrain_hold:names+=['lab/bbs/synthmodem_posttrain_runtime.py','lab/bbs/synthmodem_posttrain_validation.py','lab/bbs/check_posttrain_hold.js','docs/validation/synthmodem-posttrain-runtime.json']
 if a.buffered_runtime_proof:names+=['lab/bbs/synthmodem_buffered_runtime.py','lab/bbs/check_buffered_dmodem_build.py','nix/dmodem.nix','tools/build-dmodem',str(a.buffered_runtime_proof.resolve().relative_to(ROOT))]
 if a.key_framing_trace:names+=['docs/validation/synthmodem-key-framing-trace-runtime.json','lab/bbs/synthmodem_carrier_trace_runtime.py','docs/validation/synthmodem-carrier-trace-runtime.json']
 if a.dmodem:names+=['docs/validation/synthmodem-jitter-policy.json','nix/dmodem.nix','tools/build-dmodem']
 download_path=download_before=None
 upload_before=None
 if a.route=='download':
  import audio_download
  if pressure_download:audio_download=pressure_download
  download_path,download_before=audio_download.source()
  names+=['lab/bbs/audio_download.py','lab/bbs/audio_download_keys.asm','lab/bbs/check_audio_download_keys.py','docs/validation/audio-download-keys.json','lab/bbs/enigma_transfer.py',str(download_path.relative_to(ROOT)),str(audio_download.HELPER.relative_to(ROOT))]
  if pressure_download:names+=pressure_download.frozen_inputs+['lab/bbs/audit_audio_download.py','lab/bbs/audit_synthmodem_audio_dos.py','lab/bbs/audit_serial_io_evidence.py','lab/bbs/diagnose_audio_caller.js','lab/bbs/audit_zmodem.py']
 if a.route=='upload':
  import audio_upload
  upload_before=audio_upload.prepare(out)
  if a.upload_cancel:
   key_receipt=a.upload_key_checks.resolve();assert key_receipt.is_relative_to(ROOT/'build');kr=json.loads(key_receipt.read_text())
   assert kr['passed'] and {'success','failure','cancel'}.issubset({c['mode'] for c in kr['cases']})
   if a.upload_cancel_retry:assert 'retry' in {c['mode'] for c in kr['cases']}
   assert all(sha(ROOT/n)==h for n,h in kr['inputs'].items())
   names+=['lab/bbs/audio_upload_cancel.py','lab/bbs/check_audio_upload_keys.py',str(key_receipt.relative_to(ROOT))]
   if a.upload_cancel_retry:names+=['lab/bbs/audio_upload_retry.py','lab/bbs/audit_audio_upload_retry.py','lab/bbs/check_audio_retry_control_timing.py','lab/bbs/diagnose_audio_retry_finish.py']
  names+=['lab/bbs/audio_upload.py','lab/bbs/audio_upload_keys.asm','lab/bbs/check_audio_upload_keys.py','lab/bbs/check_audio_upload_navigation.py','docs/validation/audio-upload-keys.json','docs/validation/audio-upload-navigation.json','lab/bbs/enigma_upload_dos.py','lab/bbs/enigma_transfer.py',str(Path(upload_before['source_path']).relative_to(ROOT)),str(audio_upload.helper().relative_to(ROOT))]
 if server_fixture and a.route=='upload':
  navigation=a.fixture_lab.resolve()/'navigation/result.json';nav=json.loads(navigation.read_text())
  assert nav['passed'] and nav['server_fixture']==server_fixture
  isolation=a.fixture_lab.resolve()/'isolation/result.json';isolated=json.loads(isolation.read_text())
  assert isolated['passed'] and isolated['server_fixture']==server_fixture
  names+=['lab/bbs/enigma_receive_finish_instance.py',server_fixture['manifest'],str(navigation.relative_to(ROOT)),
   'lab/bbs/check_receive_finish_instance.py',str(isolation.relative_to(ROOT)),
   'docs/validation/sexyz-receive-finish-candidate.json','nix/sexyz-receive-finish.nix','tools/cut-sexyz-source.py',
   'lab/bbs/patches/sexyz-receive-finish/receive_finish.c','lab/bbs/patches/sexyz-receive-finish/receive_finish.h']
  names+=['lab/bbs/audit_audio_upload.py','lab/bbs/audit_synthmodem_audio_dos.py','lab/bbs/audit_serial_io_evidence.py',
   'lab/bbs/audit_audio_download.py','lab/bbs/audit_zmodem.py','lab/bbs/check_audio_control_timing.py']
 if server_fixture and a.route=='download':
  assert pressure_download and pressure_download.server_fixture==server_fixture
  isolation=a.fixture_lab.resolve()/'isolation/result.json';isolated=json.loads(isolation.read_text())
  assert isolated['passed'] and all(isolated['checks'].values()) and isolated['server_fixture']==server_fixture
  assert all(sha(ROOT/n)==h for n,h in isolated['inputs'].items())
  names+=['lab/bbs/enigma_sender_credit_instance.py',server_fixture['manifest'],str(isolation.relative_to(ROOT)),
   'lab/bbs/check_sender_credit_instance.py','docs/validation/sexyz-send-credit-eof-candidate.json',
   'nix/sexyz-send-credit-eof.nix','nix/sexyz-send-credit.nix','tools/patch-sexyz-eof-position.py','tools/patch-sexyz-send-credit.py',
   'lab/bbs/check_audio_control_timing.py']
 if server_fixture:names+=['lab/bbs/enigma_fixture.py']
 if a.zmodem_receive_credit is not None:
  names+=['src/terminal/options.asm','standalone/check_terminal_options.py','docs/validation/zmodem-receive-credit.json']
 # Bind every declared application build input, including the checked stage
 # readback owner. A binary hash alone cannot identify its source closure.
 terminal_manifest_path=ROOT/'build/terminal/manifest.json'
 terminal_manifest=json.loads(terminal_manifest_path.read_text())
 assert terminal_manifest['kind']=='source-only-interactive-dos-terminal'
 assert terminal_manifest['binary_sha256']==sha(ROOT/'build/terminal/TERMINAL.EXE')
 assert all(not n.startswith(('analysis/','build/')) and (ROOT/n).resolve().is_relative_to(ROOT) for n in terminal_manifest['sources'])
 assert all(sha(ROOT/n)==h for n,h in terminal_manifest['sources'].items())
 names+=['build/terminal/manifest.json',*terminal_manifest['sources']]
 receive_credit=a.zmodem_receive_credit or 8192
 expected_receive_offer=dict(credit=receive_credit,flags=33 if receive_credit<8192 else 35,
  position=((33 if receive_credit<8192 else 35)<<24)|receive_credit) if a.route=='download' else None
 if a.route in ('download','upload'):
  names+=['src/terminal/transfer_actions.asm','standalone/check_carrier_transfer_deadline.py','docs/validation/carrier-transfer-deadline-fixed.json']
  names+=['src/transfer/zmodem.c','src/transfer/zmodem.h','src/transfer/zmodem_wire.c','src/transfer/zmodem_wire.h','standalone/check_zmodem_completed_replay.py','standalone/check_zmodem_completion_bounds.py','docs/validation/zmodem-completed-replay-fixed.json']
  names+=['src/transfer/terminal_zmodem.c','src/transfer/ymodem.h','src/terminal/ymodem_actions.asm','src/terminal/config_abi.inc','standalone/build_terminal.py','standalone/terminal_memory.py','standalone/check_zmodem_upload_timing.py','standalone/check_zmodem_link_policy.py','standalone/record_zmodem_upload_timing.py','docs/ZMODEM_MODEM_RESPONSE.md','docs/validation/zmodem-upload-response-fixed.json']
 names+=['src/terminal/connection.asm','standalone/check_online_exit.py','docs/validation/online-exit.json']
 names+=['lab/bbs/check_audio_login_readiness.py','docs/validation/synthmodem-audio-login-readiness.json']
 if a.route=='recording':
  import audio_recording
  recording_names,recording_helper_sha=audio_recording.inputs(a.recording_key_checks)
  names+=recording_names
  if a.recording_marker_trace:
   marker_path=a.recording_marker_trace.resolve();assert marker_path.is_relative_to(ROOT/'build')
   marker=json.loads(marker_path.read_text())
   assert marker['passed'] and marker['diagnostic_marker_trace'] and len(marker['cases'])==8
   assert any(row['name']=='transient-ready-watchdog' for row in marker['cases'])
   assert all(row['passed'] and all(row['checks'].values()) for row in marker['cases'])
   assert marker['production_helper_sha256']==recording_helper_sha
   assert all(sha(ROOT/name)==h for name,h in marker['inputs'].items())
   names += [str(marker_path.relative_to(ROOT)),*marker['inputs']]
  names+=['lab/bbs/audit_synthmodem_audio_dos.py','lab/bbs/audit_serial_io_evidence.py',
   'lab/bbs/diagnose_audio_caller.js','lab/bbs/modem.py','lab/bbs/synthmodem_gateway.py']
  tcp_path=a.recording_tcp_checks.resolve();assert tcp_path.is_relative_to(ROOT/'build')
  tcp=json.loads(tcp_path.read_text())
  assert tcp['passed'] and all(tcp['checks'].values()) and tcp['helper_sha256']==recording_helper_sha
  assert tcp['binary_sha256']==sha(ROOT/'build/terminal/TERMINAL.EXE')
  assert all(sha(ROOT/name)==h for name,h in tcp['inputs'].items())
  assert all(sha(tcp_path.parent/name)==h for name,h in tcp['captures_sha256'].items())
  names += [str(tcp_path.relative_to(ROOT)),*tcp['inputs'],*[str((tcp_path.parent/name).relative_to(ROOT)) for name in tcp['captures_sha256']]]
 if a.syscall_trace:names+=['lab/bbs/check_dosbox_socket_close.py','lab/bbs/dosbox_socket_close_probe.asm','docs/validation/dosbox-socket-close.json']
 if a.route=='editor':names+=['lab/bbs/audio_editor_keys.asm','lab/bbs/check_audio_editor_watchdog.py','docs/validation/synthmodem-audio-editor-watchdog.json']
 if a.editor_burst_checks:names+=['lab/bbs/check_audio_editor_burst_keys.py',str(burst_proof.relative_to(ROOT))]
 if a.editor_multiline_checks:names+=['lab/bbs/editor_multiline_evidence.py','lab/bbs/check_editor_multiline_evidence.py','lab/bbs/audit_synthmodem_audio_dos.py','lab/bbs/audit_serial_io_evidence.py','lab/bbs/diagnose_audio_caller.js',str(multiline_proof.relative_to(ROOT)),*multiline['inputs']]
 frozen={n:sha(ROOT/n) for n in names}
 for name,digest in frozen.items():
  snapshot=out/'frozen-source'/name;snapshot.parent.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(ROOT/name,snapshot);assert sha(snapshot)==digest
 stage=out/'program';stage.mkdir()
 for n,leaf in [('build/terminal/TERMINAL.EXE','TERMINAL.EXE'),('build/aspect-runner/ASPECT.EXE','ASPECT.EXE')]:shutil.copyfile(ROOT/n,stage/leaf)
 if a.route=='recording':audio_recording.prepare(stage)
 relay=Relay(capture_dir=out);relay.server.settimeout(90);relay.thread.start()
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
 elif a.route=='upload':script+=audio_upload.navigation(wait,mark)
 else:
  script+='transmit "M^M"\n'+wait('MESSAGE AREA',150,'MESSAGES')+'waitquiet 2 120\n'+mark('MESSAGES')
  if a.route in ('menus','recording'):
   script+='transmit "Q^M"\n'+wait('Main Menu',150,'RETURN')+'waitquiet 2 120\n'+mark('RETURN')+'transmit "F^M"\n'
   script+=wait('File Base',150,'FILES')+'waitquiet 2 120\n'+mark('FILES')
  else:
   script+='transmit "P^M"\n'+wait('INS',150,'HEADER')+'waitquiet 2 120\ntransmit "^M"\nwaitquiet 2 120\ntransmit "KEYTEST^M"\nwaitquiet 2 120\n'+mark('EDITOR')
 script+='fopen 0 "D:\\SCRIPT.OK" "wb"\nfputs 0 "PASS"\nfclose 0\n'
 if a.route=='recording':script+=audio_recording.READY_MESSAGE
 script+='endproc\n'
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
 for name,leaf in [('audio_recording_keys.asm' if a.route=='recording' else 'audio_editor_keys.asm' if a.route=='editor' else 'audio_download_keys.asm' if a.route=='download' else 'audio_upload_keys.asm' if a.route=='upload' else 'audio_exit_keys.asm','EXITKEY.COM'),('audio_get_vector.asm','KEYVEC.COM')]:
  flags=[]
  if leaf=='EXITKEY.COM':
   if a.recording_marker_trace:flags+=['-DRECORD_MARKER_TRACE=1','-DRECORD_WATCHDOG_TICKS=12000']
   if a.upload_cancel:flags+=['-DAUDIO_UPLOAD_CANCEL=1']
   if a.upload_cancel_retry:flags+=['-DAUDIO_UPLOAD_RETRY=1']
   if a.editor_burst_checks:flags+=['-DAUDIO_EDITOR_BURST=1','-DAUDIO_EDITOR_KEY_TICKS=1']
   if a.editor_multiline_checks:flags+=['-DAUDIO_EDITOR_MULTILINE=1','-DAUDIO_EDITOR_KEY_TICKS=3']
   if pressure_download:flags+=['-DAUDIO_DOWNLOAD_PRESSURE=1']
  subprocess.run(['nasm','-fbin',*flags,str(ROOT/'lab/bbs'/name),'-o',str(stage/leaf)],check=True)
 if a.editor_multiline_checks:assert sha(stage/'EXITKEY.COM')==multiline['production_helper_sha256']
 if a.route=='recording':
  if a.recording_marker_trace:
   subprocess.run(['nasm','-fbin',str(ROOT/'lab/bbs/audio_recording_keys.asm'),'-o',str(stage/'KEYBASE.COM')],check=True)
   assert sha(stage/'KEYBASE.COM')==recording_helper_sha and sha(stage/'EXITKEY.COM')!=recording_helper_sha
  else:assert sha(stage/'EXITKEY.COM')==recording_helper_sha
 if pressure_download:assert sha(stage/'EXITKEY.COM')==pressure_download.production_helper_sha256
 generated={str(p.relative_to(out)):sha(p) for p in stage.iterdir()}
 from bbs_log_capture import begin as begin_log,collect as collect_log
 log=enigma.SOURCE/'logs/enigma-bbs.log';begin_log(log,out/'server-log-boundary.json')
 tool_inputs={str(Path(shutil.which(n)).resolve()):sha(Path(shutil.which(n))) for n in (['dosbox-x','nasm','strace'] if a.syscall_trace else ['dosbox-x','nasm'])}
 clock_anchors=[]
 start_manifest=dict(frozen_inputs=frozen,runtime_inputs=runtime_inputs,server_inputs=server_inputs,server_root=str(enigma.SOURCE),server_fixture=server_fixture,
  generated_inputs=generated,tool_inputs=tool_inputs,profile_sha256=sha(out/'MODEM.PRM'),directory_initial_hex=contact.hex(),
  download_metadata_before=download_before,upload_metadata_before=upload_before,download_path=str(download_path) if download_path else None,
  route=a.route,recording_marker_trace=bool(a.recording_marker_trace),recording_marker_watchdog_ticks=12000 if a.recording_marker_trace else None,recording_marker_trace_proof=str(a.recording_marker_trace.resolve().relative_to(ROOT)) if a.recording_marker_trace else None,zmodem_receive_credit=a.zmodem_receive_credit,expected_receive_offer=expected_receive_offer,pressure_preparation=str(a.download_pressure_preparation) if pressure_download else None)
 (out/'run-start.json').write_text(json.dumps(start_manifest,indent=2)+'\n')
 def clock_anchor(label):
  before=time.monotonic_ns();wall=time.time_ns();after=time.monotonic_ns()
  clock_anchors.append(dict(label=label,monotonic_before_ns=str(before),wall_ns=str(wall),monotonic_after_ns=str(after)))
  temporary=out/'clock-anchors.tmp';temporary.write_text(json.dumps(clock_anchors,indent=2)+'\n');temporary.replace(out/'clock-anchors.json')
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
TERMINAL @D:\\MODEM.PRM /E:D:\\CALL.DIR /N:1{(' /Z:'+str(a.zmodem_receive_credit)) if a.zmodem_receive_credit is not None else ''}
if errorlevel 1 goto fail
echo PASS>D:\\PASS.TXT
goto capture
:fail
echo FAIL>D:\\FAIL.TXT
:capture
{('EXITKEY R' + chr(10)) if a.route=='recording' else ''}KEYVEC
D:\\SNAP S
D:\\SNAP A
exit
'''
   (out/'dosbox.conf').write_text(cfg)
   command=['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')]
   if a.syscall_trace:command=['strace','--seccomp-bpf','-f','-ttt','-yy','-e','trace=network,close','-o',str(out/'DOS-syscalls.log')]+command
   clock_anchor('before-DOS-launch')
   dos=subprocess.Popen(command,stdout=dl,stderr=dl,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),start_new_session=True)
   doscode=dos.wait(timeout=OUTER_TIMEOUT if pressure_download else 1900 if a.route=='recording' else 1220 if a.route in ('download','upload') or a.editor_multiline_checks else 720 if a.route=='editor' else 600);clock_anchor('after-DOS-exit')
   (out/'exit-status.json').write_text(json.dumps(dict(DOS=doscode,node=None))+'\n')
   nodecode=node.wait(timeout=60);(out/'exit-status.json').write_text(json.dumps(dict(DOS=doscode,node=nodecode))+'\n')
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
 assert read('bbs-input.bin')==relay.to_bbs and read('bbs-output.bin')==relay.from_bbs
 assert read('BBS-relay-events.jsonl').decode()==''.join(json.dumps(e)+'\n' for e in relay.trace)
 rows=collect_log(out/'server-log-boundary.json',out/'server-log-capture')
 sessions={r.get('sessionId') for r in rows if r.get('menuName')=='telnetConnected'};assert len(sessions)==1,sessions
 rows=[r for r in rows if r.get('sessionId') in sessions];menus=[r['menuName'] for r in rows if r.get('menuName')]
 (out/'server-session.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
 (out/'clock-anchors.json').write_text(json.dumps(clock_anchors,indent=2)+'\n')
 n=json.loads((out/'node-result.json').read_text())
 from modem import Telnet
 sent,_=Telnet().feed(relay.to_bbs);display,_=Telnet().feed(relay.from_bbs)
 wanted=['mainMenu','fileBaseMainMenu','fileBaseSearch','fileBaseListEntries','fileBaseDownloadManager','fileTransferProtocolSelection','sendFilesToUser'] if a.route=='download' else ['mainMenu','messageBaseMainMenu','messageBaseNewPost'] if a.route=='editor' else ['mainMenu','messageBaseMainMenu','mainMenu','fileBaseMainMenu'];at=0
 if a.route=='upload':wanted=['mainMenu','fileBaseMainMenu','fileBaseUploadFiles','fileTransferProtocolSelection','recvFilesFromUser']
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
 if a.route=='editor' and not a.editor_multiline_checks:
  del checks['final_file_menu']
  clean=re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]',b'',display).decode('cp437')
  body=clean[clean.find('KEYTEST'):];positions=[(int(row),int(col)) for row,col in re.findall(r'(?:INS|OVR) (\d+),(\d+)',body)]
  expected_keys={'home':b'\x1b[H','end':b'\x1b[F','insert':b'\x1b[2~','delete':b'\x1b[3~','page_up':b'\x1b[5~','page_down':b'\x1b[6~','tab':b'\t','delete_line':b'\x19'}
  observed={key:value in sent for key,value in expected_keys.items()}
  editor={'positions':positions,'keys_emitted':observed,'key_spacing_BIOS_ticks':1 if a.editor_burst_checks else 54,'final_screen_guard':bool(a.editor_burst_checks),'scope':'Actual BIOS editor keys; one-line page keys test boundaries, no multiline scrolling. Connection closes with an unsaved draft; no Save command is sent.'}
  checks.update(editor_entered='messageBaseNewPost' in menus,typed_draft_sent=b'ABCDE' in sent,all_editor_keys_emitted=all(observed.values()),
   home_moves_before_marker=positions[:7]==[(1,2),(1,3),(1,4),(1,5),(1,6),(1,1),(1,2)],insert_toggles_overtype='OVR ' in body)
 if a.editor_multiline_checks:
  from editor_multiline_evidence import check as check_multiline
  del checks['final_file_menu']
  checks['editor_entered']='messageBaseNewPost' in menus
  extra,editor=check_multiline(display,sent,read('SCREEN.BIN'),multiline_proof);checks.update(extra)
  editor['message_count_before']=multiline_messages_before;editor['message_count_after']=message_count()
  checks['multiline_message_count_preserved']=editor['message_count_before']==editor['message_count_after']
 download=None
 upload=None
 recording=None
 if a.route=='recording':
  checks.pop('final_file_menu')
  extra,recording=audio_recording.check(out,rows);checks.update(extra)
  if a.recording_marker_trace:
   checks['diagnostic_marker_trace_is_not_production']=False
   trace_bytes=read('RECTRACE.BIN')
   recording['diagnostic_marker_trace']=list(struct.unpack('<11H',trace_bytes)) if len(trace_bytes)==22 else []
 if a.route=='download':
  checks.pop('final_file_menu')
  extra,download=audio_download.check(out,rows,download_path,download_before);checks.update(extra)
  checks['posttransfer_filename_visible']=('PCPRESS.BIN' if pressure_download else 'PCXTEST.BIN') in text
 if a.route=='upload':
  checks.pop('final_file_menu')
  if a.upload_cancel_retry:
   import audio_upload_retry
   extra,upload=audio_upload_retry.check(out,rows,upload_before)
  elif a.upload_cancel:
   import audio_upload_cancel
   extra,upload=audio_upload_cancel.check(out,rows,upload_before)
  else:extra,upload=audio_upload.check(out,rows,upload_before)
  checks.update(extra)
  checks['posttransfer_filename_visible']=('PCXTEST.BIN' if a.upload_cancel and not a.upload_cancel_retry else audio_upload.NAME) in text
 result={'passed':all(checks.values()),'checks':checks,'zmodem_receive_credit':a.zmodem_receive_credit,'frozen_inputs':frozen,'runtime_inputs':runtime_inputs,'server_inputs':server_inputs,'server_root':str(enigma.SOURCE),'server_fixture':server_fixture,
  'generated_inputs':generated,'tool_inputs':tool_inputs,'syscall_trace':a.syscall_trace,'clock_anchors':clock_anchors,'server_revision':enigma.COMMIT,'server_menus':menus,'script_stages':read('STAGES.LOG').decode('ascii'),'login_readiness':'WAITFOR plus reused one-shot WHEN latch','receive_trace':a.receive_trace,'dmodem_variant':a.dmodem,'lifecycle':a.lifecycle,'carrier':a.carrier,'carrier_trace':a.carrier_trace,'key_framing_trace':a.key_framing_trace,'input_sequence_timeout_ms':250 if a.key_framing else 0,
  'DOS_screen':text,'gateway':n,'route':a.route,'expected_receive_offer':expected_receive_offer,'upload_cancel':a.upload_cancel,'upload_cancel_retry':a.upload_cancel_retry,'posttrain_hold':a.posttrain_hold,'buffered_runtime_proof':str(a.buffered_runtime_proof.resolve().relative_to(ROOT)) if a.buffered_runtime_proof else None,'editor_burst_checks':str(burst_proof.relative_to(ROOT)) if a.editor_burst_checks else None,'editor_multiline_checks':str(multiline_proof.relative_to(ROOT)) if a.editor_multiline_checks else None,'download_pressure_preparation':str(a.download_pressure_preparation.resolve().relative_to(ROOT)) if pressure_download else None,'editor':editor,'download':download,'upload':upload,'captures_sha256':{p.name:sha(p) for p in out.iterdir() if p.suffix in ('.bin','.BIN','.log','.jsonl')},
  'recording':recording,'recording_marker_trace':bool(a.recording_marker_trace),'recording_marker_trace_proof':str(a.recording_marker_trace.resolve().relative_to(ROOT)) if a.recording_marker_trace else None,'recording_marker_watchdog_ticks':12000 if a.recording_marker_trace else None,'recording_key_checks':str(a.recording_key_checks.resolve().relative_to(ROOT)) if a.recording_key_checks else None,
  'recording_tcp_checks':str(a.recording_tcp_checks.resolve().relative_to(ROOT)) if a.recording_tcp_checks else None,
  'scope':'Actual source-built DOS terminal and ASPECT directory script through synthetic local Hayes control and real external/internal SIP, CallSession, pool, originating/guest DSP and Telnet to the explicitly recorded owned ENiGMA board. Any protocol-helper candidate is separately identified; no unmodified-stock, physical modem/ATA/UART or whole-application claim follows from a candidate result.'}
 observation_paths=[out/n for n in ['run-start.json','exit-status.json','clock-anchors.json','server-log-boundary.json']]
 observation_paths+=sorted((out/'server-log-capture').iterdir())
 if a.route=='recording':
  observation_paths += [path for path in (out/'RECKEY.PTR',stage/'PCPLUS.ASP',stage/'PCPLUS.ASX') if path.is_file()]
 result['captures_sha256'].update({str(p.relative_to(out)):sha(p) for p in observation_paths})
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'checks':checks,'result':str(out/'result.json')},indent=2));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
