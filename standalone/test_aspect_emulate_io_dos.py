#!/usr/bin/env python3
"""Actual EMULATE strict KBD failures and receive backlog across repeated imports."""
import argparse,json,struct,shutil,subprocess,sys,time
from pathlib import Path
import test_connection_dos as harness
import aspect_exit_watch
from build_path_session import ROOT,sha
from directory_fixtures import prm
from test_directory_key_bindings_dos import actions
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source

OBSERVE=r'''
; Passive entry sample only. All state belongs to this test TSR; no DOS calls,
; UART accesses or application writes. Child RX bytes are never dequeued here.
observe_rx:
 pushf
 push ax
 push bx
 push cx
 push dx
 push es
 mov cx,ax
 cmp ah,0x3d
 je .file
 cmp ah,0x3e
 je .file
 cmp ah,0x3f
 je .file
 cmp ah,0x42
 jne .done
.file:
 mov ax,ds
 cmp ax,[cs:parent_ds]
 jne .done
 or ax,ax
 jz .done
 sub ax,PARENT_DATA_SEG
 add ax,PARENT_RENDER_SEG
 mov es,ax
 cmp word [es:PARENT_BRIDGE_BUSY],1
 jne .done
 cmp word [es:PARENT_ATTACHED],1
 jne .done
 mov ax,[es:PARENT_CHILD_DS]
 or ax,ax
 jz .done
 mov es,ax
 inc word [cs:rxdata+4]
 cmp ch,0x3f
 jne .queue
 inc word [cs:rxdata+6]
.queue:
 mov ax,[es:CHILD_RX_COUNT]
 or ax,ax
 jz .maximum
 inc word [cs:rxdata+8]
.maximum:
 cmp ax,[cs:rxdata+10]
 jbe .drops
 mov [cs:rxdata+10],ax
.drops:
 mov ax,[es:CHILD_RX_DROPPED]
 cmp ax,[cs:rxdata+12]
 jbe .status
 mov [cs:rxdata+12],ax
.status:
 mov ax,[es:CHILD_SERIAL_STATUS]
 cmp ax,[cs:rxdata+14]
 jbe .done
 mov [cs:rxdata+14],ax
.done:
 pop es
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 ret
rxdata: dw 0xe620,1,0,0,0,0,0,0
'''
DUMP=r'''
 mov dx,rx_filename
 xor cx,cx
 mov ah,0x3c
 int 0x21
 jc failed
 mov bx,ax
 push ds
 push es
 pop ds
 mov dx,rxdata
 mov cx,16
 mov ah,0x40
 int 0x21
 pop ds
 jc failed
 cmp ax,16
 jne failed
 mov ah,0x3e
 int 0x21
 jc failed
'''

