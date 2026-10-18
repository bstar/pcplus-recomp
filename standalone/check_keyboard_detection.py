#!/usr/bin/env python3
"""All256 BDA flags through source-built original detection and real near wrapper."""
import hashlib,json
from pathlib import Path
from dos_image import DosImage
from unicorn import UC_HOOK_INTR
from unicorn.x86_const import UC_X86_REG_BX,UC_X86_REG_CX,UC_X86_REG_DX,UC_X86_REG_ES
ROOT=Path(__file__).resolve().parents[1];BINARY=ROOT/'build/keyboard-detection/KBDMODE.EXE'
def forbidden(*args):raise AssertionError('No BIOS/DOS/port probe belongs in keyboard detection')
def main():
 for flag in range(256):
  d=DosImage(BINARY,BINARY.parent/'keyboard_detection.map');d.uc.hook_add(UC_HOOK_INTR,forbidden);d.uc.mem_write(0x496,bytes([flag]));d.put('keyboard_bios_mode',0xa5,1)
  for reg,value in [(UC_X86_REG_BX,0x1234),(UC_X86_REG_CX,0x2345),(UC_X86_REG_DX,0x3456),(UC_X86_REG_ES,0x4567)]:d.uc.reg_write(reg,value)
  expected=16 if flag&16 else 0;assert d.call('keyboard_detect_bios_mode')==expected and d.get('keyboard_bios_mode',1)==expected
  for reg,value in [(UC_X86_REG_BX,0x1234),(UC_X86_REG_CX,0x2345),(UC_X86_REG_DX,0x3456),(UC_X86_REG_ES,0x4567)]:assert d.uc.reg_read(reg)==value
  assert bytes(d.uc.mem_read(0x496,1))==bytes([flag]);d.call('keyboard_detection_test_standard');assert d.get('keyboard_bios_mode',1)==0
 result={'passed':True,'BDA_flag_cases':256,'standard_override_cases':256,'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'scope':'Actual recovered36byte original detector with preserved maintained wrapper; synthetic physicalBDA read-only memory. BIOS/DOS interrupts forbidden; manualSTANDARD originalarg0 covered.'};(BINARY.parent/'cpu-results.json').write_text(json.dumps(result,indent=2)+'\n');print('Passed512 original/wrapper BDA detection cases')
if __name__=='__main__':main()
