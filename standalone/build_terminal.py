#!/usr/bin/env python3
"""Build interactive DOS terminal from maintained and recovered source only."""
from pathlib import Path
import hashlib,json,os,re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from transfer.native_link import build_native_receiver
from transfer.native_sender_link import build_native_sender
from terminal_memory import inspect_terminal_memory
from omf_imports import rename_imports
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/terminal';OUT.mkdir(parents=True,exist_ok=True)
modules=['ansi','attributes','screen','erase','scroll','terminal_services','cursor_shape','cursor_state','modes','reports','input_dispatch','input_controls','render','text','ui_windows','modem_commands','modem_responses']
modules += ['attribute_boundary','keyboard_reverse_tab']
sources=[]
for module in modules:
 sources += sorted((ROOT/'reconstruction'/module).glob('*.asm'))
sources += [ROOT/'reconstruction/uart/core.asm',ROOT/'reconstruction/keyboard/core.asm',ROOT/'src/uart/api.asm',ROOT/'src/ansi/decimal.asm',ROOT/'src/reports/decimal.asm',ROOT/'src/reports/data.asm']
sources = [p for p in sources if p != ROOT/'reconstruction/modem_responses/attempt.asm']
sources += [ROOT/'reconstruction/directory_dial/bounded.asm',ROOT/'reconstruction/directory_accounting/patch.asm']
sources += [ROOT/'reconstruction/keyboard_mapping/classifier.asm']
sources += [ROOT/'reconstruction/keyboard_mapping/raw_classifier.asm']
sources += [ROOT/'reconstruction/keyboard_detection/detect.asm']
sources += [ROOT/'reconstruction/line_edit/insert_line.asm',ROOT/'reconstruction/line_edit/delete_line.asm']
sources += sorted((ROOT/'reconstruction/character_edit').glob('*.asm'))
sources += [ROOT/'src/process/dos_exec.asm']
sources += [ROOT/'reconstruction/snapshot'/name for name in ['row.asm','copy.asm','video_begin.asm','video_end.asm']]
sources += sorted((ROOT/'src/terminal').glob('*.asm'))
sources += [ROOT/'src/aspect/resident_bridge.asm']
sources += [ROOT/'src/status/status_renderer_bridge.asm',ROOT/'src/status/status_helpers.asm',
 ROOT/'reconstruction/terminal_reset/status_refresh.asm',ROOT/'reconstruction/terminal_reset/status_fill.asm',
 ROOT/'reconstruction/program_exec/strlen.asm']
