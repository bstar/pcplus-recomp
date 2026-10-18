"""Lossless codecs for externally identified PCPlus2.01 KBD/KEY files.

Byte sizes are not version signatures. Opaque strings/kinds round-trip without
normalization. Strict total sizes are maintained validation: original loaders
ignore fread/close errors and do not establish EOF. No installed defaults/data.
"""
from dataclasses import dataclass
import struct

KBD_PROFILES=33
KBD_SLOTS=79
KBD_SLOT_SIZE=12
KBD_PROFILE_SIZE=KBD_SLOTS*KBD_SLOT_SIZE
KBD_SIZE=KBD_PROFILES*KBD_PROFILE_SIZE
KEY_SLOTS=10
KEY_SLOT_SIZE=54
KEY_TEXT_SIZE=52
KEY_SIZE=KEY_SLOTS*KEY_SLOT_SIZE
KEY_KINDS=('ASPECT','PROGRAM','HOOK','TEXT')

def _index(value,count):
 if type(value) is not int or not 0<=value<count:raise ValueError(f'Expected index0..{count-1}')
 return value

def _string(region):
 if b'\0' not in region:raise ValueError('Unterminated field; raw storage remains preserved')
 return region.split(b'\0',1)[0]

def _edit(raw,offset,capacity,value):
 value=bytes(value)
 if b'\0' in value or len(value)>=capacity:raise ValueError(f'Expected at most{capacity-1} non-NUL storage bytes')
 output=bytearray(raw);output[offset:offset+len(value)+1]=value+b'\0'
 return bytes(output)

@dataclass(frozen=True)
class LegacyKbd201:
 _image:bytes

 def __post_init__(self):
  object.__setattr__(self,'_image',bytes(self._image))
  if not self._image or len(self._image)%KBD_PROFILE_SIZE:raise ValueError('Expected a positive multiple of948 bytes; version/type identification is external')

 @classmethod
 def blank(cls,profiles=KBD_PROFILES):
  """Synthetic all-empty fixture, not a historical profile-default table."""
  if type(profiles) is not int or profiles<1:raise ValueError('Expected a positive profile count')
  return cls(bytes(profiles*KBD_PROFILE_SIZE))

 def to_bytes(self):return self._image

 @property
 def profile_count(self):return len(self._image)//KBD_PROFILE_SIZE

 def _offset(self,profile,slot):
  return _index(profile,self.profile_count)*KBD_PROFILE_SIZE+_index(slot,KBD_SLOTS)*KBD_SLOT_SIZE

 def raw_binding(self,profile,slot):
  at=self._offset(profile,slot);return self._image[at:at+KBD_SLOT_SIZE]

 def binding(self,profile,slot):return _string(self.raw_binding(profile,slot))

 def wire_binding(self,profile,slot):
  """Recovered emitter0a62 translates storedFF to serialNUL; no caret grammar."""
  return self.binding(profile,slot).replace(b'\xff',b'\0')

 def with_binding(self,profile,slot,storage_bytes):
  return LegacyKbd201(_edit(self._image,self._offset(profile,slot),KBD_SLOT_SIZE,storage_bytes))

 def with_wire_binding(self,profile,slot,wire_bytes):
  wire_bytes=bytes(wire_bytes)
  if b'\xff' in wire_bytes:raise ValueError('Original emitter has no literal serialFF encoding in a KBD slot')
  return self.with_binding(profile,slot,wire_bytes.replace(b'\0',b'\xff'))

@dataclass(frozen=True)
class LegacyKey201:
 _image:bytes

 def __post_init__(self):
  object.__setattr__(self,'_image',bytes(self._image))
  if len(self._image)!=KEY_SIZE:raise ValueError(f'Expected exactly{KEY_SIZE} bytes; version/type identification is external')

 @classmethod
 def empty_text(cls):
  """Re-author e24a's TEXT/empty semantic defaults; deterministic zero tails."""
  return cls((struct.pack('<H',3)+bytes(KEY_TEXT_SIZE))*KEY_SLOTS)

 def to_bytes(self):return self._image

 def raw_record(self,slot):
  at=_index(slot,KEY_SLOTS)*KEY_SLOT_SIZE;return self._image[at:at+KEY_SLOT_SIZE]

 def kind(self,slot):return struct.unpack_from('<H',self.raw_record(slot))[0]

 def kind_name(self,slot):
  value=self.kind(slot)
  if value>=len(KEY_KINDS):raise ValueError('Unknown action kind; raw storage remains preserved')
  return KEY_KINDS[value]

 def text(self,slot):return _string(self.raw_record(slot)[2:])

 def with_definition(self,slot,kind,text):
  """Storage edit; original UI allows50 content bytes, storage can hold51.

  Unknown16-bit kinds remain representable for lossless import; callers must
  validate supported action semantics before executing them.
  """
  if type(kind) is not int or not 0<=kind<=65535:raise ValueError('Expected unsigned16-bit kind')
  at=_index(slot,KEY_SLOTS)*KEY_SLOT_SIZE
  output=bytearray(_edit(self._image,at+2,KEY_TEXT_SIZE,text));struct.pack_into('<H',output,at,kind)
  return LegacyKey201(output)
