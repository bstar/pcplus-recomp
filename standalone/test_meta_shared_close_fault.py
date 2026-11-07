#!/usr/bin/env python3
"""Real shared-loader uncertain close: one attempt, held code, DOS exit14."""
import argparse,json,re,struct,subprocess
from pathlib import Path
import test_connection_dos as lab
from directory_fixtures import prm
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('terminal','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--module',choices=['line','meta'],required=True);p.add_argument('--when',choices=['before','after'],required=True);a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build')and not out.exists();out.mkdir(parents=True)
 m=json.loads(binary.with_name('manifest.json').read_text());assert m['binary_sha256']==sha(binary)and m['experimental_meta_shared_runtime']
 symbols={n:(int(s,16),int(o,16))for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',binary.with_name('terminal.map').read_text(),re.M|re.I)}
 data=symbols['terminal_program_kind'][0];config,state=symbols['_line_overlay_state'];expected=symbols['_line_overlay_expected'][1]
 watch=(ROOT/'standalone/path_dialog_watch.asm').read_text();watch=watch.replace('last_sum: dw 0','observed_state: times 16 dw 0\nlast_sum: dw 0')
 start=watch.index(' cmp word [es:806]');end=watch.index('%if WATCH_KIND',start)
 watch=watch[:start]+f''' mov ax,ss
 sub ax,{data}
 jc .done
 add ax,{config}
 jc .done
 cmp ax,0xa000
 jae .done
 mov es,ax
 cmp word [es:{expected}],{m['line_port_overlay']['bank_bytes']}
 jne .done
 cmp word [es:{state}],3
 jne .done
 cmp word [es:{state+12}],1
 jne .done
 mov si,{state}
 mov di,observed_state
 mov cx,16
.state:
 mov ax,[es:si]
 mov [di],ax
 add si,2
 add di,2
 loop .state
 mov ax,0xb800
 mov es,ax
 cmp byte [es:3202],'L'
 jne .done
'''+watch[end:]
 watch=watch.replace('4071','4103').replace(' popf\n mov dx,[es:old_vector]',''' popf
 mov si,observed_state
 mov di,buffer+4071
 mov cx,32
.state_out:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 loop .state_out
 mov dx,[es:old_vector]''',1)
 (out/'watch.asm').write_text(watch);subprocess.run(['nasm','-fbin','-DWATCH_KIND=0',str(out/'watch.asm'),'-o',str(out/'SHWATCH.COM')],check=True)
 flags=(['-DMODULE_LINE']if a.module=='line'else[])+(['-DCLOSE_BEFORE']if a.when=='before'else[])
 subprocess.run(['nasm','-fbin',*flags,str(ROOT/'standalone/shared_module_close_fault.asm'),'-o',str(out/'CFAULT.COM')],check=True)
 settings=bytearray(prm(port=3,baud=5))
 for at,v in ((0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0),(0x3e4,7),(0x3e6,11),(0x3e8,113)):struct.pack_into('<H',settings,at,v)
 lab.BINARY=binary;opening='a-p'if a.module=='line'else'a-m'
 keys='p900 enter p3500 '+opening+' p4000 a-m p300 a-p p300 a-z p300 a-1 p300 escape'
 result=lab.run(out.name,'success',keys,prm=bytes(settings),arguments='@TEST.PRM /D:CaseTest:23',com=3,irq=5,cpu='8086',working_drive='d',observer='SHWATCH',auxiliary=('CFAULT',),files={'SHWATCH.COM':(out/'SHWATCH.COM').read_bytes(),'CFAULT.COM':(out/'CFAULT.COM').read_bytes()},expected=14,timeout=30)
 drive=ROOT/'build/connection-dos'/out.name;raw=(drive/'PATHVIEW.BIN').read_bytes();state_words=struct.unpack_from('<16H',raw,4071);fault=struct.unpack('<11H',(drive/'CLOSE.BIN').read_bytes());frame=raw[6:4006]
 field='line_port_overlay'if a.module=='line'else'meta_editor_overlay';total=m[field]['bank_bytes']+m[field]['relocations']*2
 checks=dict(result['checks']);checks.update(passive_capture_complete=struct.unpack_from('<2H',raw)==(0x5044,3),uncertain_close_latched=state_words[0]==3 and state_words[6]==1,attempt_spent=state_words[2]==0xffff,all_bytes_read_before_close=state_words[3]==total,no_fixups_after_uncertain_close=state_words[4]==0,single_tracked_open_and_close=fault[0]==0x4346 and fault[1:3]==(1,1)and fault[7]==1,hook_restored=fault[8]==1,loader_close_site=fault[9]==fault[6]+16+config,all_parent_closes_recorded=fault[10]>=fault[2],close_boundary=(fault[3:5]==(0xffff,0xffff)if a.when=='before'else fault[4]&1==0),visible_recovery=b'close failed. Esc exits to DOS.'in frame[::2],no_KEY_created=not(drive/'PCPLUS.KEY').exists())
 report=dict(passed=all(checks.values()),module=a.module,when=a.when,binary_sha256=sha(binary),checks=checks,loader_state=state_words,fault_words=fault,sources={n:sha(ROOT/n)for n in ('standalone/test_meta_shared_close_fault.py','standalone/shared_module_close_fault.asm','standalone/path_dialog_watch.asm','standalone/test_connection_dos.py','standalone/directory_fixtures.py')},captures={str((drive/n).relative_to(ROOT)):sha(drive/n)for n in ('PATHVIEW.BIN','CLOSE.BIN','BEFORE.BIN','AFTER.BIN','serial.bin')},scope='Actual source parent in DOS8086; test-only INT21 fault injector matches module path, handle and opening PSP. Passive observer reads code state/video. Loader close calls counted by actual caller CS; separate total includes later shutdown calls outside that segment. One uncertain close before/after real kernel call; no app writes or physical media/DCD claims.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(a.module,a.when,{k:v for k,v in checks.items()if not v},flush=True);assert report['passed'],report
if __name__=='__main__':main()