sources += [ROOT/'reconstruction/terminal_reset/protected_home.asm']
render_import_adapters={}
sources.append(ROOT/'src/aspect/break_cursor_read.asm')
objects=[]
for index,source in enumerate(sources):
 obj=OUT/f'unit-{index}.obj';objects.append(str(obj));options=[]
 if source.parent.parent.name=='reconstruction':options=['-D'+source.parent.name.upper()+'_OMF']
 if source.parent.name in ('attribute_boundary','keyboard_reverse_tab') or source.name=='protected_home.asm':
  options += ['-DKEYBOARD_ECHO_FAR','-Dscreen_set_cursor=attribute_screen_set_cursor',
   '-Dscreen_cursor_left=attribute_screen_cursor_left','-Dscreen_cursor_right=attribute_screen_cursor_right',
   '-Dscreen_adjust_attribute_boundary=attribute_boundary_local']
 if source==ROOT/'src/aspect/resident_bridge.asm':options+=['-DRESIDENT_BRIDGE_FAR']
 if source.parent==ROOT/'reconstruction/terminal_reset':
  options+=['-DSTATUS_CONFIG_CODE','-Dtext_fill_cells=status_text_fill','-Dtext_write_packed=status_text_packed',
   '-Dterminal_reset_ui_75e8=status_ui_printf','-Dterminal_reset_ui_7630=status_character_fill',
   '-Dterminal_reset_status_message=status_message']
 if source==ROOT/'src/status/status_helpers.asm':
  options+=['-DSTATUS_HELPERS_CONFIG','-Dui_write_string=status_write_string','-Dprogram_strlen=status_strlen']
 if source==ROOT/'reconstruction/input_dispatch/dispatch.asm':options+=['-Dterminal_receive_character=terminal_receive_character_native']
 # Keep NASM's THEADR source name independent of the checkout location, so
 # recorded import-adapter object hashes also reproduce in a fresh tree.
 subprocess.run(['nasm','-f','obj',*options,'-I',str(ROOT/'reconstruction/uart')+'/', '-I',str(ROOT/'reconstruction/ansi')+'/', '-I',str(ROOT/'src/terminal')+'/', '-I',str(ROOT/'src/config')+'/', '-I',str(ROOT/'src/directory')+'/', '-I',str(ROOT/'src/aspect')+'/',str(source.relative_to(ROOT)),'-o',str(obj)],cwd=ROOT,check=True)
 if source==ROOT/'reconstruction/ansi/dispatch.asm':
  before=obj.read_bytes();normalized,counts=rename_imports(before,{'csi_set_modes':'terminal_aspect_set_modes','csi_reset_modes':'terminal_aspect_reset_modes'})
  assert counts=={'csi_set_modes':1,'csi_reset_modes':1},counts
  obj.write_bytes(normalized);render_import_adapters=dict(import_counts=counts,compiler_object_sha256=hashlib.sha256(before).hexdigest(),normalized_object_sha256=hashlib.sha256(normalized).hexdigest())
