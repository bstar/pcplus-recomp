#!/usr/bin/env python3
"""Actual DOS script-time native window, queued receive data and continuation."""
import json,re,struct,subprocess,sys
from pathlib import Path
import test_aspect_keys_dos as keys
ROOT=keys.ROOT
BASE=ROOT/'build/aspect-script-window-dos'

def definitions():
 source='proc main\nwaitfor "LOGIN:" 5\nset duplex full\ntransmit "KEYREADY"\nwaitfor "END" 30\nif waitfor\ntransmit $D_PWORD\ntransmit "^M"\npause 1\nendif\nendproc\n'
 cases=[]
 for profile,mode,kind in [(4,'STANDARD','Escape'),(6,'ENHANCED','Escape'),(4,'ENHANCED','F1'),(6,'STANDARD','help'),(4,'STANDARD','parent-menu')]:
  middle='p1000 a-z p4500 escape' if kind=='help' else 'p5500 f1' if kind=='F1' else 'p5500 escape'
  cases.append(dict(name=f'script-window-{profile}-{kind}',source=source,profile=profile,bios_policy=mode,custom=False,
   success=True,banner=keys.renderer.ESC+b'[2J'+keys.renderer.ESC+b'[HFIRST BYTE SAFE'+keys.renderer.QUERY+keys.renderer.DA+b'LOGIN:',
   keys='p1800 k e y s p200 a-z '+middle+' d o n e p2500 space p700 r e a d y p700 '+('a-z p500 escape p300 ' if kind=='parent-menu' else '')+'a-x',
   key_wire=b'keys'+(b'\x1bOP' if kind=='F1' else b'')+b'done',post=keys.renderer.QUERY,
   post_reply=keys.renderer.ESC+b'[1;31R',screen=[(0,0,'FIRST BYTE SAFE'),(0,21,'QUEUEDEND')],help=kind=='help',resume_menu=kind=='parent-menu'))
 return cases

def symbols(path):
 return {n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^\s*([0-9a-f]{4}):([0-9a-f]{4,8})[*+]?\s+(\w+)',path.read_text(),re.M|re.I)}

def make_observer(original_observer,parent,child):
 def observer(offsets):
  result=original_observer(offsets);out=keys.renderer.OUT;path=out/'observer.asm';text=path.read_text()
  old='sample_end:\nowner_table:';assert text.count(old)==1
  text=text.replace(old,'window_seen: dw 0\nhelp_seen: dw 0\nwindow_ticks: dw 0\nmax_child_rx: dw 0\nparent_menu_seen: dw 0\nsample_end:\nowner_table:')
  old='timer:\n save\n cld\n';assert text.count(old)==1
  timer=r'''timer:
 save
 cld
 mov ax,0xb800
 mov es,ax
 mov si,parent_title
 mov di,2
 call window_match_at
 or ax,ax
 jz .try_reference
 cmp word [cs:exec_done],1
 jne .try_reference
 mov word [cs:parent_menu_seen],1
.try_reference:
 mov si,reference_title
 call window_match
 or ax,ax
 jz .try_help
 mov word [cs:window_seen],1
 jmp .window_present
.try_help:
 mov si,help_title
 call window_match
 or ax,ax
 jz .window_done
 mov word [cs:help_seen],1
.window_present:
 inc word [cs:window_ticks]
 mov ax,[cs:parent_psp]
 or ax,ax
 jz .window_done
 add ax,WINDOW_CS+0x10
 mov es,ax
 mov ax,[es:CHILD_DS]
 or ax,ax
 jz .window_done
 mov es,ax
 mov ax,[es:CHILD_RX]
 cmp ax,[cs:max_child_rx]
 jbe .window_done
 mov [cs:max_child_rx],ax
.window_done:
'''
  for token,value in [('WINDOW_CS',parent['render_child_ds'][0]),('CHILD_DS',parent['render_child_ds'][1]),('CHILD_RX',child['uart_rx_count'][1])]:timer=timer.replace(token,str(value))
  text=text.replace(old,timer)
  old='resident_end:\nstart:';assert text.count(old)==1
  helper=r'''window_match:
 mov di,2*(2*80+6)
window_match_at:
.next:
 mov al,[cs:si]
 inc si
 or al,al
 jz .yes
 cmp al,[es:di]
 jne .no
 add di,2
 jmp .next
.yes:
 mov ax,1
 ret
.no:
 xor ax,ax
 ret
reference_title: db ' PCPLUS  //  TERMINAL KEYS ',0
help_title: db ' PCPLUS  //  SCRIPT KEYBOARD HELP ',0
parent_title: db 'PCPLUS  Command Menu',0
resident_end:
start:'''
  text=text.replace(old,helper);path.write_text(text)
  subprocess.run(['nasm','-fbin',str(path),'-o',str(out/'RENDER.COM')],check=True)
  return ((out/'RENDER.COM').read_bytes(),*result[1:])
 return observer

def main():
 original_adapter=keys.adapter;original_observer=keys.renderer.observer
 parent=symbols(ROOT/'build/terminal/terminal.map');child=symbols(ROOT/'build/aspect-runner/ASPECT.map')
 def adapter():
  module=original_adapter();run=module.run
  def staged(*args,**kwargs):
   kwargs['online_updates']=[(3.0,b'QUEUED')]
   return run(*args,**kwargs)
  module.run=staged;return module
 keys.OUT=BASE;keys.definitions=definitions;keys.adapter=adapter;keys.renderer.observer=make_observer(original_observer,parent,child)
 keys.main()
 # The common parser leaves appended passive-window words untouched.
 folder=BASE/sys.argv[sys.argv.index('--label')+1]
 report=json.loads((folder/'checks.json').read_text())
 for case in report['cases']:
  spec=next(c for c in definitions() if c['name']==case['case'])
  raw=(folder/case['case']/'RENDER.BIN').read_bytes();seen,help_seen,ticks,rx,menu=struct.unpack('<5H',raw[-10:])
  case['checks'].update(actual_reference_seen=seen==1,actual_help_seen=bool(help_seen)==spec['help'],
   modal_wait_exceeded_render_budget=ticks>72,actual_child_ring_retained_six_bytes=rx==6,
   parent_menu_owner_resumes=bool(menu)==spec['resume_menu'])
  case['window_observation']=dict(reference=seen,help=help_seen,ticks=ticks,max_child_rx=rx,parent_menu=menu)
  case['passed']=all(case['checks'].values());(folder/case['case']/'result.json').write_text(json.dumps(case,indent=2)+'\n')
 report.update(passed=all(c['passed'] for c in report['cases']),checker_sha256=keys.renderer.sha(Path(__file__)),
  scope='Actual source-built DOS parent/ASPECT, native script-time Alt-Z, repeated help, Escape dismissal or queued F1, both supported profiles/BIOS modes. Passive timer observes actual titles and child RX ring while six peer bytes wait; subsequent exact screen/query/wire and normal return/hardware checks retained. No physical modem, full menu actions or whole-application acceptance.')
 (folder/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Actual DOS script window',len(report['cases']),'cases',report['passed'])
 return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
