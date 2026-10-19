#!/usr/bin/env python3
"""Actual DOS parent/child BREAK, configured raw word and passive LCR/VRAM observer."""
import inspect,json,re,struct,subprocess,sys
from pathlib import Path
import test_aspect_status_dos as status
renderer=status.renderer;ROOT=status.ROOT;OUT=ROOT/'build/aspect-break-dos'

def definitions():
 base=status.definitions()[0];cases=[]
 for name,inherited,override,cancel in [('configured350',350,None,False),('configured1000',1000,None,False),('raw65535',65535,350,False),('zero',0,None,False),('cancel30000',350,30000,True)]:
  signed=inherited if inherited<32768 else inherited-65536
  setting='' if override is None else f'set break {override}\n'
  source=('integer configured\nproc main\nwaitfor "LOGIN:" 5\nfetch break configured\n'
   f'if configured == {signed}\ntransmit "POLICYOK^M"\nelse\ntransmit "BADPOLICY^M"\nendif\n'+setting+
   'break\npause 1\ntransmit $D_PWORD\ntransmit "^M"\nendproc\n')
  cases.append(dict(base,name=name,source=source,inherited=inherited,effective=override if override is not None else inherited,
   cancel=cancel,success=not cancel))
 return cases

def main():
 source=inspect.getsource(renderer.main)
 substitutions={"expectations=[{k:(v.hex() if isinstance(v,bytes) else v) for k,v in c.items()} for c in cases]":"expectations=status.encode(cases)",
  "settings=bytearray(prm());extra=' /A:NETWORK'":"settings=bytearray(prm());struct.pack_into('<H',settings,0x1a4,case['inherited']);extra=' /A:NETWORK'"}
 for old,new in substitutions.items():assert source.count(old)==1;source=source.replace(old,new)
 scope=dict(renderer.__dict__);scope.update(__file__=__file__,OUT=OUT,definitions=definitions,status=status)
 def adapter():
  previous=renderer.OUT;renderer.OUT=scope['OUT']
  try:return renderer.adapter()
  finally:renderer.OUT=previous
 def observer(offsets):
  previous=renderer.OUT;renderer.OUT=scope['OUT']
  try:
   _,modes,pairs,snapshots=renderer.observer(offsets)
   listing=(ROOT/'build/aspect-runner/ASPECT.map').read_text()
   group=int(re.search(r'DGROUP\s+([0-9a-fA-F]{4}):0000',listing)[1],16)
   def word(name):
    match=re.search(r'^\s*([0-9a-fA-F]{4}):([0-9a-fA-F]{4,8})[+*]?\s+'+re.escape(name)+r'$',listing,re.M);assert match,name
    return int(match[1],16)*16+int(match[2],16)-group*16
   psp,opcode,units=[word(n) for n in ['__psp','_runtime_last_opcode','_runtime_serial_break_units']]
   path=renderer.OUT/'observer.asm';asm=path.read_text()
   data='break_ticks: dw 0\nbreak_clear_ticks: dw 0\nbreak_child_units: dw 0\nbreak_pause_ticks: dw 0\nbreak_parent_units: dw 0\nbreak_parent_active: dw 0\nbreak_row: times 162 db 0\nsample_end:'
   assert asm.count('sample_end:')==1;asm=asm.replace('sample_end:',data)
   hook=f'''timer:
 save
 cld
 cmp word [cs:exec_seen],1
 jne .break_done
 mov dx,0x3fb
 in al,dx
 test al,0x40
 jz .break_clear
 inc word [cs:break_ticks]
 mov ax,0xb800
 mov es,ax
 mov si,3840
 mov di,break_row
 mov cx,162
.break_copy:
 mov al,[es:si]
 mov [cs:di],al
 inc si
 inc di
 loop .break_copy
 jmp .break_child
.break_clear:
 cmp word [cs:break_ticks],0
 je .break_child
 inc word [cs:break_clear_ticks]
.break_child:
 cmp word [cs:exec_done],0
 jne .break_done
 mov ax,ss
 mov es,ax
 cmp ax,{group+16}
 jb .break_done
 sub ax,{group+16}
 cmp ax,[es:{psp}]
 jne .break_done
 push es
 mov es,ax
 cmp word [es:0],0x20cd
 pop es
 jne .break_done
 mov ax,[es:{units}]
 mov [cs:break_child_units],ax
 cmp word [es:{opcode}],0x88
 jne .break_done
 inc word [cs:break_pause_ticks]
 mov ax,[cs:parent_ds]
 mov es,ax
 mov ax,[es:{offsets['terminal_break_delay_units']}]
 mov [cs:break_parent_units],ax
 mov ax,[es:{offsets['script_break_ui_active']}]
 mov [cs:break_parent_active],ax
.break_done:
'''
   old='timer:\n save\n cld\n';assert asm.count(old)==1;asm=asm.replace(old,hook);path.write_text(asm)
   subprocess.run(['nasm','-fbin',str(path),'-o',str(renderer.OUT/'RENDER.COM')],check=True)
   return (renderer.OUT/'RENDER.COM').read_bytes(),modes,pairs,snapshots
  finally:renderer.OUT=previous
 scope.update(adapter=adapter,observer=observer)
 exec(compile(source,__file__,'exec'),scope);scope['main']()
 folder=scope['OUT'];report=json.loads((folder/'checks.json').read_text());cases={c['name']:c for c in definitions()}
 for result in report['cases']:
  case=cases[result['case']];raw=(folder/result['case']/'RENDER.BIN').read_bytes()
  ticks,clear,units,pauses,parent,active=struct.unpack_from('<6H',raw,len(raw)-174);row=raw[-162:]
  wire=(folder/result['case']/'serial.bin').read_bytes();checks=result['checks']
  checks['raw_configured_word_received']=wire.count(b'POLICYOK\r')==1 and b'BADPOLICY' not in wire
  if case['effective']:
   checks['physical_virtual_LCR_assertion_observed']=ticks>0
   checks['pulse_released_after_assertion']=clear>0
   checks['native_notice_exact']=row[2:28:2]==b'*** BREAK ***' and row[3:28:2]==bytes([0x1e])*13
  if not case['cancel']:
   checks['child_PAUSE_observed']=pauses>0
   checks['script_duration_effective']=units==case['effective']
   checks['parent_raw_duration_unmodified']=parent==case['inherited']
   checks['notice_owner_closed_before_PAUSE']=active==0
  result.update(passed=all(checks.values()),break_ticks=ticks,clear_ticks=clear,pause_ticks=pauses,
   observed_child_units=units,parent_units=parent,notice_row_hex=row.hex())
  (folder/result['case']/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 report.update(passed=all(c['passed'] for c in report['cases']),
  checker_sha256=renderer.sha(Path(__file__)),reused_renderer_checker_sha256=renderer.sha(Path(renderer.__file__)),
  scope='Actual DOS source-built parent/child native BREAK/SET/FETCH with raw configured duration via capability3. Passive INT1C reads non-destructive LCR, notice VRAM and PSP-qualified duration/PAUSE/parent state. Native query/keyboard/history and IRQ/JFT restoration checks retained. Virtual UART timing observations are not physical modem timing guarantees; zero pulse may be too short for timer observation.')
 (folder/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
 print('DOS BREAK',len(report['cases']),'cases',report['passed']);assert report['passed']
if __name__=='__main__':main()
