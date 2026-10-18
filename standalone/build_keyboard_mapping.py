#!/usr/bin/env python3
"""Build recovered exact units and maintained classifier without original input."""
from pathlib import Path
import hashlib,json,re,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/keyboard-mapping';OUT.mkdir(parents=True,exist_ok=True)
CORE=ROOT/'reconstruction/keyboard_mapping';proof=json.loads((CORE/'provenance.json').read_text())
for unit in proof['units']:
 source=ROOT/unit['file'];dest=OUT/(source.stem+'.bin')
 subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(dest)],check=True)
 assert hashlib.sha256(dest.read_bytes()).hexdigest()==unit['sha256'],source
# Host uses original DS addresses for transparent shared/interior state aliases.
asmfiles=[CORE/(n+'.asm') for n in ('classifier','raw_classifier','emit','echo','dispatch','pace','dispatch_table')]
externs=set();globals_=set()
for file in asmfiles:
 text=file.read_text();externs.update(re.findall(r'^extern (\w+)',text,re.M))
 for names in re.findall(r'^global (.*)',text,re.M):globals_.update(names.split(','))
state={v:int(k,16) for k,v in proof['state'].items()}
host=['BITS 16','CPU 8086','GROUP DGROUP _DATA STACK','SEGMENT _TEXT public class=CODE use16','extern keyboard_classify,keyboard_classify_raw,keyboard_mapping_emit','..start:',' mov ax,DGROUP',' mov ds,ax',' cli',' mov ss,ax',' mov sp,stack_top',' sti',' mov ax,0x4800',' call keyboard_classify',' cmp ax,72',' jne .fail',' mov ax,0x4c00',' int 0x21','.fail:',' mov ax,0x4c01',' int 0x21']
# Self-check in actual DOS: register-input classifier and actual recovered emitter.
start=host.index(' mov ax,0x4800');host=host[:start]
host += [' mov byte [terminal_keymap+58*12],27',' mov byte [terminal_keymap+59*12],27',' mov si,classifier_vectors',' mov cx,vector_count','.next:',' mov ax,[cs:si]',' mov dx,[cs:si+2]',' add si,4',' push cx',' push dx',' call keyboard_classify_raw',' pop dx',' pop cx',' cmp ax,dx',' jne .fail',' loop .next',' mov bx,emitter_fixture',' call keyboard_mapping_emit',' cmp word [wire_count],3',' jne .fail',' cmp byte [wire_bytes],65',' jne .fail',' cmp byte [wire_bytes+1],0',' jne .fail',' cmp byte [wire_bytes+2],66',' jne .fail',' mov ax,0x4c00',' int 0x21','.fail:',' mov ax,0x4c01',' int 0x21','classifier_vectors:']
vectors=[(0x4800,72),(0x5000,73),(0x4b00,74),(0x4d00,75),(0x4700,76),(0x4f00,77),(0x5200,8),(0x5300,9),(0x4900,13),(0x5100,14),(0x7700,11),(0x7500,12),(0x0e08,10),(0x0e7f,15),(9,6),(13,78),(27,0x11b),(8,0x108),(0x8b00,0xffff),(0x8c00,0xffff),(0x7800,0xfffe)]
for first,slot in [(0x3b,16),(0x54,38),(0x5e,60)]:vectors.extend(((first+i)<<8,slot+i) for i in range(10))
vectors += [(0x8500,26),(0x8600,27),(0x8700,48),(0x8800,49),(0x8900,70),(0x8a00,71)]
vectors += [(0x372a,0),(0x4a2d,1),(0x4e2b,2),(0x532e,3),(0xe02f,4),(0xe00d,5),(0x5230,28),(0x4f31,29),(0x5032,30),(0x5133,31),(0x4b34,32),(0x4c35,33),(0x4d36,34),(0x4737,35),(0x4838,36),(0x4939,37),(0x48e0,50),(0x50e0,51),(0x4be0,52),(0x4de0,53),(0x52e0,54),(0x53e0,55),(0x47e0,56),(0x4fe0,57),(0x49e0,58),(0x51e0,59)]
for key,want in vectors:host.append(f' dw {key},{want}')
host.append(f'vector_count equ {len(vectors)}')
for name in sorted(externs-globals_):
 if name in state:continue
 if name=='keyboard_service_ab0b':
  host += ['global '+name,name+':',' push bp',' mov bp,sp',' push bx',' mov bx,[wire_count]',' mov ax,[bp+4]',' mov [wire_bytes+bx],al',' inc word [wire_count]',' pop bx',' pop bp',' ret 2'];continue
 host += ['global '+name,name+':',' int3',' ret'] # unresolved original UI service trap, not implementation
host += ['SEGMENT _DATA public class=DATA use16','global keymap_fixture','keymap_fixture:']
for name,offset in sorted(state.items(),key=lambda pair:pair[1]):
 if name in globals_:continue
 host += ['global '+name,name+f' equ keymap_fixture+0x{offset:x}']
host+=[' times 0xd000 db 0','wire_count: dw 0','wire_bytes: times 16 db 0','emitter_fixture: db 65,255,66,0','SEGMENT STACK stack align=16 class=STACK use16',' resb 1024','stack_top:']
path=OUT/'host.asm';path.write_text('\n'.join(host)+'\n');sources=asmfiles+[path];objects=[]
for i,source in enumerate(sources):
 dest=OUT/f'unit{i}.obj';objects.append(str(dest))
 subprocess.run(['nasm','-f','obj','-DKEYBOARD_MAPPING_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(dest)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(OUT/'mapping.map'),'name',str(OUT/'MAPPING.EXE'),'file',','.join(objects)],check=True)
(OUT/'manifest.json').write_text(json.dumps({'binary_sha256':hashlib.sha256((OUT/'MAPPING.EXE').read_bytes()).hexdigest(),'exact_bytes':sum(u['bytes'] for u in proof['units']),'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in asmfiles},'diagnostic_host_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'limitations':['Original UI/service dependencies deliberately trap. This diagnostic does not implement those services.','Maintained pure classifier owns zero-default hotkey/scrollback state; full original dispatcher remains unlinked in live terminal.']},indent=2)+'\n')
print('Built source-only keyboard mapping diagnostic;',sum(u['bytes'] for u in proof['units']),'exact bytes plus maintained classifier')
