#!/usr/bin/env python3
"""Invoke the real transaction from a declared BIOS-boundary fixture in DOS8086."""
import argparse,hashlib,json,re,struct,subprocess
from pathlib import Path
import test_connection_dos as harness
ROOT=harness.ROOT
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--hidden-status',action='store_true');p.add_argument('--character-edits',action='store_true');p.add_argument('--field-edits',action='store_true');p.add_argument('--scroll-fields',action='store_true');a=p.parse_args()
 assert not a.scroll_fields or a.field_edits
 binary=a.terminal.resolve();manifest=json.loads((binary.parent/'manifest.json').read_text())
 assert manifest['native_reset_transaction']and sha(binary)==manifest['binary_sha256']
 for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build')and not out.exists();out.mkdir(parents=True)
 # The MZ is unmodified. Call the public transaction from its real startup
 # geometry. Only the optional hidden-status case changes status ownership.
 rows=25 if a.hidden_status else 24
 cells=rows*132
 listing=(binary.parent/'terminal.map').read_text()
 symbols={name:(int(seg,16),int(off,16))for seg,off,name in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
 dg=int(re.search(r'^DGROUP\s+([0-9a-f]+):',listing,re.M|re.I)[1],16)
 names=['screen_attribute_row_bytes','screen_columns','screen_attributes_base','screen_attribute_cells','erase_attribute_values_base','erase_attribute_values',
  'screen_cursor_wrap','screen_attribute_checks','attributes_current','attributes_preset_value','csi_erase_attribute','attributes_normal_value','erase_cell_count','screen_cursor_row','screen_cursor_column',
  'csi_row_count','csi_last_row','screen_last_row','terminal_dec_keys','ui_flow_suppressed','screen_viewport_active','erase_shadow_segment','erase_shadow_offset']
 defines={name.upper():symbols[name][0]*16+symbols[name][1]-dg*16 for name in names}
 cs,off=symbols['terminal_native_width_far'];defines.update(DGROUP_REL=dg,LIVE_CODE_REL=cs,LIVE_OFF=off)
 (out/'line_attributes_offsets.inc').write_text(''.join(f'%define {name} {value}\n'for name,value in defines.items()))
 observer=ROOT/'standalone/line_attributes_watch.asm';text=observer.read_text()
 start=text.index(' push ds\n pop es\n mov di,SCREEN_ATTRIBUTE_CELLS')
 end=text.index(' inc word [cs:staged]',start)
 end=text.index(' jmp .done',end)+len(' jmp .done')
 text=text[:start]+''' ; Let the original BIOS cursor operation finish before invoking another
 ; BIOS-using routine. The interrupted application has already stored its
 ; cursor fields and performs no later store after its cursor-output call.
 pushf
 call far [cs:old10]
 STATUS_FIXTURE
 inc word [cs:staged]
 mov ax,ds
 sub ax,DGROUP_REL
 add ax,LIVE_CODE_REL
 mov [cs:live_call+2],ax
 mov ax,1
 sti
 call far [cs:live_call]
 cli
 mov [cs:transaction_status],ax
 call snapshot
 ; Observe the native clear before the parser redraws its next banner.
 mov ax,[ATTRIBUTES_NORMAL_VALUE]
 mov ah,al
 mov al,32
 push ds
 mov dx,0xb800
 mov ds,dx
 xor si,si
 mov cx,CONTENT_CELLS
.blank:
 cmp [si],ax
 jne .not_blank
 add si,2
 loop .blank
 inc word [cs:clear_observed]
.not_blank:
 pop ds
 restore
 iret'''+text[end:]
 text=text.replace(' STATUS_FIXTURE',' mov word [UI_FLOW_SUPPRESSED],1'if a.hidden_status else' ; Default visible status ownership is unchanged.')
 text=text.replace('CONTENT_CELLS',str(rows*80))
 text=text.replace('sample:\n','live_call: dw LIVE_OFF,0\nsample:\n')
 text=text.replace('sample_end:','transaction_status: dw 0xffff\nclear_observed: dw 0\nsample_end:')
 if a.field_edits:
  text=text.replace('sample_end:','field_seeded: dw 0\nfield_flags: times 4096 db 0\nfield_values: times 4096 db 0\nsample_end:')
  text=text.replace('.observe:\n',""".observe:
 cmp word [cs:field_seeded],0
 jne .ordinary_observe
 cmp dx,0x1511
 jne .ordinary_observe
 cmp word [SCREEN_CURSOR_ROW],21
 jne .ordinary_observe
 cmp word [SCREEN_CURSOR_COLUMN],17
 jne .ordinary_observe
 mov ax,[cs:live_call+2]
 sub ax,LIVE_CODE_REL
 add ax,DGROUP_REL
 mov bx,ds
 cmp ax,bx
 jne .ordinary_observe
 cmp word [SCREEN_ATTRIBUTE_ROW_BYTES],132
 jne .ordinary_observe
 push ds
 pop es
 mov di,SCREEN_ATTRIBUTE_CELLS
 mov cx,FIELD_CELLS
 xor ax,ax
 rep stosb
 mov di,ERASE_ATTRIBUTE_VALUES
 mov al,0x17
 mov cx,FIELD_CELLS
 rep stosb
 mov byte [SCREEN_ATTRIBUTE_CELLS+5*132+17],0x80
 mov byte [SCREEN_ATTRIBUTE_CELLS+5*132+80],0x81
 mov word [SCREEN_CURSOR_WRAP],1
 mov word [SCREEN_ATTRIBUTE_CHECKS],0
 mov word [ATTRIBUTES_CURRENT],0x9c
 mov word [ATTRIBUTES_PRESET_VALUE],0x4e
 mov word [ATTRIBUTES_NORMAL_VALUE],0xab27
 mov word [CSI_ERASE_ATTRIBUTE],0x17
 inc word [cs:field_seeded]
.ordinary_observe:
""".replace('FIELD_CELLS',str(cells)))
  if a.scroll_fields:
   text=text.replace('.observe:\n',""".observe:
 cmp word [cs:field_seeded],1
 jne .field_activation
 cmp dx,0x1411
 jne .field_activation
 cmp word [SCREEN_CURSOR_ROW],20
 jne .field_activation
 cmp word [SCREEN_CURSOR_COLUMN],17
 jne .field_activation
 mov ax,[cs:live_call+2]
 sub ax,LIVE_CODE_REL
 add ax,DGROUP_REL
 mov bx,ds
 cmp ax,bx
 jne .field_activation
 mov word [SCREEN_ATTRIBUTE_CHECKS],1
 inc word [cs:field_seeded]
.field_activation:
""",1)
   text=text.replace(' mov byte [SCREEN_ATTRIBUTE_CELLS+5*132+17],0x80',""" mov di,ERASE_ATTRIBUTE_VALUES+5*132+17
 mov al,0x1e
 mov cx,FIELD_CELLS-5*132-17
 rep stosb
 mov di,ERASE_ATTRIBUTE_VALUES+5*132+80
 mov al,0x2a
 mov cx,FIELD_CELLS-5*132-80
 rep stosb
 mov byte [SCREEN_ATTRIBUTE_CELLS+5*132+17],0x80""".replace('FIELD_CELLS',str(cells)),1)


 text=text.replace('cmp dx,0x184f','cmp dx,0x174f')
 text=text.replace('mov ax,[SCREEN_CURSOR_WRAP]','mov ax,[SCREEN_VIEWPORT_ACTIVE]')
 text=text.replace(' inc word [cs:exits]',' call snapshot\n inc word [cs:exits]')
 start=text.index(' mov si,SCREEN_ATTRIBUTE_CELLS\n mov di,flags',text.index('snapshot:'))
 end=text.index(' push ds\n mov ax,0xb800',start)
 text=text[:start]+''' mov bx,[ERASE_SHADOW_OFFSET]
 push ds
 mov ds,[ERASE_SHADOW_SEGMENT]
 mov si,bx
 mov di,flags
 mov cx,8192
 rep movsb
 pop ds
'''+text[end:]
 if a.field_edits:
  anchor=' pop ds\n push ds\n mov ax,0xb800'
  assert text.count(anchor)==1
  text=text.replace(anchor,' pop ds\n mov si,SCREEN_ATTRIBUTE_CELLS\n mov di,field_flags\n mov cx,4096\n rep movsb\n mov si,ERASE_ATTRIBUTE_VALUES\n mov di,field_values\n mov cx,4096\n rep movsb\n push ds\n mov ax,0xb800')
 (out/'observer.asm').write_text(text)
 subprocess.run(['nasm','-fbin','-I',str(out)+'/',str(out/'observer.asm'),'-o',str(out/'RWATCH.COM')],check=True)
 payload=b'\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0c\x1b[6;18H\x1b[1;1HFIRST BYTE SAFE'
 edits=[(0,131,b'R'),(5,0,b'LEFT'),(rows-1,80,b'HIDDEN'),(5,79,b'E'),(5,80,b'F')]
 expected=[0x0720]*cells
 for col,char in enumerate(b'FIRST BYTE SAFE'):expected[col]=0x700|char
 for row,col,data in edits:
  payload+=b'\x1b['+str(row+1).encode()+b';'+str(col+1).encode()+b'H'+data
  for i,char in enumerate(data):expected[row*132+col+i]=0x700|char
 if a.character_edits:
  seed=bytes(65+i%26 for i in range(132));payload+=b'\x1b[6;1H'+seed
  expected[5*132:6*132]=[0x700|char for char in seed]
  for col,insert in [(79,True),(51,False),(80,True),(131,False)]:
   payload+=b'\x1b[6;'+str(col+1).encode()+b'H\x1b[3'+(b'@'if insert else b'P')
   first=5*132+col;last=6*132;n=min(3,last-first)
   if insert:expected[first:last]=[0x0720]*n+expected[first:last-n]
   else:expected[first:last]=expected[first+n:last]+[0x0720]*n
 payload+=b'\x1b['+str(rows).encode()+b';132HZ\x1b[6n\x1b[1;16H\x1b[6n'
 expected[cells-1]=0x75a
 if a.scroll_fields:
  for line,char in [(6,66),(7,67)]:
   payload+=b'\x1b['+str(line+1).encode()+b';1H'+bytes([char])*132
   expected[line*132:(line+1)*132]=[0x700|char]*132
  payload+=b'\x1b[1;16H\x1b[6n'

 field_expected=None
 if a.field_edits:
  from check_width_fields_live import reference
  flags=bytearray(cells);flags[5*132+17]=0x80;flags[5*132+80]=0x81
  values=bytearray([0x17])*cells
  if a.scroll_fields:
   values[5*132+17:]=bytes([0x1e])*(cells-5*132-17)
   values[5*132+80:]=bytes([0x2a])*(cells-5*132-80)
  expected,flags,values,_,_=reference(expected,flags,values,rows,5,17,1,False,3,1,0)
  field_expected=(bytes(flags),bytes(values))
  payload+=b'\x1b[22;18H\x1b[6;18H\x1b[3P\x1b[1;16H\x1b[6n'
  if a.scroll_fields:
   from check_scroll_fields_live import reference as scroll_reference
   expected,flags,values,_=scroll_reference(expected,flags,values,132,rows,5,7,False,0x17,False)
   expected,flags,values,_=scroll_reference(expected,flags,values,132,rows,5,7,True,0x17,False)
   expected,flags,values,_,_=reference(expected,flags,values,rows,6,17,1,False,2,1,1)
   field_expected=(bytes(flags),bytes(values))
   payload+=b'\x1b[21;18H\x1b[6;8r\x1b[8;18H\x1bD\x1b[6;18H\x1bM\x1b[7;18H\x1b[2P\x1b[1;'+str(rows).encode()+b'r\x1b[1;16H\x1b[6n'


 source=Path(harness.__file__).read_text();needle="out=ROOT/'build/connection-dos'/name";assert source.count(needle)==1
 scope=dict(harness.__dict__);scope['LABEL_ROOT']=out
 exec(compile(source.replace(needle,'out=LABEL_ROOT/name'),str(Path(harness.__file__)),'exec'),scope)
 scope['BINARY']=binary
 # Mount a short owned copy to avoid DOSBox-X's host-path length overflow.
 short=out/'parent';short.mkdir();(short/'TERMINAL.EXE').write_bytes(binary.read_bytes());scope['BINARY']=short/'TERMINAL.EXE'
 keys=('p900 enter 'if manifest.get('special_edition')else'')+'p6500 a-x'
 settings=bytearray(harness.fixture(timeout=5))
 if manifest.get('experimental_custom_irq'):struct.pack_into('<HH',settings,0x184,4,3)
 if manifest.get('experimental_mouse'):struct.pack_into('<HH',settings,0x4e4,8,4)
 result=scope['run']('product','success',keys,arguments='@D:\\TEST.PRM /D:CaseTest:23 /A:NETWORK',banner=payload,
  files={'RWATCH.COM':(out/'RWATCH.COM').read_bytes()},observer='RWATCH',cpu='8086',prm=bytes(settings))
 raw=(out/'product/LINEATTR.BIN').read_bytes();assert len(raw)==(20414 if a.field_edits else 12220),len(raw)
 state=struct.unpack_from('<12H',raw);shadow=bytearray(raw[24:8216]);video=raw[8216:12216]
 for row in range(rows):shadow[row*264:row*264+160]=video[row*160:row*160+160]
 wire=(out/'product/serial.bin').read_bytes();checks=dict(result['checks'])
 checks.update(actual_native_transaction_committed=struct.unpack_from('<H',raw,12216)[0]==0 and state[1]==1,
  native_clear_observed_before_redraw=struct.unpack_from('<H',raw,12218)[0]==1,
  root_context_restored=state[4]==state[5]!=0,actual_logical_screen=bytes(shadow[:cells*2])==struct.pack('<'+str(cells)+'H',*expected),
  actual_132_column_CPR=b'\x1b['+str(rows).encode()+b';132R'in wire and b'\x1b[1;16R'in wire,
  cursor_and_geometry=state[6]==1 and state[8:11]==(cells,0,15),
  unmodified_terminal=sha(short/'TERMINAL.EXE')==sha(binary)==manifest['binary_sha256'])
 if a.field_edits:
  checks.update(actual_field_fixture_reached=struct.unpack_from('<H',raw,12220)[0]==(2 if a.scroll_fields else 1),
   actual_field_flags=raw[12222:12222+cells]==field_expected[0],
   actual_field_values=raw[16318:16318+cells]==field_expected[1])
 report=dict(passed=all(checks.values()),checks=checks,binary_sha256=sha(binary),state=list(state),transaction_status=struct.unpack_from('<H',raw,12216)[0],
  sources=manifest['sources'],checker_sha256=sha(Path(__file__)),observer_base_sha256=sha(observer),
  artifacts={str(path.relative_to(ROOT)):sha(path)for path in out.rglob('*')if path.is_file()},original_inputs=[],
  hidden_status_fixture=a.hidden_status,content_rows=rows,character_edits_fixture=a.character_edits,field_edits_fixture=a.field_edits,scroll_fields_fixture=a.scroll_fields,scope=__doc__+' Real startup25-row geometry; optional fixture hides status. IF-enabled far call after the BIOS operation, not a peer width request. Actual UART/parser/output/pan/CPR and hardware restoration follow. No failure injection, private-context IRQ timing, general UI/child or physical acceptance claimed.')
 (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print(('PASS'if report['passed']else'FAIL')+' DOS live transaction '+json.dumps(checks))
 return 0 if report['passed']else 1
if __name__=='__main__':raise SystemExit(main())
