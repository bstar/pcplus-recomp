#!/usr/bin/env python3
"""Production DOS startup/edit/save/cancel of the recovered separator word."""
import hashlib,json,struct,subprocess
from test_connection_dos import run,ROOT,BINARY
from modem_fixtures import fixture
from check_directory_live import word

def main():
 out=ROOT/'build/clipboard-settings-dos';out.mkdir(parents=True,exist_ok=True)
 watcher=out/'CLWATCH.COM';subprocess.run(['nasm','-f','bin',str(ROOT/'standalone/clipboard_watch.asm'),'-o',str(watcher)],check=True)
 editor=ROOT/'build/setup/PRMEDIT.EXE';cases=[]
 def case(name,raw,keys,want,expected=None,notices=()):
  folder=ROOT/'build/connection-dos'/name;(folder/'CWATCH.BIN').unlink(missing_ok=True)
  for leaf in ['PRMEDIT.BAK','PRMEDIT.$$$']:(folder/leaf).unlink(missing_ok=True)
  proof=run(name,'success',keys,prm=raw,prm_expected=expected,arguments='@TEST.PRM /D:CaseTest:23',working_drive='d',files={'CLWATCH.COM':watcher.read_bytes(),'PRMEDIT.EXE':editor.read_bytes()},observer='CLWATCH')
  data=(folder/'CWATCH.BIN').read_bytes();magic,count,ticks=struct.unpack_from('<3H',data);assert magic==0x434c and count<=32
  frames=[data[6+i*320:6+(i+1)*320] for i in range(count)];wire=(folder/'serial.bin').read_bytes()
  proof['checks'].update(expected_exact_paste=want in wire,local_names_not_transmitted=b'one.zip' not in wire,keyboard_resumes=b'ready' in wire,observer_saw_clipboard=ticks>3,editor_recovery_files_absent=not (folder/'PRMEDIT.BAK').exists() and not (folder/'PRMEDIT.$$$').exists())
  for n in notices:proof['checks']['observed_separator_'+str(n)]=any(('Separator byte: %03d'%n).encode() in f[240:] for f in frames)
  proof['passed']=all(proof['checks'].values());proof['observed_notices']=[f[240:].decode('cp437') for f in frames]
  cases.append(proof);print(name,proof['passed'],flush=True);assert proof['passed'],proof
 add='a-= p300 a o n e . z i p enter p300'
 for value in (0,32,255):
  case('clipboard-settings-start-'+str(value),word(fixture(timeout=5),0x4ea,value),'p3000 '+add+' p p400 escape p300 r e a d y p300 a-x',b'ONE.ZIP'+bytes([value])+b'\r',notices=(value,))
 raw=fixture(timeout=5)
 # Terminal page: profile, wrap, scroll, five attributes, translation, separator.
 field='pgdown tab tab tab tab p100 tab tab tab tab tab home del del'
 case('clipboard-settings-live-save',raw,'p3000 '+add+' escape p300 a-f10 p700 '+field+' 3 2 f10 p300 escape p300 space p300 a-= p300 p p400 escape p300 r e a d y p300 a-x',b'ONE.ZIP \r',expected=word(raw,0x4ea,32),notices=(13,32))
 override=add+' r 3 2 enter p300 escape p300 a-f10 p700 '
 case('clipboard-settings-cancel-keeps-R',raw,'p3000 '+override+field+' 2 5 5 escape y p300 space p300 a-= p300 p p400 escape p300 r e a d y p300 a-x',b'ONE.ZIP \r',notices=(32,))
 case('clipboard-settings-unrelated-keeps-R',raw,'p3000 '+override+'pgdown tab tab tab home del del 1 e f10 p300 escape p300 space p300 a-= p300 p p400 escape p300 r e a d y p300 a-x',b'ONE.ZIP \r',expected=word(raw,0x1ae,30),notices=(32,))
 invalid=run('clipboard-settings-invalid','reject','p1500 a-x',prm=word(raw,0x4ea,256),expected=7)
 invalid['checks']['no_modem_or_paste_bytes']=not (ROOT/'build/connection-dos/clipboard-settings-invalid/serial.bin').read_bytes()
 invalid['passed']=all(invalid['checks'].values());assert invalid['passed'];cases.append(invalid)
 sources=['standalone/test_clipboard_settings_dos.py','standalone/test_connection_dos.py','standalone/clipboard_watch.asm','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py','src/config/terminal_import.c','src/config/setup_model.c','src/config/transfer_import.c','src/config/setup_model.h','src/config/live_configuration.c','src/config/live_setup_owner.c','src/terminal/configuration.asm','src/terminal/configuration_live.asm','src/terminal/setup_live_apply.asm','src/clipboard/clipboard_ui.c']
 result=dict(passed=True,binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),editor_sha256=hashlib.sha256(editor.read_bytes()).hexdigest(),cases=cases,sources={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},scope='Actual DOS production startup/PRMEDIT/AltF10/clipboard/UART and independent INT1C observer. Raw PRM04EA values0/32/255 reach wire unchanged; exact full-file save, unsaved cancel and unrelated save preserve session R; invalid256 refuses before UART. No physical UART, native PCSETUP binding or whole-application completion claim.')
 (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print('Clipboard settings actual DOS',len(cases),'passed')
if __name__=='__main__':main()
