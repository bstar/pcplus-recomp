#!/usr/bin/env python3
"""Actual optional Alt-P in DOS, independent serial peer and passive observer."""
import argparse,hashlib,json,struct,subprocess
from pathlib import Path
import test_connection_dos as harness
from directory_fixtures import prm
ROOT=harness.ROOT
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--case',choices=('noop','escape','save','reference','browser','serviced','unsupported','readonly','conflict','portbusy'),default='noop')
 p.add_argument('--open-delay-ms',type=int,default=1300,help='Explicit diagnostic opening delay; ordinary gate uses1300ms')
 a=p.parse_args();producer=sha(Path(__file__));binary=a.terminal.resolve();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 manifest=json.loads(binary.with_name('manifest.json').read_text())
 assert manifest['binary_sha256']==sha(binary) and manifest['experimental_line_port']
 settings=bytearray(prm(port=3,baud=5))
 for at,val in ((0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0),(0x3e4,7),(0x3e6,11),(0x3e8,113)):
  struct.pack_into('<H',settings,at,val)
 watch=(ROOT/'standalone/path_dialog_watch.asm').read_text()
 watch=watch.replace('last_sum: dw 0','after_lcr: db 0\nafter_seen: db 0\npopup_cursor: dw 0\nerror_seen: db 0\nlast_sum: dw 0')
 watch=watch.replace(' inc word [sample+4]', ''' inc word [sample+4]
 mov ax,0xb800
 mov es,ax
 cmp byte [es:320],'A'
 jne .error_check
 cmp byte [es:322],'F'
 jne .error_check
 cmp byte [after_seen],0
 jne .error_check
 mov dx,0x3eb
 in al,dx
 mov [after_lcr],al
 mov byte [after_seen],1
.error_check:
 cmp byte [es:3202],'L'
 jne .popup_check
 cmp byte [es:3204],'i'
 jne .popup_check
 mov byte [error_seen],1
.popup_check:
''',1)
 start=watch.index(' cmp word [es:806]');end=watch.index('%if WATCH_KIND',start)
 watch=watch[:start]+''' cmp byte [es:356],0xc9
 jne .done
 cmp byte [es:542],'C'
 jne .done
 cmp byte [es:1000],'B'
 jne .done
'''+watch[end:]
 if a.case=='serviced':
  watch=watch.replace(' xor dx,dx\n xor si,si'," cmp byte [es:160],'U'\n jne .done\n cmp byte [es:162],'A'\n jne .done\n xor dx,dx\n xor si,si",1)
 watch=watch.replace(' mov di,frame', ''' push es
 mov ax,0x40
 mov es,ax
 mov ax,[es:50h]
 mov [popup_cursor],ax
 pop es
 mov di,frame''',1)
 watch=watch.replace('4071','4076')
 watch=watch.replace(' popf\n mov dx,[es:old_vector]', ''' popf
 mov al,[es:after_lcr]
 mov [buffer+4071],al
 mov al,[es:after_seen]
 mov [buffer+4072],al
 mov ax,[es:popup_cursor]
 mov [buffer+4073],ax
 mov al,[es:error_seen]
 mov [buffer+4075],al
 mov dx,[es:old_vector]''',1)
 (out/'watch.asm').write_text(watch)
 subprocess.run(['nasm','-fbin','-DWATCH_KIND=0',str(out/'watch.asm'),'-o',str(out/'LPOBS.COM')],check=True)
 opening='a-z p500 a-p'if a.case=='reference'else '` p500 right right right p300 p'if a.case=='browser'else 'a-p'
 edit='5 p400 e p400'if a.case in ('escape','save','readonly','conflict')else'f5 p400'if a.case=='unsupported'else'f2 p400'if a.case=='portbusy'else''
 assert 1300<=a.open_delay_ms<=10000
 delay='p'+str(max(5500,a.open_delay_ms)if a.case=='serviced'else a.open_delay_ms)
 leave='a-s'if a.case in ('save','readonly','conflict')else'escape'
 if a.case in ('readonly','conflict','portbusy'):leave+=' p1500 escape'
 keys='p900 enter p3500 '+opening+' '+delay+' '+edit+' '+leave+' p1300 r e a d y enter p1000 a-x'
 expected=bytearray(settings)
 if a.case=='save':struct.pack_into('<2H',expected,2,4,2)
 files={'LPOBS.COM':(out/'LPOBS.COM').read_bytes()};auxiliary=()
 if a.case=='readonly':
  subprocess.run(['nasm','-fbin',str(ROOT/'standalone/line_port_readonly.asm'),'-o',str(out/'LPATTR.COM')],check=True)
  files['LPATTR.COM']=(out/'LPATTR.COM').read_bytes();auxiliary=('LPATTR',)
 harness.BINARY=binary;case=out.name+'-'+a.case;drive=ROOT/'build/connection-dos'/case
 assert not drive.exists()
 result=harness.run(case,'success',keys,prm=bytes(settings),prm_expected=bytes(expected),arguments='@TEST.PRM /D:CaseTest:23',com=3,irq=5,cpu='8086',working_drive='d',observer='LPOBS',files=files,auxiliary=auxiliary,recovery_conflict=a.case=='conflict',timeout=35,
  online_triggers=((b'ready\r',b'\x1b[3;1HAFTER-LINE-PORT\x1b[6n'),),
  online_updates=((5.,b'\x1b[2;1HUART-WHILE-OPEN\x1b[6n'),)if a.case=='serviced'else())
 raw=(drive/'PATHVIEW.BIN').read_bytes();magic,flags,ticks=struct.unpack_from('<3H',raw)
 frame=raw[6:4006];wire=(drive/'serial.bin').read_bytes();screen=(drive/'SCREEN.BIN').read_bytes()
 chars=lambda r,c,n:frame[(r*80+c)*2:(r*80+c+n)*2:2]
 checks=dict(result['checks'])
 checks.update(captured_popup=magic==0x5044 and flags==3 and ticks>2,
  native_heading=chars(3,31,34)==b'CURRENT SETTINGS: 19200,N,8,1,COM3',
  native_prompt=chars(18,20,46)==b'Esc) Exit   Alt-S) Save and Exit  YOUR CHOICE:',
  popup_over_live_background=chars(0,0,15)==b'FIRST BYTE SAFE',
  ready_once=wire.count(b'ready\r')==1,post_popup_query=b'\x1b[3;16R'in wire,
  post_popup_render=screen[320:350:2]==b'AFTER-LINE-PORT',
  no_unowned_stage=not(drive/'PCPSTG.$$$').exists(),
  recovery_backup_expected=(drive/'PCPBAK.$$$').read_bytes()==b'SYNTHETIC RECOVERY CONFLICT'if a.case=='conflict'else not(drive/'PCPBAK.$$$').exists(),
  native_popup_cursor=struct.unpack_from('<H',raw,4073)[0]==0x1243,
  hardware_framing_applied=raw[4072]==1 and raw[4071]==(0x1b if a.case in ('escape','save')else 3))
 cells=[r*80+c for r in range(2,20)for c in range(18,77)]+list(range(1920,2000))
 checks['native_popup_all_cells']=hashlib.sha256(b''.join(frame[at*2:at*2+2]for at in cells)).hexdigest()=='1ae083b5f1b6cc673f6910164175ad7f1b76d26432b7246ab5ce79bc7d9eed94'
 if a.case=='serviced':checks.update(incoming_visible_while_open=chars(1,0,15)==b'UART-WHILE-OPEN',query_serviced_while_open=b'\x1b[2;16R'in wire)
 if a.case in ('readonly','conflict','portbusy'):checks['failure_notice_visible']=raw[4075]==1
 assert sha(Path(__file__))==producer
 report=dict(producer_sha256=producer,watcher_sha256=sha(out/'watch.asm'),sources={n:sha(ROOT/n)for n in ('standalone/test_line_port_terminal_dos.py','standalone/test_connection_dos.py','standalone/path_dialog_watch.asm','standalone/line_port_readonly.asm')},passed=all(checks.values()),case=a.case,checks=checks,binary_sha256=sha(binary),base_receipt=str(drive/'result.json'),frame_sha256=hashlib.sha256(frame).hexdigest(),post_lcr=raw[4071])
 report['open_delay_ms']=a.open_delay_ms
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
 print(a.case,{k:v for k,v in checks.items()if not v},flush=True);assert report['passed'],report


if __name__=='__main__':main()
