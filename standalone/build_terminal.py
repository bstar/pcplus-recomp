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
sources += sorted((ROOT/'src/terminal').glob('*.asm'))
objects=[]
for index,source in enumerate(sources):
 obj=OUT/f'unit-{index}.obj';objects.append(str(obj));options=[]
 if source.parent.parent.name=='reconstruction':options=['-D'+source.parent.name.upper()+'_OMF']
 subprocess.run(['nasm','-f','obj',*options,'-I',str(ROOT/'reconstruction/uart')+'/', '-I',str(ROOT/'reconstruction/ansi')+'/', '-I',str(ROOT/'src/config')+'/', '-I',str(ROOT/'src/directory')+'/',str(source),'-o',str(obj)],check=True)
c_sources=[ROOT/'src/config/prm_dos.c',ROOT/'src/config/terminal_import.c',ROOT/'src/config/modem_import.c',ROOT/'src/config/startup_import.c',ROOT/'src/directory/directory_dos.c',ROOT/'src/directory/directory_live.c',ROOT/'src/directory/directory_actions.c',ROOT/'src/directory/directory_replace.c',ROOT/'src/directory/directory_replace_fs.c',ROOT/'src/key_mapping/keymap_dos.c',ROOT/'src/key_mapping/keymap_dos_fs.c']
c_sources += [ROOT/'src/key_mapping/key_actions_dos.c',ROOT/'src/process/program.c']
c_sources += [ROOT/'src/transfer'/name for name in ['download_file.c','download_fs.c','native_file_bridge.c','terminal_receive.c']]
c_sources += [ROOT/'src/transfer'/name for name in ['upload_file.c','upload_fs.c','terminal_upload.c']]
c_sources += [ROOT/'src/transfer'/name for name in ['batch_header.c','batch_download.c','batch_upload.c','batch_upload_fs.c','ymodem.c','terminal_ymodem.c']]
for source in c_sources:
 obj=OUT/(source.stem+'.obj');objects.append(str(obj))
 subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-s','-w4','-we','-i='+str(ROOT/'src/config'),'-i='+str(ROOT/'src/directory'),'-i='+str(ROOT/'src/key_mapping'),'-i='+str(ROOT/'src/process'),'-i='+str(ROOT/'src/transfer'),'-fo='+str(obj),str(source)],cwd=OUT,check=True)
native=build_native_receiver(ROOT,OUT)
objects += list(map(str,native['objects']))
sender=build_native_sender(ROOT,OUT)
objects += list(map(str,sender['objects']))
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(OUT/'terminal.map'),'name',str(OUT/'TERMINAL.EXE'),'file',','.join(objects),'library',str(Path(os.environ['WATCOM'])/'lib286/dos/clibs.lib')],check=True)
listing=(OUT/'terminal.map').read_text();group=re.search(r'^DGROUP\s+[0-9a-f]+:[0-9a-f]+\s+([0-9a-f]+)',listing,re.M|re.I)
assert group and int(group[1],16)<65536,'DS=SS small-model data/stack exceeds 64KiB'
memory=inspect_terminal_memory(OUT/'TERMINAL.EXE',OUT/'terminal.map')
inputs=sources+c_sources+[ROOT/'src/config/prm_dos.h',ROOT/'src/config/terminal_import.h',ROOT/'src/config/terminal_import.inc',ROOT/'src/config/modem_import.h',ROOT/'src/config/modem_import.inc',ROOT/'src/config/startup_import.h',ROOT/'reconstruction/uart/encodings.inc',ROOT/'reconstruction/uart/layout.inc',ROOT/'reconstruction/ansi/dispatch-layout.inc']
inputs += sorted((ROOT/'src/directory').glob('*.h'))+sorted((ROOT/'src/directory').glob('*.inc'))
inputs += sorted((ROOT/'src/process').glob('*.h'))
inputs += [ROOT/'src/transfer'/name for name in ['download_file.h','download_fs.h','native_file_bridge.h','upload_file.h','upload_fs.h','batch_header.h','batch_download.h','batch_upload.h','batch_upload_fs.h','ymodem.h']]+native['inputs']+[ROOT/'standalone/terminal_memory.py']
inputs += sender['inputs']
inputs += sorted((ROOT/'src/key_mapping').glob('*.h'))+sorted((ROOT/'src/key_mapping').glob('*.inc'))
manifest={'kind':'source-only-interactive-dos-terminal','binary_sha256':hashlib.sha256((OUT/'TERMINAL.EXE').read_bytes()).hexdigest(),'data_stack_bytes':int(group[1],16),'memory_layout':memory,'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},'limitations':['Interactive terminal milestone, not the complete PCPlus application.','Selected ANSI/ordinary controls and ASCII/raw CP437 output; all79 raw keyboard binding slots, function/modifier/keypad banks and bounded binary output now integrated. Specialized controls, fonts, other profiles and full UI remain unfinished.','Standard BIOS-listed COM1..4; explicit partial2.01 PRM import and CLI category overrides. Explicit KBD profile import stages and validates before UART access. AUTO BIOS detection and manual STANDARD/ENHANCED selection supported; no complete PRM schema/default generation.','Explicit-target and directory/browser MODEM/DIRECT connections supported. Native 16-field editor stages changes until acceptance; explicit saves use validated full-file staging and backup replacement.', 'Successful directory connections queue date/call-count updates for deferred foreground persistence. Replacement does not guarantee crash atomicity or concurrent-writer exclusion.', 'Stored password remains private metadata, masked in the editor and never automatically transmitted. Scripts, KEY/META bindings and HALF mode fail explicitly; cycles, advanced transfers, Host and the complete original settings/UI remain unfinished.','NETWORK line editing clips counts to the active region and preserves the column. ORIGINAL ANSI CSI M uses a serviced36-tick discard wait; the exact unbounded original helper is not linked. Complex attribute repair remains explicit. Supported-profile RIS restores a captured source-owned startup state and keymap without DOS/file IO.', 'KBD defaults are maintained network choices, not recovered factory per-profile blocks. Unknown original local actions stop explicitly; Explicit /T:FILE.KEY stages ten actions before UART installation. Alt1..Alt0 execute bounded nonblocking TEXT; PROGRAM uses bounded COMSPEC/PATH lookup, static-parent DOS EXEC, serial handoff, screen restoration and a return key prompt. ASPECT/HOOK execution and binding UI remain unfinished.', 'AltR receives ordinary XMODEM CRC/checksum128/1024 using the real UART and checked staged DOS storage. HARD/NONE only; SOFT rejects before staging. FinalACK follows checked installation. AltS uses the native ordinary sender with checked read-only DOS source files and automatic1K blocks; only actual ACKs advance maintained progress. F2 inside the transfer prompt selects maintained CRC YMODEM batch transfer with checked per-file ownership and exact declared lengths. Window/streaming/other protocols, full transfer settings/UI and physical peers remain unfinished.', 'PROGRAM preserves DTR, pauses configured flow and releases its UART IRQ during child execution; NONE cannot guarantee incoming-data preservation while a child owns the machine. No physical UART/modem/public BBS validation. ENiGMA editor escape-fragmentation behavior remains a server/packetization compatibility boundary.']}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Built build/terminal/TERMINAL.EXE',manifest['binary_sha256'],'DS/SS bytes',manifest['data_stack_bytes'])
