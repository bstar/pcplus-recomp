#!/usr/bin/env python3
"""Actual external PROGRAM failures, local acknowledgement and same-parent reuse."""
import argparse,json,struct,subprocess
from pathlib import Path
import test_connection_dos as harness
from directory_fixtures import prm
from build_path_session import ROOT,sha

PROBE='''
error_seen: dw 0
current_error: dw 0
error_text: db 'Program could not run. Press a key to return.'
watch_error:
 mov word [current_error],0
 mov ax,0b800h
 mov es,ax
 xor si,si
.next:
 xor bx,bx
 mov di,si
.match:
 mov al,[es:di]
 cmp al,[error_text+bx]
 jne .miss
 add di,2
 inc bx
 cmp bx,45
 jb .match
 mov word [error_seen],1
 mov word [current_error],1
 ret
.miss:
 add si,2
 cmp si,(2000-45)*2
 jb .next
.done:
 ret
'''

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['terminal','output']:p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--case',choices=['missing-target','missing-comspec','large-comspec','nonzero-child','empty-path-fallback'])
 a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 m=json.loads(binary.with_name('manifest.json').read_text());assert m['experimental_external_viewer'] and sha(binary)==m['binary_sha256']
 names=['standalone/test_viewer_external_failures.py','standalone/viewer_external_child.asm','standalone/viewer_dialog_watch.asm','standalone/test_connection_dos.py','standalone/directory_fixtures.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py','standalone/test_terminal.py']
 frozen=dict(m['sources']);frozen.update({n:sha(ROOT/n) for n in names})
 for n,h in frozen.items():assert sha(ROOT/n)==h,n
 out.mkdir(parents=True);source=(ROOT/'standalone/viewer_dialog_watch.asm').read_text()
 source=source.replace(' inc word [sample+4]',' call watch_error\n inc word [sample+4]',1).replace('resident_end:',PROBE+'\nresident_end:',1)
 source=source.replace('.live_after:\n','.live_after:\n cmp word [current_error],0\n jne .done\n',1)
 source=source.replace(' popf\n mov dx,[es:old]',' popf\n mov ax,[es:error_seen]\n mov [buffer+12083],ax\n mov dx,[es:old]',1).replace('12083','12085')
 # The existing12083-byte record stays intact; only the appended error word moves back.
 source=source.replace('[buffer+12085]','[buffer+12083]')
 (out/'observer.asm').write_text(source);subprocess.run(['nasm','-fbin','-DWATCH_KIND=9',str(out/'observer.asm'),'-o',str(out/'VIEWOBS.COM')],check=True)
 child=out/'VTEST.COM';subprocess.run(['nasm','-fbin',str(ROOT/'standalone/viewer_external_child.asm'),'-o',str(child)],check=True)
 nonzero=(ROOT/'standalone/viewer_external_child.asm').read_text().replace('mov ax,4c00h','mov ax,4c25h');(out/'nonzero.asm').write_text(nonzero)
 subprocess.run(['nasm','-fbin',str(out/'nonzero.asm'),'-o',str(out/'NONZERO.COM')],check=True)
 harness.BINARY=binary;cases=[]
 for name in ['missing-target','missing-comspec','large-comspec','nonzero-child','empty-path-fallback']:
  if a.case and a.case!=name:continue
  settings=bytearray(prm(port=3,baud=5))
  for at,v in [(0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0)]:struct.pack_into('<H',settings,at,v)
  command=b'D:\\ABSENT.COM' if name=='missing-target' else b'D:\\VTEST.COM';settings[0x35d:0x39e]=command.ljust(65,b'\0')
  # A valid37-byte MZ requests at least65535 extra paragraphs: DOS error8.
  large=struct.pack('<14H',0x5a4d,37,1,0,2,65535,65535,0,0xfffe,0,0,0,28,0)+bytes(4)+b'\xb8\x00\x4c\xcd\x21'
  files={'VIEWOBS.COM':(out/'VIEWOBS.COM').read_bytes(),'VTEST.COM':(out/'NONZERO.COM').read_bytes() if name=='nonzero-child' else child.read_bytes(),'LARGE.EXE':large}
  environment={'COMSPEC':'D:\\ABSENT.COM'} if name in ['missing-comspec','empty-path-fallback'] else {'COMSPEC':'D:\\LARGE.EXE'} if name=='large-comspec' else {}
  if name=='empty-path-fallback':environment['PATH']='D:\\ABSENT'
  error=name=='large-comspec';label=out.name+'-'+name;drive=ROOT/'build/connection-dos'/label
  keys='p900 enter p3500 a-v p1000 enter p1800 '+('space p900 ' if error else '')+'r e a d y enter p900 a-x'
  actions=()
  if name=='missing-target':
   def install(folder):(folder/'ABSENT.COM').write_bytes(child.read_bytes())
   actions=((b'ready\r',install),)
   keys=keys.replace('p900 a-x','p900 a-v p900 enter p1800 a g a i n enter p900 a-x')
  base=harness.run(label,'success',keys,prm=bytes(settings),arguments='@TEST.PRM /D:CaseTest:23',com=3,irq=5,cpu='8086',working_drive='d',observer='VIEWOBS',timeout=35,files=files,environment=environment,keyboard_program='Z:\\BIN\\ADDKEY.COM',online_actions=actions,online_triggers=((b'ready\r',b'\x1b[3;1HAFTER-VIEWER\x1b[6n'),))
  raw=(drive/'VIEWUI.BIN').read_bytes();words=struct.unpack_from('<9H',raw);wire=(drive/'serial.bin').read_bytes();report=drive/'VCHILD.BIN'
  checks=dict(base['checks'],observer_complete=len(raw)==12085 and words[:2]==(0x5656,15),exact_terminal_frame=raw[18:4018]==raw[8018:12018],exact_cursor_shape=words[3:5]==words[7:9],local_error_acknowledgement=struct.unpack_from('<H',raw,12083)[0]==int(error),child_presence=report.exists()==(name in ['missing-target','missing-comspec','nonzero-child','empty-path-fallback']),ordinary_keyboard_after_return=wire.count(b'ready\r')==1,fresh_CPR_after_return=b'\x1b[3;13R' in wire)
  if name=='missing-target':checks['same_parent_successful_retry']=b'again\r' in wire and report.exists()
  r=dict(case=name,passed=all(checks.values()),checks=checks,error_observed=struct.unpack_from('<H',raw,12083)[0],drive=str(drive.relative_to(ROOT)),capture_sha256=sha(drive/'VIEWUI.BIN'));cases.append(r);(out/(name+'.json')).write_text(json.dumps(r,indent=2)+'\n');print(name,{k:v for k,v in checks.items() if not v},flush=True)
 for n,h in frozen.items():assert sha(ROOT/n)==h,n
 result=dict(passed=all(r['passed'] for r in cases),binary_sha256=sha(binary),cases=cases,sources=frozen,original_inputs=[],scope=__doc__+' Synthetic serial peer and DOSBox8086. Owned excessive-allocation MZ interpreter, missing configured interpreter with ordinary/empty PATH, missing target followed by actual same-parent retry and exit37 child. Timer observer only reads VGA and retains one appended error-prompt flag; no product memory patch. COMMAND.COM child-result policy is observed through the composed shell, not inferred as direct child status. No physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');assert result['passed'],'See per-case checks in result.json'
if __name__=='__main__':main()
