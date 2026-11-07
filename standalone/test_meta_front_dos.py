#!/usr/bin/env python3
"""Exercise the normal Alt-M frontend with a live DOS UART and synthetic files."""
import argparse,hashlib,json,shutil,struct,subprocess
from pathlib import Path
import test_connection_dos as harness
from directory_fixtures import prm
ROOT=harness.ROOT
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--case',choices=('edit','save','reference','browser','load','reload','cancel','missing','reference-cancel','reference-help','script-cancel','info-cancel'),default='edit')
 a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 manifest=json.loads(binary.with_name('manifest.json').read_text())
 assert manifest['binary_sha256']==sha(binary) and manifest['experimental_meta_editor']
 product=out/'product';product.mkdir()
 for n in ('TERMINAL.EXE','PCLINE.OVL','PCMETA.OVL'):
  if n=='PCMETA.OVL' and a.case=='missing':continue
  shutil.copyfile(binary.with_name(n),product/n)
 settings=bytearray(prm(port=3,baud=5))
 for at,val in ((0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0),(0x3e4,7),(0x3e6,11),(0x3e8,113)):
  struct.pack_into('<H',settings,at,val)
 watch=(ROOT/'standalone/path_dialog_watch.asm').read_text()
 start=watch.index(' cmp word [es:806]');end=watch.index('%if WATCH_KIND',start)
 notice_at=3202 if manifest.get('experimental_meta_shared_runtime') else 1604
 marker=f" cmp byte [es:{notice_at}],'M'\n jne .done"if a.case=='missing'else" cmp byte [es:522],'M'\n jne .done\n cmp byte [es:524],'E'\n jne .done\n cmp byte [es:160],'U'\n jne .done"
 watch=watch[:start]+marker+'\n'+watch[end:]

 (out/'watch.asm').write_text(watch)
 subprocess.run(['nasm','-fbin','-DWATCH_KIND=0',str(out/'watch.asm'),'-o',str(out/'MFOBS.COM')],check=True)
 opening='a-z p1200 escape p500 a-m'if a.case=='reference-cancel'else'a-z p1200 down down f1 p500 escape p1200 a-m'if a.case=='reference-help'else'a-f5 p700 escape p1200 a-m'if a.case=='script-cancel'else'a-i p500 escape p1200 a-m'if a.case=='info-cancel'else'a-z p500 a-m'if a.case=='reference'else'` p500 right right right p300 m'if a.case=='browser'else'a-m p10 escape p1000 a-m'if a.case=='cancel'else'a-m'
 edit='r p300 enter p300 h e l l o enter p500'
 if a.case=='load':edit='l p300 n e x t enter p1500'
 if a.case=='missing':edit=''
 if a.case=='save':edit+=' s p1500'
 leave='escape p1500'
 if a.case=='reload':leave+=' a-m p2500 escape p1500'
 keys='p900 enter p3500 '+opening+' p3000 '+edit+' '+leave+' '+('a-1 p800 'if a.case!='missing'else'')+'r e a d y enter p1000 a-x'
 files={'MFOBS.COM':(out/'MFOBS.COM').read_bytes()}
 if a.case=='load':files['NEXT.KEY']=b''.join(b'\x03\0'+(b'loaded'if i==0 else b'') .ljust(52,b'\0')for i in range(10))
 harness.BINARY=product/'TERMINAL.EXE';case=out.name+'-'+a.case;drive=ROOT/'build/connection-dos'/case
 assert not drive.exists()
 result=harness.run(case,'success',keys,prm=bytes(settings),arguments='@TEST.PRM /D:CaseTest:23',com=3,irq=5,cpu='8086',working_drive='d',observer='MFOBS',files=files,timeout=35,
  online_updates=((4.8,b'\x1b[2;1HUART-META-OPEN\x1b[6n'),),
  online_triggers=((b'ready\r',b'\x1b[3;1HAFTER-META\x1b[6n'),))
 raw=(drive/'PATHVIEW.BIN').read_bytes();magic,flags,ticks=struct.unpack_from('<3H',raw)
 frame=raw[6:4006];wire=(drive/'serial.bin').read_bytes();screen=(drive/'SCREEN.BIN').read_bytes()
 chars=lambda r,c,n:frame[(r*80+c)*2:(r*80+c+n)*2:2]
 checks=dict(result['checks'])
 checks.update(captured_popup=magic==0x5044 and flags==3 and ticks>2,
  ready_once=wire.count(b'ready\r')==1,post_popup_query=b'\x1b[3;11R'in wire,
  post_popup_render=screen[320:340:2]==b'AFTER-META',
  no_unowned_stage=not(drive/'PCPSTG.$$$').exists(),no_unowned_backup=not(drive/'PCPBAK.$$$').exists())
 if a.case!='missing':checks.update(heading=chars(3,20,11)==b' META KEYS ',incoming_visible_while_open=chars(1,0,14)==b'UART-META-OPEN',query_serviced_while_open=b'\x1b[2;15R'in wire,
  adopted_text_on_wire=(b'loadedready\r'if a.case=='load'else b'helloready\r')in wire)
 else:checks['missing_notice']=b'Meta Keys could not open.'in frame[::2]
 if a.case=='save':
  expected=bytearray(540)
  for i in range(10):expected[i*54]=3
  expected[2:8]=b'hello\0'
  checks['exact_saved_key']=(drive/'PCPLUS.KEY').read_bytes()==expected
 else:checks['no_implicit_save']=not(drive/'PCPLUS.KEY').exists()
 report=dict(passed=all(checks.values()),case=a.case,checks=checks,binary_sha256=sha(binary),base_receipt=str(drive/'result.json'),frame_sha256=hashlib.sha256(frame).hexdigest(),sources={n:sha(ROOT/n)for n in ('standalone/test_meta_front_dos.py','standalone/test_connection_dos.py','standalone/path_dialog_watch.asm','standalone/directory_fixtures.py')},scope='Actual source-built DOS parent, BIOS keys, passive VGA observer and independent synthetic UART peer. No physical modem or native-pixel-equivalence claim.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
 print(a.case,{k:v for k,v in checks.items()if not v},flush=True);assert report['passed'],report

if __name__=='__main__':main()
