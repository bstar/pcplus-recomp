#!/usr/bin/env python3
"""Source-linked Script menu, direct EXEC, and UART/video child restoration.
Only DOS kernel/BIOS/UART hardware is modeled; the ASPECT child interpreter is
verified separately by actual DOS tests, not by this EXEC boundary model.
"""
import hashlib,json
from check_translation_edit_live import Editor,ROOT
from check_program_actions_live import BINARY

def main():
 cases=[]
 def done(name,n):cases.append(dict(case=name,inputs=n,passed=True));print(name,n,flush=True)
 def model(**kw):
  m=Editor(**kw) if kw else Editor()
  m.install_program_name();m.child_status=0;return m
 def path(m,p):m.uc.mem_write(m.symbols['_command_menu_script'],p+b'\0')
 for p in [b'TEST.ASX',b'D:\\TEST.ASX',b'D:\\SCRIPTS\\TEST.ASX',b'D:TEST.ASX',b'\\TEST.ASX']:
  m=model();path(m,p);assert m.call('terminal_script_start')==0
  assert m.get('terminal_program_pending') and m.get('terminal_program_kind')==4 and not m.children
  m.keys.append(32);m.safe();assert m.children==[dict(path=b'D:\\APP\\ASPECT.EXE',tail=b' '+p)]
  assert m.get('terminal_program_status')==4 and not m.get('terminal_program_active');m.restored()
 done('relative-drive-rooted-direct-sibling-child-and-real-foreground-restore',5)
 for p in [b'',b'..\\T.ASX',b'.\\T.ASX',b'LONGNAME9.ASX',b'T.LONG',b'T A.ASX',b'T.ASX /c',b'CON.ASX',b'D:\\COM1\\T.ASX',b'T;X',b'T".ASX',b'T*',b'D:\\',b'T/ABC']:
  m=model();path(m,p);assert m.call('terminal_script_start')==0;m.keys.append(32);m.safe()
  assert not m.children and m.get('terminal_program_status')==5;m.restored()
 done('invalid-traversal-devices-shellsyntax-and-unbounded-components-denied-before-EXEC',14)
 for fault in ['missing','child-error','trailer','memory']:
  m=model();path(m,b'TEST.ASX')
  if fault=='missing':m.exec_error=2
  if fault=='child-error':m.child_status=7
  if fault=='trailer':m.environment(b'PCPLUS=D:\\WRONG\0\0')
  if fault=='memory':m.resize_error=8
  assert m.call('terminal_script_start')==0;m.keys.append(32);m.safe()
  assert m.get('terminal_program_status')==5 and not m.get('terminal_quit');m.restored()
  if fault=='trailer':assert not m.children and 0x4a not in m.calls
 done('missing-helper-child-error-malformed-trailer-allocation-failure-resume',4)
 m=model();m.keys.extend([0x2c00,ord('a')]);m.poll();m.poll()
 assert m.get('_command_menu_active') and not m.get('terminal_program_pending')
 m.keys.extend(map(ord,'TEST.ASX'));m.keys.append(13)
 for _ in range(9):m.poll()
 assert not m.get('_command_menu_active') and m.get('terminal_program_pending')
 m.keys.append(32);m.safe();assert m.children==[dict(path=b'D:\\APP\\ASPECT.EXE',tail=b' TEST.ASX')];m.restored()
 done('File-menu-Script-prompt-produces-complete-argument-only-after-view-restoration',1)
 m=model();m.keys.extend([0x2c00,ord('a'),ord('T'),27,27])
 for _ in range(5):m.poll()
 assert not m.get('_command_menu_active') and not m.get('terminal_program_pending') and not m.children
 done('Script-filename-Escape-and-menu-Escape-no-child',1)
 for marker in ['terminal_program_pending','terminal_macro_active','terminal_monitor_active','terminal_controller_active','uart_break_hold']:
  m=model();path(m,b'TEST.ASX');m.put(marker,1)
  # Macro owner is guarded in the real transport before Script dispatch.
  if marker=='terminal_macro_active':
   m.keys.append(0xfe00);m.poll();assert not m.get('terminal_program_pending')
  else:assert m.call('terminal_script_start')!=0
  assert not m.children
 done('existing-foreground-owner-admission-refuses-nesting',5)
 result=dict(passed=True,binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=cases,
  inputs=sum(x['inputs'] for x in cases),sources={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['src/terminal/script_launch.asm','src/terminal/script_launch.c','src/redisplay/command_menu.c',__file__.split(str(ROOT)+'/')[-1]]},
  limitations=['DOS EXEC boundary modeled; interpreter semantics and actual child launch require separate DOS test.','Script child has no live UART scheduling API. Capture closes before child; terminal screen/UART resume using existing PROGRAM owner.'])
 (ROOT/'build/terminal/script-launch-live-checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