def observer(parent,child,out):
 p=aspect_exit_watch.symbols(parent.with_name('terminal.map'));c=aspect_exit_watch.symbols(child.with_name('ASPECT.map'))
 fields=dict(CHILD_ERROR='_runtime_error',CHILD_OPCODE='_runtime_last_opcode',CHILD_RAW='_runtime_external_raw_status',CHILD_CLEANUP='_runtime_external_cleanup_error',CHILD_CALLS='_runtime_external_calls',CHILD_SCOPE='_runtime_external_scope_storage',CHILD_DISPLAY='_native_display_owned',CHILD_BUSY='_native_program_busy',CHILD_PROCESS='_native_process_busy',CHILD_HEADER='_runtime_header',CHILD_NEAR='_native_near_calls',CHILD_FAR='_native_far_calls',CHILD_BACKUP='_native_backup_extent',CHILD_ERRNO='_native_crt_error',CHILD_DOSERR='_native_dos_error',CHILD_RX_COUNT='uart_rx_count',CHILD_RX_DROPPED='uart_rx_dropped',CHILD_SERIAL_STATUS='_aspect_serial_status')
 assert all(c[n][0]==c['_runtime_error'][0] for n in fields.values())
 values={n:c[s][1] for n,s in fields.items()}
 assert p['resident_bridge_busy'][0]==p['render_child_ds'][0]==p['render_attached'][0]
 values.update(PARENT_DATA_SEG=p['terminal_program_kind'][0],PARENT_RENDER_SEG=p['render_child_ds'][0],PARENT_CHILD_DS=p['render_child_ds'][1],PARENT_BRIDGE_BUSY=p['resident_bridge_busy'][1],PARENT_ATTACHED=p['render_attached'][1])
 source=(ROOT/'standalone/aspect_exit_watch.asm').read_text()
 assert source.count(' push es\n cmp ah,0x48')==1
 source=source.replace(' push es\n cmp ah,0x48',' push es\n call observe_rx\n cmp ah,0x48')
 source=source.replace('resident_end:',OBSERVE+'\nresident_end:',1)
 needle=' mov ax,0x4c00\n int 0x21\nfailed:';assert source.count(needle)==1
 source=source.replace(needle,DUMP+needle)
 source+='\nrx_filename: db "D:\\RXSTAT.BIN",0\n'
 source='\n'.join('%define '+k+' '+str(v) for k,v in values.items())+'\n'+source
 (out/'EMUWATCH.ASM').write_text(source);subprocess.run(['nasm','-fbin',str(out/'EMUWATCH.ASM'),'-o',str(out/'EMUWATCH.COM')],check=True)
 return {n:sha(ROOT/n) for n in ('standalone/aspect_exit_watch.asm','standalone/aspect_exit_watch.py')}

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('terminal','runner','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--case',choices=['missing','short','receive'],required=True);p.add_argument('--cpu',choices=['8086','386'],default='386');p.add_argument('--rounds',type=int,default=128)
 a=p.parse_args();parent=a.terminal.resolve();child=a.runner.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
 assert 1<=a.rounds<=512
 sources={};products={}
 for path,flag in ((parent,'experimental_aspect_emulate_policy'),(child,'experimental_emulate_VM')):
  m=json.loads(path.with_name('manifest.json').read_text());assert sha(path)==m['binary_sha256'] and m[flag] and not m.get('diagnostic_build')
  for n,h in m['sources'].items():assert sha(ROOT/n)==h,n;sources[n]=h
  products[path.name]=sha(path)
 for n in ('standalone/test_aspect_emulate_io_dos.py','standalone/test_connection_dos.py','standalone/test_directory_key_bindings_dos.py','standalone/test_terminal.py','standalone/directory_fixtures.py','standalone/directory_test_support.py','standalone/modem_fixtures.py','src/aspect/compiler.py'):sources[n]=sha(ROOT/n)
 sources.update(observer(parent,child,out));stage=out/'program';stage.mkdir()
 for path in (parent,child):shutil.copyfile(path,stage/path.name)
 kbd=bytearray(7*948)
 for profile_index in range(7):
  for slot in (5,78):kbd[profile_index*948+slot*12]=13
 kbd=bytes(kbd)
 files={'TEST.KBD':kbd,'EMUWATCH.COM':(out/'EMUWATCH.COM').read_bytes()}
 profile='emulate vt220\ntransmit "PROFILE4^M"\nwaitfor "ACK4" 2\nemulate ansi\ntransmit "PROFILE6^M"\nwaitfor "ACK6" 2\n'
 first='proc main\n'+profile+'transmit "FIRSTOK^M"\nendproc\n'
 six='proc main\n'
 if a.case!='receive':six+='delete "D:\\TEST.KBD"\nrename "D:\\BACK.KBD" "D:\\TEST.KBD"\n'
 for i in range(6):six+=f'fopen {i} "D:\\SLOT{i}.TXT" "wb"\nif failure\nexit\nendif\n'
 for i in range(6):six+=f'fputs {i} "SLOT{i}|"\nfclose {i}\n'
 six+='transmit "SIXOK^M"\nendproc\n'
 missing='proc main\nfopen 0 "D:\\ABSENT.TXT" "rb"\nif failure\ntransmit "MISSINGOK^M"\nendif\nendproc\n'
 if a.case=='receive':
  body='when 0 "PKT" transmit "a"\ntransmit "RXREADY^M"\n'
  body+=''.join('emulate '+('vt220' if i%2==0 else 'ansi')+'\n' for i in range(a.rounds))
  body+='transmit "RXWAIT^M"\nwaitfor "RXEND" 10\ntransmit "RXDONE^M"\n'
  scenario='proc main\n'+body+'endproc\n'
  chunks=[(i*.01,b'PKT'*16) for i in range(32)]
  triggers=((b'RXREADY\r',chunks),(b'RXWAIT\r',[(.3,b'RXEND')]),(b'PROFILE4\r',b'\x1b[0cACK4'),(b'PROFILE6\r',b'\x1b[0cACK6'))
 else:
  mutation='delete "D:\\TEST.KBD"\n' if a.case=='missing' else 'fopen 0 "D:\\TEST.KBD" "wb"\nfputs 0 "BAD"\nfclose 0\n'
  scenario='proc main\n'+mutation+'transmit "IOBEGIN^M"\nemulate vt220\ntransmit "IOBAD^M"\nendproc\n'
  triggers=((b'IOBEGIN\r',[(.3,b'\x1b[0c')]),(b'PROFILE4\r',b'\x1b[0cACK4'),(b'PROFILE6\r',b'\x1b[0cACK6'))
 keys=bytearray(actions(b'D:\\SCENE.ASX',0))
 for i,(n,text) in enumerate((('SCENE',scenario),('SIX',six),('MISSING',missing),('FIRST',first))):
  (out/(n+'.ASP')).write_text(text);files[n+'.ASX']=compile_source(text);keys[i*54:(i+1)*54]=struct.pack('<H',0)+('D:\\'+n+'.ASX').encode().ljust(52,b'\0')
 files['ACTIONS.KEY']=bytes(keys)
 settings=bytearray(prm(port=3,baud=5))
 for at,value in [(0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0)]:struct.pack_into('<H',settings,at,value)
 drive=ROOT/'build/connection-dos'/out.name;assert not drive.exists();drive.mkdir(parents=True)
 (drive/'BACK.KBD').write_bytes(kbd)
 harness.BINARY=stage/'TERMINAL.EXE'
 times={}
 events=tuple((marker,lambda folder,key=key:times.setdefault(key,time.monotonic())) for marker,key in ((b'RXREADY\r','ready'),(b'RXWAIT\r','waiting'),(b'RXDONE\r','done'))) if a.case=='receive' else ()
 r=harness.run(out.name,'success','p900 enter p3500 a-1 p5000 a-2 p1300 a-3 p1300 a-4 p1300 r e a d y enter p700 a-x',prm=bytes(settings),arguments='@TEST.PRM /T:D:\\ACTIONS.KEY /K:D:\\TEST.KBD /D:CaseTest:23',com=3,irq=5,cpu=a.cpu,working_drive='d',timeout=35,files=files,observer='EMUWATCH',observer_high=a.cpu=='386',online_triggers=triggers,online_actions=events)
 drive=ROOT/'build/connection-dos'/out.name;wire=(drive/'serial.bin').read_bytes();checks=dict(r['checks'])
 checks.pop('immediate_banner_not_dropped')

 exits=aspect_exit_watch.read(drive/'EXITSTAT.BIN');records=exits['exits']
 rx=struct.unpack('<8H',(drive/'RXSTAT.BIN').read_bytes());assert rx[:2]==(0xe620,1)
 checks.update(expected_native_errors=len(records)==4 and [e['error'] for e in records]==([0]*4 if a.case=='receive' else [5,0,0,0]),all_native_owners_retired=len(records)==4 and all(e[k]==0 for e in records for k in ('cleanup_error','external_scope','display_owned','program_busy','process_busy')),all_exit_DS_equals_SS=len(records)==4 and all(e['ds']==e['ss']!=0 for e in records),later_three_scripts_succeed=b'SIXOK\rMISSINGOK\rPROFILE4\r\x1b[?62;2cPROFILE6\r\x1b[?1;2cFIRSTOK\r' in wire,six_files=all((drive/f'SLOT{i}.TXT').exists() and (drive/f'SLOT{i}.TXT').read_bytes()==f'SLOT{i}|'.encode() for i in range(6)),strict_keyboard_restored=(drive/'TEST.KBD').read_bytes()==kbd,final_reset_view=(drive/'SCREEN.BIN').read_bytes()[:3840]==b''.join(bytes([v,7]) for v in b'ACK6'.ljust(1920,b' ')),keyboard_after_scripts=wire.endswith(b'ready\r+++ATH\r'),real_strict_keyboard_reads=rx[3]>=2,no_sampled_RX_drops=rx[6]==0,no_sampled_serial_error=rx[7]==0)
 if a.case=='receive':
  first=wire.split(b'RXREADY\r',1)[1].split(b'RXDONE\r',1)[0] if b'RXREADY\r' in wire and b'RXDONE\r' in wire else b''
  checks.update(all_received_markers_acknowledged=first.count(b'RXWAIT\r')==1 and first.replace(b'RXWAIT\r',b'',1)==b'a'*512,queued_input_observed_during_KBD_IO=rx[4]>0,receive_test_completed=wire.count(b'RXDONE\r')==1)
 else:checks.update(old_profile_survives_failed_EMULATE=b'IOBEGIN\r\x1b[?1;2cSIXOK\r' in wire,actual_EMULATE_IO_error=len(records)==4 and records[0]['opcode']==47 and records[0]['exit']==5,stops_before_following_statement=wire.count(b'IOBEGIN\r')==1 and b'IOBAD' not in wire,backup_consumed_by_recovery=not(drive/'BACK.KBD').exists())
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 report=dict(passed=all(checks.values()),checks=checks,products=products,case=a.case,cpu=a.cpu,rounds=a.rounds if a.case=='receive' else 0,observer=exits,receive_observer=dict(IO_entries=rx[2],read_entries=rx[3],pending_entries=rx[4],maximum_queued=rx[5],maximum_dropped=rx[6],maximum_serial_status=rx[7]),sources=sources,receive_timing={k:round(v-times['ready'],6) for k,v in times.items()} if times else {},original_inputs=[],scope=__doc__+' Normal products, actual DOS COM3/IRQ5 and native opcode2F. Synthetic serial peer and authored7-profile keyboard file with Enter and otherwise empty bindings. Passive diagnostic observer adds resident memory; no product writes/UART reads in hook. Entry backlog samples do not establish worst-case latency or physical CTS/SIP/audio acceptance.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('EMULATE IO',a.case,report['passed'],report['receive_observer'],{k:v for k,v in checks.items() if not v});return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
