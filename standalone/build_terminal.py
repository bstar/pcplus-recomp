#!/usr/bin/env python3
"""Build interactive DOS terminal from maintained and recovered source only."""
from pathlib import Path
import hashlib,json,os,re,subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/terminal';OUT.mkdir(parents=True,exist_ok=True)
modules=['ansi','attributes','screen','erase','scroll','terminal_services','cursor_shape','cursor_state','modes','reports','input_dispatch','input_controls','render','text','ui_windows','modem_commands','modem_responses']
sources=[]
for module in modules:
 sources += sorted((ROOT/'reconstruction'/module).glob('*.asm'))
sources += [ROOT/'reconstruction/uart/core.asm',ROOT/'reconstruction/keyboard/core.asm',ROOT/'src/uart/api.asm',ROOT/'src/ansi/decimal.asm',ROOT/'src/reports/decimal.asm',ROOT/'src/reports/data.asm']
sources = [p for p in sources if p != ROOT/'reconstruction/modem_responses/attempt.asm']
sources += [ROOT/'reconstruction/directory_dial/bounded.asm',ROOT/'reconstruction/directory_accounting/patch.asm']
sources += sorted((ROOT/'src/terminal').glob('*.asm'))
objects=[]
for index,source in enumerate(sources):
 obj=OUT/f'unit-{index}.obj';objects.append(str(obj));options=[]
 if source.parent.parent.name=='reconstruction':options=['-D'+source.parent.name.upper()+'_OMF']
 subprocess.run(['nasm','-f','obj',*options,'-I',str(ROOT/'reconstruction/uart')+'/', '-I',str(ROOT/'reconstruction/ansi')+'/', '-I',str(ROOT/'src/config')+'/', '-I',str(ROOT/'src/directory')+'/',str(source),'-o',str(obj)],check=True)
c_sources=[ROOT/'src/config/prm_dos.c',ROOT/'src/config/terminal_import.c',ROOT/'src/config/modem_import.c',ROOT/'src/config/startup_import.c',ROOT/'src/directory/directory_dos.c',ROOT/'src/directory/directory_live.c',ROOT/'src/directory/directory_actions.c',ROOT/'src/directory/directory_replace.c',ROOT/'src/directory/directory_replace_fs.c']
for source in c_sources:
 obj=OUT/(source.stem+'.obj');objects.append(str(obj))
 subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-s','-w4','-we','-i='+str(ROOT/'src/config'),'-i='+str(ROOT/'src/directory'),'-fo='+str(obj),str(source)],cwd=OUT,check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(OUT/'terminal.map'),'name',str(OUT/'TERMINAL.EXE'),'file',','.join(objects),'library',str(Path(os.environ['WATCOM'])/'lib286/dos/clibs.lib')],check=True)
listing=(OUT/'terminal.map').read_text();group=re.search(r'^DGROUP\s+[0-9a-f]+:[0-9a-f]+\s+([0-9a-f]+)',listing,re.M|re.I)
assert group and int(group[1],16)<65536,'DS=SS small-model data/stack exceeds 64KiB'
inputs=sources+c_sources+[ROOT/'src/config/prm_dos.h',ROOT/'src/config/terminal_import.h',ROOT/'src/config/terminal_import.inc',ROOT/'src/config/modem_import.h',ROOT/'src/config/modem_import.inc',ROOT/'src/config/startup_import.h',ROOT/'reconstruction/uart/encodings.inc',ROOT/'reconstruction/uart/layout.inc',ROOT/'reconstruction/ansi/dispatch-layout.inc']
inputs += sorted((ROOT/'src/directory').glob('*.h'))+sorted((ROOT/'src/directory').glob('*.inc'))
manifest={'kind':'source-only-interactive-dos-terminal','binary_sha256':hashlib.sha256((OUT/'TERMINAL.EXE').read_bytes()).hexdigest(),'data_stack_bytes':int(group[1],16),'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},'limitations':['Interactive terminal milestone, not the complete PCPlus application.','Selected ANSI/ordinary controls, ASCII/raw CP437 output and four arrow mappings; specialized controls, fonts, profiles and UI remain unfinished.','Standard BIOS-listed COM1..4; explicit partial2.01 PRM import, with CLI category overrides. No complete schema/default generation or KBD import.','Explicit-target and directory/browser MODEM/DIRECT connections supported. Native 16-field editor stages changes until acceptance; explicit saves use validated full-file staging and backup replacement.', 'Successful directory connections queue date/call-count updates for deferred foreground persistence. Replacement does not guarantee crash atomicity or concurrent-writer exclusion.', 'Stored password remains private metadata, masked in the editor and never automatically transmitted. Scripts, KEY/META bindings and HALF mode fail explicitly; cycles, transfers, Host and the complete original settings/UI remain unfinished.','No physical UART/modem/public BBS validation.']}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Built build/terminal/TERMINAL.EXE',manifest['binary_sha256'],'DS/SS bytes',manifest['data_stack_bytes'])
