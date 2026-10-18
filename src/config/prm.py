"""Partial, lossless codec for the proved PCPlus 2.01 1264-byte memory image.

There is no proved format signature/version field. Matching the length does not
identify a file. No file IO or defaults copied from a user's installation occur
here. Unknown bytes remain opaque and are preserved exactly.
"""
from dataclasses import dataclass
import struct

IMAGE_SIZE=0x4f0
ORIGINAL_DS_BASE=0x1b84
BAUD_RATES=(300,1200,2400,4800,9600,19200,38400,57600,115200)
PARITIES=('N','O','E','M','S')
# Offsets proved by memory-image IO plus recovered consumer instructions.
WORD_FIELDS={
 'port_index':0,'baud_index':2,'parity_index':4,'stop_bits':6,'data_bits':8,
 'terminal_id':0x1d18-ORIGINAL_DS_BASE,
 'autowrap':0x1d20-ORIGINAL_DS_BASE,
 'scroll_enabled':0x1d22-ORIGINAL_DS_BASE,
 'normal_attribute':0x1d32-ORIGINAL_DS_BASE,
 'bold_attribute':0x1d34-ORIGINAL_DS_BASE,
 'preset_attribute':0x1d36-ORIGINAL_DS_BASE,
 'reverse_attribute':0x1d38-ORIGINAL_DS_BASE,
 'underline_attribute':0x1d3a-ORIGINAL_DS_BASE,
 'current_attribute':0x1f70-ORIGINAL_DS_BASE,
}

@dataclass(frozen=True)
class SerialSettings:
 port_index:int
 baud_index:int
 parity_index:int
 stop_bits:int
 data_bits:int

 def validate(self):
  """Enforce the settings actually selectable by the recovered line/port UI."""
  for name,low,high in [('port_index',0,7),('baud_index',0,8),('parity_index',0,4),('stop_bits',1,2),('data_bits',7,8)]:
   value=getattr(self,name)
   if type(value) is not int or not low<=value<=high:raise ValueError(f'{name} outside supported UI range {low}..{high}')

 @property
 def baud(self):
  self.validate();return BAUD_RATES[self.baud_index]

 @property
 def parity(self):
  self.validate();return PARITIES[self.parity_index]

@dataclass(frozen=True)
class LegacyPrm201:
 _image:bytes

 def __post_init__(self):
  object.__setattr__(self,'_image',bytes(self._image))
  if len(self._image)!=IMAGE_SIZE:raise ValueError(f'Expected exactly {IMAGE_SIZE} bytes; version/type identification is external')

 def to_bytes(self):return self._image

 def word(self,name):return struct.unpack_from('<H',self._image,WORD_FIELDS[name])[0]

 def with_word(self,name,value):
  """Edit a proved word location; semantic validation beyond serial is unresolved."""
  if type(value) is not int or not 0<=value<=65535:raise ValueError('Expected unsigned 16-bit integer')
  output=bytearray(self._image);struct.pack_into('<H',output,WORD_FIELDS[name],value)
  return LegacyPrm201(output)

 @property
 def serial(self):return SerialSettings(*(self.word(name) for name in ('port_index','baud_index','parity_index','stop_bits','data_bits')))

 def with_serial(self,settings):
  settings.validate();output=bytearray(self._image)
  struct.pack_into('<5H',output,0,settings.port_index,settings.baud_index,settings.parity_index,settings.stop_bits,settings.data_bits)
  return LegacyPrm201(output)

 def port_io_base(self,index):
  if type(index) is not int or not 0<=index<8:raise ValueError('Expected port index 0..7')
  return struct.unpack_from('<H',self._image,0x1cf8-ORIGINAL_DS_BASE+index*2)[0]

 def port_irq(self,index):
  if type(index) is not int or not 0<=index<8:raise ValueError('Expected port index 0..7')
  return struct.unpack_from('<H',self._image,0x1d08-ORIGINAL_DS_BASE+index*2)[0]
