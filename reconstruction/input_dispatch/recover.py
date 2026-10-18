#!/usr/bin/env python3
"""Explicit analyst step: regenerate exact input/control source from the verified original."""
from pathlib import Path
import hashlib,json,re,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'reconstruction/input_dispatch'
ORIGINAL=ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE'
EXPECTED='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
UNITS=[('dispatch',0x0610,0x0730),('logging',0x09b6,0x0a3a),('tab',0x0a8c,0x0b4e),('ignore',0x0e60,0x0e61),('backspace',0x0eea,0x0f3d),('linefeed',0x0f3e,0x0f62),('carriage_return',0x1002,0x1040),('home',0x1f56,0x1f6f),('history',0x5832,0x58ce),('history_pair',0x58ce,0x58ea),('divide',0x830c,0x8318)]
FUNCTIONS={0x0610:'terminal_receive_character',0x09b6:'terminal_log_character',0x0a8c:'terminal_tab',0x0e60:'terminal_ignore_control',0x0eea:'terminal_backspace',0x0f3e:'terminal_linefeed',0x1002:'terminal_carriage_return',0x1f56:'terminal_control_home',0x5832:'terminal_history_character',0x58ce:'terminal_history_pair',0x830c:'terminal_signed_divide'}
SERVICES={0x0730:'render_character',0xabde:'ansi_unread_byte',0xb973:'ansi_escape_entry',0x1bbe:'screen_set_cursor',0x1ea0:'screen_cursor_right',0x12c8:'screen_wrap_forward',0x2adc:'screen_adjust_attribute_boundary',0x1e30:'screen_cursor_left',0x6c4a:'text_write_bios',0x1d88:'screen_linefeed',0x1fc4:'scroll_up',0x36fc:'terminal_sink_36fc',0x8436:'terminal_sink_8436',0x427f:'terminal_sink_427f',0xbb23:'terminal_sink_bb23',0x2fb8:'screen_viewport_refresh'}
STATE={0x1d18:'csi_terminal_id',0x445e:'terminal_escape_dispatch_table',0x44a0:'terminal_control_dispatch_table',0x8ff6:'attributes_monochrome',0x3340:'scroll_suppress_next_linefeed',0x8fe8:'terminal_input_mode_8fe8',0x1d30:'terminal_c1_enabled',0x3988:'terminal_sink_3988_enabled',0x1d24:'terminal_cr_adds_lf',0x398a:'terminal_sink_398a_enabled',0x398c:'terminal_sink_398c_disabled',0xd114:'terminal_sink_handle',0x418a:'terminal_sink_error_state',0x3342:'csi_wrap_pending',0x900c:'screen_cursor_wrap',0x3734:'screen_attribute_checks',0x325c:'erase_cell_count',0x3346:'screen_attribute_offset',0x39c4:'screen_attributes_base',0x325a:'screen_attribute_row_bytes',0x399e:'screen_cursor_column',0x399c:'screen_cursor_row',0x3258:'screen_last_column',0x903e:'terminal_tab_wrap',0x8ff8:'terminal_tab_mode_8ff8',0x9058:'terminal_backspace_mode_9058',0x1d26:'terminal_backspace_erases',0xcf86:'screen_line_flags',0x1f70:'attributes_current',0x9020:'terminal_newline_mode_9020',0xce3a:'screen_last_row',0x1d22:'scroll_enabled',0x4ecc:'terminal_history_pending',0x4ebe:'terminal_history_pointer',0x4ec6:'terminal_history_end',0x4eba:'terminal_history_start',0x4ec8:'terminal_history_wrapped',0xce10:'terminal_tab_stops'}
TABLES=[(0x648,0x684,'terminal_low_control_table'),(0x6dc,0x70c,'terminal_c1_table')]

