#!/usr/bin/env python3
"""Link real escape/parameter/dispatch/attribute/cursor/report/save-restore/modes code in a DOS diagnostic."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path)
parser.add_argument('--chat-echo-cursor',action='store_true',help='Link the cursor-context primitive and its diagnostic position adapter')
args=parser.parse_args()
out=args.output.resolve() if args.output else ROOT/'build/input_dispatch'
assert out.is_relative_to(ROOT/'build') and (not args.output or not out.exists())
out.mkdir(parents=True,exist_ok=True)
sources=[ROOT/'reconstruction/ansi'/name for name in ['escape.asm','parameters.asm','transition.asm','dispatch.asm']]
sources+=sorted((ROOT/'reconstruction/attributes').glob('*.asm'))
sources+=sorted((ROOT/'reconstruction/screen').glob('*.asm'))
sources+=sorted((ROOT/'reconstruction/erase').glob('*.asm'))
sources+=sorted((ROOT/'reconstruction/scroll').glob('*.asm'))
sources+=sorted((ROOT/'reconstruction/terminal_services').glob('*.asm'))
sources+=sorted((ROOT/'reconstruction/cursor_shape').glob('*.asm'))
sources+=[ROOT/'reconstruction/cursor_state/core.asm',ROOT/'reconstruction/modes/core.asm']
sources+=[ROOT/'reconstruction/reports/core.asm',ROOT/'src/reports/decimal.asm',ROOT/'src/reports/data.asm']
sources+=[ROOT/'src/ansi/decimal.asm',ROOT/'standalone/input_dispatch_host.asm']
sources+=sorted((ROOT/'reconstruction/input_dispatch').glob('*.asm'))
sources+=sorted((ROOT/'reconstruction/render').glob('*.asm'))
sources+=sorted((ROOT/'reconstruction/text').glob('*.asm'))
if args.chat_echo_cursor:
 sources += [ROOT/'src/chat/echo_cursor.asm',ROOT/'standalone/chat_echo_cursor_host.asm']
# Verify each recovered input region without reading an original binary.
proof=json.loads((ROOT/'reconstruction/input_dispatch/provenance.json').read_text())
for unit in proof['units']:
 flat=out/(Path(unit['file']).stem+'.bin')
 subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/',str(ROOT/unit['file']),'-o',str(flat)],check=True)
 assert len(flat.read_bytes())==unit['bytes'] and hashlib.sha256(flat.read_bytes()).hexdigest()==unit['sha256']
tableproof=json.loads((ROOT/'reconstruction/input_dispatch/tables-provenance.json').read_text())
flat=out/'tables.bin'
subprocess.run(['nasm','-f','bin',str(ROOT/'reconstruction/input_dispatch/tables.asm'),'-o',str(flat)],check=True)
assert len(flat.read_bytes())==tableproof['bytes'] and hashlib.sha256(flat.read_bytes()).hexdigest()==tableproof['table_sha256']
objects=[]
for index,source in enumerate(sources):
 obj=out/f'unit-{index}.obj';objects.append(str(obj))
 options=['-DANSI_OMF'] if source.parent.name=='ansi' and source.parent.parent.name=='reconstruction' else []
 if source.parent.name=='attributes':options=['-DATTRIBUTES_OMF']
 if source.parent.name=='screen':options=['-DSCREEN_OMF']
 if source.parent.name=='erase':options=['-DERASE_OMF']
 if source.parent.name=='scroll':options=['-DSCROLL_OMF']
 if source.parent.name=='terminal_services':options=['-DTERMINAL_SERVICES_OMF']
 if source.parent.name=='cursor_shape':options=['-DCURSOR_SHAPE_OMF']
 if source.parent.name=='cursor_state':options=['-DCURSOR_STATE_OMF']
 if source.parent.name=='modes':options=['-DMODES_OMF']
 if source.parent.name=='reports' and source.parent.parent.name=='reconstruction':options=['-DREPORTS_OMF']
 if source.parent.name=='input_dispatch':options=['-DINPUT_DISPATCH_OMF']
 if source.parent.name=='render':options=['-DRENDER_OMF']
 if source.parent.name=='text':options=['-DTEXT_OMF']
 subprocess.run(['nasm','-f','obj',*options,'-I',str(ROOT/'reconstruction/uart')+'/',
                 '-I',str(ROOT/'reconstruction/ansi')+'/', '-o',str(obj),str(source)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(out/'input_dispatch.map'),
                'name',str(out/'INPUT.EXE'),'file',','.join(objects)],check=True)
inputs=sources+[ROOT/'reconstruction/uart/encodings.inc',ROOT/'reconstruction/ansi/dispatch-layout.inc',
 ROOT/'reconstruction/input_dispatch/provenance.json',ROOT/'reconstruction/input_dispatch/tables-provenance.json',Path(__file__).resolve()]
manifest={'kind':'source-only-continuous-input-ansi-control-render-history-diagnostic',
 'chat_echo_cursor':args.chat_echo_cursor,
 'binary_sha256':hashlib.sha256((out/'INPUT.EXE').read_bytes()).hexdigest(),
 'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
 'limitations':['Actual input/control/ANSI/render/cursor/scroll/history and guarded-log paths linked.',
 'Memory input provider replaces a modem; unsupported control families and enabled logging sinks trap.',
 'Host supplies configuration, a4096-byte history ring, graphics map fixtures and ordinary tab stops.']}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Built',str(out.relative_to(ROOT)/'INPUT.EXE'),manifest['binary_sha256'],flush=True)