c_sources=[ROOT/'src/config/prm_dos.c',ROOT/'src/config/terminal_import.c',ROOT/'src/config/modem_import.c',ROOT/'src/config/startup_import.c',ROOT/'src/directory/directory_dos.c',ROOT/'src/directory/directory_live.c',ROOT/'src/directory/directory_actions.c',ROOT/'src/directory/directory_replace.c',ROOT/'src/directory/directory_replace_fs.c',ROOT/'src/key_mapping/keymap_dos.c',ROOT/'src/key_mapping/keymap_dos_fs.c']
c_sources += [ROOT/'src/key_mapping/key_actions_dos.c',ROOT/'src/process/program.c']
c_sources += [ROOT/'src/config/live_configuration.c']
c_sources += [ROOT/'src/config/live_setup_owner.c']
c_sources += [ROOT/'src/config'/name for name in ['terminal_preferences.c','transfer_import.c']]
c_sources += [ROOT/'src/translation/xlt_dos.c',ROOT/'src/translation/xlt_dos_fs.c']
c_sources += [ROOT/'src/translation/xlt_default.c',ROOT/'src/config/resource_path.c']
c_sources += [ROOT/'src/translation/xlt_live.c',ROOT/'src/redisplay/redisplay.c']
c_sources += [ROOT/'src/redisplay/command_menu.c',ROOT/'src/terminal/script_launch.c']
c_sources += sorted((ROOT/'src/clipboard').glob('*.c'))
c_sources += [ROOT/'src/transfer'/name for name in ['download_file.c','download_fs.c','native_file_bridge.c','terminal_receive.c']]
c_sources += [ROOT/'src/transfer'/name for name in ['upload_file.c','upload_fs.c','terminal_upload.c']]
c_sources += [ROOT/'src/transfer'/name for name in ['batch_header.c','batch_download.c','batch_upload.c','batch_upload_fs.c','ymodem.c','terminal_ymodem.c']]
c_sources += [ROOT/'src/transfer'/name for name in ['zmodem.c','zmodem_wire.c','terminal_zmodem.c']]
c_sources += [ROOT/'src/transfer'/name for name in ['zmodem_autostart.c','terminal_autostart.c']]
c_sources += sorted((ROOT/'src/capture').glob('*.c'))
c_sources += sorted((ROOT/'src/printer').glob('*.c'))
c_sources += [ROOT/'src/aspect/renderer_client.c',ROOT/'src/aspect/renderer_policy.c']
c_sources += [ROOT/'src/status/status_formatter.c']
config_sources={ROOT/'src/directory/directory_live.c',ROOT/'src/config/live_configuration.c',ROOT/'src/config/live_setup_owner.c'}
config_sources.update({ROOT/'src/config'/name for name in ['terminal_preferences.c','transfer_import.c']})
config_sources.update({ROOT/'src/transfer'/name for name in ['zmodem_autostart.c','terminal_autostart.c']})
config_sources.add(ROOT/'src/translation/xlt_dos.c')
config_sources.update({ROOT/'src/translation/xlt_default.c',ROOT/'src/config/resource_path.c'})
config_sources.add(ROOT/'src/translation/xlt_live.c')
config_sources.add(ROOT/'src/redisplay/redisplay.c')
config_sources.add(ROOT/'src/redisplay/command_menu.c')
config_sources.add(ROOT/'src/terminal/script_launch.c')
config_sources.update((ROOT/'src/clipboard').glob('*.c'))
config_sources.add(ROOT/'src/process/program.c')
config_sources.update({ROOT/'src/transfer/ymodem.c',ROOT/'src/transfer/batch_header.c'})
config_sources.update({ROOT/'src/transfer'/name for name in ['zmodem.c','zmodem_wire.c','terminal_zmodem.c']})
config_aliases={'terminal_script_prepare':'terminal_script_prepare_impl'}
config_aliases.update({name:name+'_impl' for name in ['directory_live_decode','directory_live_read','directory_live_read_context','directory_live_context_matches','live_configuration_decode','live_setup_bind','live_setup_begin','live_setup_finish','live_setup_abort','live_setup_finish_policy','live_setup_acknowledge']})
config_aliases.update({name:'config_'+name+'_service' for name in ['memcpy','memset','memcmp','strchr','strcmp']})
config_aliases.update({name:name+'_impl' for name in ['terminal_preferences_read','terminal_directory_preferences_read','live_setup_transfer_settings']})
config_aliases.update({name:name+'_impl' for name in ['terminal_autostart_initialize','terminal_autostart_flush','terminal_autostart_poll','terminal_autostart_input']})
config_aliases.update({name:'config_'+name+'_service' for name in ['terminal_auto_deliver','terminal_auto_allowed','terminal_auto_start','terminal_auto_ticks']})
config_aliases['memmove']='config_memmove_service'
config_aliases.update({'terminal_import_decode':'config_terminal_decode_service','modem_import_decode':'config_modem_decode_service','prm_dos_load':'config_prm_read_service','directory_dos_read':'config_directory_read_service','directory_number_expand':'config_number_expand_service'})
config_aliases.update({'capture_fs_canonical':'config_canonical_service','live_modem_expand':'config_live_expand_service'})
config_aliases.update({'xlt_dos_read':'xlt_dos_read_impl',
 'xlt_dos_read_default':'xlt_dos_read_default_impl',
 'clipboard_transport':'config_clipboard_transport_service','history_file_event':'config_history_file_service','program_execute':'program_execute_impl','process_run':'config_process_run_service',
 'redisplay_event':'redisplay_event_impl','xlt_live_bind':'xlt_live_bind_impl','xlt_live_stage':'xlt_live_stage_impl','xlt_live_commit':'xlt_live_commit_impl',
 'xlt_live_initialize':'xlt_live_initialize_impl','xlt_live_reload':'xlt_live_reload_impl','xlt_live_editor':'xlt_live_editor_impl',
 'xlt_fs_open':'config_xlt_open_service','xlt_fs_read':'config_xlt_read_service',
 'xlt_fs_close':'config_xlt_close_service'})
