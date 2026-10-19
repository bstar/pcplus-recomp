"""Synthetic-only tests. These fixtures are not complete startup configurations."""
import random
import struct
import unittest
from prm import IMAGE_SIZE,LegacyPrm201,SerialSettings
class PrmTests(unittest.TestCase):
 def test_opaque_roundtrip_and_no_implicit_validation(self):
  rng=random.Random(201)
  for _ in range(64):
   data=bytes(rng.randrange(256) for _ in range(IMAGE_SIZE))
   self.assertEqual(LegacyPrm201(data).to_bytes(),data)
 def test_only_serial_prefix_changes(self):
  original=bytes((i*17+3)%256 for i in range(IMAGE_SIZE));prm=LegacyPrm201(original)
  updated=prm.with_serial(SerialSettings(7,8,2,1,8))
  self.assertEqual(updated.to_bytes()[:10],struct.pack('<5H',7,8,2,1,8))
  self.assertEqual(updated.to_bytes()[10:],original[10:]);self.assertEqual(prm.to_bytes(),original)
  self.assertEqual(updated.serial.baud,115200);self.assertEqual(updated.serial.parity,'E')
 def test_serial_ui_range_and_no_mutation_on_error(self):
  for values in [(8,1,0,1,8),(0,9,0,1,8),(0,1,5,1,8),(0,1,0,0,8),(0,1,0,1,6)]:
   with self.assertRaises(ValueError):LegacyPrm201(bytes(IMAGE_SIZE)).with_serial(SerialSettings(*values))
  for n in range(9):self.assertEqual(SerialSettings(0,n,0,1,8).baud,[300,1200,2400,4800,9600,19200,38400,57600,115200][n])
 def test_exact_length_and_snapshot(self):
  for size in [0,10,IMAGE_SIZE-1,IMAGE_SIZE+1]:
   with self.assertRaises(ValueError):LegacyPrm201(bytes(size))
  data=bytearray(IMAGE_SIZE);prm=LegacyPrm201(data);data[0]=255;self.assertEqual(prm.word('port_index'),0)
 def test_translation_selection_location_and_opaque_neighbors(self):
  data=bytes((i*29+7)&255 for i in range(IMAGE_SIZE));prm=LegacyPrm201(data)
  for mode in (0,1,2,65535):
   output=prm.with_word('translation_mode',mode)
   self.assertEqual(output.word('translation_mode'),mode)
   self.assertEqual(output.to_bytes()[:0x1e0],data[:0x1e0])
   self.assertEqual(output.to_bytes()[0x1e0:0x1e2],struct.pack('<H',mode))
   self.assertEqual(output.to_bytes()[0x1e2:],data[0x1e2:])
 def test_clipboard_word_location_and_lossless_opaque_neighbors(self):
  data=bytes((i*31+11)&255 for i in range(IMAGE_SIZE));prm=LegacyPrm201(data)
  # The lossless codec also represents malformed raw words. Application
  # validation separately rejects values above255 without altering the image.
  for value in (*range(256),256,65535):
   output=prm.with_word('clipboard_separator',value).to_bytes()
   self.assertEqual(output[:0x4ea],data[:0x4ea])
   self.assertEqual(output[0x4ea:0x4ec],struct.pack('<H',value))
   self.assertEqual(output[0x4ec:],data[0x4ec:])
   self.assertEqual(LegacyPrm201(output).word('clipboard_separator'),value)
  self.assertEqual(prm.to_bytes(),data)
 def test_transfer_locations_and_opaque_tail_preservation(self):
  data=bytes((i*37+5)&255 for i in range(IMAGE_SIZE));prm=LegacyPrm201(data)
  for value in (0,1,2,255,256,65535):
   result=prm.with_word('auto_download',value)
   self.assertEqual(result.word('auto_download'),value)
   self.assertEqual(result.to_bytes()[:0x42c],data[:0x42c])
   self.assertEqual(result.to_bytes()[0x42e:],data[0x42e:])
  for value in (b'',b'C:\\GAMES',b'A'*63,b'\xff'):
   result=prm.with_download_path_bytes(value)
   self.assertEqual(result.download_path_bytes(),value)
   expected=bytearray(data);expected[0x31c:0x31c+len(value)+1]=value+b'\0'
   self.assertEqual(result.to_bytes(),bytes(expected))
  for value in (b'A'*64,b'A\0B'):
   with self.assertRaises(ValueError):prm.with_download_path_bytes(value)
  malformed=bytearray(data);malformed[0x31c:0x35c]=b'X'*64
  with self.assertRaises(ValueError):LegacyPrm201(malformed).download_path_bytes()
  self.assertEqual(prm.to_bytes(),data)
 def test_verified_word_and_port_array_locations(self):
  data=bytearray(IMAGE_SIZE)
  struct.pack_into('<H',data,0x194,6);struct.pack_into('<H',data,0x1ae,0x17)
  for i in range(8):
   struct.pack_into('<H',data,0x174+i*2,0x3f8+i*8)
   struct.pack_into('<H',data,0x184+i*2,3+i)
  prm=LegacyPrm201(data);self.assertEqual(prm.word('terminal_id'),6);self.assertEqual(prm.word('normal_attribute'),0x17)
  for i in range(8):self.assertEqual(prm.port_io_base(i),0x3f8+i*8);self.assertEqual(prm.port_irq(i),3+i)
  changed=prm.with_word('normal_attribute',7);self.assertEqual(changed.to_bytes()[0x1ae:0x1b0],b'\x07\0')
  for bad in [-1,8,65535]:
   with self.assertRaises(ValueError):prm.port_irq(bad)
if __name__=='__main__':unittest.main()
