import random,struct,unittest
from codec import LegacyKbd201,LegacyKey201,KBD_SIZE,KBD_PROFILE_SIZE,KEY_SIZE

class KeyFiles(unittest.TestCase):
 def test_lossless_arbitrary_storage_and_external_identification(self):
  rng=random.Random(201)
  for typ,size in [(LegacyKbd201,KBD_SIZE),(LegacyKey201,KEY_SIZE)]:
   raw=bytes(rng.randrange(256) for _ in range(size));self.assertEqual(typ(raw).to_bytes(),raw)
   for invalid in [raw[:-1],raw+b'X',b'']:
    with self.assertRaises(ValueError):typ(invalid)

 def test_profile_slot_offsets_and_opaque_tail(self):
  raw=bytes([0xa5])*KBD_SIZE;k=LegacyKbd201(raw)
  for profile in range(33):
   for slot in range(79):
    edited=k.with_binding(profile,slot,b'\x1b[A');at=profile*KBD_PROFILE_SIZE+slot*12
    self.assertEqual(edited.to_bytes(),raw[:at]+b'\x1b[A\0'+raw[at+4:]);self.assertEqual(edited.binding(profile,slot),b'\x1b[A')

 def test_kbd_wire_nul_is_ff_storage_caret_and_pause_literal(self):
  k=LegacyKbd201.blank().with_wire_binding(4,0,b'\0^A~\x1b[A')
  self.assertEqual(k.binding(4,0),b'\xff^A~\x1b[A');self.assertEqual(k.wire_binding(4,0),b'\0^A~\x1b[A')
  with self.assertRaises(ValueError):k.with_wire_binding(6,0,b'\xff')
  with self.assertRaises(ValueError):k.with_binding(0,0,b'X'*12)
  with self.assertRaises(ValueError):k.with_binding(0,0,b'X\0')

 def test_key_records_action_word_and_text_tail(self):
  raw=bytes([0xa5])*KEY_SIZE;k=LegacyKey201(raw)
  for slot in range(10):
   for kind in [0,1,2,3,65535]:
    edited=k.with_definition(slot,kind,b'mixedCase^M~');at=slot*54
    value=b'mixedCase^M~\0';want=raw[:at]+struct.pack('<H',kind)+value+raw[at+2+len(value):]
    self.assertEqual(edited.to_bytes(),want);self.assertEqual(edited.kind(slot),kind);self.assertEqual(edited.text(slot),b'mixedCase^M~')
  self.assertEqual(k.with_definition(0,3,b'X'*51).text(0),b'X'*51)
  with self.assertRaises(ValueError):k.with_definition(0,3,b'X'*52)

 def test_semantic_defaults_do_not_copy_opaque_original_data(self):
  k=LegacyKey201.empty_text()
  for slot in range(10):self.assertEqual((k.kind_name(slot),k.text(slot)),('TEXT',b''))
  self.assertEqual(LegacyKbd201.blank().to_bytes(),bytes(KBD_SIZE))
  self.assertEqual(LegacyKbd201.blank(34).profile_count,34)

 def test_malformed_slots_unknown_kinds_preserved_but_accessors_fail(self):
  k=LegacyKbd201(bytes([0xff])*KBD_SIZE)
  with self.assertRaises(ValueError):k.binding(0,0)
  q=LegacyKey201(bytes([0xff])*KEY_SIZE)
  with self.assertRaises(ValueError):q.text(0)
  with self.assertRaises(ValueError):q.kind_name(0)
  for obj,method,args in [(k,k.binding,(33,0)),(k,k.binding,(0,79)),(q,q.text,(10,)),(q,q.kind,(-1,))]:
   with self.assertRaises(ValueError):method(*args)

if __name__=='__main__':unittest.main()
