"""Synthetic tests for source-proved command fields; never reads real PRM files."""
import random,struct,unittest
from prm import LegacyPrm201,IMAGE_SIZE,ORIGINAL_DS_BASE,MODEM_COMMAND_FIELDS,expand_modem_command,modem_command_events
class ModemTests(unittest.TestCase):
 def test_each_field_and_opaque_tail_preservation(self):
  original=bytes((i*29+7)%256 for i in range(IMAGE_SIZE));prm=LegacyPrm201(original)
  for name,(offset,size) in MODEM_COMMAND_FIELDS.items():
   for value in (b'',b'AT^M',b'X'*(size-1)):
    changed=prm.with_modem_bytes(name,value);expect=bytearray(original);expect[offset:offset+len(value)+1]=value+b'\0'
    self.assertEqual(changed.to_bytes(),expect);self.assertEqual(changed.modem_bytes(name),value)
   with self.assertRaises(ValueError):prm.with_modem_bytes(name,b'X'*size)
  self.assertEqual(prm.to_bytes(),original)
 def test_response_fields_store_expanded_bytes(self):
  prm=LegacyPrm201(bytes(IMAGE_SIZE))
  for i in range(11):
   value=bytes([i+1,255,128,32]);changed=prm.with_modem_bytes('response',value,i)
   offset=0xc4+i*16;self.assertEqual(changed.to_bytes()[offset:offset+5],value+b'\0')
   self.assertEqual(changed.modem_bytes('response',i),value)
  for i in (-1,11,True):
   with self.assertRaises(ValueError):prm.modem_bytes('response',i)
  with self.assertRaises(ValueError):prm.with_modem_bytes('response',b'X'*16,0)
 def test_malformed_images_remain_lossless(self):
  image=bytes([255])*IMAGE_SIZE;prm=LegacyPrm201(image)
  with self.assertRaises(ValueError):prm.modem_bytes('initialization')
  with self.assertRaises(ValueError):prm.with_modem_bytes('hangup',b'A\0B')
  self.assertEqual(prm.to_bytes(),image)
 def test_byte_and_word_locations(self):
  prm=LegacyPrm201(bytes(IMAGE_SIZE))
  changed=prm.with_byte('dial_abort_character',13).with_byte('command_pause_character',126).with_word('dial_timeout_seconds',60).with_word('redial_pause_seconds',15).with_word('command_character_delay_units',30)
  changed=changed.with_word('software_flow',1).with_word('hardware_flow',1)
  self.assertEqual(changed.to_bytes()[0x198:0x19c],b'\x01\0\x01\0')
  image=changed.to_bytes();self.assertEqual(image[0x12],13);self.assertEqual(image[0x1e2],126)
  self.assertEqual(struct.unpack_from('<H',image,10)[0],60);self.assertEqual(struct.unpack_from('<H',image,12)[0],15)
  self.assertEqual(changed.word('command_character_delay_units'),30)
 def test_break_word_preserves_every_unrelated_byte(self):
  original=bytes((i*29+7)%256 for i in range(IMAGE_SIZE))
  prm=LegacyPrm201(original)
  for value in (0,1,54,55,56,350,65535):
   changed=prm.with_word('break_delay_units',value)
   expected=bytearray(original);struct.pack_into('<H',expected,0x1a4,value)
   self.assertEqual(changed.to_bytes(),expected)
   self.assertEqual(changed.word('break_delay_units'),value)
  self.assertEqual(prm.to_bytes(),original)
 def test_caret_rules_and_rejections(self):
  self.assertEqual(expand_modem_command(b'AT^M^J^@^^^?'),b'AT\r\n\xff^?')
  self.assertEqual(expand_modem_command(b'^^'),b'\x1e')
  self.assertEqual(expand_modem_command(b'^^^'),b'^')
  for value in range(1,256):
   if value==94:continue
   self.assertEqual(expand_modem_command(b'^'+bytes([value])),bytes([255 if value==64 else value&31]))
  for value in (b'^',b'x^',b'A\0B',b'A'*129):
   with self.assertRaises(ValueError):expand_modem_command(value)
 def test_sender_plan_priority_and_delay_units(self):
  self.assertEqual(modem_command_events(b'~A^@^M',126,30),(('pause_bios_tick_changes',10),('transmit',65),('character_delay_units',30),('transmit',0),('transmit',13),('character_delay_units',30)))
  self.assertEqual(modem_command_events(b'^@',255,0),(('pause_bios_tick_changes',10),))
  # Non-@ caret controls can expand to0; original C-string sender stops there.
  self.assertEqual(modem_command_events(b'A^`B',126,0),(('transmit',65),('character_delay_units',0)))
if __name__=='__main__':unittest.main()
