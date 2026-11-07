#!/usr/bin/env python3
"""Real DOS module refusal/reopen, visible notice, serial service and cleanup."""
import argparse,json,shutil,struct,subprocess
from pathlib import Path
import test_connection_dos as lab
from directory_fixtures import prm
from build_context_help import ROOT,sha


def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('terminal','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--module',choices=['line','meta'],default='line')
 p.add_argument('--fault',choices=['missing','short','corrupt','extra'],required=True)
 a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 product=out/'product';product.mkdir()
 m=json.loads(binary.with_name('manifest.json').read_text())
 assert m['binary_sha256']==sha(binary) and m['experimental_line_port_overlay']
 leaf='PCMETA.OVL'if a.module=='meta'else'PCLINE.OVL'
 field='meta_editor_overlay'if a.module=='meta'else'line_port_overlay'
 notice=b'Meta Keys could not open. Check PCMETA.OVL. Esc returns.'if a.module=='meta'else b'Line/Port module unavailable or mismatched. Esc returns.'
 opening='a-m'if a.module=='meta'else'a-p'
 original=binary.with_name(leaf).read_bytes()
 assert sha(binary.with_name(leaf))==m[field]['sha256']
 data=None
 if a.fault=='short':data=original[:513]
 if a.fault=='corrupt':data=bytes([original[0]^128])+original[1:]
 if a.fault=='extra':data=original+b'X'
 shutil.copyfile(binary,product/'TERMINAL.EXE')
 if data is not None:(product/leaf).write_bytes(data)
 source=(ROOT/'standalone/path_dialog_watch.asm').read_text()
 start=source.index(' cmp word [es:806]');end=source.index('%if WATCH_KIND',start)
 source=source[:start]+''' cmp byte [es:3202],'L'
 jne .done
 cmp byte [es:3204],'i'
 jne .done
 cmp byte [es:3206],'n'
 jne .done
'''+source[end:]
 if a.module=='meta':source=source.replace("[es:3202],'L'","[es:3202],'M'").replace("[es:3204],'i'","[es:3204],'e'").replace("[es:3206],'n'","[es:3206],'t'")
 (out/'observer.asm').write_text(source)
 subprocess.run(['nasm','-fbin','-DWATCH_KIND=0',str(out/'observer.asm'),'-o',str(out/'LOFAULT.COM')],check=True)
 settings=bytearray(prm(port=3,baud=5))
 for at,value in ((0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0),(0x3e4,7),(0x3e6,11),(0x3e8,113)):
  struct.pack_into('<H',settings,at,value)
 lab.BINARY=product/'TERMINAL.EXE'
 result=lab.run(out.name,'success','p900 enter p3500 '+opening+' p2000 escape p700 '+opening+' p1800 escape p1000 r e a d y enter p700 a-x',
  prm=bytes(settings),arguments='@TEST.PRM /D:CaseTest:23',com=3,irq=5,cpu='8086',working_drive='d',observer='LOFAULT',
  files={'LOFAULT.COM':(out/'LOFAULT.COM').read_bytes()},timeout=35,
  online_triggers=((b'ready\r',b'\x1b[3;1HAFTER-LINE-PORT\x1b[6n'),))
 capture=ROOT/'build/connection-dos'/out.name
 raw=(capture/'PATHVIEW.BIN').read_bytes();frame=raw[6:4006];wire=(capture/'serial.bin').read_bytes()
 checks=dict(result['checks'],visible_module_refusal=frame[3202:3202+len(notice)*2:2]==notice,
  observer_completed=struct.unpack_from('<2H',raw)==(0x5044,3),
  ordinary_input_after_two_refusals=wire.count(b'ready\r')==1,
  parser_reply_after_refusal=b'\x1b[3;16R'in wire,
  no_prm_recovery_files=not any((capture/n).exists()for n in ('PCPSTG.$$$','PCPBAK.$$$')),
  module_fixture_unchanged=not(product/leaf).exists()if data is None else(product/leaf).read_bytes()==data)
 report=dict(passed=all(checks.values()),fault=a.fault,module=a.module,checks=checks,parent_sha256=sha(binary),
  expected_overlay_sha256=m[field]['sha256'],fixture_sha256=sha(product/leaf)if data is not None else None,
  observer_sha256=sha(out/'LOFAULT.COM'),sources={n:sha(ROOT/n)for n in ('standalone/test_line_port_overlay_fault_dos.py','standalone/path_dialog_watch.asm','standalone/test_connection_dos.py')},
  limitations=['DOS8086/synthetic peer; two refusals then ordinary input/parser service. No injected close fault, physical media fault or adversarial authentication claim.'])
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
 print(a.fault,{k:v for k,v in checks.items()if not v});assert report['passed']


if __name__=='__main__':main()
