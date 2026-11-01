#!/usr/bin/env python3
"""Observe release of the old PIC bit during a real editor IRQ-only handoff."""
import argparse,hashlib,json,re,struct,subprocess
from pathlib import Path
import test_setup_port_dos as setup
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
INITIAL='''BITS 16
CPU 8086
ORG 100h
in al,21h
and al,0dfh
or al,80h
out 21h,al
mov ax,4c00h
int 21h
'''
OBSERVER='''BITS 16
CPU 8086
ORG 100h
jmp start
old: dw 0,0
sample: dw 0x4951,0,0,0
debug: times 10 dw 0
handler:
 pushf
 push ax
 push ds
 push cs
 pop ds
 inc word [sample+2]
 mov ax,ss
 mov ds,ax
 cmp word [PORT],1
 jne .mask
 cmp word [BASE],3f8h
 jne .mask
 mov ax,[BIND]
 mov [cs:debug],ax
 mov ax,[SETUP]
 mov [cs:debug+2],ax
 mov ax,[KIND]
 mov [cs:debug+4],ax
 mov ax,[STATUS]
 mov [cs:debug+6],ax
 mov ax,[OPTIONS]
 mov [cs:debug+8],ax
 mov ax,[IRQ]
 mov [cs:debug+10],ax
 mov ax,[APPLY]
 mov [cs:debug+12],ax
 mov ax,[RESULT]
 mov [cs:debug+14],ax
 mov ax,[RESULT+2]
 mov [cs:debug+16],ax
 mov ax,[RESULT+4]
 mov [cs:debug+18],ax
.mask:
 push cs
 pop ds
 in al,21h
 test al,80h
 jnz .done
 inc word [sample+4]
 test al,20h
 jz .done
 inc word [sample+6]
.done:
 pop ds
 pop ax
 popf
 jmp far [cs:old]
resident_end:
start:
 mov ax,351ch
 int 21h
 cmp byte [82h],'T'
 jne collect
 mov [old],bx
 mov [old+2],es
 mov dx,handler
 mov ax,251ch
 int 21h
 mov dx,(resident_end-$$+100h+15)/16
 mov ax,3100h
 int 21h
collect:
 cmp bx,handler
 jne failed
 push ds
 push es
 pop ds
 mov dx,[old]
 mov ax,[old+2]
 mov ds,ax
 mov ax,251ch
 int 21h
 pop ds
 mov dx,name
 mov cx,0
 mov ah,3ch
 int 21h
 jc failed
 mov bx,ax
 push ds
 push es
 pop ds
 mov dx,sample
 mov cx,28
 mov ah,40h
 int 21h
 pop ds
 mov ah,3eh
 int 21h
 mov ax,4c00h
 int 21h
failed:
 mov ax,4c01h
 int 21h
name: db 'IRQMASK.BIN',0
'''
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--package',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args();package=a.package.resolve();m=json.loads((package/'manifest.json').read_text());assert m['experimental_directory_adopt']
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 setup.OUT=out;setup.BINARY=package/'PCPLUSSE/TERMINAL.EXE';setup.EDITOR=package/'PCPLUSSE/PRMEDIT.EXE'
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 real_run=subprocess.run
 def run(command,*args,**kwargs):
  if Path(command[0]).name=='dosbox-x':
   config=Path(command[command.index('-conf')+1]);folder=config.parent;assert folder.is_relative_to(out)
   for name,source in [('PICINIT',INITIAL),('IRQWATCH',OBSERVER)]:
    
    if name=='IRQWATCH':
     product=ROOT/'build'/m['products']['TERMINAL.EXE']['folder']
     symbols={n:int(o,16) for seg,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',(product/'terminal.map').read_text(),re.M|re.I)}
     source=''.join('%define '+key+' '+str(symbols[value])+'\n' for key,value in [('PORT','terminal_port_number'),('BASE','uart_port_rbr'),('BIND','terminal_setup_binding_status'),('SETUP','terminal_setup_status'),('KIND','terminal_program_kind'),('STATUS','terminal_program_status'),('OPTIONS','terminal_option_mask'),('IRQ','uart_irq_indices'),('APPLY','terminal_setup_apply_status'),('RESULT','terminal_program_result')])+source
    (folder/(name+'.asm')).write_text(source);real_run(['nasm','-fbin',str(folder/(name+'.asm')),'-o',str(folder/(name+'.COM'))],check=True)
   text=config.read_text();assert 'd:\nWATCH T\n' in text
   text=text.replace('d:\nWATCH T\n','d:\nPICINIT\nIRQWATCH T\nWATCH T\n',1).replace('WATCH\nexit','WATCH\nIRQWATCH\nexit',1)
   # The frozen helper identity is derived from DOS's executable path.
   # Use the explicit absolute invocation used by the application harness.
   text=text.replace('TERMINAL @TEST.PRM','D:\\TERMINAL.EXE @TEST.PRM',1)
   config.write_text(text)
  return real_run(command,*args,**kwargs)
 setup.subprocess.run=run
 keys='p900 enter p4500 a-s p2500 home del 1'+' tab'*8+' home del 7 f10 p900 escape p900 y p8000 r e a d y p1800 a-x'
 try:base=setup.run('same-COM1-IRQ5-to7',1,1,source_irq=5,target_irq=7,accept=True,keyboard=keys,peer_delay=18,timeout=45)
 finally:setup.subprocess.run=real_run
 folder=out/'same-COM1-IRQ5-to7';magic,ticks,new_irq_samples,wrong_old_mask=struct.unpack('<4H',(folder/'IRQMASK.BIN').read_bytes()[:8])
 assert base['passed'] and magic==0x4951 and ticks>0 and new_irq_samples>0 and wrong_old_mask==0,(magic,ticks,new_irq_samples,wrong_old_mask)
 state=struct.unpack('<10H',(folder/'IRQMASK.BIN').read_bytes()[8:])
 assert state==(0,0,1,4,16,7,0,0,0,0),state
 report=dict(passed=True,binary_sha256=m['files']['TERMINAL.EXE'],package_manifest_sha256=sha(package/'manifest.json'),checks=base['checks'],timer_ticks=ticks,new_IRQ7_active_samples=new_irq_samples,old_IRQ5_mask_violations=wrong_old_mask,original_inputs=[],sources={n:sha(ROOT/n) for n in ['standalone/test_adoption_irq_restore_dos.py','standalone/test_setup_port_dos.py','standalone/port_watch.asm','standalone/test_terminal.py','standalone/check_setup_model.py','standalone/check_directory_live.py']},artifacts={str(q.relative_to(out)):sha(q) for q in out.rglob('*') if q.is_file()},scope=__doc__+' Actual DOS8086 PRMEDIT confirmation, shared handoff/native snapshot/IRQ/transport code and late loopback peer traffic. Fixture starts IRQ5 unmasked; passive observer requires it released while IRQ7 is active. This covers the shared branch through SETUP kind1, not full preview-A IRQ-only adoption or physical hardware.')
 report['final_setup_observation']=dict(zip(['binding','setup','kind','program_status','option_mask','irq','apply','process_status','DOS_error','child_exit'],state))
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS native IRQ5 release during IRQ7 ownership;',new_irq_samples,'active samples')
if __name__=='__main__':main()