def main():
 image=ORIGINAL.read_bytes();assert hashlib.sha256(image).hexdigest()==EXPECTED
 manifest={'source_sha256':EXPECTED,'units':[],'state':{f'{k:04x}':v for k,v in STATE.items()},'services':{f'{k:04x}':v for k,v in SERVICES.items()},'maintained_changes':['OMF entry masks its word character argument to eight bits before control-table indexing; flat recovery remains exact.'],'rea_evidence_id':'ev_d53d1c66282bc50e670ae82baf3d89c2e48f0e66887e64c4c498cb484047acbb','limitations':['State/service names are analyst annotations. DS372c meaning and serviceb9f7 semantics remain unresolved.','Unsupported terminal-control families and enabled logging sinks remain explicit external dependencies.']}
 with tempfile.TemporaryDirectory() as temp:
  work=Path(temp)
  def assemble(text,at):
   (work/'one.asm').write_text(f'BITS 16\nCPU 8086\nORG {at}\n%include "encodings.inc"\n'+text+'\n')
   p=subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/',str(work/'one.asm'),'-o',str(work/'one.bin')],capture_output=True)
   return (work/'one.bin').read_bytes() if p.returncode==0 else None
  for name,start,end in UNITS:
   blob=image[0x1200+start:0x1200+end];(work/'part').write_bytes(blob)
   decoded=''
   chunks=[(start,end)] if name!='dispatch' else [(start,0x648),(0x684,0x6dc),(0x70c,end)]
   for lo,hi in chunks:
    (work/'part').write_bytes(image[0x1200+lo:0x1200+hi])
    decoded+=subprocess.check_output(['ndisasm','-b16',f'-o{lo}',str(work/'part')],text=True)
   rows=[]
   for line in decoded.splitlines():
    m=re.fullmatch(r'([0-9A-F]+)\s+([0-9A-F]+)\s+(.*)',line);assert m,line
    at,raw,text=int(m[1],16),bytes.fromhex(m[2]),m[3];assert not text.startswith('db ')
    instruction=text
    if raw[0]==0xeb:instruction=instruction.replace('jmp ','jmp short ',1)
    elif raw[0]==0xe9:instruction=instruction.replace('jmp ','jmp near ',1)
    elif 0x70<=raw[0]<=0x7f:instruction=instruction.replace(' ',' short ',1)
    if assemble(instruction,at)!=raw:
     candidates=[]
     if len(raw)==2 and raw[1]>=0xc0 and raw[0] in (2,3,10,11,18,19,26,27,34,35,42,43,50,51,58,59,138,139):
      op,operands=text.split(' ',1);candidates.append(op+'_load '+operands)
     for width in ('word','byte'):candidates.append(re.sub(r',(-?0x[0-9a-f]+)$',rf',strict {width} \1',instruction))
     instruction=next((c for c in candidates if assemble(c,at)==raw),None)
     assert instruction is not None,(hex(at),text,raw.hex())

    for state_at in STATE:
     signed=state_at-65536
     if signed<0:instruction=instruction.replace(f'-0x{-signed:x}',f'+0x{state_at:x}')
    rows.append((at,instruction))
   header=['; Recovered PCPlus 2.01 input/control instructions; see docs/INPUT_DISPATCH.md.','BITS 16','CPU 8086','%ifdef INPUT_DISPATCH_OMF','SEGMENT _TEXT public class=CODE use16','global '+','.join(v for k,v in FUNCTIONS.items() if start<=k<end)]
   calls=set()
   for _,text in rows:
    m=re.fullmatch(r'call (0x[0-9a-f]+)',text)
    if m:calls.add(int(m[1],16))
   external={k:v for k,v in (FUNCTIONS|SERVICES).items() if k in calls and not start<=k<end}
   for v in external.values():header.append('extern '+v)
   state_used={k:v for k,v in STATE.items() if any(re.search(r'(?<![\da-f])0x'+f'{k:x}'+r'(?![\da-f])',t) for _,t in rows)}
   for v in state_used.values():header.append('extern '+v)
   header+=['%define short','%else',f'ORG 0x{start:x}']
   for k,v in external.items():header.append(f'%define {v} 0x{k:x}')
   for k,v in state_used.items():header.append(f'%define {v} 0x{k:x}')
   header+=['%endif','%include "encodings.inc"',FUNCTIONS[start]+':']
   for at,text in rows:
    if name=='dispatch':
     for lo,hi,label in TABLES:
      if at==hi:
       values=__import__('struct').unpack('<'+'H'*((hi-lo)//2),image[0x1200+lo:0x1200+hi])
       header.append(label+':');header.extend(f' dw L_{value:04x}' for value in values)
      text=text.replace(f'0x{lo:x}',label)
    for k,v in state_used.items():text=re.sub(r'(?<![\da-f])0x'+f'{k:x}'+r'(?![\da-f])',v,text)
    branch=re.fullmatch(r'(j\w+|loop|call)\s+(?:(short|near)\s+)?(0x[0-9a-f]+)',text)
    if branch:
     target=int(branch[3],16)
     symbol=f'L_{target:04x}' if start<=target<end else (FUNCTIONS|SERVICES)[target]
     text=branch[1]+' '+(branch[2]+' ' if branch[2] else '')+symbol

    if at in FUNCTIONS and at != start:header.append(FUNCTIONS[at]+':')
    header.append(f'L_{at:04x}: '+text)
    if at==0x0614:header.extend(['%ifdef INPUT_DISPATCH_OMF',' and si,0xff ; Maintained byte ABI: prevent negative word indices before control tables.','%endif'])
   path=SOURCE/(name+'.asm');path.write_text('\n'.join(header)+'\n')
   subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/',str(path),'-o',str(work/'whole.bin')],check=True)
   assert (work/'whole.bin').read_bytes()==blob,name
   manifest['units'].append({'file':str(path.relative_to(ROOT)),'start':start,'end':end,'bytes':len(blob),'instructions':len(rows),'sha256':hashlib.sha256(blob).hexdigest(),'matched_original':True})
 (SOURCE/'provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('Recovered',sum(u['bytes'] for u in manifest['units']),'bytes')
if __name__=='__main__':main()

# Startup DS pointers are re-authored as linker symbols, never copied as a blob.
def recover_tables():
 import struct
 image=ORIGINAL.read_bytes();assert hashlib.sha256(image).hexdigest()==EXPECTED
 data=image[153936:153936+60080]
 assert hashlib.sha256(data).hexdigest()=='41b5e49c3f2bc40b7007d311af4282d9724b4cf0b11a696ca2bd6062ef4132c7'
 rows=[(0x445e,33,'terminal_escape_dispatch_table'),(0x44a0,32,'terminal_control_dispatch_table')]
 known=FUNCTIONS|{0xb973:'ansi_escape_entry',0x12c8:'screen_wrap_forward'}
 values={name:struct.unpack_from('<'+'H'*count,data,start) for start,count,name in rows}
 pointers={value:known.get(value,('terminal_escape_' if start==0x445e else 'terminal_control_')+f'{value:04x}') for start,count,name in rows for value in values[name]}
 lines=['; Symbolic startup function pointers; verified original DS tables.','BITS 16','CPU 8086','%ifdef INPUT_DISPATCH_OMF','SEGMENT _DATA public align=16 class=DATA use16']
 lines+=['extern '+name for name in sorted(set(pointers.values()))]
 lines+=['global terminal_escape_dispatch_table,terminal_control_dispatch_table','%else','ORG 0x445e']
 lines += [f'%define {name} 0x{at:04x}' for at,name in pointers.items()]
 lines += ['%endif']
 for start,count,name in rows:
  lines.append(name+':');lines.extend(' dw '+pointers[value] for value in values[name])
 path=SOURCE/'tables.asm';path.write_text('\n'.join(lines)+'\n')
 with tempfile.TemporaryDirectory() as tmp:
  output=Path(tmp)/'tables.bin';subprocess.run(['nasm','-f','bin',str(path),'-o',str(output)],check=True)
  blob=output.read_bytes();assert blob==data[0x445e:0x44e0]
 proof={'source_sha256':EXPECTED,'startup_data_sha256':hashlib.sha256(data).hexdigest(),'table_sha256':hashlib.sha256(blob).hexdigest(),'bytes':len(blob),'tables':{name:{'start':start,'entries':[{'original':value,'symbol':pointers[value]} for value in values[name]]} for start,count,name in rows},'limitations':['Pointers re-authored as symbols; only ANSI escape profiles2..11 and selected ordinary controls implemented. Unsupported targets remain explicit link dependencies.']}
 (SOURCE/'tables-provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
 print('Recovered',len(blob),'bytes of symbolic startup pointer tables')
if __name__=='__main__':recover_tables()
