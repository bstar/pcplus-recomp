#!/usr/bin/env python3
"""Actual offline Alt-P COM/IRQ migration with independent UART peers/snapshots."""
import argparse,json,struct
from pathlib import Path
import test_setup_port_dos as lab
from build_context_help import ROOT,sha


def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--terminal',type=Path,required=True);p.add_argument('--editor',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 lab.OUT=out;lab.BINARY=a.terminal.resolve();lab.EDITOR=a.editor.resolve()
 original=lab.image
 def image():
  data=bytearray(original())
  for at,value in ((0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0),(0x3e4,7),(0x3e6,11),(0x3e8,113),(0x4e4,8),(0x4e6,4)):
   struct.pack_into('<H',data,at,value)
  return bytes(data)
 lab.image=image
 result=lab.run('offline-COM3-IRQ5-to-COM1-IRQ4',3,1,source_irq=5,target_irq=4,
  keyboard='enter p2200 a-p p1000 f1 p500 a-s p1500 p6000 r e a d y p1500 a-x',timeout=35)
 assert result['passed']
 folder=out/result['case']
 assert not any((folder/name).exists()for name in ('PCPSTG.$$$','PCPBAK.$$$'))
 sources={n:sha(ROOT/n)for n in ('standalone/test_line_port_move_dos.py','standalone/test_setup_port_dos.py','standalone/port_watch.asm','standalone/check_setup_model.py','standalone/test_terminal.py')}
 report=dict(passed=True,terminal_sha256=sha(lab.BINARY),result=result,sources=sources,
  captures={str(p.relative_to(out)):sha(p)for p in folder.iterdir()if p.suffix in ('.BIN','.bin','.json')},
  limitations=['Actual DOSBox-X8086 with three independent serial ports, source/target UART IRQs and four before/after register/vector/PIC snapshots.',
   'Timer observer temporarily toggles DLAB with interrupts masked to inspect divisors, restoring LCR; it does not read RBR or change product memory.',
   'PRMEDIT is copied by the reusable lab but is never invoked by this Alt-P keyboard sequence. No physical hardware/BBS acceptance.'])
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Alt-P offline COM3/IRQ5 -> COM1/IRQ4: real handoff, saved prefix and post-move traffic passed')


if __name__=='__main__':main()