config_aliases.update({name:name+'_impl' for name in ['ymodem_run','batch_header_end','batch_header_encode','batch_header_decode']})
config_aliases.update({'terminal_zmodem_store':'terminal_zmodem_store_impl','strcpy':'config_strcpy_service',
 'batch_upload_seek':'config_bu_seek_service','batch_upload_skip':'config_bu_skip_service',
 'batch_download_exact':'config_bd_exact_service'})
config_aliases.update({name:'config_'+short+'_service' for name,short in {
 'transfer_crc_buffer_original':'ym_crc','ymodem_io_read':'ym_read','ymodem_io_put':'ym_put','ymodem_io_unread':'ym_unread',
 'ymodem_io_poll':'ym_poll','ymodem_io_progress':'ym_progress',
 'batch_download_begin':'bd_begin','batch_download_open':'bd_open','batch_download_append':'bd_append',
 'batch_download_finish':'bd_finish','batch_download_cleanup':'bd_cleanup',
 'batch_upload_begin':'bu_begin','batch_upload_read':'bu_read','batch_upload_next':'bu_next',
 'batch_upload_close':'bu_close','batch_upload_abort':'bu_abort'}.items()})
helper_adapters={}
for source in c_sources:
 obj=OUT/(source.stem+'.obj');objects.append(str(obj))
 options=['-nt=CONFIG_CODE','-nc=FARCODE']+['-d'+name+'='+alias for name,alias in config_aliases.items()] if source in config_sources else []
 if source.parent==ROOT/'src/aspect':options=['-nt=ASPECT_CODE','-nc=FARCODE']
 if source==ROOT/'src/status/status_formatter.c':options=['-ecc']
 subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-s','-w4','-we',*options,'-i='+str(ROOT/'src/config'),'-i='+str(ROOT/'src/directory'),'-i='+str(ROOT/'src/key_mapping'),'-i='+str(ROOT/'src/process'),'-i='+str(ROOT/'src/transfer'),'-fo='+str(obj),str(source)],cwd=OUT,check=True)
 if source==ROOT/'src/transfer/batch_header.c':
  before=obj.read_bytes();normalized,counts=rename_imports(before,{'__U4D':'config_u4div_service_','__U4M':'config_u4mul_service_'})
  (OUT/'batch-header-compiler.obj').write_bytes(before);obj.write_bytes(normalized)
  helper_adapters=dict(import_counts=counts,compiler_object_sha256=hashlib.sha256(before).hexdigest(),normalized_object_sha256=hashlib.sha256(normalized).hexdigest())
