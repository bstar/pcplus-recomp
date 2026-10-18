#!/usr/bin/env python3
"""Replay actual linked attribute instructions with independent expected-state vectors."""
from pathlib import Path
import json,hashlib
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1]
BINARY=ROOT/'build/attributes/ATTRIB.EXE'
class Attributes(DosImage):
 def __init__(self):super().__init__(BINARY,ROOT/'build/attributes/attributes.map')
 def check(self,current,**kwargs):
  assert self.get('attributes_current')==current,(hex(self.get('attributes_current')),hex(current))
  for name,value in kwargs.items():assert self.get('attributes_'+name,1 if name=='reverse_active' else 2)==value

def run():
 cases=[]
 def check(name,operation):
  operation();cases.append({'case':name,'passed':True});print(name,'passed',flush=True)
 def normal():
  a=Attributes();a.put('attributes_normal_value',0x23);a.put('attributes_bold_active',1);a.put('attributes_blink_active',1);a.put('attributes_reverse_active',1,1)
  a.call('attributes_normal');a.check(0x23,bold_active=0,blink_active=0,reverse_active=0)
  a.put('attributes_monochrome',1);a.call('attributes_normal');a.check(7)
  a.put('attributes_normal_value',0x34);a.call('attributes_reset');a.check(0x34)
 check('normal-reset-and-monochrome-override',normal)
 def presets():
  a=Attributes();a.put('attributes_preset_value',0x27);a.call('attributes_preset');a.check(0x27)
  a.put('attributes_underline_value',0x13);a.call('attributes_underline');a.check(0x13)
  a.put('attributes_monochrome',1);a.call('attributes_underline');a.check(1)
 check('configured-presets-and-underline',presets)
 def bold_blink():
  a=Attributes();a.put('attributes_color_mode',1);a.put('attributes_current',0x21);a.call('attributes_bold');a.check(0x29,bold_active=1)
  a.call('attributes_blink');a.check(0xa9,blink_active=1)
  a.put('attributes_color_mode',0);a.put('attributes_bold_value',0x16);a.call('attributes_bold');a.check(0x16,bold_active=1)
 check('bold-and-blink-in-color-and-preset-modes',bold_blink)
 def reverse():
  a=Attributes()
  for value in range(256):
   a.put('attributes_current',value);a.put('attributes_reverse_active',0,1);a.put('attributes_color_mode',1);a.put('attributes_monochrome',0)
   a.call('attributes_reverse');expected=((value & 7)<<4)|((value>>4)&7)|(value&0x88);a.check(expected,reverse_active=1)
   a.call('attributes_reverse');a.check(expected,reverse_active=1)
  a.put('attributes_current',0x8f);a.put('attributes_reverse_active',0,1);a.put('attributes_monochrome',1);a.call('attributes_reverse');a.check(0xf8)
  a.put('attributes_color_mode',0);a.put('attributes_monochrome',0);a.put('attributes_current',0x8f);a.put('attributes_reverse_value',0x21);a.call('attributes_reverse');a.check(0xa9)
 check('all-256-reverse-values-and-repeat-latch',reverse)
 def transform():
  a=Attributes()
  for value in range(256):
   a.put('attributes_normal_value',value);a.call('attributes_default_transform')
   # Original performs signed shift after setting AH's low nibble, then AND.
   expected=((value|0xf00)>>4)&(value|0xf)
   a.check(expected)
 check('default-nibble-transform-all-byte-values',transform)
 result={'passed':True,'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'cases':cases,'scope':'Actual linked recovered helpers in Unicorn; representative host state, no original binary.'}
 (ROOT/'build/attributes/checks.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':run()
