#!/usr/bin/env python3
"""Verify the local-control bank ABI and reject damaged, unexecuted images."""
import argparse,hashlib,json,struct
from pathlib import Path
from dos_image import DosImage
from terminal_memory import inspect_terminal_memory
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=False);mapping=a.terminal.parent/'terminal.map'
layout=inspect_terminal_memory(a.terminal,mapping);assert layout['local_controls_bridge_pairs_verified']==4
m=DosImage(a.terminal,mapping);header=struct.unpack_from('<14H',m.image);start=header[4]*16;cases=[]
for name in ('terminal_control_clear_far','terminal_control_reset_far','terminal_control_duplex_far','terminal_control_defer_far','local_reset_1368','local_duplex_3316'):
 data=bytearray(m.image);offset=start+m.symbols[name]-m.base;data[offset]=0x90
 mutant=a.output/(name+'.bad');mutant.write_bytes(data)
 try:inspect_terminal_memory(mutant,mapping)
 except AssertionError:cases.append(dict(case=name,damaged_image_rejected=True))
 else:raise AssertionError('ABI verifier accepted damaged '+name)
r=dict(passed=True,terminal_sha256=hashlib.sha256(m.image).hexdigest(),cases=cases,bridge_pairs=4,native_entry_bytes=24,scope='Positive MZ/map bank/relocation ABI verification and rejection of six nonexecuted byte-mutated images. No runtime/hardware acceptance.')
(a.output/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS checked local-control ABI; six damaged images rejected')