config_end=ROOT/'src/config/far_end.asm';config_end_obj=OUT/'config-end.obj'
subprocess.run(['nasm','-f','obj',str(config_end),'-o',str(config_end_obj)],check=True)
objects.append(str(config_end_obj));sources.append(config_end)
native=build_native_receiver(ROOT,OUT)
objects += list(map(str,native['objects']))
sender=build_native_sender(ROOT,OUT)
objects += list(map(str,sender['objects']))
subprocess.run(['wlink','system','dos','order','clname','CODE','clname','FARCODE','clname','DATA','clname','BSS','clname','STACK','option','quiet','option','map='+str(OUT/'terminal.map'),'name',str(OUT/'TERMINAL.EXE'),'file',','.join(objects),'library',str(Path(os.environ['WATCOM'])/'lib286/dos/clibs.lib')],check=True)
listing=(OUT/'terminal.map').read_text();group=re.search(r'^DGROUP\s+[0-9a-f]+:[0-9a-f]+\s+([0-9a-f]+)',listing,re.M|re.I)
assert group and int(group[1],16)<65536,'DS=SS small-model data/stack exceeds 64KiB'
memory=inspect_terminal_memory(OUT/'TERMINAL.EXE',OUT/'terminal.map')
inputs=sources+c_sources+[ROOT/'src/config/prm_dos.h',ROOT/'src/config/terminal_import.h',ROOT/'src/config/terminal_import.inc',ROOT/'src/config/modem_import.h',ROOT/'src/config/modem_import.inc',ROOT/'src/config/startup_import.h',ROOT/'reconstruction/uart/encodings.inc',ROOT/'reconstruction/uart/layout.inc',ROOT/'reconstruction/ansi/dispatch-layout.inc']
inputs += [ROOT/'src/config/live_configuration.h',ROOT/'src/aspect/resident_render.h',ROOT/'src/aspect/resident_bridge.inc',ROOT/'src/aspect/renderer_policy.h',ROOT/'src/aspect/serial_handoff.h']
inputs += [ROOT/'src/status/status_state.inc',ROOT/'src/status/status_formatter.h']
inputs += [ROOT/'src/config/live_setup_owner.h',ROOT/'src/config/terminal_preferences.h',ROOT/'src/config/transfer_import.h']
inputs += [ROOT/'src/config/resource_path.h']
inputs += sorted((ROOT/'src/directory').glob('*.h'))+sorted((ROOT/'src/directory').glob('*.inc'))
inputs += sorted((ROOT/'src/process').glob('*.h'))
inputs += sorted((ROOT/'src/capture').glob('*.h'))
inputs += sorted((ROOT/'src/printer').glob('*.h'))
inputs += sorted((ROOT/'src/clipboard').glob('*.h'))
inputs += sorted((ROOT/'src/redisplay').glob('*.h'))
inputs += [ROOT/'src/transfer'/name for name in ['download_file.h','download_fs.h','native_file_bridge.h','upload_file.h','upload_fs.h','batch_header.h','batch_download.h','batch_upload.h','batch_upload_fs.h','ymodem.h']]+native['inputs']+[ROOT/'standalone/terminal_memory.py']
inputs += sender['inputs']
inputs += [ROOT/'src/transfer/zmodem.h',ROOT/'src/transfer/zmodem_wire.h',ROOT/'src/transfer/zmodem_autostart.h']
inputs += [ROOT/'standalone/omf_imports.py']
inputs += sorted((ROOT/'src/terminal').glob('*.inc'))
inputs += sorted((ROOT/'src/translation').glob('*.h'))
inputs += sorted((ROOT/'src/key_mapping').glob('*.h'))+sorted((ROOT/'src/key_mapping').glob('*.inc'))
manifest={'aspect_renderer_import_adapters':render_import_adapters,'kind':'source-only-interactive-dos-terminal','binary_sha256':hashlib.sha256((OUT/'TERMINAL.EXE').read_bytes()).hexdigest(),'data_stack_bytes':int(group[1],16),'memory_layout':memory,'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},'limitations':['Interactive terminal milestone, not the complete PCPlus application.','Explicit /X:FILE.XLT stages an exact256-byte input table before UART ownership. Normal terminal bytes translate after connection/raw-monitor/controller/transfer filtering; parser continuations, TX and binary/dedicated owners stay raw. RIS preserves selection. Saved PRM modes0/1/2 select identity, current-directory then bounded PCPLUS-environment PCPLUS.XLT lookup, or a7-bit driver mask; /X overrides valid saved modes. Binary transfers reject non-FF masks. AltF10 mode changes use a frozen pre-child current/PCPLUS namespace, checked table staging and separate confirmation before table/enabled/mask commit while serial ownership is handed off. Explicit /X pins its selection. Queued raw input uses the accepted mode after return. Alt-F9 or Setup/Reload input table stages the frozen active canonical source and asks before accepting a same-mode reload over the drained PROGRAM UART owner, without DOS EXEC. Failed/declined reloads retain the table; queued input uses an accepted table. Startup canonical source paths are limited to63 bytes, including resolved CWD. Alt-F8/menu launches sibling XLTEDIT for the frozen active canonical table via a bounded DOS3+ PSP trailer and direct EXEC. A fresh checked snapshot requires separate confirmation after return. The editor accepts DOS8.3 leaves and absolute63-byte paths with same-parent recovery. Complete resource and settings integration remain unfinished.','Selected ANSI/ordinary controls and ASCII/raw CP437 output; all79 raw keyboard binding slots, function/modifier/keypad banks and bounded binary output now integrated. Specialized controls, fonts, other profiles and full UI remain unfinished.','Maintained /S @8.3-leaf runs local source-built PRMEDIT.EXE directly before UART ownership; failure stops startup and successful return reloads through existing validation/CLI precedence. Alt-F10 invokes the editor through the live PROGRAM handoff for an explicit current-directory8.3 leaf. A canonical startup binding, validated candidate and selective commit adopt display, pacing, future modem commands/responses and BREAK; A separate Y/N choice permits same-port baud/line/flow changes after old-format XON/TEMT handoff; Supported4/6 profile changes use a separate confirmation, staged canonical KBD selection and clean RIS/view baseline. Confirmed COM moves require idle ports, preserve target DTR, restore old hardware/vector ownership and recheck acquisition after profile confirmation. No automatic hangup/redial, original PCSETUP ABI, complete emulation collection or source of defaults.', 'Standard BIOS-listed COM1..4; explicit partial2.01 PRM import and CLI category overrides. Explicit KBD profile import stages and validates before UART access. AUTO BIOS detection and manual STANDARD/ENHANCED selection supported; no complete PRM schema/default generation.','Explicit-target and directory/browser MODEM/DIRECT connections supported. Native 16-field editor stages changes until acceptance; explicit saves use validated full-file staging and backup replacement.', 'Successful directory connections queue date/call-count updates for deferred foreground persistence. Replacement does not guarantee crash atomicity or concurrent-writer exclusion.', 'Stored password remains private metadata, masked in the editor and never automatically transmitted. Scripts, KEY/META bindings and HALF mode fail explicitly; cycles, advanced transfers, Host and the complete original settings/UI remain unfinished.','NETWORK line editing clips counts to the active region and preserves the column. ORIGINAL ANSI CSI M uses a serviced36-tick discard wait; the exact unbounded original helper is not linked. Complex attribute repair remains explicit. Supported-profile RIS restores a captured source-owned startup state and keymap without DOS/file IO.', 'KBD defaults are maintained network choices, not recovered factory per-profile blocks. Unknown original local actions stop explicitly; Explicit /T:FILE.KEY stages ten actions before UART installation. Alt1..Alt0 execute bounded nonblocking TEXT; PROGRAM uses bounded COMSPEC/PATH lookup, static-parent DOS EXEC, serial handoff, screen restoration and a return key prompt. ASPECT/HOOK execution and binding UI remain unfinished.', 'Alt-G freezes80x25 characters through recovered row helpers and appends checked PCPLUS.SCR rows via an independent canonical-path file owner. Far memory is retained across PROGRAM. Full original snapshot/printer/script/UI modes remain unfinished.', 'Alt-F1/F2 processed text capture uses checked append/exclusive creation, pause/resume and periodic buffering. Alt-F3 toggles CR-adds-LF. Write/close failures retain partial logs and sticky exit12; PROGRAM closes capture before EXEC. Full capture/printer/settings/UI and ASPECT modes remain unfinished.', 'Ctrl-backslash enters a serviced raw monitor using the actual UART and renderer. Explicit Y replaces PCPLUS.DMP through a third checked canonical-path owner; other answers select view-only. Binary256-byte buffering, periodic flush and failure-aware shutdown preserve text-capture ownership. Nested local/KEY/PROGRAM owners are blocked; the exact original owner/resolver/prompt remain separate diagnostics. Native HOOK and complete monitor/UI geometry remain unfinished.', 'AltR receives ordinary XMODEM CRC/checksum128/1024 using the real UART and checked staged DOS storage. HARD/NONE only; SOFT rejects before staging. FinalACK follows checked installation. AltS uses the native ordinary sender with checked read-only DOS source files and automatic1K blocks; only actual ACKs advance maintained progress. F2 inside the transfer prompt selects maintained CRC YMODEM batch transfer with checked per-file ownership and exact declared lengths. Window/streaming/other protocols, full transfer settings/UI and physical peers remain unfinished.', 'CtrlPgUp opens a maintained63000-byte frozen history viewer in80x25 BIOS mode3/page0 with local line/page/Home/End navigation, ASCII case-insensitive incremental search/F3 and Escape return to the updated live screen. UART/parser/history/capture/replies continue, with frame swaps at top-level receive/idle and64 search candidates per turn. W appends the frozen snapshot through a fourth checked file owner, expanding CR to CRLF in128-source-byte foreground chunks. Append/create, short writes, cancellation, close ambiguity and DOS child inheritance are checked. Alt-= opens a maintained filename clipboard and C enters it from redisplay. The15-entry list supports bounded extraction, add/edit/delete/purge, tags, runtime decimal separator and one/all/tagged paste. Whole-packet TX admission requires an empty queue; cancellation removes only the unsent prefix and preserves later parser replies. Single removal waits for actual UART acceptance, and connection queue resets retain the entry as interrupted. PRM04EA imports a validated0..255 separator through the44-byte settings plan; PRMEDIT offers46 fields. Live setup applies deliberate saved separator edits and preserves session R across canceled/no-op/unrelated returns using an acknowledged source baseline in the628-byte candidate owner. Full native UI, transfer-prompt workflows and other geometries remain unfinished.', 'PROGRAM preserves DTR, pauses configured flow and releases its UART IRQ during child execution; NONE cannot guarantee incoming-data preservation while a child owns the machine. No physical UART/modem/public BBS validation. ENiGMA editor escape-fragmentation behavior remains a server/packetization compatibility boundary.']}
manifest['limitations'].append('Alt-Z opens a source-owned five-group command menu, contextual help and bounded ASCII help search. Existing commands run only after the shared redisplay owner restores the live screen; history/clipboard re-enter their usual guards. Incoming UART/parser/history/replies continue while browsing. Menu code and read-only text reside in CONFIG_CODE, with only bounded state/query bytes near. Original pull-down layout, advertised mouse paths, full settings/key editing and other video geometries remain unfinished.')
manifest['limitations'].append('An otherwise eligible Alt-Z read during normal parser ownership is retained until a distinct resident foreground service can recheck all guards. All BIOS key values, including AX0, retain their key meaning. Subsequent keys remain in the existing32-word typeahead FIFO; repeated Alt-Z coalesces. Escape cancels locally; Alt-X/Alt-H cancel then use normal dispatch. Changed owners/geometry or foreground stop discard the owned pending typeahead. Overflow retains the existing explicit exit3 policy. This is maintained behavior; it does not identify the cause of the earlier unobserved Synchronet refusal.')
manifest['compiler_helper_adapters']={'import_counts':helper_adapters['import_counts'],'record_policy':'Only EXTDEF names/record lengths/checksums change; symbol indices, code, data, local symbols and fixups are preserved.'}
(OUT/'compiler-helper-adapters.json').write_text(json.dumps({'binary_sha256':manifest['binary_sha256'],**helper_adapters},indent=2)+'\n')
manifest['limitations'].append('Maintained YMODEM framing and header codec execute in CONFIG_CODE with unchanged near data and protocol logic. Explicit callbacks bridge resident UART/CRC/file owners; zero-argument callbacks have their own declared family. Newly compiled batch_header OMF imports for Watcom32-bit arithmetic are renamed to local register adapters; all code/data/fixup records and external indices are preserved. Original ordinary XMODEM modules remain resident and unchanged.')
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Built build/terminal/TERMINAL.EXE',manifest['binary_sha256'],'DS/SS bytes',manifest['data_stack_bytes'])
