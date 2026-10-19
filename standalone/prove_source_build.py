#!/usr/bin/env python3
"""Rebuild application components in a fresh public-source tree without originals."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,time,tempfile
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/application-source-proof';OUT.mkdir(parents=True,exist_ok=True);SNAP=Path(tempfile.mkdtemp(prefix='pcplus-source-proof-'))/'checkout'
assert not SNAP.exists(),'Fresh destination required'
paths=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).split(b'\0')
files={}
excluded={'analysis','build','install','original','originals','.git'}
for raw in sorted(set(paths)):
 if not raw:continue
 rel=Path(os.fsdecode(raw))
 if rel.parts[0] in excluded or '__pycache__' in rel.parts:continue
 if rel.suffix.lower() in {'.exe','.com','.obj','.o','.bin','.zip','.img','.dtp','.cfg','.pyc','.db','.gpr','.gzf','.rep'}:raise AssertionError(f'Unexpected artifact in public-source list: {rel}')
 source=ROOT/rel
 assert source.is_file() and not source.is_symlink(),rel
 data=source.read_bytes();target=SNAP/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);target.chmod(source.stat().st_mode)
 files[str(rel)]=hashlib.sha256(data).hexdigest()
assert not any((SNAP/name).exists() for name in excluded)
canonical=json.dumps(files,sort_keys=True,separators=(',',':')).encode()
snapshot={'source_checkout':str(SNAP),'files':files,'file_count':len(files),'sha256':hashlib.sha256(canonical).hexdigest(),'digest_recipe':'SHA256 UTF8 json.dumps(files,sort_keys=True,separators=(comma,colon)); each file hash covers exact copied bytes','excluded_top_level_paths':sorted(excluded),'build_directory_present_before_build':False,'no_binary_artifacts_in_snapshot':True}
(OUT/'snapshot.json').write_text(json.dumps(snapshot,indent=2)+'\n')
builds=['terminal','config_dos','config_replace','config_abi','ui_windows','modem_commands','modem_responses','modem_send','directory_dial','directory_browser','directory_editor','directory_accounting','keyboard_mapping','keyboard_detection','line_edit','meta_keys','character_edit','process','program_exec','terminal_reset','transfer_blocks','transfer_receive','transfer_send','transfer_files','transfer_session','transfer_uart','download_file','transfer_session_composite','transfer_storage','upload_file','transfer_metadata','batch_header']
# All commands execute inside the fresh checkout's pinned Nix shell.
builds.append('clipboard')
builds.append('snapshot')
builds.append('printer')
builds.append('monitor')
builds.append('print_screen')
builds.append('print_controller')
builds.append('setup')
builds.append('live_configuration')
builds.append('directory_context')
builds.append('xlt_editor')
builds.append('live_translation_child')
builds.append('aspect_literal')
builds.append('aspect_dispatch')
builds.append('aspect_globals')
builds.append('aspect_stack')
builds.append('aspect_unwind')
builds.append('aspect_flow')
builds.append('aspect_file')
builds.append('aspect_operands')
builds.append('aspect_operations')
builds.append('aspect_runtime')
builds.append('aspect_long')
builds.append('aspect_arithmetic')
builds.append('aspect_parameters')
builds.append('aspect_strings')
builds.append('aspect_string_services')
builds.append('aspect_string_commands')
builds.append('aspect_conversions')
builds.append('aspect_conversion_services')
builds.append('aspect_console')
builds.append('aspect_runner')
builds.append('aspect_serial_commands')
builds.append('aspect_serial')
builds.append('aspect_receive_commands')
builds.append('aspect_receive_policy')
builds.append('aspect_directory')
builds.append('aspect_set')
builds.append('aspect_txpace')
builds.append('aspect_find_case')
builds.append('aspect_find_owner')
builds.append('aspect_break_native')
builds.append('aspect_fetch_native')
builds.append('aspect_chain_native')
builds.append('aspect_end_wait_native')
builds.append('aspect_paths')
builds.append('aspect_file_info')
builds.append('aspect_enumeration')
builds.append('aspect_script_files')
builds.append('aspect_script_file_backend')
builds.append('aspect_compiler_lexer')
builds.append('aspect_compiler_unit')
builds.append('aspect_compiler_expression')
builds.append('aspect_compiler_dos')
builds.append('status_helpers')
builds.append('status_renderer')
builds.append('keyboard_reverse_tab')
builds.append('attribute_boundary')
builds.append('attribute_repair')
program='import subprocess\n'+''.join(f"subprocess.run(['python3','standalone/build_{name}.py'],check=True)\n" for name in builds)
owner_checks=['standalone/check_batch_download.py','standalone/check_batch_upload.py','standalone/check_capture_file.py','standalone/check_capture_session.py','standalone/check_capture_owners.py']
owner_checks.append('standalone/check_keyboard_reverse_tab.py')
owner_checks.append('standalone/check_terminal_key_edit.py')
owner_checks.append('standalone/check_attribute_boundary.py')
owner_checks.append('standalone/check_attribute_repair.py')
owner_checks.append('standalone/check_attribute_repair_live.py')
owner_checks.append('standalone/check_aspect_enumeration.py')
owner_checks.append('standalone/check_aspect_enumeration_compiler.py')
owner_checks.append('standalone/check_aspect_file_info.py')
owner_checks.append('standalone/check_aspect_file_info_compiler.py')
owner_checks.append('standalone/check_zmodem_names.py')
owner_checks.append('standalone/check_zmodem_name_ui.py')
owner_checks.append('standalone/check_line_edit_live.py')
owner_checks.append('standalone/check_line_callbacks_live.py')
owner_checks.append('standalone/check_line_controller_layout.py')
owner_checks.append('standalone/check_line_attributes_live.py')
owner_checks.append('standalone/check_terminal_reverse_tab.py')
owner_checks.append('standalone/check_monitor_file.py')
owner_checks.append('standalone/check_printer_device.py')
owner_checks.append('standalone/test_resource_path_dos.py')
owner_checks.append('standalone/test_aspect_compiler.py')
owner_checks.append('standalone/test_aspect_set_compiler.py')
owner_checks.append('standalone/test_aspect_find_case_compiler.py')
owner_checks.append('standalone/test_aspect_break_compiler.py')
owner_checks.append('standalone/check_aspect_set.py')
owner_checks.append('standalone/check_aspect_txpace.py')
owner_checks.append('standalone/check_aspect_find_case.py')
owner_checks.append('standalone/check_aspect_find_owner.py')
owner_checks.append('standalone/check_status_helpers.py')
owner_checks.append('standalone/check_status_renderer.py')
owner_checks.append('standalone/check_status_live.py')
owner_checks.append('standalone/check_aspect_runner.py')
owner_checks.append('standalone/check_aspect_txpace_linked.py')
owner_checks.append('standalone/check_aspect_break_native.py')
owner_checks.append('standalone/check_aspect_fetch_native.py')
owner_checks.append('standalone/check_aspect_break_policy.py')
owner_checks.append('standalone/check_aspect_break_ui.py')
owner_checks.append('standalone/check_aspect_break_owner.py')
owner_checks.append('standalone/check_aspect_break_linked.py')
owner_checks.append('standalone/check_aspect_directory.py')
owner_checks.append('standalone/check_aspect_paths.py')
owner_checks.append('standalone/check_aspect_path_compiler.py')
owner_checks.append('standalone/check_aspect_script_files.py')
owner_checks.append('standalone/check_aspect_script_file_compiler.py')
owner_checks.append('standalone/check_aspect_script_file_backend.py')
owner_checks.append('standalone/package_dos.py')
program+=''.join(f"subprocess.run(['python3',{name!r}],check=True)\n" for name in owner_checks)
with (OUT/'build.log').open('w') as log:
 subprocess.run([str(SNAP/'tools/dev'),'--command','python3','-c',program],cwd=SNAP,stdout=log,stderr=log,check=True,timeout=300)
outputs=['terminal/TERMINAL.EXE','config-dos/CONFIG.EXE','config-dos/CFGFAULT.EXE','config-replace/REPLACE.EXE','config-replace/REPFAULT.EXE','config-abi/ABI.EXE','ui-windows/WINDOWS.EXE','modem-commands/MODEMCMD.EXE','modem-responses/MODEMRSP.EXE','modem-send/MODEMSND.EXE','directory-dial/DIRDIAL.EXE','directory-browser/BROWSER.EXE','directory-editor/EDITOR.EXE','directory-accounting/DIRSTATS.EXE','keyboard-mapping/MAPPING.EXE','keyboard-detection/KBDMODE.EXE','line-edit/LINES.EXE','meta-keys/METAKEYS.EXE','character-edit/CHAREDIT.EXE','process/PROCESS.EXE','process/PROGRAM.EXE','process/CHILD.COM','program-exec/EXECUTOR.EXE','program-exec/CHILD.COM','terminal-reset/RESET.EXE','transfer-blocks/BLOCKS.EXE','transfer-receive/RECEIVE.EXE','transfer-send/SEND.EXE','transfer-files/FILES.EXE','transfer-session/SESSION.EXE','transfer-uart/TUART.EXE','download-file/DOWNLOAD.EXE','download-file/DLFAULT.EXE','transfer-session-composite/TRANSFER.EXE','transfer-storage/TRANSFER.EXE','upload-file/UPLOAD.EXE','upload-file/UPFAULT.EXE','transfer-metadata/METADATA.EXE','batch-header/HEADER.EXE']
outputs += ['batch-download/BATCHDL.EXE','batch-download/BDFAULT.EXE','batch-upload/BATCH.EXE','batch-upload/BUFAULT.EXE']
outputs += ['capture-file/CAPTURE.EXE','capture-file/CAPFAULT.EXE','capture-session/CAPSESS.EXE','capture-session/CSFAULT.EXE']
outputs += ['clipboard/CLIPCORE.EXE']
outputs += ['snapshot/SNAPSHOT.EXE','capture-owners/OWNERS.EXE','capture-owners/OWFAULT.EXE']
outputs += ['printer/PRINTER.EXE']
outputs += ['print_screen/PRINTSCR.EXE','printer-device/PRINTER.EXE']
outputs += ['print_controller/PRINTCTL.EXE']
outputs += ['setup/PRMEDIT.EXE']
outputs += ['live-configuration/LIVE.EXE']
outputs += ['directory-context/CONTEXT.EXE']
outputs += ['xlt-editor/XLTEDIT.EXE']
outputs += ['resource-path/RESOURCE.EXE']
outputs += ['live-translation-child/CHDIR.EXE']
outputs += ['aspect-literal/LITERAL.EXE']
outputs += ['aspect-dispatch/DISPATCH.EXE']
outputs += ['aspect-globals/GLOBALS.EXE']
outputs += ['aspect-stack/STACK.EXE','aspect-unwind/UNWIND.EXE']
outputs += ['aspect-flow/FLOW.EXE','aspect-file/FILE.EXE']
outputs += ['aspect-string-services/SERVICES.EXE','aspect-string-commands/STRCMD.EXE']
outputs += ['aspect-conversions/CONVERT.EXE','aspect-conversion-services/CONVERT.EXE']
outputs += ['aspect-receive-policy/POLICY.EXE']
outputs += ['aspect-directory/DIRBUILT.EXE']
outputs += [f'aspect-set/unit{n}.bin' for n in range(1,15)]
outputs += ['aspect-set/set_commands.obj']
outputs += ['aspect-txpace/delay.bin','aspect-txpace/native.obj','aspect-txpace/txpace.obj','aspect-txpace/TXPACE.EXE']
outputs += [f'aspect-find-case/find_commands-{unit}.bin' for unit in range(1,5)]
outputs += [f'aspect-find-case/case_commands-{unit}.bin' for unit in range(1,3)]
outputs += ['aspect-find-case/find_commands.obj','aspect-find-case/case_commands.obj']
outputs += ['aspect-find-owner/OWNER.EXE']
outputs += ['aspect-break-native/'+u['name']+'.bin' for u in json.loads((ROOT/'standalone/fixtures/aspect_break_native_units.json').read_text())['units']]
outputs += ['aspect-break-native/break_commands.obj']
outputs += ['aspect-fetch-native/'+u['name']+'.bin' for u in json.loads((ROOT/'standalone/fixtures/aspect_fetch_native_units.json').read_text())['units']]
outputs += ['aspect-fetch-native/fetch_command.obj','aspect-fetch-native/break_cursor_read.obj']
outputs += ['aspect-chain-native/'+name for name in ['command.bin','file_open.bin','finish.bin','scratch.bin','strcpy.bin','dispatch.bin','chain_command.obj']]
outputs += ['aspect-end-wait-native/'+name for name in ['end_wait.bin','receive-1.bin','receive-2.bin','end_wait.obj']]
outputs += [f'aspect-paths/command{n}.bin' for n in range(1,5)]
outputs += [f'aspect-paths/service{n}.bin' for n in range(1,6)]
outputs += ['aspect-paths/'+name+'.bin' for name in ('error_map','error_access','error_exec','map_error')]
outputs += ['aspect-paths/'+name+'.obj' for name in ('path_commands','path_services','path_state','error_access','error_exec','map_error')]
outputs += ['aspect-script-files/'+u['name']+'.bin' for u in json.loads((ROOT/'standalone/fixtures/aspect_script_file_native_units.json').read_text())['units']]
outputs += ['aspect-script-files/script_file_commands.obj','aspect-script-files/script_file_services.obj','aspect-script-files/script_file_setting.obj','aspect-script-files/boolean.bin']
outputs += ['aspect-file-info/'+u['name']+'.bin' for u in json.loads((ROOT/'standalone/fixtures/aspect_file_info_native_units.json').read_text())['units']]
outputs += ['aspect-file-info/file_info.obj']
outputs += ['aspect-enumeration/'+u['name']+'.bin' for u in json.loads((ROOT/'standalone/fixtures/aspect_enumeration_native_units.json').read_text())['units']]
outputs += ['aspect-enumeration/enumeration.obj']
outputs += ['aspect-script-file-backend/SCRIPTIO.EXE']
outputs += ['aspect-compiler-lexer/ASPLEX.EXE','aspect-compiler-unit/ASPINV.EXE']
outputs += ['aspect-compiler-expression/ASPEXP.EXE']
outputs += ['aspect-compiler-dos/ASPCOMP.EXE']
outputs += [f'status-helpers/unit{n}.bin' for n in range(1,5)]
outputs += ['status-helpers/STATUS.EXE','status-renderer/STATUS.EXE']
outputs += ['keyboard-reverse-tab/reverse_tab.bin','keyboard-reverse-tab/reverse_tab.obj','keyboard-reverse-tab/left-oracle.bin']
outputs += ['attribute-boundary/'+name+'.'+suffix for name in ('boundary','position','offset','divide') for suffix in ('bin','obj')]
outputs += ['attribute-repair/'+name+'.'+suffix for name in ('attribute_repair-write','attribute_repair-advance','attribute_repair-repair','attribute_boundary-position','erase-default_attribute','erase-previous_attribute','text-char') for suffix in ('bin','obj')]
outputs += ['aspect-receive-commands/RECEIVE.EXE','aspect-runtime/CASES.DAT']
outputs += ['aspect-serial-commands/SERIAL.EXE','aspect-serial/SERIAL.EXE']
outputs += ['aspect-console/CONSOLE.EXE','aspect-runner/ASPECT.EXE','aspect-runner/tests/RUNTEST.EXE']
outputs += ['aspect-parameters/PARAM.EXE','aspect-strings/STRINGS.EXE']
outputs += ['aspect-long/LONG.EXE','aspect-arithmetic/ARITH.EXE']
outputs += ['aspect-operands/OPERANDS.EXE','aspect-operations/OPERATE.EXE','aspect-runtime/EXECUTE.EXE']
outputs += ['monitor/MONITOR.EXE','monitor-file/MONITOR.EXE','monitor-file/MOFAULT.EXE']
results={}
for rel in outputs:
 path=SNAP/'build'/rel;workspace=ROOT/'build'/rel
 digest=hashlib.sha256(path.read_bytes()).hexdigest();expected=hashlib.sha256(workspace.read_bytes()).hexdigest()
 results[rel]={'sha256':digest,'matches_workspace':digest==expected,'workspace_sha256':expected}
assert all(r['matches_workspace'] for r in results.values()),results
manifest=json.loads((SNAP/'build/terminal/manifest.json').read_text());workspace_manifest=json.loads((ROOT/'build/terminal/manifest.json').read_text())
assert manifest==workspace_manifest,'Terminal manifests differ'
for rel,digest in manifest['sources'].items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==digest,rel
common={'passed':True,'source_snapshot':'Fresh maintained public tracked+untracked source snapshot; entire analysis/original/install paths, REA databases and previous build outputs absent before compilation.','source_snapshot_sha256':snapshot['sha256'],'source_file_count':len(files),'snapshot_digest_recipe':snapshot['digest_recipe'],'excluded_top_level_paths':snapshot['excluded_top_level_paths'],'original_executable_present':False,'original_install_present':False,'REA_database_present':False,'previous_build_outputs_present':False,'build_log_sha256':hashlib.sha256((OUT/'build.log').read_bytes()).hexdigest(),'toolchain':'Pinned Nix development shell from copied nix/flake.lock; NASM/Open Watcom DOS8086 small model where applicable.','proof_artifacts':'build/application-source-proof/{snapshot.json,build.log,result.json}','source_checkout':str(SNAP),'scope_note':'Snapshot taken after current runtime freeze; test/docs metadata may subsequently change. Exact runtime source hashes independently reconciled against workspace manifest.','limitation':'Actual isolated source-tree rebuild, not a hermetic filesystem sandbox or complete PCPlus application reconstruction.'}
application={**common,'scope':f'{len(outputs)} current interactive-terminal, maintained application-component and native diagnostic outputs; complete PCPlus application remains unfinished.','output_count':len(outputs),'outputs':results,'build_scripts':[f'standalone/build_{name}.py' for name in builds]+owner_checks}
terminal={**common,'scope':'Source-only interactive DOS terminal with imported keyboard/action settings, directory UI, recovered line/character editing, maintained current-profile RIS, bounded process handoff, retained far shadow/history and live checked XMODEM receive/send and maintained CRC YMODEM batch ownership; full PCPlus application remains incomplete.','binary_sha256':manifest['binary_sha256'],'matches_workspace_binary':True,'matches_workspace_manifest':True,'manifest':manifest}
(OUT/'result.json').write_text(json.dumps({'application':application,'terminal':terminal},indent=2)+'\n')
for name,result in [('application-components-source-build.json',application),('terminal-source-build.json',terminal)]:
 (ROOT/'docs/validation'/name).write_text(json.dumps(result,indent=2)+'\n')
print(f'Fresh source-only proof:{len(outputs)} byte-identical workspace outputs;',manifest['binary_sha256'],'DS/SS',manifest['data_stack_bytes'])
