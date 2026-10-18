#!/usr/bin/env python3
"""Build interactive DOS terminal from maintained and recovered source only."""
from pathlib import Path
import hashlib,json,os,re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from transfer.native_link import build_native_receiver
from transfer.native_sender_link import build_native_sender
from terminal_memory import inspect_terminal_memory
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/terminal';OUT.mkdir(parents=True,exist_ok=True)
modules=['ansi','attributes','screen','erase','scroll','terminal_services','cursor_shape','cursor_state','modes','reports','input_dispatch','input_controls','render','text','ui_windows','modem_commands','modem_responses']
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
objects=[]
for index,source in enumerate(sources):
 obj=OUT/f'unit-{index}.obj';objects.append(str(obj));options=[]
 if source.parent.parent.name=='reconstruction':options=['-D'+source.parent.name.upper()+'_OMF']
 subprocess.run(['nasm','-f','obj',*options,'-I',str(ROOT/'reconstruction/uart')+'/', '-I',str(ROOT/'reconstruction/ansi')+'/', '-I',str(ROOT/'src/terminal')+'/', '-I',str(ROOT/'src/config')+'/', '-I',str(ROOT/'src/directory')+'/',str(source),'-o',str(obj)],check=True)
c_sources=[ROOT/'src/config/prm_dos.c',ROOT/'src/config/terminal_import.c',ROOT/'src/config/modem_import.c',ROOT/'src/config/startup_import.c',ROOT/'src/directory/directory_dos.c',ROOT/'src/directory/directory_live.c',ROOT/'src/directory/directory_actions.c',ROOT/'src/directory/directory_replace.c',ROOT/'src/directory/directory_replace_fs.c',ROOT/'src/key_mapping/keymap_dos.c',ROOT/'src/key_mapping/keymap_dos_fs.c']
c_sources += [ROOT/'src/key_mapping/key_actions_dos.c',ROOT/'src/process/program.c']
c_sources += [ROOT/'src/config/live_configuration.c']
c_sources += [ROOT/'src/config/live_setup_owner.c']
c_sources += [ROOT/'src/transfer'/name for name in ['download_file.c','download_fs.c','native_file_bridge.c','terminal_receive.c']]
c_sources += [ROOT/'src/transfer'/name for name in ['upload_file.c','upload_fs.c','terminal_upload.c']]
c_sources += [ROOT/'src/transfer'/name for name in ['batch_header.c','batch_download.c','batch_upload.c','batch_upload_fs.c','ymodem.c','terminal_ymodem.c']]
c_sources += sorted((ROOT/'src/capture').glob('*.c'))
c_sources += sorted((ROOT/'src/printer').glob('*.c'))
config_sources={ROOT/'src/directory/directory_live.c',ROOT/'src/config/live_configuration.c',ROOT/'src/config/live_setup_owner.c'}
config_aliases={name:name+'_impl' for name in ['directory_live_decode','directory_live_read','directory_live_read_context','directory_live_context_matches','live_configuration_decode','live_setup_bind','live_setup_begin','live_setup_finish','live_setup_abort','live_setup_finish_policy','live_setup_acknowledge']}
config_aliases.update({name:'config_'+name+'_service' for name in ['memcpy','memset','memcmp','strchr']})
config_aliases.update({'terminal_import_decode':'config_terminal_decode_service','modem_import_decode':'config_modem_decode_service','prm_dos_load':'config_prm_read_service','directory_dos_read':'config_directory_read_service','directory_number_expand':'config_number_expand_service'})
config_aliases.update({'capture_fs_canonical':'config_canonical_service','live_modem_expand':'config_live_expand_service'})
for source in c_sources:
 obj=OUT/(source.stem+'.obj');objects.append(str(obj))
 options=['-nt=CONFIG_CODE','-nc=FARCODE']+['-d'+name+'='+alias for name,alias in config_aliases.items()] if source in config_sources else []
 subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-s','-w4','-we',*options,'-i='+str(ROOT/'src/config'),'-i='+str(ROOT/'src/directory'),'-i='+str(ROOT/'src/key_mapping'),'-i='+str(ROOT/'src/process'),'-i='+str(ROOT/'src/transfer'),'-fo='+str(obj),str(source)],cwd=OUT,check=True)
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
inputs += [ROOT/'src/config/live_configuration.h']
inputs += [ROOT/'src/config/live_setup_owner.h']
inputs += sorted((ROOT/'src/directory').glob('*.h'))+sorted((ROOT/'src/directory').glob('*.inc'))
inputs += sorted((ROOT/'src/process').glob('*.h'))
inputs += sorted((ROOT/'src/capture').glob('*.h'))
inputs += sorted((ROOT/'src/printer').glob('*.h'))
inputs += [ROOT/'src/transfer'/name for name in ['download_file.h','download_fs.h','native_file_bridge.h','upload_file.h','upload_fs.h','batch_header.h','batch_download.h','batch_upload.h','batch_upload_fs.h','ymodem.h']]+native['inputs']+[ROOT/'standalone/terminal_memory.py']
inputs += sender['inputs']
inputs += sorted((ROOT/'src/terminal').glob('*.inc'))
inputs += sorted((ROOT/'src/key_mapping').glob('*.h'))+sorted((ROOT/'src/key_mapping').glob('*.inc'))
manifest={'kind':'source-only-interactive-dos-terminal','binary_sha256':hashlib.sha256((OUT/'TERMINAL.EXE').read_bytes()).hexdigest(),'data_stack_bytes':int(group[1],16),'memory_layout':memory,'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},'limitations':['Interactive terminal milestone, not the complete PCPlus application.','Selected ANSI/ordinary controls and ASCII/raw CP437 output; all79 raw keyboard binding slots, function/modifier/keypad banks and bounded binary output now integrated. Specialized controls, fonts, other profiles and full UI remain unfinished.','Maintained /S @8.3-leaf runs local source-built PRMEDIT.EXE directly before UART ownership; failure stops startup and successful return reloads through existing validation/CLI precedence. Alt-F10 invokes the editor through the live PROGRAM handoff for an explicit current-directory8.3 leaf. A canonical startup binding, validated candidate and selective commit adopt display, pacing, future modem commands/responses and BREAK; A separate Y/N choice permits same-port baud/line/flow changes after old-format XON/TEMT handoff; Supported4/6 profile changes use a separate confirmation, staged canonical KBD selection and clean RIS/view baseline. COM changes remain deferred. No original PCSETUP ABI, cross-port migration, complete emulation collection or source of defaults.', 'Standard BIOS-listed COM1..4; explicit partial2.01 PRM import and CLI category overrides. Explicit KBD profile import stages and validates before UART access. AUTO BIOS detection and manual STANDARD/ENHANCED selection supported; no complete PRM schema/default generation.','Explicit-target and directory/browser MODEM/DIRECT connections supported. Native 16-field editor stages changes until acceptance; explicit saves use validated full-file staging and backup replacement.', 'Successful directory connections queue date/call-count updates for deferred foreground persistence. Replacement does not guarantee crash atomicity or concurrent-writer exclusion.', 'Stored password remains private metadata, masked in the editor and never automatically transmitted. Scripts, KEY/META bindings and HALF mode fail explicitly; cycles, advanced transfers, Host and the complete original settings/UI remain unfinished.','NETWORK line editing clips counts to the active region and preserves the column. ORIGINAL ANSI CSI M uses a serviced36-tick discard wait; the exact unbounded original helper is not linked. Complex attribute repair remains explicit. Supported-profile RIS restores a captured source-owned startup state and keymap without DOS/file IO.', 'KBD defaults are maintained network choices, not recovered factory per-profile blocks. Unknown original local actions stop explicitly; Explicit /T:FILE.KEY stages ten actions before UART installation. Alt1..Alt0 execute bounded nonblocking TEXT; PROGRAM uses bounded COMSPEC/PATH lookup, static-parent DOS EXEC, serial handoff, screen restoration and a return key prompt. ASPECT/HOOK execution and binding UI remain unfinished.', 'Alt-G freezes80x25 characters through recovered row helpers and appends checked PCPLUS.SCR rows via an independent canonical-path file owner. Far memory is retained across PROGRAM. Full original snapshot/printer/script/UI modes remain unfinished.', 'Alt-F1/F2 processed text capture uses checked append/exclusive creation, pause/resume and periodic buffering. Alt-F3 toggles CR-adds-LF. Write/close failures retain partial logs and sticky exit12; PROGRAM closes capture before EXEC. Full capture/printer/settings/UI and ASPECT modes remain unfinished.', 'Ctrl-backslash enters a serviced raw monitor using the actual UART and renderer. Explicit Y replaces PCPLUS.DMP through a third checked canonical-path owner; other answers select view-only. Binary256-byte buffering, periodic flush and failure-aware shutdown preserve text-capture ownership. Nested local/KEY/PROGRAM owners are blocked; the exact original owner/resolver/prompt remain separate diagnostics. Native HOOK and complete monitor/UI geometry remain unfinished.', 'AltR receives ordinary XMODEM CRC/checksum128/1024 using the real UART and checked staged DOS storage. HARD/NONE only; SOFT rejects before staging. FinalACK follows checked installation. AltS uses the native ordinary sender with checked read-only DOS source files and automatic1K blocks; only actual ACKs advance maintained progress. F2 inside the transfer prompt selects maintained CRC YMODEM batch transfer with checked per-file ownership and exact declared lengths. Window/streaming/other protocols, full transfer settings/UI and physical peers remain unfinished.', 'PROGRAM preserves DTR, pauses configured flow and releases its UART IRQ during child execution; NONE cannot guarantee incoming-data preservation while a child owns the machine. No physical UART/modem/public BBS validation. ENiGMA editor escape-fragmentation behavior remains a server/packetization compatibility boundary.']}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Built build/terminal/TERMINAL.EXE',manifest['binary_sha256'],'DS/SS bytes',manifest['data_stack_bytes'])
